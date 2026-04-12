"""Pre-commit hook: resize and compress JPEG images."""

import argparse
import sys

from PIL import Image


def _optimize_file(filepath, max_width, quality):
    """Resize and compress a single JPEG file if needed.

    Args:
        filepath: Path to the JPEG file.
        max_width: Maximum allowed width in pixels.
        quality: JPEG compression quality (1-95).

    Returns:
        True if the file was modified, False otherwise.
    """
    with Image.open(filepath) as img:
        width, height = img.size
        if width <= max_width:
            return False

        ratio = max_width / width
        new_size = (max_width, int(height * ratio))

        resized = img.resize(new_size, Image.LANCZOS)
        # Convert to RGB to drop alpha channel and EXIF data (privacy: GPS etc.)
        if resized.mode in ("RGBA", "P"):
            resized = resized.convert("RGB")
        resized.save(filepath, "JPEG", quality=quality, optimize=True)

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
    for filepath in args.filenames:
        try:
            if _optimize_file(filepath, args.max_width, args.quality):
                modified.append(filepath)
        except Exception as exc:  # pylint: disable=broad-exception-caught
            print(f"WARNING: Failed to process {filepath}: {exc}")

    if modified:
        print("")
        print("Images were resized/compressed by this hook:")
        print("")
        for f in modified:
            print(f"  {f}")
        print("")
        print("Run the following to stage the optimized files:")
        print(f"  git add {' '.join(modified)}")
        return 1

    return 0


if __name__ == "__main__":
    sys.exit(main())
