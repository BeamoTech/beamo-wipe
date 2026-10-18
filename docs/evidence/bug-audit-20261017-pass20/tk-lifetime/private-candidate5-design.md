# Private candidate5 source handoff

2026-10-17 / pass20_tk_lifetime. **AST-parsed source only; no runtime by author.**
Active private tree, shared product source, and canonical tests were not edited.

Base: `/tmp/pass20-primary/private-candidate4-agent.py`, SHA256
`68b25648c658e5dc9de1e9f7edf3663c90f4dc52520852a8ea8458aa40f8327f`.
Candidate: `/tmp/pass20-primary/private-candidate5-agent.py`, SHA256
`6b5be8d70416318a83b24e3ce6bc9dc212ab63293d2498889810401ecccbfdbe`.
The exact patch, AST receipt, and transformation script are beside the candidate.

Root reports original/fixed-candidate evidence separately: v3 on candidate3 is
14 assertion failures/5 controls; v3 on candidate4 is 5 assertion failures/14
passes. Root also reproduced Font equality failure in list.remove when an
uninitialized Font wrapper precedes a real Font. Those are root-owned runtime
results, not executions by this reviewer. They support the next private change;
they do not establish candidate5 acceptance.

Changes from candidate4:

- Real partial Tk wrappers expose native state through their actual instance
  dictionary. No Tk.__getattr__ lookup occurs before `tk` initialization.
- Asset/interpreter pools use integer identity keys. Drains snapshot dictionary
  items and remove a key only when its current record is the exact same tuple.
  Font/Variable value equality is never called. The separate asset helper still
  returns before raw interpreter draining, preserving correct temporary-ref
  ordering and creating-thread-only native release.
- `TkWizard.run` encloses focus/map setup and mainloop in the same original-error
  preserving retirement boundary. The outer run_tk boundary remains a second
  idempotent ownership guard.
- Public `run_tk_startup` owns root allocation and every subsequent exit. The
  existing window configuration/widgets/stage worker/render/poll logic moves
  into a private window helper. A failure constructing the first Frame or Label
  now reaches the outer root close, as do geometry/configuration failures and
  propagated interruptions.
- Startup native TclError construction still raises StartupDisplayUnavailable
  with the original TclError cause and original message. Other controlled
  exceptions retain their exact object and traceback. Lightweight callable root
  factories retain their normal call contract.
- The window helper still breaks the recursive poll cell and cancels the exact
  owned after IDs. The public owner performs final root destruction after that
  cleanup. Immediate close/poll callbacks retain their existing destruction and
  startup outcome behavior. Secondary timer-cleanup errors cannot replace an
  already propagating original error.

The public startup wrapper creates its actual StartupRun before root allocation,
as before. Native setup failure starts no build thread. On a live control,
StartupRun's actual worker, report queue, outcome poll, and result tuple remain
unchanged. No app, engine, physical disk, mount, firmware, or host operation is
introduced by the prepared proof or private source.

No full collection was added to redraw; its drain is lightweight. No native
wrapper handle, destructor, traceback frame, GC mode, or threshold is changed.
Pool entries with external peer/traceback owners deliberately defer until a
later creating-thread sweep or process exit. Non-main external Tk embeddings
whose owner thread exits before settlement remain outside qualification.

Root must independently review/freeze the candidate, execute all prepared
original/fixed proofs and adjacent behavior, then refresh the exact-source full
local gate and artifact verification. This handoff claims no candidate5 test,
native acceptance, commit, push, or release.
