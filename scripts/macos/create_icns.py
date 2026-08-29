#!/usr/bin/env python3
"""Create a macOS ICNS file from the project SVG icon."""

from __future__ import annotations

import argparse
import subprocess
from pathlib import Path

import cairosvg


ICON_FILES = {
    "icon_16x16.png": 16,
    "icon_16x16@2x.png": 32,
    "icon_32x32.png": 32,
    "icon_32x32@2x.png": 64,
    "icon_128x128.png": 128,
    "icon_128x128@2x.png": 256,
    "icon_256x256.png": 256,
    "icon_256x256@2x.png": 512,
    "icon_512x512.png": 512,
    "icon_512x512@2x.png": 1024,
}


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("source", type=Path)
    parser.add_argument("output", type=Path)
    args = parser.parse_args()

    iconset = args.output.with_suffix(".iconset")
    iconset.mkdir(parents=True, exist_ok=True)
    svg = args.source.read_bytes()

    for filename, size in ICON_FILES.items():
        cairosvg.svg2png(
            bytestring=svg,
            write_to=str(iconset / filename),
            output_width=size,
            output_height=size,
        )

    args.output.parent.mkdir(parents=True, exist_ok=True)
    subprocess.run(
        ["iconutil", "--convert", "icns", "--output", str(args.output), str(iconset)],
        check=True,
    )
    print(f"[OK] {args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
