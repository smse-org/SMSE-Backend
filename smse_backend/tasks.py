"""
This module contains Celery tasks for processing files with SMSE.
"""

import tempfile
import os
from pathlib import Path
from celery import shared_task

from smse.device import get_device
from smse.models import ImageBindModel
from smse.pipelines.audio import AudioConfig, AudioPipeline
from smse.pipelines.image import ImageConfig, ImagePipeline
from smse.pipelines.text import TextConfig, TextPipeline
from smse.types import Modality

from smse_backend.models import Content, Embedding, Model
from smse_backend import db
from smse_backend.services.file_storage import file_storage


# Global variables to store models and pipelines
_model = None
_image_pipeline = None
_audio_pipeline = None
_text_pipeline = None


def _initialize_model():
    """Initialize the SMSE model if it's not already initialized."""
    global _model, _image_pipeline, _audio_pipeline, _text_pipeline

    if _model is None:
        device = get_device()

        # Initialize ImageBind model
        _model = ImageBindModel(device=device)

        # Initialize image pipeline
        _image_pipeline = ImagePipeline(
            ImageConfig(
                target_size=(224, 224),
                center_crop=224,
                normalize=True,
                mean=(0.48145466, 0.4578275, 0.40821073),
                std=(0.26862954, 0.26130258, 0.27577711),
                device=device,
            )
        )

        # Initialize audio pipeline
        _audio_pipeline = AudioPipeline(
            AudioConfig(
                sampling_rate=16000,
                mono=True,
                normalize_audio=False,
                use_clips=True,
                apply_melspec=True,
                num_mel_bins=128,
                target_length=204,
                clip_duration=2.0,
                clips_per_audio=3,
                mean=-4.268,
                std=9.138,
                device=device,
            )
        )

        # Initialize text pipeline
        from imagebind.data import return_bpe_path  # type: ignore[import]
        from imagebind.models.multimodal_preprocessors import SimpleTokenizer  # type: ignore[import]

        _text_pipeline = TextPipeline(
            TextConfig(
                chunk_size=240,
                chunk_overlap=10,
                tokenizer=SimpleTokenizer(bpe_path=return_bpe_path()),
                device=device,
            )
        )


def _download_file_for_processing(file_path):
    """
    Download a file from storage to a temporary location for processing.

    Args:
        file_path (str): Storage path/key of the file

    Returns:
        str: Path to the temporary local file
    """
    from smse_backend.services.file_storage import S3StorageBackend

    # Check if we're using S3 storage
    if isinstance(file_storage.backend, S3StorageBackend):
        # For S3 storage, download the file to a temporary location
        file_info = file_storage.get_file_info(file_path)
        if not file_info:
            raise FileNotFoundError(f"File not found in storage: {file_path}")

        # Get file extension to preserve it in temp file
        file_extension = os.path.splitext(file_path)[1]

        # Create a temporary file with the same extension
        with tempfile.NamedTemporaryFile(
            delete=False, suffix=file_extension
        ) as temp_file:
            temp_path = temp_file.name

        # Download file from S3 to temporary location
        try:
            s3_client = file_storage.backend.s3_client
            bucket_name = file_storage.backend.bucket_name
            s3_client.download_file(bucket_name, file_path, temp_path)
            return temp_path
        except Exception as e:
            # Clean up temp file if download failed
            if os.path.exists(temp_path):
                os.unlink(temp_path)
            raise e
    else:
        # For local storage, return the full path directly
        return file_storage.get_full_path(file_path)


def _cleanup_temp_file(temp_path, original_path):
    """
    Clean up temporary file if it was created for S3 storage.

    Args:
        temp_path (str): Path to temporary file
        original_path (str): Original storage path
    """
    from smse_backend.services.file_storage import S3StorageBackend

    # Only clean up if we're using S3 storage and the paths are different
    if isinstance(
        file_storage.backend, S3StorageBackend
    ) and temp_path != file_storage.get_full_path(original_path):
        try:
            if os.path.exists(temp_path):
                os.unlink(temp_path)
        except Exception as e:
            # Log the error but don't fail the task
            print(f"Warning: Failed to clean up temporary file {temp_path}: {e}")


def _get_smse_modality_for_file(file_path):
    """
    Determine the modality based on the file extension.

    Args:
        file_path (str): Path to the file

    Returns:
        Modality: The determined modality
    """
    from smse_backend.utils.file_extensions import get_modality_from_extension

    modality_str = get_modality_from_extension(file_path)

    # Convert string modality to Modality enum
    if modality_str == "image":
        return Modality.IMAGE
    elif modality_str == "audio":
        return Modality.AUDIO
    else:
        return Modality.TEXT


