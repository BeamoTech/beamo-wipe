// SPDX-License-Identifier: GPL-3.0-or-later
package main

import (
	"os"
	"syscall"
)

func openReadOnlyReplaceableFixture(path string) (*os.File, error) {
	name, err := syscall.UTF16PtrFromString(path)
	if err != nil {
		return nil, err
	}
	// Go's ordinary Windows open disallows rename while the handle is open.
	// Permit that operation in this synthetic replacement-race fixture, while
	// retaining a genuinely read-only handle so the write must fail.
	handle, err := syscall.CreateFile(name, syscall.GENERIC_READ,
		syscall.FILE_SHARE_READ|syscall.FILE_SHARE_WRITE|syscall.FILE_SHARE_DELETE,
		nil, syscall.OPEN_EXISTING, syscall.FILE_ATTRIBUTE_NORMAL, 0)
	if err != nil {
		return nil, err
	}
	return os.NewFile(uintptr(handle), path), nil
}
