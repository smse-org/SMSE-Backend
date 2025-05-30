"""
File storage service for handling all file operations in the SMSE backend.

This module provides a centralized interface for file operations including:
- File uploads and downloads
- Directory management
- File cleanup
- Path resolution and validation
- User file management
"""

import os
import shutil
import uuid
from datetime import datetime, timedelta
from typing import Optional, Tuple, List
from werkzeug.datastructures import FileStorage
from werkzeug.utils import secure_filename
from flask import current_app


class FileStorageService:
    """Centralized file storage service for the SMSE backend."""

    def __init__(self):
        """Initialize the file storage service."""
        self._upload_folder = None

    @property
    def upload_folder(self) -> str:
        """Get the upload folder path from Flask app config."""
        if self._upload_folder is None:
            self._upload_folder = current_app.config["UPLOAD_FOLDER"]
        return self._upload_folder

    def get_full_path(self, relative_path: str) -> str:
        """
        Convert a relative file path to an absolute path within the upload folder.

        Args:
            relative_path: Path relative to the upload folder

        Returns:
            Absolute path to the file
        """
        return os.path.abspath(os.path.join(self.upload_folder, relative_path))

    def ensure_directory_exists(self, directory_path: str) -> None:
        """
        Ensure a directory exists, creating it if necessary.

        Args:
            directory_path: Path to the directory to create
        """
        os.makedirs(directory_path, exist_ok=True)

    def generate_unique_filename(self, original_filename: str, prefix: str = "") -> str:
        """
        Generate a unique filename based on the original filename.

        Args:
            original_filename: Original name of the file
            prefix: Optional prefix to add to the filename

        Returns:
            Unique filename with UUID prefix
        """
        secure_name = secure_filename(original_filename)
        uuid_prefix = uuid.uuid4().hex

        if prefix:
            return f"{uuid_prefix}_{prefix}_{secure_name}"
        return f"{uuid_prefix}_{secure_name}"

    def get_file_size_info(self, file: FileStorage) -> Tuple[int, float]:
        """
        Get file size information from an uploaded file.

        Args:
            file: Uploaded file object

        Returns:
            Tuple of (size_in_bytes, size_in_kb)
        """
        file_stream = file.stream
        file_stream.seek(0, os.SEEK_END)
        size_bytes = file_stream.tell()
        file_stream.seek(0)  # Reset stream position
        size_kb = round(size_bytes / 1024, 2)
        return size_bytes, size_kb

    def save_uploaded_file(
        self,
        file: FileStorage,
        user_id: int,
        subdirectory: Optional[str] = None,
        filename_prefix: str = "",
    ) -> Tuple[str, float]:
        """
        Save an uploaded file to the user's directory.

        Args:
            file: Uploaded file object
            user_id: ID of the user uploading the file
            subdirectory: Optional subdirectory within user folder
            filename_prefix: Optional prefix for the filename

        Returns:
            Tuple of (relative_file_path, file_size_kb)
        """
        # Generate unique filename
        unique_filename = self.generate_unique_filename(file.filename, filename_prefix)

        # Build relative path
        if subdirectory:
            relative_path = os.path.join(str(user_id), subdirectory, unique_filename)
        else:
            relative_path = os.path.join(str(user_id), unique_filename)

        # Get full path and ensure directory exists
        full_path = self.get_full_path(relative_path)
        self.ensure_directory_exists(os.path.dirname(full_path))

        # Get file size before saving
        _, size_kb = self.get_file_size_info(file)

        # Save the file
        print(full_path)
        file.save(full_path)

        return relative_path, size_kb

    def save_query_file(self, file: FileStorage, user_id: int) -> Tuple[str, str]:
        """
        Save a temporary query file for search operations.

        Args:
            file: Uploaded query file
            user_id: ID of the user performing the search

        Returns:
            Tuple of (relative_file_path, full_file_path)
        """
        relative_path, _ = self.save_uploaded_file(
            file, user_id, subdirectory="queries", filename_prefix="query"
        )
        full_path = self.get_full_path(relative_path)
        return relative_path, full_path

    def delete_file(self, relative_path: str) -> bool:
        """
        Delete a file given its relative path.

        Args:
            relative_path: Path relative to the upload folder

        Returns:
            True if file was deleted successfully, False otherwise
        """
        try:
            full_path = self.get_full_path(relative_path)
            if os.path.exists(full_path):
                os.remove(full_path)
                return True
            return False
        except Exception as e:
            current_app.logger.error(f"Error deleting file {relative_path}: {str(e)}")
            return False

    def file_exists(self, relative_path: str) -> bool:
        """
        Check if a file exists.

        Args:
            relative_path: Path relative to the upload folder

        Returns:
            True if file exists, False otherwise
        """
        full_path = self.get_full_path(relative_path)
        return os.path.exists(full_path)

    def create_user_directory(self, user_id: int) -> str:
        """
        Create a directory for a new user.

        Args:
            user_id: ID of the user

        Returns:
            Path to the created user directory
        """
        user_dir_path = self.get_full_path(str(user_id))
        self.ensure_directory_exists(user_dir_path)
        return user_dir_path

    def delete_user_directory(self, user_id: int) -> bool:
        """
        Delete a user's entire directory and all its contents.

        Args:
            user_id: ID of the user

        Returns:
            True if directory was deleted successfully, False otherwise
        """
        try:
            user_dir_path = self.get_full_path(str(user_id))
            if os.path.exists(user_dir_path):
                shutil.rmtree(user_dir_path)
                return True
            return False
        except Exception as e:
            current_app.logger.error(
                f"Error deleting user directory {user_id}: {str(e)}"
            )
            return False

    def cleanup_temp_query_files(self, age_in_hours: int = 24) -> int:
        """
        Clean up temporary query files older than the specified age.

        Args:
            age_in_hours: Age threshold in hours. Files older than this will be deleted.

        Returns:
            Number of files deleted
        """
        try:
            queries_dir = self.get_full_path("queries")

            # If directory doesn't exist, nothing to clean up
            if not os.path.exists(queries_dir):
                return 0

            files_deleted = 0
            threshold_time = datetime.now() - timedelta(hours=age_in_hours)

            # Walk through all user directories in queries folder
            for user_dir in os.listdir(queries_dir):
                user_path = os.path.join(queries_dir, user_dir)

                # Skip if not a directory
                if not os.path.isdir(user_path):
                    continue

                # Process all files in user directory
                for filename in os.listdir(user_path):
                    file_path = os.path.join(user_path, filename)

                    # Skip if not a file
                    if not os.path.isfile(file_path):
                        continue

                    # Check file modification time
                    mod_time = datetime.fromtimestamp(os.path.getmtime(file_path))

                    # If file is older than threshold, delete it
                    if mod_time < threshold_time:
                        os.remove(file_path)
                        files_deleted += 1

                # Check if user directory is empty after cleanup
                if not os.listdir(user_path):
                    os.rmdir(user_path)

            return files_deleted

        except Exception as e:
            current_app.logger.error(f"Error during temp file cleanup: {str(e)}")
            return 0

    def get_directory_size(self, relative_path: str) -> int:
        """
        Calculate the total size of a directory in bytes.

        Args:
            relative_path: Path relative to the upload folder

        Returns:
            Total size in bytes
        """
        full_path = self.get_full_path(relative_path)
        total_size = 0

        try:
            for dirpath, dirnames, filenames in os.walk(full_path):
                for filename in filenames:
                    file_path = os.path.join(dirpath, filename)
                    if os.path.exists(file_path):
                        total_size += os.path.getsize(file_path)
        except Exception as e:
            current_app.logger.error(
                f"Error calculating directory size for {relative_path}: {str(e)}"
            )

        return total_size

    def list_user_files(
        self, user_id: int, subdirectory: Optional[str] = None
    ) -> List[str]:
        """
        List all files in a user's directory or subdirectory.

        Args:
            user_id: ID of the user
            subdirectory: Optional subdirectory to list

        Returns:
            List of relative file paths
        """
        try:
            if subdirectory:
                base_path = os.path.join(str(user_id), subdirectory)
            else:
                base_path = str(user_id)

            full_path = self.get_full_path(base_path)

            if not os.path.exists(full_path):
                return []

            files = []
            for item in os.listdir(full_path):
                item_path = os.path.join(full_path, item)
                if os.path.isfile(item_path):
                    relative_path = os.path.join(base_path, item)
                    files.append(relative_path)

            return files

        except Exception as e:
            current_app.logger.error(
                f"Error listing files for user {user_id}: {str(e)}"
            )
            return []

    def move_file(self, old_relative_path: str, new_relative_path: str) -> bool:
        """
        Move a file from one location to another.

        Args:
            old_relative_path: Current relative path of the file
            new_relative_path: New relative path for the file

        Returns:
            True if file was moved successfully, False otherwise
        """
        try:
            old_full_path = self.get_full_path(old_relative_path)
            new_full_path = self.get_full_path(new_relative_path)

            if not os.path.exists(old_full_path):
                return False

            # Ensure destination directory exists
            self.ensure_directory_exists(os.path.dirname(new_full_path))

            # Move the file
            shutil.move(old_full_path, new_full_path)
            return True

        except Exception as e:
            current_app.logger.error(
                f"Error moving file from {old_relative_path} to {new_relative_path}: {str(e)}"
            )
            return False

    def copy_file(self, source_relative_path: str, dest_relative_path: str) -> bool:
        """
        Copy a file from one location to another.

        Args:
            source_relative_path: Source relative path of the file
            dest_relative_path: Destination relative path for the file

        Returns:
            True if file was copied successfully, False otherwise
        """
        try:
            source_full_path = self.get_full_path(source_relative_path)
            dest_full_path = self.get_full_path(dest_relative_path)

            if not os.path.exists(source_full_path):
                return False

            # Ensure destination directory exists
            self.ensure_directory_exists(os.path.dirname(dest_full_path))

            # Copy the file
            shutil.copy2(source_full_path, dest_full_path)
            return True

        except Exception as e:
            current_app.logger.error(
                f"Error copying file from {source_relative_path} to {dest_relative_path}: {str(e)}"
            )
            return False

    def get_file_info(self, relative_path: str) -> Optional[dict]:
        """
        Get information about a file.

        Args:
            relative_path: Path relative to the upload folder

        Returns:
            Dictionary with file information or None if file doesn't exist
        """
        try:
            full_path = self.get_full_path(relative_path)

            if not os.path.exists(full_path):
                return None

            stat = os.stat(full_path)

            return {
                "path": relative_path,
                "full_path": full_path,
                "size_bytes": stat.st_size,
                "size_kb": round(stat.st_size / 1024, 2),
                "created_at": datetime.fromtimestamp(stat.st_ctime),
                "modified_at": datetime.fromtimestamp(stat.st_mtime),
                "is_file": os.path.isfile(full_path),
                "is_directory": os.path.isdir(full_path),
            }

        except Exception as e:
            current_app.logger.error(
                f"Error getting file info for {relative_path}: {str(e)}"
            )
            return None

    def get_first_directory(self, path):
        parts = path.lstrip(os.sep).split(os.sep)  # Remove leading slashes & split
        return parts[0] if parts else None  # Return first part if exists


# Create a singleton instance
file_storage = FileStorageService()