def _process_file(file_path, modality):
    """
    Process a file based on its modality.

    Args:
        file_path (str): Storage path of the file
        modality (Modality): The modality of the file

    Returns:
        np.ndarray: The embedding vector
    """
    _initialize_model()

    # Download file to local temporary location if needed
    local_path = _download_file_for_processing(file_path)

    try:
        path = Path(local_path)

        if modality == Modality.IMAGE:
            processed_input = _image_pipeline([path])
        elif modality == Modality.AUDIO:
            processed_input = _audio_pipeline([path])
        elif modality == Modality.TEXT:
            processed_input = _text_pipeline([path])
        else:
            raise ValueError(f"Unsupported modality: {modality}")

        # Create inputs dictionary with only the relevant modality
        inputs = {modality: processed_input}

        # Get embeddings
        embeddings = _model.encode(inputs)

        # Return the first embedding vector
        return embeddings[modality][0].cpu().numpy()

    finally:
        # Clean up temporary file if it was created
        _cleanup_temp_file(local_path, file_path)


def _process_text(text_content):
    """
    Process raw text content and generate an embedding.

    Args:
        text_content (str): The text content to process

    Returns:
        np.ndarray: The embedding vector
    """
    _initialize_model()

    # Process the text directly
    processed_input = _text_pipeline.process([text_content])

    # Create inputs dictionary with only the TEXT modality
    inputs = {Modality.TEXT: processed_input}

    # Get embeddings
    embeddings = _model.encode(inputs)

    # Return the first embedding vector
    return embeddings[Modality.TEXT][0].cpu().numpy()


@shared_task(bind=True, name="process_file")
def process_file(self, file_path, content_id=None):
    """
    Celery task to process a file with SMSE and create an embedding.

    Args:
        file_path (str): Storage path/key of the file to process
        content_id (int, optional): ID of the content if it already exists

    Returns:
        dict: Task result information
    """
    try:
        # Determine the modality based on file extension
        modality = _get_smse_modality_for_file(file_path)

        # Process the file to get embedding vector
        embedding_vector = _process_file(file_path, modality)
        # Get user chosen model (using model ID 1 for now)
        try:
            model = db.session.get(Model, 1)
            if model is None:
                # If model doesn't exist, create a default model
                model = Model(
                    name="Default Model", description="Default model created by system"
                )
                db.session.add(model)
                db.session.commit()

            model_id = model.id
        except Exception as db_error:
            self.update_state(
                state="FAILURE",
                meta={
                    "exc_type": "DatabaseError",
                    "exc_message": f"Error accessing model: {str(db_error)}",
                    "status": "error",
                },
            )
            raise db_error

        # Create new embedding record
        new_embedding = Embedding(
            vector=embedding_vector,
            model_id=model_id,
            modality=modality.name.lower(),
        )
        db.session.add(new_embedding)

        try:
            if content_id:
                # Update existing content with new embedding
                content = db.session.get(Content, content_id)
                if content:
                    content.embedding = new_embedding

            db.session.commit()
        except Exception as db_error:
            db.session.rollback()
            self.update_state(
                state="FAILURE",
                meta={
                    "exc_type": "DatabaseError",
                    "exc_message": f"Error updating content with embedding: {str(db_error)}",
                    "status": "error",
                },
            )
            raise db_error
        return {
            "status": "success",
            "embedding_id": new_embedding.id,
            "content_id": content_id,
            "modality": modality.name,
        }

    except Exception as e:
        # If there was an error, update the task state
        self.update_state(
            state="FAILURE",
            meta={
                "exc_type": type(e).__name__,
                "exc_message": str(e),
                "status": "error",
                "message": str(e),
            },
        )
        # Re-raise the exception
        raise e


@shared_task(
    bind=True, name="process_query", priority=10
)  # Higher priority than content processing
def process_query(self, query_content, is_file=False, file_path=None):
    """
    Celery task to process a search query with high priority.
    Can handle both text queries and file-based queries.

    Args:
        query_content (str): The query text or file path
        is_file (bool): Whether the query is a file
        file_path (str, optional): Storage path of the file if is_file is True

    Returns:
        dict: Task result with the embedding vector
    """
    try:
        if is_file:
            # Determine the modality based on file extension
            modality = _get_smse_modality_for_file(file_path)
            # Process the file to get embedding vector (handles download automatically)
            embedding_vector = _process_file(file_path, modality)
            modality_str = modality.name.lower()  # Convert enum to string
        else:
            # Process the text directly
            embedding_vector = _process_text(query_content)
            modality_str = "text"  # Text queries always have text modality

        return {
            "status": "success",
            "embedding": embedding_vector.tolist(),  # Convert numpy array to list for JSON serialization
            "modality": modality_str,  # Include modality information
        }

    except Exception as e:
        # If there was an error, update the task state
        self.update_state(
            state="FAILURE",
            meta={
                "exc_type": type(e).__name__,
                "exc_message": str(e),
                "status": "error",
                "message": str(e),
            },
        )
        # Re-raise the exception
        raise e
