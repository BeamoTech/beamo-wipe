// SPDX-License-Identifier: GPL-3.0-or-later
package main

import (
	"bytes"
	"context"
	"crypto/sha256"
	"os"
	"path/filepath"
	"runtime"
	"strings"
	"testing"
)

// Mutate at the first completed digest's context handoff, independently of
// how many bounded reader calls the implementation needed to hash the file.
type mediaHandoffContextPass13 struct {
	context.Context
	handoffs int
	mutate   func()
}

func (c *mediaHandoffContextPass13) Err() error {
	pc, _, _, ok := runtime.Caller(1)
	if ok && strings.HasSuffix(runtime.FuncForPC(pc).Name(), ".mediaDigest") {
		c.handoffs++
		if c.handoffs == 2 {
			c.mutate()
		}
	}
	return nil
}

func TestMediaDigestFinalSnapshotPass13(t *testing.T) {
	for _, change := range []string{"unchanged", "same-size", "restored-mtime", "mode", "replace", "append", "truncate"} {
		t.Run(change, func(t *testing.T) {
			if change == "replace" && runtime.GOOS == "windows" {
				t.Skip("Windows denies replacing a file while mediaDigest holds it open")
			}
			path := filepath.Join(t.TempDir(), "owned-media-input")
			t.Cleanup(func() { _ = os.Chmod(path, 0600) })
			original := []byte("fixture-content-0123456789")
			if err := os.WriteFile(path, original, 0600); err != nil {
				t.Fatal(err)
			}
			metadata, err := os.Stat(path)
			if err != nil {
				t.Fatal(err)
			}
			changed := false
			ctx := &mediaHandoffContextPass13{Context: context.Background(), mutate: func() {
				changed = true
				var err error
				switch change {
				case "same-size", "restored-mtime":
					err = os.WriteFile(path, bytes.Repeat([]byte("X"), len(original)), 0600)
				case "mode":
					err = os.Chmod(path, 0400)
				case "replace":
					replacement := path + ".replacement"
					err = os.WriteFile(replacement, original, 0600)
					if err == nil {
						err = os.Rename(replacement, path)
					}
				case "append":
					err = os.WriteFile(path, append(append([]byte{}, original...), []byte("new")...), 0600)
				case "truncate":
					err = os.WriteFile(path, original[:len(original)-3], 0600)
				}
				if err != nil {
					t.Fatal(err)
				}
				if change == "restored-mtime" {
					if err = os.Chtimes(path, metadata.ModTime(), metadata.ModTime()); err != nil {
						t.Fatal(err)
					}
				}
			}}
			digest, err := mediaDigest(ctx, path, 1024)
			if !changed {
				t.Fatal("post-digest handoff did not execute")
			}
			if change == "unchanged" {
				sum := sha256.Sum256(original)
				if err != nil || !bytes.Equal(digest, sum[:]) {
					t.Fatalf("normal digest=%x err=%v", digest, err)
				}
			} else if err == nil {
				t.Fatalf("accepted changed media snapshot: %s", change)
			}
			current, readErr := os.ReadFile(path)
			if readErr != nil {
				t.Fatal(readErr)
			}
			if change == "same-size" || change == "restored-mtime" {
				if !bytes.Equal(current, bytes.Repeat([]byte("X"), len(original))) {
					t.Fatal("mutation was altered")
				}
			}
		})
	}
}
