# SPDX-License-Identifier: GPL-3.0-or-later
"""Photo record of a finished erase: plain text plus an offline QR matrix.

Backlog #127. The record repeats facts this session already shows on the
result screen, so a person without a second USB can photograph it. Rules:

- The Result line is the on-screen outcome text, never a stronger claim.
- Plain text only: no link, no tracking, no app or network needed to read it.
- Built on demand for the screen. Never written to the target disk or any
  other storage; the full report stays the USB export of result.json.
"""

from __future__ import annotations

import functools
from dataclasses import dataclass

from beamo_wipe import progress as _progress
from beamo_wipe import result_summary as RS
from beamo_wipe.build_identity import BUILD_ID_RE
from beamo_wipe.evidence import valid_wall

# Translated (locales/*: "erase_record"). Labels shared with RESULT.txt come
# from result_summary so the photo and the saved report use the same words.
RECORD_HEADER = "Beamo Wipe erase summary. Not a certificate."
RECORD_PREVIEW_HEADER = "Beamo Wipe preview. Nothing was erased. Not a record."
H_REPORT = "Report"
H_SOFTWARE = "Software"
REPORT_SAVED_CHECKSUM = "Saved to USB, checksum {checksum}"
REPORT_SAVED = "Saved to USB"
REPORT_NOT_SAVED = "Not saved to USB"
REPORT_NOT_STORED = "Not saved. The full report could not be stored in this session."
_SOFTWARE_LINE = "Beamo Wipe {version}, build {build}, nwipe {engine}"
_SOFTWARE_LINE_NO_BUILD = "Beamo Wipe {version}, nwipe {engine}"
_WALL_UTC = "{date} {time} UTC"

# Medium error correction keeps the matrix small enough for 4 px modules on
# an 800x600 screen while tolerating glare and moiré in a phone photo.
_ERROR_CORRECTION = "M"
QUIET_ZONE = 4
# ECI designator 26 declares UTF-8, so phone cameras show accented French,
# German, Spanish and Italian text correctly instead of guessing Latin-1.
ECI_UTF8 = 26
# Per-value cap for disk, method and identity facts read from the device.
# Long models or serials are cut with a visible marker rather than growing the
# code past what a phone reads reliably from a screen. The app's own
# sentences (Result, Report, Elapsed, Software) use MAX_RESULT and are never cut.
MAX_VALUE = 64
MAX_RESULT = 400
CHECKSUM_CHARS = 12
BUILD_CHARS = 8


@dataclass(frozen=True)
class EraseRecord:
    """Exact record content. ``text`` is the QR payload, byte for byte."""

    header: str
    fields: tuple[tuple[str, str], ...]
    preview: bool = False

    @property
    def lines(self) -> tuple[str, ...]:
        return (self.header, *(f"{label}: {value}" for label, value in self.fields))

    @property
    def text(self) -> str:
        return "\n".join(self.lines)


def _value(text: object, *, limit: int = MAX_VALUE) -> str:
    """Flatten untrusted text; empty and unavailable values become ""."""
    cleaned = RS.sanitize_value(text, limit=limit)
    return "" if cleaned == RS.UNAVAILABLE else cleaned


def _result_value(result: object) -> str:
    """The on-screen outcome exactly, or a refusal: never a shortened claim."""
    if not isinstance(result, str):
        raise ValueError("An erase record needs the on-screen result.")
    cleaned = RS.sanitize_value(result, limit=MAX_RESULT)
    if cleaned == RS.UNAVAILABLE or cleaned != " ".join(result.split()):
        raise ValueError("The on-screen result cannot be recorded exactly.")
    return cleaned


def wall_text(value: object) -> str:
    """Readable UTC wall time from a validated stamp, or "" when invalid."""
    wall = valid_wall(value)
    if not wall:
        return ""
    return _WALL_UTC.format(date=wall[:10], time=wall[11:19])


def checksum_text(sha256: object) -> str:
    if isinstance(sha256, str) and RS.HEX64_RE.fullmatch(sha256):
        return sha256[:CHECKSUM_CHARS]
    return ""


def software_text(version: object, build_id: object, engine: object) -> str:
    version_text = _value(version)
    engine_text = _value(engine)
    if not version_text or not engine_text:
        return ""
    if isinstance(build_id, str) and BUILD_ID_RE.fullmatch(build_id):
        return _SOFTWARE_LINE.format(
            version=version_text, build=build_id[:BUILD_CHARS], engine=engine_text
        )
    return _SOFTWARE_LINE_NO_BUILD.format(version=version_text, engine=engine_text)


