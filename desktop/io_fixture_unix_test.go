//go:build !windows

// SPDX-License-Identifier: GPL-3.0-or-later
package main

import "os"

func openReadOnlyReplaceableFixture(path string) (*os.File, error) {
	return os.Open(path)
}
