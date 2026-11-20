#!/usr/bin/env python3
"""Ship entry.png: copy it into $MAKEFUN_OUTPUT_DIR (default ./out) and
check it is a real 1024x1024 PNG of at most 1 MiB first. Any failed check
prints a plain error and exits non-zero, so a bad image never ships
silently.

Usage:
    mkdir -p out && MAKEFUN_OUTPUT_DIR=out python3 main.py
"""
import os
import shutil
import sys

from PIL import Image

LIMIT_BYTES = 1024 * 1024
SIDE = 1024


def die(reason):
    print(f"ERROR: {reason}", file=sys.stderr)
    raise SystemExit(1)


def check_image(path):
    """Confirm `path` is a PNG of the expected size and dimensions."""
    size = os.path.getsize(path)
    if size > LIMIT_BYTES:
        die(f"{path} is {size} bytes, over the 1 MiB ({LIMIT_BYTES}) limit")
    try:
        with Image.open(path) as picture:
            if picture.format != "PNG":
                die(f"{path} is {picture.format}, not PNG")
            dims = picture.size
            picture.verify()
    except SystemExit:
        raise
    except Exception as exc:  # corrupt or unreadable file
        die(f"{path} is not a readable PNG ({exc})")
    if dims != (SIDE, SIDE):
        die(f"{path} is {dims[0]}x{dims[1]}, expected {SIDE}x{SIDE}")
    return size, dims


def run():
    folder = os.path.dirname(os.path.abspath(__file__))
    source = os.path.join(folder, "entry.png")
    if not os.path.isfile(source):
        die(f"entry.png not found at {source}")

    size, dims = check_image(source)
    out_dir = os.environ.get("MAKEFUN_OUTPUT_DIR") or os.path.join(".", "out")
    os.makedirs(out_dir, exist_ok=True)
    target = os.path.join(out_dir, "entry.png")
    shutil.copyfile(source, target)
    # Re-check the copy itself, not just the source: a truncated copy
    # must fail here rather than ship.
    copied_size, copied_dims = check_image(target)
    if (copied_size, copied_dims) != (size, dims):
        die(f"copy mismatch: {target} is {copied_dims[0]}x{copied_dims[1]} "
            f"{copied_size} bytes, source was {dims[0]}x{dims[1]} {size} bytes")
    print(f"OK: {target}  {dims[0]}x{dims[1]}  {size} bytes")


if __name__ == "__main__":
    run()
