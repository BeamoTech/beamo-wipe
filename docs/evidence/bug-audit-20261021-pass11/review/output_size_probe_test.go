// SPDX-License-Identifier: GPL-3.0-or-later
package main

import (
	"context"
	"fmt"
	"os/exec"
	"testing"
	"time"
)

func TestPass11RootOutputCaptureLimit(t *testing.T) {
	for _, limits := range [][2]int{{0, 0}, {1, 1}, {1024, 1024}, {0, 1}, {1, 2}, {1024, 1025}, {1024, 65536}} {
		max, size := limits[0], limits[1]
		t.Run(fmt.Sprintf("max%d-size%d", max, size), func(t *testing.T) {
			ctx, cancel := context.WithTimeout(context.Background(), 2*time.Second)
			defer cancel()
			cmd := exec.CommandContext(ctx, "/workspace/beamo-wipe/.venv-linux/bin/python", "/workspace/beamo-tools/audit-pass11-20261021/root/output_size_helper.py", fmt.Sprint(size))
			data, err := boundedOutput(cmd, max)
			if size <= max {
				if err != nil || len(data) != size {
					t.Fatalf("normal output changed: max=%d size=%d got=%d err=%v", max, size, len(data), err)
				}
			} else if err == nil || len(data) > max {
				t.Fatalf("capture limit bypass: max=%d size=%d got=%d err=%v", max, size, len(data), err)
			}
		})
	}
}
