# PASS9 boot/build bounded review

Baseline `e28487d7595ee45a53d503fa1a76d8c22979f012`. Read-only review completed;
no new product defect proved, no source edit, ownership released.

Reviewed desktop API authentication, JSON decoding, revision/single-use consent,
readiness/probe timeouts, Windows manual-only restart policy, EFI route parsing,
firmware inventory, exclusive BootNext transaction/rollback, regular-input binding,
media/fingerprint identity, compiler-input snapshots, output lock/publication and
manifest validation, staged live assets, entrypoint isolation and kiosk fallback.
No suspected issue was promoted without a concrete supported failing behavior.

Fresh results:
- 25 focused Python modules:255 unique passes; no failures/errors/skips/Python warnings.
- Full Linux Go suite with race:338 named pass events; two explicitly unverified
  native inventory skips (`TestLinuxInventoryRetainsPartitionParents`,
  `TestWindowsInventoryReportsOnlyLauncherPartitionPass13`); vet exits0.
- External deterministic firmware model:150 inventory cases including40 readable
  positive controls;6,048 transaction cases including9 successful restart controls,
  6,039 refusals and288 foreign-request preservation controls. Zero mismatches or
  native callbacks. Its sole Go test event is supporting evidence, not canonical
  Go/Python suite coverage. Model formatted and rerun on exact final bytes.

Model uses fake firmware maps only; callbacks labelled reboot never call an OS API.
Native inventory was not enabled. There were no Docker, actual inventory, firmware,
restart, engine, physical-device, guest, hosted CI or publication actions.
Owned regular temporary fixtures used by existing tests remain test-only.
Native Windows, actual firmware/boot/USB and isolated ISO/KVM remain unverified.
Root must independently replay model and validate summary/source hashes.

Reproduce:
`source /workspace/beamo-tools/activate.sh`
`cd /workspace/beamo-wipe/desktop`
`go test -count=1 -race -overlay=/workspace/beamo-tools/audit-pass9-20261021/boot/overlay.json -run '^TestPass9FirmwareContractMatrix$' -v .`

The overlay maps a nonexistent test path to this external model; it changes no
tracked checkout file. Metrics output path is external and may be rebound for
root's independent run. Exact commands, actual exit receipts and source hashes
are adjacent. The two initial boot-prefixed group receipts also remain under
`../root/` because the shared root runner chooses its own containing directory;
identical copies are retained here, with no outcome relabeling.
