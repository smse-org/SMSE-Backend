"""
Centralized definition of file extensions and modality mapping.
This module provides consistent file extension handling throughout the application.
"""

import os

# Extensions allowed for upload - read from environment variable if available
env_extensions = os.getenv("ALLOWED_EXTENSIONS", "txt,jpg,jpeg,wav")
ALLOWED_EXTENSIONS = set(env_extensions.split(","))

# Mapping of file extensions to modalities
EXTENSION_TO_MODALITY = {
    # Images
    ".jpg": "image",
    ".jpeg": "image",
    ".png": "image",
    ".gif": "image",
    ".webp": "image",
    # Audio
    ".mp3": "audio",
    ".wav": "audio",
    ".ogg": "audio",
    ".flac": "audio",
    # Text
    ".txt": "text",
    ".md": "text",
    ".pdf": "text",
}


def get_modality_from_extension(file_path):
    """
    Determine the modality based on the file extension.

    Args:
        file_path (str): Path to the file

    Returns:
        str: The determined modality ("image", "audio", "text")
    """
    import os

    ext = os.path.splitext(file_path)[1].lower()
    return EXTENSION_TO_MODALITY.get(ext, None)


def is_allowed_file(filename):
    """
    Check if the file extension is allowed for upload.

    Args:
        filename (str): Name of the file to check

    Returns:
        bool: True if the file extension is allowed, False otherwise
    """
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS


def get_allowed_extensions():
    """
    Get the list of allowed file extensions.

    Returns:
        list: List of allowed file extensions
    """
    return list(ALLOWED_EXTENSIONS)
