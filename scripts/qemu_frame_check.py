#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-3.0-or-later
"""Judge the BW-168 screen-awake probe's QEMU screendump frames.

`scripts/qemu-verify.sh` runs this only for the opt-in QEMU_SCREEN_AWAKE=1
journey. It decodes QEMU's PNG screendumps with the standard library only
(no PIL on the worker), decides which frames are blank, and writes one JSON
receipt with every frame's sha256 and pixel-value summary.

A frame is blank when every pixel has the same value: that is what the X
screensaver leaves in the framebuffer once it blanks the kiosk.

Verdicts (exit status):
  0  PASS          the screen stayed lit through the erase, blanked again
                   after it, and one harmless key woke it without acting.
  1  FAIL          one of PASS-1, PASS-2 or PASS-3 did not hold.
  3  INCONCLUSIVE  the probe could not judge: the erase ended before the
                   last in-erase frame, or a frame is missing. Never a pass.
"""

from __future__ import annotations

import argparse
from collections import Counter
import hashlib
import json
from pathlib import Path
import struct
import sys
import zlib

PNG_SIGNATURE = b"\x89PNG\r\n\x1a\n"
# 8-bit greyscale, RGB, greyscale+alpha and RGBA: what QEMU's screendump
# writes (RGB) plus the obvious neighbours. Palette and 16-bit are refused.
CHANNELS = {0: 1, 2: 3, 4: 2, 6: 4}

EXIT_PASS = 0
EXIT_FAIL = 1
EXIT_INCONCLUSIVE = 3

# Frame names written by qemu-verify.sh, in capture order.
ERASE_FRAMES = ("erase-030", "erase-570", "erase-645")
AFTER_FRAMES = ("after-030", "after-645")
WAKE_FRAME = "wake"


class FrameError(ValueError):
    """The file is not a PNG this checker can judge."""


def decode_png(data: bytes) -> tuple[int, int, int, bytes]:
    """Return (width, height, channels, raw pixel bytes) for a simple PNG."""
    if not data.startswith(PNG_SIGNATURE):
        raise FrameError("not a PNG file")
    offset = len(PNG_SIGNATURE)
    header = None
    idat = bytearray()
    while offset + 8 <= len(data):
        (length,) = struct.unpack(">I", data[offset : offset + 4])
        kind = data[offset + 4 : offset + 8]
        body = data[offset + 8 : offset + 8 + length]
        if len(body) != length:
            raise FrameError("truncated PNG chunk")
        offset += 12 + length
        if kind == b"IHDR":
            header = struct.unpack(">IIBBBBB", body)
        elif kind == b"IDAT":
            idat += body
        elif kind == b"IEND":
            break
    if header is None:
        raise FrameError("PNG has no IHDR")
    width, height, depth, colour, _compression, _filter, interlace = header
    if depth != 8 or colour not in CHANNELS or interlace != 0:
        raise FrameError(
            f"unsupported PNG layout depth={depth} colour={colour} interlace={interlace}"
        )
    if width == 0 or height == 0:
        raise FrameError("PNG has no pixels")
    channels = CHANNELS[colour]
    stride = width * channels
    try:
        filtered = zlib.decompress(bytes(idat))
    except zlib.error as exc:
        raise FrameError(f"PNG image data is corrupt: {exc}") from exc
    if len(filtered) != height * (stride + 1):
        raise FrameError("PNG image data has the wrong size")
    pixels = bytearray(height * stride)
    previous = bytearray(stride)
    for row in range(height):
        start = row * (stride + 1)
        kind = filtered[start]
        line = bytearray(filtered[start + 1 : start + 1 + stride])
        for i in range(stride):
            left = line[i - channels] if i >= channels else 0
            up = previous[i]
            if kind == 0:
                continue
            if kind == 1:
                line[i] = (line[i] + left) & 0xFF
            elif kind == 2:
                line[i] = (line[i] + up) & 0xFF
            elif kind == 3:
                line[i] = (line[i] + ((left + up) >> 1)) & 0xFF
            elif kind == 4:
                upper_left = previous[i - channels] if i >= channels else 0
                estimate = left + up - upper_left
                pa, pb, pc = (
                    abs(estimate - left),
                    abs(estimate - up),
                    abs(estimate - upper_left),
                )
                if pa <= pb and pa <= pc:
                    predictor = left
                elif pb <= pc:
                    predictor = up
                else:
                    predictor = upper_left
                line[i] = (line[i] + predictor) & 0xFF
            else:
                raise FrameError(f"unknown PNG row filter {kind}")
        pixels[row * stride : (row + 1) * stride] = line
        previous = line
    return width, height, channels, bytes(pixels)


def summarize(path: Path) -> dict:
    data = path.read_bytes()
    width, height, channels, pixels = decode_png(data)
    values = Counter(pixels[i : i + channels] for i in range(0, len(pixels), channels))
    return {
        "file": path.name,
        "sha256": hashlib.sha256(data).hexdigest(),
        "width": width,
        "height": height,
        "distinct_values": len(values),
        "top_values": [[value.hex(), count] for value, count in values.most_common(3)],
        "blank": len(values) == 1,
        "_pixels": pixels,
    }


