"""Pre-commit hook: resize and compress JPEG and PNG images."""

import argparse
import shlex
import sys

from PIL import Image, ImageOps


def _optimize_file(filepath, max_width, quality):
    """Resize, compress, and strip metadata from a single image file.

    Supports JPEG and PNG formats. JPEGs are compressed with the given quality
    and have EXIF data stripped. PNGs are saved with Pillow's optimize flag
    and have text metadata stripped.

    Args:
        filepath: Path to the image file.
        max_width: Maximum allowed width in pixels.
        quality: JPEG compression quality (1-95). Ignored for PNG.

    Returns:
        True if the file was modified, False otherwise.
    """
    with Image.open(filepath) as img:
        img_format = img.format  # "JPEG" or "PNG"
        if img_format not in ("JPEG", "PNG"):
            msg = f"Unsupported format '{img_format}' for {filepath}"
            raise ValueError(msg)
        has_png_text = img_format == "PNG" and bool(getattr(img, "text", None))
        img = ImageOps.exif_transpose(img)
        width, height = img.size
        needs_resize = width > max_width
        has_exif = bool(img.info.get("exif"))

        if not needs_resize and not has_exif and not has_png_text:
            return False

        if needs_resize:
            ratio = max_width / width
            new_height = max(1, round(height * ratio))
            new_size = (max_width, new_height)
            img = img.resize(new_size, Image.LANCZOS)

        if img_format == "PNG":
            # Strip metadata by creating a clean image without materializing
            # the pixel stream as a Python list.
            clean = Image.new(img.mode, img.size)
            if img.mode == "P":
                palette = img.getpalette()
                if palette is not None:
                    clean.putpalette(palette)
            clean.frombytes(img.tobytes())
            clean.save(filepath, "PNG", optimize=True)
        else:
            if img.mode in ("RGBA", "P"):
                img = img.convert("RGB")
            img.save(filepath, "JPEG", quality=quality, optimize=True)

    return True


def main():
    """Entry point for the optimize-images pre-commit hook."""
    parser = argparse.ArgumentParser(description="Resize and compress images.")
    parser.add_argument("filenames", nargs="*", help="Image files to check.")
    parser.add_argument(
        "--max-width",
        type=int,
        default=1920,
        help="Maximum image width in pixels (default: 1920).",
    )
    parser.add_argument(
        "--quality",
        type=int,
        default=85,
        help="JPEG compression quality 1-95 (default: 85).",
    )
    args = parser.parse_args()

    modified = []
    failed = False
    for filepath in args.filenames:
        try:
            if _optimize_file(filepath, args.max_width, args.quality):
                modified.append(filepath)
        except Exception as exc:  # pylint: disable=broad-exception-caught
            print(f"ERROR: Failed to process {filepath}: {exc}")
            failed = True

    if modified:
        quoted = " ".join(shlex.quote(f) for f in modified)
        print("")
        print("Images were resized/compressed by this hook:")
        print("")
        for f in modified:
            print(f"  {f}")
        print("")
        print("Run the following to stage the optimized files:")
        print(f"  git add {quoted}")
        return 1

    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
