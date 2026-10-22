package main

import (
	"encoding/binary"
	"strings"
	"testing"
)

func TestPass12IndependentNativeJSONBoundary(t *testing.T) {
	cases := []struct {
		name   string
		body   string
		direct bool
	}{
		{"normal-usb", linuxFixture, true},
		{"normal-sata", strings.Replace(linuxFixture, `"tran":"usb"`, `"tran":"sata"`, 1), false},
		{"transport-alias", strings.Replace(linuxFixture, `"tran":"usb"`, `"TRAN":"sata","tran":"usb"`, 1), false},
		{"nested-type-alias", strings.Replace(linuxFixture, `"type":"part"`, `"type":"disk","ty\u0070e":"part"`, 1), false},
		{"identity-null-overwrite", strings.Replace(linuxFixture, `"serial":"BEAMO123"`, `"serial":"BEAMO123","serial":null`, 1), false},
		{"invalid-utf8-identity", strings.Replace(linuxFixture, "BEAMO123", "BEAMO\xfe123", 1), false},
		{"unpaired-surrogate-identity", strings.Replace(linuxFixture, "BEAMO123", `BEAMO\udfff123`, 1), false},
	}
	for _, tc := range cases {
		t.Run(tc.name, func(t *testing.T) {
			id, routes, err := linuxMedia([]byte(tc.body), "/dev/sdb1")
			snapshot := Snapshot{UEFI: true, Layout: "owned-fixture", MediaID: id, Partitions: routes, Entries: map[uint16][]byte{}}
			if err == nil {
				entry := option(1)
				entry[48], entry[49] = 1, 1
				binary.LittleEndian.PutUint32(entry[32:], 0x12345678)
				snapshot.Entries[4] = entry
			} else {
				snapshot.Problem = "media"
			}
			plan := makePlanForHost(snapshot, "linux")
			if plan.Direct != tc.direct {
				t.Fatalf("direct=%t id=%q routes=%v parseErr=%v want=%t", plan.Direct, id, routes, err, tc.direct)
			}
		})
	}
}
