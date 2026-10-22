package main

import (
 "strings"
 "testing"
)

func TestPass12NativeParseProbe(t *testing.T) {
 base := linuxFixture
 cases := []struct { name, body string; accept bool }{
  {"valid", base, true},
  {"sata-refused", strings.Replace(base, `"tran":"usb"`, `"tran":"sata"`, 1), false},
  {"contradictory-transport", strings.Replace(base, `"tran":"usb"`, `"tran":"sata","tran":"usb"`, 1), false},
  {"duplicate-same-transport", strings.Replace(base, `"tran":"usb"`, `"tran":"usb","tran":"usb"`, 1), false},
  {"escaped-duplicate-transport", strings.Replace(base, `"tran":"usb"`, `"tran":"sata","tr\u0061n":"usb"`, 1), false},
  {"case-duplicate-transport", strings.Replace(base, `"tran":"usb"`, `"tran":"sata","TRAN":"usb"`, 1), false},
  {"contradictory-source-path", strings.Replace(base, `"path":"/dev/sdb1"`, `"path":"/dev/sdc1","path":"/dev/sdb1"`, 1), false},
  {"duplicate-root", strings.Replace(base, `{"blockdevices":`, `{"blockdevices":[],"blockdevices":`, 1), false},
  {"serial-null-last", strings.Replace(base, `"serial":"BEAMO123"`, `"serial":"BEAMO123","serial":null`, 1), false},
  {"string-size-control", strings.Replace(base, `"size":8000000000`, `"size":"8000000000"`, 1), true},
  {"overflow-size-refused", strings.Replace(base, `"size":8000000000`, `"size":18446744073709551616`, 1), false},
  {"invalid-utf8-serial", strings.Replace(base, `BEAMO123`, "BEAMO\xff123", 1), false},
  {"invalid-utf16-serial", strings.Replace(base, `BEAMO123`, `BEAMO\ud800123`, 1), false},
 }
 for _, tc := range cases { t.Run(tc.name, func(t *testing.T) {
  id, routes, err := linuxMedia([]byte(tc.body), "/dev/sdb1")
  if (err == nil && id != "" && len(routes) == 1) != tc.accept { t.Fatalf("accepted=%v id=%q routes=%v err=%v want=%v", err == nil, id, routes, err, tc.accept) }
 }) }
}
