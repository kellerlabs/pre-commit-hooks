"""Tests for optimize_images hook."""

from unittest import mock

from PIL import Image
from PIL.PngImagePlugin import PngInfo

from pre_commit_hooks.optimize_images import main


def _create_jpeg(path, width, height, exif=False):
    """Create a test JPEG file.

    Args:
        path: File path to write.
        width: Image width in pixels.
        height: Image height in pixels.
        exif: If True, embed a fake EXIF marker.
    """
    img = Image.new("RGB", (width, height), color="red")
    if exif:
        # Minimal EXIF with a GPS IFD pointer (privacy test)
        # EXIF header: Exif\x00\x00 + TIFF header (little-endian)
        exif_bytes = b"Exif\x00\x00II\x2a\x00\x08\x00\x00\x00\x00\x00\x00\x00"
        img.info["exif"] = exif_bytes
        img.save(str(path), "JPEG", quality=95, exif=exif_bytes)
    else:
        img.save(str(path), "JPEG", quality=95)


def _create_png(path, width, height, text_meta=False):
    """Create a test PNG file.

    Args:
        path: File path to write.
        width: Image width in pixels.
        height: Image height in pixels.
        text_meta: If True, embed text metadata chunks.
    """
    img = Image.new("RGBA", (width, height), color="blue")
    pnginfo = PngInfo()
    if text_meta:
        pnginfo.add_text("Software", "TestSuite")
        pnginfo.add_text("Comment", "test metadata")
    img.save(str(path), "PNG", pnginfo=pnginfo)


