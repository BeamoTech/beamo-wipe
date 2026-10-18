# Pass16 discovery repair design review

2026-10-17, source-only review by discovery delegate. Original351-case module independently replayed by root:159 intended AssertionError failures/192controls,0errors/skips on unchanged751 starting inputs. This note approves the proposed design, not unseen final bytes or any unrun gate.

## Repeated physical observations

Approve retaining a per-call set of canonical physical paths encountered more than once, populated beside the existing physical signature comparison. Keep existing immediate refusal for contradictory core facts. After the ordinary selectable list is constructed, refuse when a repeated physical path is represented by exactly one surviving selectable row.

Why this preserves contracts:

- The surviving row cannot prove uniqueness when another physical observation disappeared through malformed model/vendor/layout validation. This applies even when retained core facts match; it must not rely on finding a particular different valid metadata field.
- Two complete identical target rows remain two rows, so existing exact-one identity validation refuses. Do not collapse or remove them merely to repair this bug.
- Identical boot/read-only/hidden duplicates do not have a surviving selectable target at that path and preserve unrelated legitimate targets. Optical boot presentation may retain only one rom row; it is never selectable and must not trigger a blanket count rule.
- A malformed standalone row at another physical path does not enter the repeated set and keeps the existing per-row skip contract. Safety-only alias/mount context remains available, so an omitted row cannot weaken boot/mounted closure.
- Mounted malformed metadata still triggers existing full refusal. Invalid-vs-missing IDs and core RO/size/transport/identity contradictions remain handled by current physical signatures.
- Canonical paths must be used consistently in both the repeated set and selectable-row counts. Raw /dev alias spelling cannot establish a second unique device.
- Per-call local sets/counts cannot contaminate clean retries. The public wrapper returns a closed result for raised ValueError; direct parser retains its existing malformed-input exception behavior.

No new public model field or identity-API change is required for the normal discovery path. A caller can already construct arbitrary DiscoveryResult/selectable data; that is not a supported reason to expand this minimal repair. Existing runner/wizard rediscovery uses public discovery, which will enforce the invariant.

## Optical cmdline competition

Approve replacing both type=disk-only hit/competitor loops within the cmdline fallback with a local flattened collection restricted to disk and rom. Preserve the current early authoritative live-mount return, source-resolution checks, and `_could_be_live_medium` positive-size rule.

- A cmdline hit resolved to rom must compete with every other target-sized physical disk, because stale optical metadata cannot establish which disk is the live USB while mounts are unavailable.
- A cmdline disk hit also must see a competing nonzero rom; the existing label fallback already uses disk+rom competition.
- Zero-size competitor rows remain noncompeting. No threshold other than positive size, transport claim, hotplug flag or naming heuristic proves that another actual disk is not the live medium.
- Authoritative live-mount identity remains usable with other disks present, including ordinary optical live boots. Env/test override semantics and the disk picker helper are unchanged.
- Nested/stacked live sources still fail in existing `_resolve_boot_path` validation. This change cannot promote a holder/partition/loop to a physical boot path.

No supported new concern found in the proposed design. Final approval remains conditional on inspecting the actual incremental diff/hashes and required regression/gate outcomes. No product edits, runtime work, staging, commit, push or release performed by this reviewer.
