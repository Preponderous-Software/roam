#!/usr/bin/env python3
"""Turn the frames from scripts/capture_3d_hero.js into the README hero media.

    python3 scripts/make_3d_hero.py FRAMES_DIR [--out-dir pics]

Writes into ``--out-dir``:

- ``roam3d-hero.gif``: the walk. The world part of the game area (the band
  above the hotbar) scaled down, one palette shared by every frame (no colour
  flicker), each frame shown for the time the capture script gave it. It is
  made as large as fits under ``--max-bytes`` (default 1 MB) so the README
  stays light: widest first, then the most colours.
- ``roam3d-hero.png``: the capture's still (its opening view) at full size,
  HUD included.

Needs only Pillow.
"""

import argparse
import io
import json
import os
import sys

from PIL import Image

# The GIF's band of the (square) game area, as fractions of its height: from
# just under the "Day" label to just above the hotbar.
BAND_TOP = 0.0625
BAND_BOTTOM = 0.755


def loadFrames(framesDir):
    with open(os.path.join(framesDir, "frames.json"), encoding="utf-8") as f:
        frames = json.load(f)["frames"]
    if len(frames) < 2:
        sys.exit("need at least two frames")
    images = [
        Image.open(os.path.join(framesDir, fr["file"])).convert("RGB") for fr in frames
    ]
    durations = [int(fr["ms"]) for fr in frames]
    return images, durations


def band(image):
    w, h = image.size
    return image.crop((0, round(h * BAND_TOP), w, round(h * BAND_BOTTOM)))


def encodeGif(images, durations, width, colors):
    cropped = [band(im) for im in images]
    height = round(cropped[0].height * width / cropped[0].width)
    scaled = [im.resize((width, height), Image.LANCZOS) for im in cropped]
    # One palette from all the frames stacked, so every part of the walk
    # gets its colours. Octree keeps small bright details (the white status
    # label, the player's card) that median cut gives away to the grass, and
    # its flatter areas compress better.
    strip = Image.new("RGB", (width, height * len(scaled)))
    for k, im in enumerate(scaled):
        strip.paste(im, (0, height * k))
    palette = strip.quantize(colors=colors, method=Image.FASTOCTREE)
    frames = [im.quantize(palette=palette, dither=Image.NONE) for im in scaled]
    buf = io.BytesIO()
    frames[0].save(
        buf,
        format="GIF",
        save_all=True,
        append_images=frames[1:],
        duration=durations,
        loop=0,
        optimize=True,
    )
    return buf.getvalue(), (width, height)


def main():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("frames_dir")
    ap.add_argument("--out-dir", default="pics")
    ap.add_argument("--max-bytes", type=int, default=1_000_000)
    args = ap.parse_args()

    images, durations = loadFrames(args.frames_dir)
    os.makedirs(args.out_dir, exist_ok=True)

    data = None
    for width in (480, 440, 400, 360, 320):
        for colors in (128, 96, 64):
            data, size = encodeGif(images, durations, width, colors)
            if len(data) <= args.max_bytes:
                break
        if len(data) <= args.max_bytes:
            break
    if len(data) > args.max_bytes:
        sys.exit(
            f"the smallest GIF tried is still {len(data)} bytes; record fewer frames"
        )
    gifPath = os.path.join(args.out_dir, "roam3d-hero.gif")
    with open(gifPath, "wb") as f:
        f.write(data)
    print(
        f"{gifPath}: {size[0]}x{size[1]}, {len(images)} frames, {colors} colours, "
        f"{sum(durations) / 1000:.1f} s, {len(data) // 1024} KB"
    )

    still = Image.open(os.path.join(args.frames_dir, "still.png")).convert("RGB")
    pngPath = os.path.join(args.out_dir, "roam3d-hero.png")
    still.save(pngPath, optimize=True)
    print(
        f"{pngPath}: {still.width}x{still.height}, "
        f"{os.path.getsize(pngPath) // 1024} KB"
    )


if __name__ == "__main__":
    main()
