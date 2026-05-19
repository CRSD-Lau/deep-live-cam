import cv2
import numpy as np
import pytest
from PIL import Image, features

from modules.utilities import IMAGE_FILE_FILTER, has_image_extension, read_image


def test_has_image_extension_accepts_webp_and_avif():
    assert has_image_extension("source.webp")
    assert has_image_extension("target.AVIF")


def test_image_file_filter_exposes_webp_and_avif_to_file_dialogs():
    assert "*.webp" in IMAGE_FILE_FILTER
    assert "*.avif" in IMAGE_FILE_FILTER


def test_read_image_decodes_webp_upload(tmp_path):
    path = tmp_path / "upload.webp"
    Image.new("RGB", (3, 2), (10, 80, 200)).save(path, "WEBP")

    image = read_image(str(path))

    assert image is not None
    assert image.shape == (2, 3, 3)
    assert image.dtype == np.uint8


@pytest.mark.skipif(not features.check("avif"), reason="Pillow was built without AVIF support")
def test_read_image_decodes_avif_upload(tmp_path):
    path = tmp_path / "upload.avif"
    Image.new("RGB", (4, 3), (200, 80, 10)).save(path, "AVIF")

    image = read_image(str(path))

    assert image is not None
    assert image.shape == (3, 4, 3)
    assert image.dtype == np.uint8


def test_read_image_honors_grayscale_flag(tmp_path):
    path = tmp_path / "upload.webp"
    Image.new("RGB", (3, 2), (10, 80, 200)).save(path, "WEBP")

    image = read_image(str(path), cv2.IMREAD_GRAYSCALE)

    assert image is not None
    assert image.shape == (2, 3)