def differing_pixels(first: dict, second: dict) -> int | None:
    """Count pixels that differ between two frames of the same size."""
    if (first["width"], first["height"]) != (second["width"], second["height"]):
        return None
    a, b = first["_pixels"], second["_pixels"]
    channels = len(a) // (first["width"] * first["height"])
    return sum(
        1
        for i in range(0, len(a), channels)
        if a[i : i + channels] != b[i : i + channels]
    )


def judge(frames_dir: Path, observations: dict) -> tuple[int, dict]:
    """Apply PASS-1..3 to the captured frames; return (exit status, receipt)."""
    receipt: dict = {
        "observations": observations,
        "frames": {},
        "checks": {},
        "reasons": [],
    }
    reasons = receipt["reasons"]
    summaries: dict[str, dict] = {}
    for name in (*ERASE_FRAMES, *AFTER_FRAMES, WAKE_FRAME):
        path = frames_dir / f"screen-awake-{name}.png"
        if not path.is_file():
            continue
        try:
            summaries[name] = summarize(path)
        except FrameError as exc:
            reasons.append(f"{name}: {exc}")
    for name, summary in summaries.items():
        receipt["frames"][name] = {
            k: v for k, v in summary.items() if not k.startswith("_")
        }

    if observations.get("done_before_last_erase_frame"):
        reasons.append(
            "the erase finished before the last in-erase frame; use a larger or slower target"
        )
        receipt["verdict"] = "INCONCLUSIVE"
        return EXIT_INCONCLUSIVE, receipt
    missing = [
        n for n in (*ERASE_FRAMES, *AFTER_FRAMES, WAKE_FRAME) if n not in summaries
    ]
    if missing:
        reasons.append("missing or unreadable frames: " + ",".join(missing))
        receipt["verdict"] = "INCONCLUSIVE"
        return EXIT_INCONCLUSIVE, receipt

    # PASS-1: lit throughout the erase, and live rather than a frozen buffer.
    change = differing_pixels(summaries["erase-030"], summaries["erase-645"])
    receipt["checks"]["erase_645_vs_030_differing_pixels"] = change
    lit = all(not summaries[n]["blank"] for n in ERASE_FRAMES)
    pass1 = lit and bool(change)
    receipt["checks"]["pass1_lit_during_erase"] = pass1
    if not lit:
        reasons.append("PASS-1: a frame during the erase was blank")
    elif not change:
        reasons.append(
            "PASS-1: the 10 min 45 s frame did not change from the 30 s frame"
        )

    # PASS-2: the launcher's blanking policy came back after the erase.
    pass2 = not summaries["after-030"]["blank"] and summaries["after-645"]["blank"]
    receipt["checks"]["pass2_blanking_restored"] = pass2
    if summaries["after-030"]["blank"]:
        reasons.append("PASS-2: the screen was already blank 30 s after the erase")
    elif not summaries["after-645"]["blank"]:
        reasons.append("PASS-2: the screen was still lit 10 min 45 s after the erase")

    # PASS-3: one harmless key woke the screen and did not act in the app.
    new_screens = int(observations.get("screen_markers_after_wake", 0)) - int(
        observations.get("screen_markers_before_wake", 0)
    )
    receipt["checks"]["new_screen_markers_after_wake"] = new_screens
    pass3 = not summaries[WAKE_FRAME]["blank"] and new_screens == 0
    receipt["checks"]["pass3_woke_without_acting"] = pass3
    if summaries[WAKE_FRAME]["blank"]:
        reasons.append("PASS-3: the screen stayed blank after the wake key")
    if new_screens:
        reasons.append("PASS-3: the wake key changed the app's screen")

    if int(observations.get("blanking_change_failed", 0)):
        reasons.append("the guest logged power/display_blanking_change_failed")
    ok = (
        pass1
        and pass2
        and pass3
        and not int(observations.get("blanking_change_failed", 0))
    )
    receipt["verdict"] = "PASS" if ok else "FAIL"
    return (EXIT_PASS if ok else EXIT_FAIL), receipt


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("frames_dir", type=Path)
    parser.add_argument("receipt", type=Path)
    parser.add_argument(
        "--observation", action="append", default=[], metavar="KEY=VALUE"
    )
    args = parser.parse_args(argv)
    observations: dict = {}
    for item in args.observation:
        key, sep, value = item.partition("=")
        if not sep or not key:
            parser.error(f"observation must be KEY=VALUE: {item!r}")
        observations[key] = int(value) if value.lstrip("-").isdigit() else value
    status, receipt = judge(args.frames_dir, observations)
    args.receipt.write_text(
        json.dumps(receipt, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    print(f"screen_awake={receipt['verdict'].lower()}")
    for reason in receipt["reasons"]:
        print(f"screen_awake_reason={reason}", file=sys.stderr)
    return status


if __name__ == "__main__":
    raise SystemExit(main())
