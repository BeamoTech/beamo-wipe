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
	"time"
)

// Mutate after both content reads but before mediaDigest's final descriptor
// and pathname checks. The final checks must still describe the returned hash.
type mediaFinalHandoffContextPass14 struct {
	context.Context
	handoffs int
	mutate   func()
}

func (c *mediaFinalHandoffContextPass14) Err() error {
	pc, _, _, ok := runtime.Caller(1)
	if ok && strings.HasSuffix(runtime.FuncForPC(pc).Name(), ".mediaDigest") {
		c.handoffs++
		if c.handoffs == 3 {
			c.mutate()
		}
	}
	return nil
}

func TestMediaDigestFinalChangeTimeSnapshotPass14(t *testing.T) {
	for _, change := range []string{"unchanged", "restored-mtime"} {
		t.Run(change, func(t *testing.T) {
			path := filepath.Join(t.TempDir(), "media-input")
			original := []byte("original-media-bytes")
			if err := os.WriteFile(path, original, 0600); err != nil {
				t.Fatal(err)
			}
			metadata, err := os.Stat(path)
			if err != nil {
				t.Fatal(err)
			}
			changed := false
			ctx := &mediaFinalHandoffContextPass14{
				Context: context.Background(),
				mutate: func() {
					changed = true
					if change == "unchanged" {
						return
					}
					// Some overlay filesystems expose change time at one-second
					// resolution. Cross one tick so the final snapshot assertion
					// exercises the same check deterministically on those hosts.
					time.Sleep(1100 * time.Millisecond)
					if err := os.WriteFile(path, bytes.Repeat([]byte("X"), len(original)), 0600); err != nil {
						t.Fatal(err)
					}
					if err := os.Chtimes(path, metadata.ModTime(), metadata.ModTime()); err != nil {
						t.Fatal(err)
					}
				},
			}
			digest, err := mediaDigest(ctx, path, 1024)
			if !changed {
				t.Fatal("final digest handoff did not execute")
			}
			if change == "unchanged" {
				want := sha256.Sum256(original)
				if err != nil || !bytes.Equal(digest, want[:]) {
					t.Fatalf("normal digest=%x err=%v", digest, err)
				}
			} else if err == nil {
				t.Fatalf("accepted digest for bytes changed before final snapshot: %x", digest)
			}
		})
	}
}
