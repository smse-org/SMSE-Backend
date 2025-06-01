"""
Thumbnail service for generating and managing image thumbnails.

This module provides functionality to generate thumbnails for image files
using Pillow (PIL). It supports various image formats and creates optimized
thumbnails for faster loading and reduced bandwidth usage.
"""

import os
import io
from typing import Optional, Tuple
from PIL import Image, ImageOps
from werkzeug.datastructures import FileStorage
from flask import current_app


class ThumbnailService:
    """Service for generating and managing image thumbnails."""

    # Default thumbnail dimensions (16:9 aspect ratio)
    DEFAULT_THUMBNAIL_SIZE = (320, 180)
    THUMBNAIL_QUALITY = 85
    THUMBNAIL_FORMAT = "JPEG"

    # Supported image formats for thumbnail generation
    SUPPORTED_FORMATS = {".jpg", ".jpeg", ".png", ".gif", ".webp", ".bmp", ".tiff"}

    def __init__(self, file_storage_service):
        """
        Initialize the thumbnail service.

        Args:
            file_storage_service: The file storage service instance
        """
        self.file_storage = file_storage_service

    def is_supported_file(self, file_path: str) -> bool:
        """
        Check if the file is a supported image format.

        Args:
            file_path (str): Path to the file

        Returns:
            bool: True if the file is a supported image format
        """
        _, ext = os.path.splitext(file_path)
        return ext.lower() in self.SUPPORTED_FORMATS

    def generate_thumbnail_path(self, original_path: str) -> str:
        """
        Generate the thumbnail path based on the original file path.
        Thumbnails are stored in a 'thumbnails' subdirectory within the user's folder.

        Args:
            original_path (str): Original file path

        Returns:
            str: Thumbnail file path
        """
        # Get directory and filename without extension
        directory = os.path.dirname(original_path)
        filename_without_ext = os.path.splitext(os.path.basename(original_path))[0]

        # Create thumbnail filename with _thumb suffix
        thumbnail_filename = f"{filename_without_ext}_thumb.jpg"

        return os.path.join(directory, "thumbnails", thumbnail_filename)

    def generate_thumbnail_from_file_storage(
        self, file: FileStorage, thumbnail_size: Tuple[int, int] = None
    ) -> Optional[bytes]:
        """
        Generate a thumbnail from a FileStorage object.

        Args:
            file (FileStorage): The uploaded file object
            thumbnail_size (Tuple[int, int], optional): Thumbnail dimensions

        Returns:
            Optional[bytes]: Thumbnail image bytes or None if generation failed
        """
        if thumbnail_size is None:
            thumbnail_size = self.DEFAULT_THUMBNAIL_SIZE

        try:
            # Read the file content
            file.seek(0)  # Reset file pointer
            image_bytes = file.read()
            file.seek(0)  # Reset again for other operations

            return self.generate_thumbnail_from_bytes(image_bytes, thumbnail_size)

        except Exception as e:
            current_app.logger.error(
                f"Failed to generate thumbnail from FileStorage: {e}"
            )
            return None

    def generate_thumbnail_from_bytes(
        self, image_bytes: bytes, thumbnail_size: Tuple[int, int] = None
    ) -> Optional[bytes]:
        """
        Generate a thumbnail from image bytes.

        Args:
            image_bytes (bytes): Raw image data
            thumbnail_size (Tuple[int, int], optional): Thumbnail dimensions

        Returns:
            Optional[bytes]: Thumbnail image bytes or None if generation failed
        """
        if thumbnail_size is None:
            thumbnail_size = self.DEFAULT_THUMBNAIL_SIZE

        try:
            # Open image from bytes
            image = Image.open(io.BytesIO(image_bytes))

            # Convert to RGB if necessary (for formats like PNG with transparency)
            if image.mode in ("RGBA", "LA", "P"):
                # Create a white background
                background = Image.new("RGB", image.size, (255, 255, 255))
                if image.mode == "P":
                    image = image.convert("RGBA")
                background.paste(
                    image, mask=image.split()[-1] if image.mode == "RGBA" else None
                )
                image = background
            elif image.mode != "RGB":
                image = image.convert("RGB")

            # Generate thumbnail using ImageOps.fit for better quality
            # This maintains aspect ratio and crops to exact size
            thumbnail = ImageOps.fit(image, thumbnail_size, Image.Resampling.LANCZOS)

            # Save thumbnail to bytes
            thumbnail_io = io.BytesIO()
            thumbnail.save(
                thumbnail_io,
                format=self.THUMBNAIL_FORMAT,
                quality=self.THUMBNAIL_QUALITY,
                optimize=True,
            )

            return thumbnail_io.getvalue()

        except Exception as e:
            current_app.logger.error(f"Failed to generate thumbnail from bytes: {e}")
            return None

    def generate_thumbnail_from_path(
        self, file_path: str, thumbnail_size: Tuple[int, int] = None
    ) -> Optional[bytes]:
        """
        Generate a thumbnail from a file path using the file storage service.

        Args:
            file_path (str): Path to the image file
            thumbnail_size (Tuple[int, int], optional): Thumbnail dimensions

        Returns:
            Optional[bytes]: Thumbnail image bytes or None if generation failed
        """
        try:
            # Download file content using file storage service
            image_bytes = self.file_storage.download_file(file_path)
            if image_bytes is None:
                current_app.logger.error(
                    f"Failed to download file for thumbnail: {file_path}"
                )
                return None

            return self.generate_thumbnail_from_bytes(image_bytes, thumbnail_size)

        except Exception as e:
            current_app.logger.error(
                f"Failed to generate thumbnail from path {file_path}: {e}"
            )
            return None

    def save_thumbnail(self, thumbnail_bytes: bytes, thumbnail_path: str) -> bool:
        """
        Save thumbnail bytes to storage.

        Args:
            thumbnail_bytes (bytes): Thumbnail image data
            thumbnail_path (str): Path where thumbnail should be saved

        Returns:
            bool: True if saved successfully, False otherwise
        """
        try:
            # For local storage, we need to save directly to file
            if hasattr(self.file_storage.backend, "_get_full_path"):
                # Local storage backend
                full_path = self.file_storage.backend._get_full_path(thumbnail_path)
                self.file_storage.backend._ensure_directory_exists(
                    os.path.dirname(full_path)
                )

                with open(full_path, "wb") as f:
                    f.write(thumbnail_bytes)
                return True
            else:
                # S3 storage backend
                thumbnail_file = io.BytesIO(thumbnail_bytes)
                # For S3, we can use the upload_fileobj method directly
                try:
                    self.file_storage.backend.s3_client.upload_fileobj(
                        thumbnail_file,
                        self.file_storage.backend.bucket_name,
                        thumbnail_path,
                    )
                    return True
                except Exception as e:
                    current_app.logger.error(f"Failed to upload thumbnail to S3: {e}")
                    return False

        except Exception as e:
            current_app.logger.error(
                f"Failed to save thumbnail to {thumbnail_path}: {e}"
            )
            return False

    def generate_and_save_thumbnail(
        self,
        file: FileStorage,
        original_path: str,
        thumbnail_size: Tuple[int, int] = None,
    ) -> Optional[str]:
        """
        Generate and save a thumbnail for an uploaded file.

        Args:
            file (FileStorage): The uploaded file object
            original_path (str): Path where the original file is stored
            thumbnail_size (Tuple[int, int], optional): Thumbnail dimensions

        Returns:
            Optional[str]: Thumbnail path if successful, None otherwise
        """
        if not self.is_supported_file(original_path):
            current_app.logger.error(
                f"Unsupported image format for thumbnail: {original_path}"
            )
            return None

        # Generate thumbnail path
        thumbnail_path = self.generate_thumbnail_path(original_path)

        # Generate thumbnail bytes
        thumbnail_bytes = self.generate_thumbnail_from_file_storage(
            file, thumbnail_size
        )
        if thumbnail_bytes is None:
            current_app.logger.error(
                f"Failed to generate thumbnail from file storage for {original_path}"
            )
            return None

        # Save thumbnail
        if self.save_thumbnail(thumbnail_bytes, thumbnail_path):
            return thumbnail_path
        else:
            current_app.logger.error(
                f"Failed to save thumbnail for {original_path} at {thumbnail_path}"
            )

        return None

    def generate_and_save_thumbnail_from_path(
        self,
        original_path: str,
        thumbnail_size: Tuple[int, int] = None,
    ) -> Optional[str]:
        """
        Generate and save a thumbnail for a file that's already stored.

        Args:
            original_path (str): Path where the original file is stored
            thumbnail_size (Tuple[int, int], optional): Thumbnail dimensions

        Returns:
            Optional[str]: Thumbnail path if successful, None otherwise
        """
        if not self.is_supported_file(original_path):
            return None

        # Generate thumbnail path
        thumbnail_path = self.generate_thumbnail_path(original_path)

        # Generate thumbnail bytes from the stored file
        thumbnail_bytes = self.generate_thumbnail_from_path(
            original_path, thumbnail_size
        )
        if thumbnail_bytes is None:
            return None

        # Save thumbnail
        if self.save_thumbnail(thumbnail_bytes, thumbnail_path):
            return thumbnail_path

        return None

    def delete_thumbnail(self, thumbnail_path: str) -> bool:
        """
        Delete a thumbnail file.

        Args:
            thumbnail_path (str): Path to the thumbnail file

        Returns:
            bool: True if deleted successfully, False otherwise
        """
        try:
            if self.file_storage.file_exists(thumbnail_path):
                return self.file_storage.delete_file(thumbnail_path)
            return True  # File doesn't exist, consider it "deleted"

        except Exception as e:
            current_app.logger.error(
                f"Failed to delete thumbnail {thumbnail_path}: {e}"
            )
            return False
