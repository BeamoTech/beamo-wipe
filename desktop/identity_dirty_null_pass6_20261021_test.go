// SPDX-License-Identifier: GPL-3.0-or-later
package main

import (
	"fmt"
	"path/filepath"
	"strings"
	"testing"
)

func TestUSBIdentityDirtyFieldMustBeBooleanPass620261021(t *testing.T) {
	oldCommit, oldDirty := sourceCommit, sourceDirty
	t.Cleanup(func() { sourceCommit, sourceDirty = oldCommit, oldDirty })
	sourceCommit = strings.Repeat("a", 40)
	const releaseBuild = "12345678-1234-1234-1234-123456789abc"
	for _, tc := range []struct {
		name, dirtyJSON, compiledDirty, buildID, status string
		manufactured                                    bool
	}{
		{"null-clean-launcher", "null", "false", releaseBuild, "unavailable", false},
		{"null-dirty-launcher", "null", "true", releaseBuild, "unavailable", false},
		{"null-unknown-launcher", "null", "unknown", releaseBuild, "unavailable", false},
		{"false-production", "false", "false", releaseBuild, "production", true},
		{"false-development", "false", "false", "local", "development", false},
		{"true-dirty", "true", "true", releaseBuild, "dirty", false},
		{"true-mismatch", "true", "false", releaseBuild, "source mismatch", false},
		{"false-mismatch", "false", "true", releaseBuild, "source mismatch", false},
		{"string", `"false"`, "false", releaseBuild, "unavailable", false},
		{"number", "0", "false", releaseBuild, "unavailable", false},
		{"object", "{}", "false", releaseBuild, "unavailable", false},
		{"array", "[]", "false", releaseBuild, "unavailable", false},
	} {
		t.Run(tc.name, func(t *testing.T) {
			sourceDirty = tc.compiledDirty
			root := mediaFixture(t)
			fixtureFile(t, root, "build-identity.json", fmt.Sprintf(
				`{"source_commit":"%s","source_sha256":"%s","build_id":"%s","source_dirty":%s}`,
				sourceCommit, strings.Repeat("b", 64), tc.buildID, tc.dirtyJSON,
			))
			got := loadUSBIdentity(filepath.Join(root, "Start Beamo Wipe Linux"))
			if got.Manufactured != tc.manufactured || got.Status != tc.status {
				t.Fatalf("source_dirty=%s compiled=%q: got %+v; want manufactured=%t status=%q", tc.dirtyJSON, tc.compiledDirty, got, tc.manufactured, tc.status)
			}
		})
	}
}
