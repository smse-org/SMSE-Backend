"""
File storage service for handling all file operations in the SMSE backend.

This module provides a centralized interface for file operations including:
- File uploads and downloads
- Directory management
- File cleanup
- Path resolution and validation
- User file management
- Support for both local and S3-compatible storage
"""

import os
import shutil
import uuid
from abc import ABC, abstractmethod
from datetime import datetime, timedelta
from typing import Optional, Tuple, List, Union
from werkzeug.datastructures import FileStorage
from werkzeug.utils import secure_filename
from flask import current_app

try:
    import boto3
    from botocore.exceptions import ClientError

    HAS_BOTO3 = True
except ImportError:
    HAS_BOTO3 = False


class StorageBackend(ABC):
    """Abstract base class for storage backends."""

    @abstractmethod
    def save_file(self, file_obj: Union[FileStorage, str], key: str) -> bool:
        """Save a file to storage."""
        pass

    @abstractmethod
    def delete_file(self, key: str) -> bool:
        """Delete a file from storage."""
        pass

    @abstractmethod
    def file_exists(self, key: str) -> bool:
        """Check if a file exists in storage."""
        pass

    @abstractmethod
    def list_files(self, prefix: str) -> List[str]:
        """List files with a given prefix."""
        pass

    @abstractmethod
    def get_file_info(self, key: str) -> Optional[dict]:
        """Get file information."""
        pass

    @abstractmethod
    def copy_file(self, source_key: str, dest_key: str) -> bool:
        """Copy a file within storage."""
        pass

    @abstractmethod
    def move_file(self, old_key: str, new_key: str) -> bool:
        """Move a file within storage."""
        pass


class LocalStorageBackend(StorageBackend):
    """Local filesystem storage backend."""

    def __init__(self, base_path: str):
        self.base_path = base_path
        self._ensure_directory_exists(self.base_path)

    def _get_full_path(self, key: str) -> str:
        """Convert a storage key to a full local path."""
        return os.path.abspath(os.path.join(self.base_path, key))

    def _ensure_directory_exists(self, directory_path: str) -> None:
        """Ensure a directory exists, creating it if necessary."""
        os.makedirs(directory_path, exist_ok=True)

    def save_file(self, file_obj: Union[FileStorage, str], key: str) -> bool:
        """Save a file to local storage."""
        try:
            full_path = self._get_full_path(key)
            self._ensure_directory_exists(os.path.dirname(full_path))

            if isinstance(file_obj, FileStorage):
                file_obj.save(full_path)
            else:
                # file_obj is a path to an existing file
                shutil.copy2(file_obj, full_path)
            return True
        except Exception as e:
            current_app.logger.error(f"Error saving file {key}: {str(e)}")
            return False

    def delete_file(self, key: str) -> bool:
        """Delete a file from local storage."""
        try:
            full_path = self._get_full_path(key)
            if os.path.exists(full_path):
                if os.path.isfile(full_path):
                    os.remove(full_path)
                elif os.path.isdir(full_path):
                    shutil.rmtree(full_path)
                return True
            return False
        except Exception as e:
            current_app.logger.error(f"Error deleting file {key}: {str(e)}")
            return False

    def file_exists(self, key: str) -> bool:
        """Check if a file exists in local storage."""
        full_path = self._get_full_path(key)
        return os.path.exists(full_path)

    def list_files(self, prefix: str) -> List[str]:
        """List files with a given prefix in local storage."""
        try:
            full_prefix_path = self._get_full_path(prefix)
            files = []

            if os.path.exists(full_prefix_path):
                if os.path.isfile(full_prefix_path):
                    files.append(prefix)
                else:
                    for root, _, filenames in os.walk(full_prefix_path):
                        for filename in filenames:
                            full_file_path = os.path.join(root, filename)
                            relative_path = os.path.relpath(
                                full_file_path, self.base_path
                            )
                            files.append(relative_path.replace(os.sep, "/"))

            return files
        except Exception as e:
            current_app.logger.error(
                f"Error listing files with prefix {prefix}: {str(e)}"
            )
            return []

    def get_file_info(self, key: str) -> Optional[dict]:
        """Get file information from local storage."""
        try:
            full_path = self._get_full_path(key)
            if not os.path.exists(full_path):
                return None

            stat = os.stat(full_path)
            return {
                "key": key,
                "size": stat.st_size,
                "last_modified": datetime.fromtimestamp(stat.st_mtime),
                "created": datetime.fromtimestamp(stat.st_ctime),
            }
        except Exception as e:
            current_app.logger.error(f"Error getting file info for {key}: {str(e)}")
            return None

    def copy_file(self, source_key: str, dest_key: str) -> bool:
        """Copy a file within local storage."""
        try:
            source_path = self._get_full_path(source_key)
            dest_path = self._get_full_path(dest_key)

            if not os.path.exists(source_path):
                return False

            self._ensure_directory_exists(os.path.dirname(dest_path))
            shutil.copy2(source_path, dest_path)
            return True
        except Exception as e:
            current_app.logger.error(
                f"Error copying file from {source_key} to {dest_key}: {str(e)}"
            )
            return False

    def move_file(self, old_key: str, new_key: str) -> bool:
        """Move a file within local storage."""
        try:
            old_path = self._get_full_path(old_key)
            new_path = self._get_full_path(new_key)

            if not os.path.exists(old_path):
                return False

            self._ensure_directory_exists(os.path.dirname(new_path))
            shutil.move(old_path, new_path)
            return True
        except Exception as e:
            current_app.logger.error(
                f"Error moving file from {old_key} to {new_key}: {str(e)}"
            )
            return False


