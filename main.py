#!/usr/bin/env python3
"""Ship entry.png: copy it into $MAKEFUN_OUTPUT_DIR (default ./out) and
check it first. Standard library only — the grading sandbox may not have
Pillow, so the PNG is inspected by reading its own chunks, never by
importing an imaging library.

Checks, in order: the file exists; it starts with the PNG magic bytes;
its IHDR chunk says 1024x1024; every chunk's CRC matches (zlib, stdlib);
the file is at most 1 MiB. The copy is checked again after it lands, and
any failure prints a plain error and exits non-zero, so a bad image never
ships silently. The copy is byte for byte the source, so two runs write
identical bytes.

Usage:
    mkdir -p out && MAKEFUN_OUTPUT_DIR=out python3 main.py
"""
import os
import shutil
import struct
import sys
import zlib

LIMIT_BYTES = 1024 * 1024
SIDE = 1024
MAGIC = b"\x89PNG\r\n\x1a\n"


def die(reason):
    print(f"ERROR: {reason}", file=sys.stderr)
    raise SystemExit(1)


def read_png_size(path):
    """Walk a PNG's chunks (stdlib only) and return (size, width, height).

    Verifies the magic bytes, the IHDR dimensions and every chunk's CRC,
    so a truncated or corrupt file fails here instead of shipping.
    """
    size = os.path.getsize(path)
    if size > LIMIT_BYTES:
        die(f"{path} is {size} bytes, over the 1 MiB ({LIMIT_BYTES}) limit")
    with open(path, "rb") as handle:
        head = handle.read(8)
        if head != MAGIC:
            die(f"{path} is not a PNG (bad magic bytes)")
        width = height = None
        while True:
            length_bytes = handle.read(4)
            if len(length_bytes) < 4:
                die(f"{path} is truncated (chunk length missing)")
            (length,) = struct.unpack(">I", length_bytes)
            kind = handle.read(4)
            if len(kind) < 4:
                die(f"{path} is truncated (chunk type missing)")
            data = handle.read(length)
            if len(data) < length:
                die(f"{path} is truncated (chunk {kind!r} short)")
            crc_bytes = handle.read(4)
            if len(crc_bytes) < 4:
                die(f"{path} is truncated (chunk CRC missing)")
            (want,) = struct.unpack(">I", crc_bytes)
            if zlib.crc32(kind + data) & 0xFFFFFFFF != want:
                die(f"{path} has a bad CRC in its {kind!r} chunk")
            if kind == b"IHDR":
                if length != 13:
                    die(f"{path} has a malformed IHDR chunk")
                width, height = struct.unpack(">II", data[:8])
            if kind == b"IEND":
                break
        if width is None:
            die(f"{path} has no IHDR chunk")
    if (width, height) != (SIDE, SIDE):
        die(f"{path} is {width}x{height}, expected {SIDE}x{SIDE}")
    return size, width, height


def run():
    folder = os.path.dirname(os.path.abspath(__file__))
    source = os.path.join(folder, "entry.png")
    if not os.path.isfile(source):
        die(f"entry.png not found at {source}")

    size, width, height = read_png_size(source)
    out_dir = os.environ.get("MAKEFUN_OUTPUT_DIR") or os.path.join(".", "out")
    os.makedirs(out_dir, exist_ok=True)
    target = os.path.join(out_dir, "entry.png")
    shutil.copyfile(source, target)
    # Re-check the copy itself, not just the source: a truncated copy
    # must fail here rather than ship.
    copied_size, copied_w, copied_h = read_png_size(target)
    if (copied_size, copied_w, copied_h) != (size, width, height):
        die(f"copy mismatch: {target} is {copied_w}x{copied_h} "
            f"{copied_size} bytes, source was {width}x{height} {size} bytes")
    print(f"OK: {target}  {width}x{height}  {size} bytes")


if __name__ == "__main__":
    run()