class TestOptimizeImages:
    """Tests for the optimize-images hook."""

    def test_large_image_resized(self, tmp_path):
        """Images wider than max-width are resized."""
        img_path = tmp_path / "large.jpg"
        _create_jpeg(img_path, 3000, 2000)

        with mock.patch("sys.argv", ["optimize-images", "--max-width=1920", str(img_path)]):
            result = main()

        assert result == 1  # hook fails because file was modified
        with Image.open(img_path) as img:
            assert img.size[0] == 1920
            assert img.size[1] == 1280  # proportional

    def test_small_image_untouched(self, tmp_path):
        """Small images without EXIF are not modified."""
        img_path = tmp_path / "small.jpg"
        _create_jpeg(img_path, 800, 600)
        original_size = img_path.stat().st_size

        with mock.patch("sys.argv", ["optimize-images", "--max-width=1920", str(img_path)]):
            result = main()

        assert result == 0  # hook passes
        assert img_path.stat().st_size == original_size

    def test_exact_width_untouched(self, tmp_path):
        """Images at exactly max-width are not modified."""
        img_path = tmp_path / "exact.jpg"
        _create_jpeg(img_path, 1920, 1080)

        with mock.patch("sys.argv", ["optimize-images", "--max-width=1920", str(img_path)]):
            result = main()

        assert result == 0

    def test_exif_stripped(self, tmp_path):
        """EXIF data is stripped from resized images."""
        img_path = tmp_path / "gps.jpg"
        _create_jpeg(img_path, 3000, 2000, exif=True)

        with mock.patch("sys.argv", ["optimize-images", "--max-width=1920", str(img_path)]):
            main()

        with Image.open(img_path) as img:
            assert img.info.get("exif") is None

    def test_custom_quality(self, tmp_path):
        """Custom quality setting is applied."""
        img_path = tmp_path / "quality.jpg"
        _create_jpeg(img_path, 3000, 2000)

        with mock.patch("sys.argv", ["optimize-images", "--quality=50", "--max-width=1920", str(img_path)]):
            result = main()

        assert result == 1
        with Image.open(img_path) as img:
            assert img.size[0] == 1920

    def test_multiple_files(self, tmp_path):
        """Multiple files are processed; only oversized ones are modified."""
        large = tmp_path / "large.jpg"
        small = tmp_path / "small.jpg"
        _create_jpeg(large, 4000, 3000)
        _create_jpeg(small, 800, 600)
        small_size = small.stat().st_size

        with mock.patch("sys.argv", ["optimize-images", "--max-width=1920", str(large), str(small)]):
            result = main()

        assert result == 1  # large was modified
        with Image.open(large) as img:
            assert img.size[0] == 1920
        assert small.stat().st_size == small_size

    def test_no_files(self):
        """Hook passes when no files are provided."""
        with mock.patch("sys.argv", ["optimize-images"]):
            assert main() == 0

    def test_exif_stripped_small_image(self, tmp_path):
        """EXIF data is stripped even when image is within max-width."""
        img_path = tmp_path / "small_exif.jpg"
        _create_jpeg(img_path, 800, 600, exif=True)

        with mock.patch("sys.argv", ["optimize-images", "--max-width=1920", str(img_path)]):
            result = main()

        assert result == 1  # file was modified (EXIF stripped)
        with Image.open(img_path) as img:
            assert img.info.get("exif") is None

    def test_error_causes_failure(self, tmp_path):
        """Hook fails when processing a file raises an exception."""
        bad_path = tmp_path / "not_a_jpeg.jpg"
        bad_path.write_text("not an image")

        with mock.patch("sys.argv", ["optimize-images", str(bad_path)]):
            result = main()

        assert result == 1

    # --- PNG tests ---

    def test_large_png_resized(self, tmp_path):
        """PNGs wider than max-width are resized."""
        img_path = tmp_path / "large.png"
        _create_png(img_path, 3000, 2000)

        with mock.patch("sys.argv", ["optimize-images", "--max-width=1920", str(img_path)]):
            result = main()

        assert result == 1
        with Image.open(img_path) as img:
            assert img.size[0] == 1920
            assert img.size[1] == 1280

    def test_small_png_untouched(self, tmp_path):
        """Small PNGs without metadata are not modified."""
        img_path = tmp_path / "small.png"
        _create_png(img_path, 800, 600)
        original_size = img_path.stat().st_size

        with mock.patch("sys.argv", ["optimize-images", "--max-width=1920", str(img_path)]):
            result = main()

        assert result == 0
        assert img_path.stat().st_size == original_size

    def test_png_metadata_stripped(self, tmp_path):
        """Text metadata is stripped from PNGs."""
        img_path = tmp_path / "meta.png"
        _create_png(img_path, 800, 600, text_meta=True)

        with mock.patch("sys.argv", ["optimize-images", "--max-width=1920", str(img_path)]):
            result = main()

        assert result == 1
        with Image.open(img_path) as img:
            assert not getattr(img, "text", None)

    def test_png_preserves_transparency(self, tmp_path):
        """PNGs retain their alpha channel after optimization."""
        img_path = tmp_path / "alpha.png"
        img = Image.new("RGBA", (3000, 2000), color=(0, 0, 255, 128))
        img.save(str(img_path), "PNG")

        with mock.patch("sys.argv", ["optimize-images", "--max-width=1920", str(img_path)]):
            result = main()

        assert result == 1
        with Image.open(img_path) as img:
            assert img.mode == "RGBA"
            assert img.size[0] == 1920

    def test_mixed_jpeg_and_png(self, tmp_path):
        """Both JPEG and PNG files are handled in a single run."""
        jpg_path = tmp_path / "big.jpg"
        png_path = tmp_path / "big.png"
        _create_jpeg(jpg_path, 4000, 3000)
        _create_png(png_path, 4000, 3000)

        with mock.patch(
            "sys.argv",
            ["optimize-images", "--max-width=1920", str(jpg_path), str(png_path)],
        ):
            result = main()

        assert result == 1
        with Image.open(jpg_path) as img:
            assert img.size[0] == 1920
        with Image.open(png_path) as img:
            assert img.size[0] == 1920

    def test_paletted_png_resized(self, tmp_path):
        """Paletted PNGs are resized and palette is preserved."""
        img_path = tmp_path / "palette.png"
        img = Image.new("P", (3000, 2000))
        img.putpalette([i % 256 for i in range(768)])
        img.save(str(img_path), "PNG")

        with mock.patch("sys.argv", ["optimize-images", "--max-width=1920", str(img_path)]):
            result = main()

        assert result == 1
        with Image.open(img_path) as img:
            assert img.mode == "P"
            assert img.size[0] == 1920
            assert img.getpalette() is not None

    def test_paletted_png_with_transparency(self, tmp_path):
        """Paletted PNGs with transparency are handled correctly."""
        img_path = tmp_path / "palette_alpha.png"
        img = Image.new("RGBA", (3000, 2000), color=(255, 0, 0, 128))
        img = img.convert("P")
        img.save(str(img_path), "PNG")

        with mock.patch("sys.argv", ["optimize-images", "--max-width=1920", str(img_path)]):
            result = main()

        assert result == 1
        with Image.open(img_path) as img:
            assert img.size[0] == 1920

    def test_unsupported_format_raises(self, tmp_path):
        """Unsupported image formats cause a failure."""
        img_path = tmp_path / "image.bmp"
        img = Image.new("RGB", (800, 600), color="green")
        img.save(str(img_path), "BMP")

        with mock.patch("sys.argv", ["optimize-images", str(img_path)]):
            result = main()

        assert result == 1