class S3StorageBackend(StorageBackend):
    """S3-compatible storage backend using boto3."""

    def __init__(
        self,
        bucket_name: str,
        endpoint_url: str,
        access_key: str,
        secret_key: str,
        region_name: str = "us-east-1",
        use_ssl: bool = True,
    ):
        if not HAS_BOTO3:
            raise ImportError("boto3 is required for S3 storage backend")

        self.bucket_name = bucket_name
        self.s3_client = boto3.client(
            "s3",
            endpoint_url=endpoint_url,
            aws_access_key_id=access_key,
            aws_secret_access_key=secret_key,
            region_name=region_name,
            use_ssl=use_ssl,
        )
        self._ensure_bucket_exists()

    def _ensure_bucket_exists(self) -> None:
        """Ensure the S3 bucket exists, create it if not."""
        try:
            self.s3_client.head_bucket(Bucket=self.bucket_name)
            current_app.logger.info(f"S3 bucket {self.bucket_name} already exists")
        except ClientError as e:
            error_code = e.response["Error"]["Code"]
            current_app.logger.info(f"Bucket check failed with error code: {error_code}")
            
            # Handle both 404 (NoSuchBucket) and 403 (Forbidden) as bucket doesn't exist
            # MinIO can return 403 when bucket doesn't exist depending on configuration
            if error_code in ["404", "NoSuchBucket", "403", "Forbidden"]:
                try:
                    current_app.logger.info(f"Attempting to create bucket: {self.bucket_name}")
                    
                    # Create bucket with proper configuration
                    region = getattr(self.s3_client._client_config, 'region_name', 'us-east-1')
                    if region == 'us-east-1':
                        # For us-east-1, don't specify location constraint
                        self.s3_client.create_bucket(Bucket=self.bucket_name)
                    else:
                        # For other regions, specify location constraint
                        self.s3_client.create_bucket(
                            Bucket=self.bucket_name,
                            CreateBucketConfiguration={
                                'LocationConstraint': region
                            }
                        )
                    
                    current_app.logger.info(f"Successfully created S3 bucket: {self.bucket_name}")
                    
                    # Verify bucket was created by trying to access it again
                    try:
                        self.s3_client.head_bucket(Bucket=self.bucket_name)
                        current_app.logger.info(f"Verified bucket {self.bucket_name} is accessible")
                    except ClientError as verify_error:
                        current_app.logger.warning(
                            f"Bucket created but verification failed: {str(verify_error)}"
                        )
                        
                except ClientError as create_error:
                    error_code = create_error.response["Error"]["Code"]
                    if error_code == "BucketAlreadyExists":
                        current_app.logger.info(f"Bucket {self.bucket_name} already exists (race condition)")
                    elif error_code == "BucketAlreadyOwnedByYou":
                        current_app.logger.info(f"Bucket {self.bucket_name} already owned by you")
                    else:
                        current_app.logger.error(
                            f"Error creating bucket {self.bucket_name}: {str(create_error)}"
                        )
                        raise
            else:
                current_app.logger.error(
                    f"Unexpected error accessing bucket {self.bucket_name}: {str(e)}"
                )
                raise

    def save_file(self, file_obj: Union[FileStorage, str], key: str) -> bool:
        """Save a file to S3 storage."""
        try:
            if isinstance(file_obj, FileStorage):
                self.s3_client.upload_fileobj(file_obj.stream, self.bucket_name, key)
            else:
                # file_obj is a path to an existing file
                self.s3_client.upload_file(file_obj, self.bucket_name, key)
            return True
        except Exception as e:
            current_app.logger.error(f"Error saving file {key} to S3: {str(e)}")
            return False

    def delete_file(self, key: str) -> bool:
        """Delete a file from S3 storage."""
        try:
            self.s3_client.delete_object(Bucket=self.bucket_name, Key=key)
            return True
        except Exception as e:
            current_app.logger.error(f"Error deleting file {key} from S3: {str(e)}")
            return False

    def file_exists(self, key: str) -> bool:
        """Check if a file exists in S3 storage."""
        try:
            self.s3_client.head_object(Bucket=self.bucket_name, Key=key)
            return True
        except ClientError:
            return False
        except Exception as e:
            current_app.logger.error(
                f"Error checking if file {key} exists in S3: {str(e)}"
            )
            return False

    def list_files(self, prefix: str) -> List[str]:
        """List files with a given prefix in S3 storage."""
        try:
            response = self.s3_client.list_objects_v2(
                Bucket=self.bucket_name, Prefix=prefix
            )

            files = []
            if "Contents" in response:
                files = [obj["Key"] for obj in response["Contents"]]

            return files
        except Exception as e:
            current_app.logger.error(
                f"Error listing files with prefix {prefix} in S3: {str(e)}"
            )
            return []

    def get_file_info(self, key: str) -> Optional[dict]:
        """Get file information from S3 storage."""
        try:
            response = self.s3_client.head_object(Bucket=self.bucket_name, Key=key)
            return {
                "key": key,
                "size": response["ContentLength"],
                "last_modified": response["LastModified"],
                "etag": response["ETag"].strip('"'),
            }
        except ClientError:
            return None
        except Exception as e:
            current_app.logger.error(
                f"Error getting file info for {key} from S3: {str(e)}"
            )
            return None

    def copy_file(self, source_key: str, dest_key: str) -> bool:
        """Copy a file within S3 storage."""
        try:
            copy_source = {"Bucket": self.bucket_name, "Key": source_key}
            self.s3_client.copy_object(
                CopySource=copy_source, Bucket=self.bucket_name, Key=dest_key
            )
            return True
        except Exception as e:
            current_app.logger.error(
                f"Error copying file from {source_key} to {dest_key} in S3: {str(e)}"
            )
            return False

    def move_file(self, old_key: str, new_key: str) -> bool:
        """Move a file within S3 storage."""
        try:
            # Copy the file to the new location
            if self.copy_file(old_key, new_key):
                # Delete the old file
                return self.delete_file(old_key)
            return False
        except Exception as e:
            current_app.logger.error(
                f"Error moving file from {old_key} to {new_key} in S3: {str(e)}"
            )
            return False


