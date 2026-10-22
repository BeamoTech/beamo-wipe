// SPDX-License-Identifier: GPL-3.0-or-later
package main

import (
	"context"
	"os/exec"
	"strings"
	"testing"
	"time"
)

func TestPass11RootOutputDrainDeadline(t *testing.T) {
	for _, mode := range []string{"normal", "direct-timeout", "stdout", "stderr", "both"} {
		t.Run(mode, func(t *testing.T) {
			ctx, cancel := context.WithTimeout(context.Background(), 150*time.Millisecond)
			defer cancel()
			cmd := exec.CommandContext(ctx, "/workspace/beamo-wipe/.venv-linux/bin/python", "/workspace/beamo-tools/audit-pass11-20261021/root/pipe_lifetime_helper.py", mode)
			start := time.Now()
			data, err := boundedOutput(cmd, 1024)
			elapsed := time.Since(start)
			if mode == "normal" {
				if err != nil || strings.TrimSpace(string(data)) != "normal-output" {
					t.Fatalf("normal helper: data=%q err=%v", data, err)
				}
			} else if err == nil {
				t.Errorf("expired helper/pipes reported success: data=%q elapsed=%v", data, elapsed)
			}
			// Four times the process deadline permits scheduling overhead while
			// distinguishing the finite 1.2s inherited-pipe fixture.
			if elapsed > 600*time.Millisecond {
				t.Errorf("output drain exceeded caller deadline: %v", elapsed)
			}
		})
	}
}
