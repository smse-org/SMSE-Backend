"""
Unit tests for the ThumbnailService
"""

import io
import pytest
from PIL import Image
from unittest.mock import MagicMock, patch, mock_open
from smse_backend.services.thumbnail import ThumbnailService


@pytest.fixture
def mock_file_storage():
    """Create a mock file storage service."""
    mock_storage = MagicMock()
    mock_storage.backend = MagicMock()
    return mock_storage


@pytest.fixture
def thumbnail_service(mock_file_storage):
    """Create a ThumbnailService instance with mocked dependencies."""
    return ThumbnailService(mock_file_storage)


def create_test_image_bytes():
    """Create test image bytes."""
    img = Image.new("RGB", (100, 100), color="red")
    img_bytes = io.BytesIO()
    img.save(img_bytes, format="JPEG")
    return img_bytes.getvalue()


class TestThumbnailService:

    def test_is_image_file(self, thumbnail_service):
        """Test image file detection."""
        assert thumbnail_service.is_supported_file("test.jpg") == True
        assert thumbnail_service.is_supported_file("test.jpeg") == True
        assert thumbnail_service.is_supported_file("test.png") == True
        assert thumbnail_service.is_supported_file("test.gif") == True
        assert thumbnail_service.is_supported_file("test.txt") == False
        assert thumbnail_service.is_supported_file("test.pdf") == False

    def test_generate_thumbnail_path(self, thumbnail_service):
        """Test thumbnail path generation."""
        original_path = "user123/subfolder/image.jpg"
        thumbnail_path = thumbnail_service.generate_thumbnail_path(original_path)

        assert thumbnail_path == "user123/subfolder/image_thumb.jpg"

    def test_generate_thumbnail_from_bytes(self, thumbnail_service):
        """Test thumbnail generation from bytes."""
        test_image_bytes = create_test_image_bytes()

        thumbnail_bytes = thumbnail_service.generate_thumbnail_from_bytes(
            test_image_bytes, (50, 50)
        )

        assert thumbnail_bytes is not None
        assert len(thumbnail_bytes) > 0

        # Verify the thumbnail is a valid image
        thumbnail_image = Image.open(io.BytesIO(thumbnail_bytes))
        assert thumbnail_image.size == (50, 50)
        assert thumbnail_image.format == "JPEG"

    @patch("builtins.open", new_callable=mock_open)
    def test_save_thumbnail_local_storage(self, mock_file_open, thumbnail_service):
        """Test saving thumbnail to local storage."""
        # Mock local storage backend
        thumbnail_service.file_storage.backend._get_full_path = MagicMock(
            return_value="/full/path/thumb.jpg"
        )
        thumbnail_service.file_storage.backend._ensure_directory_exists = MagicMock()

        # Set up hasattr to return True for local storage
        with patch("builtins.hasattr", return_value=True):
            result = thumbnail_service.save_thumbnail(b"test_bytes", "thumb.jpg")

        assert result == True
        mock_file_open.assert_called_once_with("/full/path/thumb.jpg", "wb")
        mock_file_open().write.assert_called_once_with(b"test_bytes")

    def test_generate_and_save_thumbnail_from_path_not_image(self, thumbnail_service):
        """Test that non-image files return None."""
        result = thumbnail_service.generate_and_save_thumbnail_from_path("test.txt")
        assert result is None

    @patch.object(ThumbnailService, "generate_thumbnail_from_path")
    @patch.object(ThumbnailService, "save_thumbnail")
    @patch.object(ThumbnailService, "generate_thumbnail_path")
    def test_generate_and_save_thumbnail_from_path_success(
        self, mock_gen_path, mock_save, mock_gen_thumb, thumbnail_service
    ):
        """Test successful thumbnail generation from path."""
        # Setup mocks
        mock_gen_path.return_value = "thumb_path.jpg"
        mock_gen_thumb.return_value = b"thumbnail_bytes"
        mock_save.return_value = True

        result = thumbnail_service.generate_and_save_thumbnail_from_path("test.jpg")

        assert result == "thumb_path.jpg"
        mock_gen_path.assert_called_once_with("test.jpg")
        mock_gen_thumb.assert_called_once_with("test.jpg", None)
        mock_save.assert_called_once_with(b"thumbnail_bytes", "thumb_path.jpg")
