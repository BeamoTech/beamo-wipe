# Restart to boot options on Windows (#183)

The Windows launcher can offer **Restart to boot options**: one confirmed
click restarts Windows to its "Choose an option" screen (Windows Recovery
Environment), where the owner chooses **Use a device** and then the Beamo USB.
Nobody has to find the boot-menu key. It is optional. The #184 boot-menu key
for the computer's brand stays on the same page, and it is the fallback.

## When it is offered

Only when every one of these holds; otherwise the page shows today's
boot-menu guidance unchanged:

- Windows on a 64-bit Intel/AMD UEFI computer (legacy BIOS has no Use a device).
- The launcher was opened from the identified Beamo USB (the existing USB check).
- Windows 10 or later (build 10240+, read with `RtlGetVersion`).
- A completed check (`/api/check`) whose revision the request repeats.

Linux keeps its guided restart. macOS, Chromebooks and the preview never
offer it. Preview answers "No restart was requested" and calls nothing.

## What happens

1. The page explains the next screens and warns the owner to save their work.
2. The owner ticks "I've saved my work and closed my applications. Restart
   this computer now." and chooses **Restart to boot options**.
3. The launcher runs `%WINDIR%\System32\shutdown.exe /r /o /t 0`: restart
   (`/r`) to the advanced boot options (`/o`), no delay (`/t 0`). It names the
   full path (no PATH lookup) and never adds `/f`.
4. Windows shows **Choose an option** → **Use a device** → the Beamo USB, which
   may be listed as **EFI USB Device** or by the USB's brand.
5. Beamo Wipe starts from the USB. The owner still ticks ownership, types the
   confirmation, waits through the countdown and presses Erase now. A restart
   never authorizes an erase.

The reviewed check is single-use, like the Linux guided restart: after one
request the page needs Check again.

## Elevation

None. `shutdown /r` needs the **Shut down the system** user right
(SeShutdownPrivilege), which ordinary users of Windows client editions have by
default ([Microsoft: shutdown](https://learn.microsoft.com/en-us/windows-server/administration/windows-commands/shutdown),
"Users must be assigned the Shut down the system user right"). The launcher does
not ask for administrator rights and does not elevate. If a policy removes
the right, or another signed-in user blocks the restart, `shutdown.exe` exits
nonzero and the page says "Windows did not restart to the boot options.
Nothing was changed and nothing was erased." and points to the boot-menu key
and the Settings → Recovery → Advanced startup path.

`/o` must be used with `/r` (same Microsoft page). With `/t 0`, `/f` is not
implied, so Windows can still stop for an application with unsaved work. If
the owner cancels at that point, the page has already said to use the
boot-menu key instead.

## BitLocker

- The launcher changes no firmware setting, boot order, BootNext, Secure Boot
  or BCD entry, and does not suspend or touch BitLocker.
- **Use a device** is a one-time firmware start of the USB. It is the same
  path the Boot helper already documents through Settings. Choosing it should
  not need the recovery key.
- Other choices on the **Choose an option** screen (Troubleshoot → Command
  Prompt, System Restore, Startup Settings and so on) can ask for the
  BitLocker recovery key, because Windows Recovery Environment must unlock
  the drive for them ([Microsoft: BitLocker recovery overview](https://learn.microsoft.com/en-us/windows/security/operating-system-security/data-protection/bitlocker/recovery-overview)).
  The page says to choose only Use a device and that Beamo Wipe does not need
  those tools.
- Returning to Windows afterwards (choose Continue, or start without the USB)
  is an ordinary start. The Boot helper's BitLocker section still applies to
  any firmware change, which this route avoids.

## Safety of the code path

- The browser can only POST `/api/advanced-startup` with `{"confirm":true,
  "revision":N}` and the session token. It cannot pass a command, path or
  switch. The server rejects a missing confirmation, a stale revision, a plan
  that did not offer the restart and the Linux direct plan (409).
- `app.advancedStartup` is an injected function. `run()` is the only place
  that wires the real `platformAdvancedStartup`; tests build `app` values
  with fakes and never call `run()` or `main()`.
- `platformAdvancedStartup` on Windows starts with `advancedStartupGuard()`,
  which returns an error inside any `go test` binary (`testing.Testing()`),
  before any command is built. Linux and other builds return "unavailable".
- `desktop/advanced_startup_test.go` proves these facts from the parsed
  source: no test names the real runner or calls `run()`/`main()`; production
  code references it only from `run()`; the Windows runner's first statement
  is the guard and its command comes only from `advancedStartupArgs`; the
  string `shutdown.exe` appears nowhere else. Removing the guard or the
  wiring makes the test fail (mutation-checked on 2026-11-08).
- The launcher still erases nothing.

## Not verified here

The task asks for checks on supported Windows versions in a VM. No VM is
authorized on the development host, and that host must never restart, so the
real restart, the WinRE screens, "EFI USB Device" naming, the policy-denied
exit code and BitLocker behavior are **NOT TESTED**. They need an isolated,
disposable Windows 10 and Windows 11 UEFI guest (with and without BitLocker,
standard and administrator users, a policy that removes the shutdown right)
before release.

Also not verified: whether Windows, after the owner cancels the restart at the
"apps are preventing restart" prompt, still opens the boot options at the next
restart. If it does, choosing Continue returns to Windows. No BootNext or
other firmware variable is written either way.
