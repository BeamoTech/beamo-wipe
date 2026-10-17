# Startup Tcl callback candidate

Source-only review, 2026-10-17, pass17 UI/boot peer.

`run_tk_startup` queues the polling timer and initial focus idle callback, but its close,
completion and finally paths call `root.destroy` without retiring those callbacks.
Tkinter widget destruction deletes the registered Tcl command; Tcl's global event queue
retains pending `after` scripts. A later interpreter event loop can then emit `invalid
command name`. Pass16's owner-based retirement helper protects `TkWizard`, not this
separate startup presenter. No product edit yet. The native proof will capture Tcl
`bgerror` with `errorInfo` as well as Python callback errors, including abandonment,
external destruction, startup worker failure, mainloop failure and normal results.
Only private interpreters, ordinary fake strings, controlled worker events and fake
native application effects are permitted. Runtime execution awaits root admission.
