# Test run record (#116)

Copy this file once per run. A run is one sitting at one computer with one
Beamo USB. Name the copy `run-<run ID>.md`, for example
`run-RUN-20270115-01.md`.

Write what you saw, not what you expected. Keep every Fail.

## Run

| Field | Value |
| --- | --- |
| Run ID | RUN-________-__ |
| Operator initials or lab handle (no full names) | |
| Second person present (initials), if any | |
| Date and start/end time (UTC) | |
| Machine ID (from the intake form) | |
| Rows run (matrix IDs) | |
| Physical hardware? (a virtual machine never counts) | must be Yes |

## Image and Beamo USB

| Field | Value |
| --- | --- |
| Product version shown in Technical details | |
| Source commit (from BUILD-IDENTITY) | |
| Image file name | |
| Image SHA-256 | |
| Image byte size | |
| Manifest SHA-256 and release signature check result | |
| Secure Boot component receipt for this image (or "none": `-03` rows BLOCKED) | |
| Readback run ID and result (`READBACK MATCH` required) | |
| Beamo USB model, capacity, serial (last 4), lab label | |
| Port used (direct USB-A, USB-C, hub …) | |

## Destructive rows only

Leave empty when no erase ran.

| Field | Value |
| --- | --- |
| Written authorization: role of the person who approved, date, where it is kept | |
| Target disk ID (intake form) and label `DISPOSABLE` checked | |
| Seed marker used (P5) and `present` hit count before the erase | |
| Method chosen | |
| Erase start and end time (UTC) | |
| Result headline exactly as shown | |
| Cold-readback form file name | |

## Steps observed

One line per step. Use the procedure's step numbers. Quote screen text.

| Row ID | Procedure step | What you saw (quote the screen) | Matches expected? |
| --- | --- | --- | --- |
| | | | |
| | | | |
| | | | |

## Evidence files

Every photo, screenshot, recording and log you keep. Compute SHA-256 with
`sha256sum <file>` (Linux), `shasum -a 256 <file>` (macOS) or
`Get-FileHash -Algorithm SHA256 <file>` (Windows).

| File name | Row ID | SHA-256 | Where stored (git path or private store) | Redacted? |
| --- | --- | --- | --- | --- |
| | | | | |
| | | | | |

## Results

Use only: Pass, Fail, Excluded, NOT TESTED, BLOCKED, Unknown
(definitions in the [packet README](../README.md#result-words)).

| Row ID | Result | Evidence file(s) | Reason (required for Fail, Excluded, BLOCKED, Unknown) |
| --- | --- | --- | --- |
| | | | |
| | | | |

## Deviations

Anything you did differently from the procedure, and why. Anything that
surprised you. A deviation can turn a Pass into Unknown; say so here.

-

Operator initials: ____ Date (UTC): ____