def build_record(
    *,
    result: str,
    disk: str = "",
    capacity: str = "",
    id_label: str = "",
    id_value: str = "",
    method: str = "",
    started: str = "",
    ended: str = "",
    elapsed_line: str = "",
    report: str = "",
    software: str = "",
) -> EraseRecord:
    """Labeled record in the current language. Empty facts are omitted.

    ``result`` must be the exact on-screen outcome text; ``elapsed_line`` is
    the on-screen elapsed line, already labeled.
    """
    result_text = _result_value(result)
    fields: list[tuple[str, str]] = [(RS.H_RESULT, result_text)]
    optional = (
        (RS.H_DISK, disk),
        (RS.H_CAPACITY, capacity),
        (_value(id_label, limit=MAX_RESULT), id_value),
        (RS.H_METHOD, method),
        (RS.H_STARTED, started),
        (RS.H_ENDED, ended),
    )
    for label, raw in optional:
        value = _value(raw)
        if label and value:
            fields.append((label, value))
    elapsed = _elapsed_field(elapsed_line)
    if elapsed is not None:
        fields.append(elapsed)
    # Report and software lines are the app's own translated sentences, so
    # they use the larger cap: a long translation must never be cut.
    for label, raw in ((H_REPORT, report), (H_SOFTWARE, software)):
        value = _value(raw, limit=MAX_RESULT)
        if value:
            fields.append((label, value))
    return EraseRecord(header=RECORD_HEADER, fields=tuple(fields))


def _elapsed_field(line: str) -> tuple[str, str] | None:
    """The on-screen elapsed line is already "Label: value"; keep its words."""
    text = _value(line, limit=MAX_RESULT)
    label, sep, value = text.partition(":")
    label, value = label.strip(), value.strip()
    if not sep or not label or not value or value == _progress.DURATION_UNAVAILABLE:
        return None
    return label, value


def build_preview_record(result: str, software: str = "") -> EraseRecord:
    """Preview sample: says nothing was erased and holds no disk identity."""
    fields = [(RS.H_RESULT, _result_value(result))]
    software_value = _value(software, limit=MAX_RESULT)
    if software_value:
        fields.append((H_SOFTWARE, software_value))
    return EraseRecord(header=RECORD_PREVIEW_HEADER, fields=tuple(fields), preview=True)


def error_correction() -> str:
    return _ERROR_CORRECTION


def _utf8_codewords(version: int, level: int, data: bytes):
    """Data codewords: ECI(UTF-8) + one byte-mode segment, padded per ISO 18004.

    python3-qrcode (bookworm 7.4.2, dev 8.2) has no ECI API. This mirrors its
    util.create_data with the 12-bit ECI header first, then reuses its own
    Reed-Solomon blocks, so masking and layout stay the library's.
    """
    from qrcode import base, util

    buffer = util.BitBuffer()
    buffer.put(0b0111, 4)  # ECI mode indicator
    buffer.put(ECI_UTF8, 8)
    buffer.put(util.MODE_8BIT_BYTE, 4)
    buffer.put(len(data), util.length_in_bits(util.MODE_8BIT_BYTE, version))
    for byte in data:
        buffer.put(byte, 8)
    blocks = base.rs_blocks(version, level)
    limit = sum(block.data_count * 8 for block in blocks)
    if len(buffer) > limit:
        return None
    for _ in range(min(limit - len(buffer), 4)):
        buffer.put_bit(False)
    if len(buffer) % 8:
        for _ in range(8 - len(buffer) % 8):
            buffer.put_bit(False)
    for index in range((limit - len(buffer)) // 8):
        buffer.put(util.PAD0 if index % 2 == 0 else util.PAD1, 8)
    return util.create_bytes(buffer, blocks)


@functools.lru_cache(maxsize=8)
def qr_matrix(text: str) -> tuple[tuple[bool, ...], ...]:
    """Dark-module matrix, quiet zone included. Offline; raises if unavailable."""
    if not isinstance(text, str) or not text:
        raise ValueError("QR text is required.")
    import qrcode
    from qrcode.constants import ERROR_CORRECT_M

    data = text.encode("utf-8")
    code = qrcode.QRCode(error_correction=ERROR_CORRECT_M, border=QUIET_ZONE)
    for version in range(1, 41):
        codewords = _utf8_codewords(version, ERROR_CORRECT_M, data)
        if codewords is not None:
            break
    else:
        raise ValueError("Record text does not fit a QR code.")
    code.version = version
    code.data_cache = codewords
    code.makeImpl(False, code.best_mask_pattern())
    return tuple(tuple(bool(cell) for cell in row) for row in code.get_matrix())


def qr_svg(text: str, *, label: str) -> str:
    """Offline vector code for the browser preview. No scripts, no links."""
    import html

    matrix = qr_matrix(text)
    size = len(matrix)
    rects = []
    for y, row in enumerate(matrix):
        start = None
        for x, dark in enumerate((*row, False)):
            if dark and start is None:
                start = x
            elif not dark and start is not None:
                rects.append(
                    f'<rect x="{start}" y="{y}" width="{x - start}" height="1"/>'
                )
                start = None
    return (
        f'<svg viewBox="0 0 {size} {size}" role="img"'
        f' aria-label="{html.escape(label, quote=True)}"'
        ' shape-rendering="crispEdges">'
        f'<rect width="{size}" height="{size}" fill="#fff"/>'
        f'<g fill="#000">{"".join(rects)}</g></svg>'
    )
