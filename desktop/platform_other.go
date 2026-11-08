// SPDX-License-Identifier: GPL-3.0-or-later
//go:build !linux && !windows

package main

import (
	"context"
	"errors"
	"fmt"
	"os"
	"os/exec"
)

func platformProbe(context.Context) Snapshot        { return Snapshot{Problem: "platform"} }
func platformRestart(string) error                  { return errors.New("unsupported platform") }
func platformElevate(context.Context, string) error { return errors.New("unsupported platform") }
func openBrowser(url string) error                  { return exec.Command("/usr/bin/open", url).Start() }
func notifyFailure(message string)                  { fmt.Fprintln(os.Stderr, message) }
func prepareDesktop() (bool, error)                 { return false, nil }

// Restart to boot options (#183) is Windows only.
func platformAdvancedStartup(context.Context) error { return errAdvancedStartupUnavailable }

// The launcher does not ship for macOS and refuses to plan a restart there, so
// it reads no brand (no sysctl or ioreg). The Boot helper lists the Intel Mac
// key instead.
func platformMachine(context.Context) (machineInfo, error) {
	return machineInfo{}, errMachineUnsupported
}
