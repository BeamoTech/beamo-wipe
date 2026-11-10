# Cold-readback form (#116)

Copy this file once per erased disk. Name the copy
`cold-<row ID>-<run ID>.md`, for example `cold-PHY-COLD-01-RUN-20270115-01.md`.
The procedure is [P7](../procedures.md#p7-cold-readback-after-an-erase).

A warm read in the same session, a software re-scan or a virtual disk never
fills this form. If the disk was not powered off and reconnected, stop.

## Link to the erase

| Field | Value |
| --- | --- |
| Cold row ID (PHY-COLD-__) | |
| Erase row ID (PHY-ERASE-__ or PHY-INT-__) and run ID | |
| Target disk ID, model, capacity, serial (last 4) | |
| Method and result headline shown | |
| Seed marker and `present` hit count before the erase (P5 step 7) | |

## Cold handling

| Field | Value |
| --- | --- |
| Computer shut down from the wizard and fully off at (UTC) | |
| Wall power removed and waited 60 seconds? | yes / no |
| Route A: disk removed and moved to the QA workstation (enclosure model, if any) | |
| Route B: same computer, separate read-only Linux live USB (name and SHA-256) | |
| Time from power-off to read (minutes) | |
| QA workstation automount off? Disk never mounted? | yes / no |
| Whole-disk path used (`/dev/disk/by-id/…`, serial part redacted) | |
| `lsblk -o NAME,SIZE,MODEL,TRAN,RM,MOUNTPOINTS` output file and SHA-256 | |

## Scanner result

| Field | Value |
| --- | --- |
| Scanner mode (`zero`, `absent` or `present`) | |
| Command as run (marker shown, device path redacted) | |
| Exit code (0 PASS, 1 FAIL, 2 STOP) | |
| `Read … bytes` line | |
| SHA-256 line | |
| `All bytes zero` / first non-zero offset / marker hits | |
| `COLD READBACK …` line | |
| Output saved as (file name and SHA-256) | |
| Disk size the firmware or label states, if it differs from bytes read | |

## Result

| Field | Value |
| --- | --- |
| Row result (Pass / Fail / BLOCKED / Unknown) | |
| Reason | |

A Pass means the bytes the computer can read matched. It does not cover
hidden areas (HPA, DCO, spare or remapped flash). It is not a certificate.

Operator initials: ____ Date (UTC): ____
