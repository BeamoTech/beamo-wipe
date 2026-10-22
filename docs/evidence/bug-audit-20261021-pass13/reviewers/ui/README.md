# Pass13 UI review

Main GTK view construction and event-loop exits now retire the owned window, timer and queued callbacks. Primary failures survive cleanup failures, the exception hook is restored, and peer/nested loops remain owned by their callers.

- Original actual-GTK probe: 4 failures / 1 normal-close control. Root independently reproduced 3 failures / 1 control.
- Exact final 32-case regression bytes before product edit: 28 failures / 4 normal-close controls; repaired: 32 passes.
- Final narrow existing/new lifetime adjacency: 71 passes, no skips/errors/failures, strict warnings, private 72-DPI Xvfb and XDG/D-Bus. Earlier broad baseline review: 683 passes.
- Broader repaired-source adjacency: 344 passes / 2 failures. Existing Orca child startup failed; existing method geometry failed identically on exact baseline source. Both histories are retained and excluded from pass claims. Root will run canonical gates in the supported container.
- Finite nested review-hold/shutdown-discard epoch model: 108 scenarios / 1,926 modeled events, 108 accepted discard controls, 216 old-epoch refusals, 90 busy refusals, 108 immediate-review refusals, 180 overlay refusals and 108 elapsed-gate controls. Zero mismatches or native callbacks. Counts overlap canonical coverage.

Only `src/beamo_wipe/ui/accessible_wizard.py` and `tests/test_accessible_main_lifetime_pass13.py` were edited. Ownership was released to root before the full gate. Final hashes are in `final-owned-source-sha256.json`; all evidence is bound by `artifact-sha256.json`. No engine, native inventory, device, sysfs, mount, firmware, power, guest, network/remote, Docker or build action was performed. Private test children/resources were reaped, and displays :1/:99 were preserved.
