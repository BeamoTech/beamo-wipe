// SPDX-License-Identifier: GPL-3.0-or-later
package main

import (
	"encoding/binary"
	"strings"
	"testing"
)

func TestNativeInventoryJSONEvidencePass12(t *testing.T) {
	replace := func(old, value string) string { return strings.Replace(linuxFixture, old, value, 1) }
	cases := []struct {
		name, body string
		valid      bool
	}{
		{"ordinary", linuxFixture, true},
		{"whitespace", " \n\t" + linuxFixture + "\n ", true},
		{"single-case-alias", replace(`"tran"`, `"TRAN"`), true},
		{"single-escaped-key", replace(`"tran"`, `"tr\u0061n"`), true},
		{"numeric-strings", strings.NewReplacer(`:8000000000`, `:"8000000000"`, `:512`, `:"512"`, `:2048`, `:"2048"`, `:2097152`, `:"2097152"`).Replace(linuxFixture), true},
		{"unicode-serial", replace("BEAMO123", "BEAMO-雪-🛰"), true},
		{"paired-surrogates", replace("BEAMO123", `BEAMO-\ud83d\udef0`), true},
		{"unknown-nested-fields", replace(`"serial":"BEAMO123"`, `"serial":"BEAMO123","extra":{"first":[1,{"second":true}],"third":null}`), true},
		{"unknown-large-number", replace(`"serial":"BEAMO123"`, `"serial":"BEAMO123","extra":1e400`), true},
		{"repeated-key-in-separate-objects", replace(`"serial":"BEAMO123"`, `"serial":"BEAMO123","extra":[{"x":1},{"x":2}]`), true},
		{"sata", replace(`"tran":"usb"`, `"tran":"sata"`), false},
		{"root-exact-duplicate", replace(`{"blockdevices":`, `{"blockdevices":[],"blockdevices":`), false},
		{"root-case-duplicate", replace(`{"blockdevices":`, `{"BLOCKDEVICES":[],"blockdevices":`), false},
		{"root-escaped-duplicate", replace(`{"blockdevices":`, `{"blockdevice\u0073":[],"blockdevices":`), false},
		{"transport-exact-duplicate", replace(`"tran":"usb"`, `"tran":"sata","tran":"usb"`), false},
		{"transport-case-duplicate", replace(`"tran":"usb"`, `"tran":"sata","TRAN":"usb"`), false},
		{"transport-escaped-duplicate", replace(`"tran":"usb"`, `"tran":"sata","tr\u0061n":"usb"`), false},
		{"identical-duplicate", replace(`"tran":"usb"`, `"tran":"usb","tran":"usb"`), false},
		{"null-last-duplicate", replace(`"serial":"BEAMO123"`, `"serial":"BEAMO123","serial":null`), false},
		{"unicode-fold-duplicate", replace(`"serial":"BEAMO123"`, `"serial":"BEAMO123","\u017ferial":"OTHER"`), false},
		{"nested-source-duplicate", replace(`"path":"/dev/sdb1"`, `"path":"/dev/sdc1","path":"/dev/sdb1"`), false},
		{"nested-geometry-duplicate", replace(`"start":2048`, `"START":4096,"start":2048`), false},
		{"nested-array-duplicate", replace(`"children":[`, `"children":[],"CHILDREN":[`), false},
		{"unknown-object-duplicate", replace(`"serial":"BEAMO123"`, `"serial":"BEAMO123","extra":{"x":1,"X":2}`), false},
		{"unknown-array-object-duplicate", replace(`"serial":"BEAMO123"`, `"serial":"BEAMO123","extra":[{"x":1,"\u0078":2}]`), false},
		{"invalid-utf8-serial", replace("BEAMO123", "BEAMO\xff123"), false},
		{"invalid-utf8-unknown-key", replace(`"serial":"BEAMO123"`, "\"serial\":\"BEAMO123\",\"bad\xffkey\":true"), false},
		{"unpaired-high-surrogate", replace("BEAMO123", `BEAMO\ud800123`), false},
		{"unpaired-low-surrogate", replace("BEAMO123", `BEAMO\udc00123`), false},
		{"reversed-surrogates", replace("BEAMO123", `BEAMO\udef0\ud83d`), false},
		{"replacement-rune", replace("BEAMO123", "BEAMO�123"), false},
		{"escaped-replacement-rune", replace("BEAMO123", `BEAMO\ufffd123`), false},
		{"malformed-unknown-string", replace(`"serial":"BEAMO123"`, `"serial":"BEAMO123","extra":"\ud800"`), false},
		{"malformed-unknown-key", replace(`"serial":"BEAMO123"`, `"serial":"BEAMO123","\ud800":true`), false},
		{"wrong-size-type", replace(`"size":8000000000`, `"size":true`), false},
		{"overflow-size", replace(`"size":8000000000`, `"size":18446744073709551616`), false},
		{"trailing-object", linuxFixture + `{}`, false},
		{"trailing-null", linuxFixture + `null`, false},
		{"stray-delimiter", linuxFixture + `]`, false},
		{"truncated", strings.TrimSuffix(linuxFixture, "}"), false},
	}
	for _, tc := range cases {
		t.Run(tc.name, func(t *testing.T) {
			id, routes, err := linuxMedia([]byte(tc.body), "/dev/sdb1")
			if !tc.valid {
				if err == nil {
					t.Fatalf("ambiguous or malformed native evidence accepted: id=%q routes=%v", id, routes)
				}
				return
			}
			if err != nil || id == "" || len(routes) != 1 || routes[0] != "mbr:12345678:1:2048:4096" {
				t.Fatalf("valid native evidence refused: id=%q routes=%v err=%v", id, routes, err)
			}
			entry := option(1)
			entry[48], entry[49] = 1, 1
			binary.LittleEndian.PutUint32(entry[32:], 0x12345678)
			snapshot := Snapshot{UEFI: true, Layout: "fake-layout", MediaID: id, Partitions: routes, Entries: map[uint16][]byte{4: entry}}
			plan := makePlanForHost(snapshot, "linux")
			checks, _ := explainReadiness(snapshot, plan)
			if !plan.Direct || checks[0].State != "pass" || checks[2].State != "pass" {
				t.Fatalf("positive fake readiness control refused: plan=%+v checks=%v", plan, checks)
			}
		})
	}
}
