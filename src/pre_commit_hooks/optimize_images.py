"""Pre-commit hook: resize and compress JPEG images."""

import argparse
import shlex
import sys

from PIL import Image, ImageOps


def _optimize_file(filepath, max_width, quality):
    """Resize, compress, and strip EXIF from a single JPEG file.

    Args:
        filepath: Path to the JPEG file.
        max_width: Maximum allowed width in pixels.
        quality: JPEG compression quality (1-95).

    Returns:
        True if the file was modified, False otherwise.
    """
    with Image.open(filepath) as img:
        # Apply EXIF orientation before checking size
        img = ImageOps.exif_transpose(img)
        width, height = img.size
        needs_resize = width > max_width
        has_exif = bool(img.info.get("exif"))

        if not needs_resize and not has_exif:
            return False

        if needs_resize:
            ratio = max_width / width
            new_height = max(1, round(height * ratio))
            new_size = (max_width, new_height)
            img = img.resize(new_size, Image.LANCZOS)

        if img.mode in ("RGBA", "P"):
            img = img.convert("RGB")
        img.save(filepath, "JPEG", quality=quality, optimize=True)

    return True


def main():
    """Entry point for the optimize-images pre-commit hook."""
    parser = argparse.ArgumentParser(description="Resize and compress JPEG images.")
    parser.add_argument("filenames", nargs="*", help="JPEG files to check.")
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
