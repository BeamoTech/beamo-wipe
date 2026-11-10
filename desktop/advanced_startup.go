// SPDX-License-Identifier: GPL-3.0-or-later
package main

import (
	"context"
	"errors"
	"net/http"
	"path/filepath"
	"testing"
	"time"
)

// Restart to boot options (#183).
//
// On Windows the launcher may restart the computer into Windows Recovery
// Environment's "Choose an option" screen, where the owner picks Use a device
// and then the Beamo USB. This is the documented equivalent of
// `shutdown /r /o /t 0`. It writes no BootNext or other startup setting, does
// not force applications closed (no /f), needs no administrator rights (only
// the ordinary "Shut down the system" user right) and never erases anything.
//
// Safety of this development and test host: the real runner is reached only
// through app.advancedStartup, which only run() wires to
// platformAdvancedStartup. Tests construct app values directly with a fake
// runner. platformAdvancedStartup also refuses inside any `go test` binary
// (advancedStartupGuard) before it builds a command, and
// advanced_startup_test.go checks both facts on the source.

var errAdvancedStartupUnavailable = errors.New("restart to boot options is unavailable")
var errAdvancedStartupInTest = errors.New("restart to boot options refused inside a test binary")

// advancedStartupGuard is the first statement of every real runner.
func advancedStartupGuard() error {
	if testing.Testing() {
		return errAdvancedStartupInTest
	}
	return nil
}

// advancedStartupArgs is the exact command: Windows' own shutdown.exe from
// the Windows directory (never a PATH lookup), restart (/r) to the advanced
// boot options (/o) with no delay (/t 0). /t 0 keeps /f off, so Windows still
// lets applications with unsaved work stop the restart.
func advancedStartupArgs(windowsDir string) []string {
	return []string{filepath.Join(windowsDir, "System32", "shutdown.exe"), "/r", "/o", "/t", "0"}
}

const advancedStartupRunTimeout = 30 * time.Second

const advancedStartupAccepted = "Windows accepted the restart. On the blue Choose an option screen, choose Use a device, then the Beamo USB (it may be listed as EFI USB Device). If an application asks to save, save and let Windows continue, or cancel and use the boot-menu key instead."

const advancedStartupFailed = "Windows did not restart to the boot options. Nothing was changed and nothing was erased. Use the boot-menu key for this computer shown on this page, or Windows Settings → System → Recovery → Advanced startup → Restart now → Use a device."

// advancedStartupRequest answers /api/advanced-startup. The caller holds a.mu.
func (a *app) advancedStartupRequest(w http.ResponseWriter, body apiRequest) {
	if !body.Confirm || !a.p.AdvancedStartup || (a.revision != 0 && body.Revision != a.revision) {
		a.mu.Unlock()
		http.Error(w, "Check readiness and confirm first", 409)
		return
	}
	if a.preview {
		a.mu.Unlock()
		sendJSON(w, map[string]string{"message": "Preview complete. No restart was requested and nothing was erased."})
		return
	}
	runner := a.advancedStartup
	a.busy = true
	a.p = Plan{}
	// The reviewed plan is single-use, as for the Linux guided restart.
	a.revision++
	a.current = planView(Plan{}, false)
	a.current.Revision = a.revision
	a.mu.Unlock()
	err := errAdvancedStartupUnavailable
	if runner != nil {
		ctx, cancel := context.WithTimeout(context.Background(), advancedStartupRunTimeout)
		err = runner(ctx)
		cancel()
	}
	a.mu.Lock()
	a.busy = false
	a.mu.Unlock()
	if err != nil {
		http.Error(w, advancedStartupFailed, 503)
		return
	}
	sendJSON(w, map[string]string{"message": advancedStartupAccepted})
}