class FileStorageService:
    """Centralized file storage service for the SMSE backend."""

    def __init__(self):
        """Initialize the file storage service."""
        self._backend = None

    @property
    def backend(self) -> StorageBackend:
        """Get the storage backend instance."""
        if self._backend is None:
            storage_type = current_app.config.get("STORAGE_TYPE", "local")

            if storage_type == "local":
                upload_folder = current_app.config["UPLOAD_FOLDER"]
                self._backend = LocalStorageBackend(upload_folder)
            elif storage_type == "s3":
                self._backend = S3StorageBackend(
                    bucket_name=current_app.config["S3_BUCKET_NAME"],
                    endpoint_url=current_app.config["S3_ENDPOINT_URL"],
                    access_key=current_app.config["S3_ACCESS_KEY_ID"],
                    secret_key=current_app.config["S3_SECRET_KEY"],
                    region_name=current_app.config["S3_REGION_NAME"],
                    use_ssl=current_app.config["S3_USE_SSL"],
                )
            else:
                raise ValueError(f"Unsupported storage type: {storage_type}")

        return self._backend

    @property
    def upload_folder(self) -> str:
        """Get the upload folder path (for backward compatibility)."""
        return current_app.config["UPLOAD_FOLDER"]

    def get_full_path(self, relative_path: str) -> str:
        """
        Convert a relative file path to an absolute path within the upload folder.
        Note: This method is kept for backward compatibility with local storage.
        For S3 storage, this returns the key as-is.

        Args:
            relative_path: Path relative to the upload folder

        Returns:
            Absolute path to the file (local) or key (S3)
        """
        if isinstance(self.backend, LocalStorageBackend):
            return self.backend._get_full_path(relative_path)
        else:
            # For S3, return the key as-is
            return relative_path

    def ensure_directory_exists(self, directory_path: str) -> None:
        """
        Ensure a directory exists, creating it if necessary.
        Note: This is only relevant for local storage.

        Args:
            directory_path: Path to the directory to create
        """
        if isinstance(self.backend, LocalStorageBackend):
            self.backend._ensure_directory_exists(directory_path)
        # For S3, directories don't need to be explicitly created

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

        # Build relative path/key
        if subdirectory:
            relative_path = f"{user_id}/{subdirectory}/{unique_filename}"
        else:
            relative_path = f"{user_id}/{unique_filename}"

        # Get file size before saving
        _, size_kb = self.get_file_size_info(file)

        # Save the file using the backend
        success = self.backend.save_file(file, relative_path)
        if not success:
            raise RuntimeError(f"Failed to save file {relative_path}")

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
        return self.backend.delete_file(relative_path)

    def file_exists(self, relative_path: str) -> bool:
        """
        Check if a file exists.

        Args:
            relative_path: Path relative to the upload folder

        Returns:
            True if file exists, False otherwise
        """
        return self.backend.file_exists(relative_path)

    def create_user_directory(self, user_id: int) -> str:
        """
        Create a directory for a new user.
        Note: For S3, this is a no-op as directories are created implicitly.

        Args:
            user_id: ID of the user

        Returns:
            Path to the created user directory
        """
        user_dir_path = str(user_id)
        if isinstance(self.backend, LocalStorageBackend):
            full_path = self.backend._get_full_path(user_dir_path)
            self.backend._ensure_directory_exists(full_path)
            return full_path
        else:
            # For S3, return the user prefix
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
            user_prefix = f"{user_id}/"

            # List all files with the user prefix
            files = self.backend.list_files(user_prefix)

            # Delete all files
            success = True
            for file_key in files:
                if not self.backend.delete_file(file_key):
                    success = False
                    current_app.logger.error(f"Failed to delete file: {file_key}")

            # For local storage, also try to remove the directory
            if isinstance(self.backend, LocalStorageBackend):
                try:
                    user_dir_path = self.backend._get_full_path(str(user_id))
                    if os.path.exists(user_dir_path):
                        shutil.rmtree(user_dir_path)
                except Exception as e:
                    current_app.logger.error(
                        f"Error removing user directory {user_id}: {str(e)}"
                    )
                    success = False

            return success
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
            files_deleted = 0
            threshold_time = datetime.now() - timedelta(hours=age_in_hours)

            # Get all query files
            query_files = self.backend.list_files("queries/")

            for file_key in query_files:
                file_info = self.backend.get_file_info(file_key)
                if file_info and file_info.get("last_modified"):
                    file_time = file_info["last_modified"]
                    # Handle timezone-aware datetime from S3
                    if file_time.tzinfo is not None:
                        file_time = file_time.replace(tzinfo=None)

                    if file_time < threshold_time:
                        if self.backend.delete_file(file_key):
                            files_deleted += 1

            return files_deleted

        except Exception as e:
            current_app.logger.error(f"Error cleaning up temp query files: {str(e)}")
            return 0

    def get_directory_size(self, relative_path: str) -> int:
        """
        Calculate the total size of a directory in bytes.

        Args:
            relative_path: Path relative to the upload folder

        Returns:
            Total size in bytes
        """
        try:
            total_size = 0
            prefix = relative_path.rstrip("/") + "/"

            files = self.backend.list_files(prefix)
            for file_key in files:
                file_info = self.backend.get_file_info(file_key)
                if file_info:
                    total_size += file_info.get("size", 0)

            return total_size
        except Exception as e:
            current_app.logger.error(
                f"Error calculating directory size for {relative_path}: {str(e)}"
            )
            return 0

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
                prefix = f"{user_id}/{subdirectory}/"
            else:
                prefix = f"{user_id}/"

            return self.backend.list_files(prefix)
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
        return self.backend.move_file(old_relative_path, new_relative_path)

    def copy_file(self, source_relative_path: str, dest_relative_path: str) -> bool:
        """
        Copy a file from one location to another.

        Args:
            source_relative_path: Source relative path of the file
            dest_relative_path: Destination relative path for the file

        Returns:
            True if file was copied successfully, False otherwise
        """
        return self.backend.copy_file(source_relative_path, dest_relative_path)

    def get_file_info(self, relative_path: str) -> Optional[dict]:
        """
        Get information about a file.

        Args:
            relative_path: Path relative to the upload folder

        Returns:
            Dictionary with file information or None if file doesn't exist
        """
        return self.backend.get_file_info(relative_path)

    def get_first_directory(self, path: str) -> Optional[str]:
        """
        Get the first directory component from a path.

        Args:
            path: The path to parse

        Returns:
            First directory name or None if path is empty
        """
        parts = path.lstrip("/").split("/")
        return parts[0] if parts and parts[0] else None


# Create a singleton instance
file_storage = FileStorageService()
