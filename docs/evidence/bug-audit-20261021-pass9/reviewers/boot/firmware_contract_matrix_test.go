// External PASS9 evidence: pure fake firmware, no platform callbacks.
package main

import (
	"bytes"
	"encoding/binary"
	"encoding/json"
	"errors"
	"fmt"
	"os"
	"testing"
)

type pass9InventoryFirmware struct {
	values          map[string][]byte
	denied          map[string]bool
	writes, removes int
}

func (f *pass9InventoryFirmware) read(n string) ([]byte, error) {
	if f.denied[n] {
		return nil, errors.New("fake unreadable")
	}
	v, ok := f.values[n]
	if !ok {
		return nil, errAbsent
	}
	return append([]byte(nil), v...), nil
}
func (f *pass9InventoryFirmware) write(string, []byte) (bool, error) {
	f.writes++
	return false, errors.New("unexpected fake write")
}
func (f *pass9InventoryFirmware) remove(string) error {
	f.removes++
	return errors.New("unexpected fake remove")
}

type pass9TxFirmware struct {
	state                              []byte
	blocked                            bool
	reads, writes, removes             int
	pre, writeMode, verify, removeMode string
}

func (f *pass9TxFirmware) read(string) ([]byte, error) {
	f.reads++
	if f.reads == 1 {
		switch f.pre {
		case "present":
			return []byte{89, 0}, nil
		case "unreadable":
			return nil, errors.New("fake unreadable")
		}
		return nil, errAbsent
	}
	if f.reads == 2 && f.writeMode == "success" {
		switch f.verify {
		case "absent":
			f.state = nil
		case "different":
			f.state = []byte{89, 0}
		case "unreadable":
			f.blocked = true
		}
	}
	if f.blocked {
		return nil, errors.New("fake unreadable")
	}
	if f.state == nil {
		return nil, errAbsent
	}
	return append([]byte(nil), f.state...), nil
}
func (f *pass9TxFirmware) write(_ string, v []byte) (bool, error) {
	f.writes++
	switch f.writeMode {
	case "success":
		f.state = append([]byte(nil), v...)
		return true, nil
	case "foreign_same":
		f.state = append([]byte(nil), v...)
		return false, errors.New("fake competing exclusive create")
	case "foreign_different":
		f.state = []byte{89, 0}
		return false, errors.New("fake competing exclusive create")
	case "owned_error":
		f.state = append([]byte(nil), v...)
		return true, errors.New("fake partial write")
	case "owned_error_absent":
		return true, errors.New("fake absent partial write")
	case "owned_error_different":
		f.state = []byte{89, 0}
		return true, errors.New("fake competing change")
	default:
		return false, errors.New("fake permission refusal")
	}
}
func (f *pass9TxFirmware) remove(string) error {
	f.removes++
	switch f.removeMode {
	case "failure":
		return errors.New("fake removal failure")
	case "unconfirmed":
		return nil
	}
	f.state = nil
	return nil
}

func TestPass9FirmwareContractMatrix(t *testing.T) {
	inventoryCases, inventorySuccess, txCases, txSuccess, foreignPreserved, refusals := 0, 0, 0, 0, 0, 0
	orderCases := []string{"one", "two", "reverse", "maximum", "empty", "odd", "duplicate", "oversized", "unreadable", "missing_entry"}
	for _, orderMode := range orderCases {
		for _, pending := range []string{"absent", "present", "unreadable"} {
			for _, secure := range []string{"enabled", "disabled", "malformed", "absent", "unreadable"} {
				f := &pass9InventoryFirmware{values: map[string][]byte{}, denied: map[string]bool{}}
				ids := []uint16{4}
				valid := true
				switch orderMode {
				case "two":
					ids = []uint16{4, 9}
				case "reverse":
					ids = []uint16{9, 4}
				case "maximum":
					ids = make([]uint16, 256)
					for i := range ids {
						ids[i] = uint16(i)
					}
				case "empty":
					ids = nil
					valid = false
				case "odd":
					valid = false
				case "duplicate":
					ids = []uint16{4, 4}
					valid = false
				case "oversized":
					ids = make([]uint16, 257)
					valid = false
				case "unreadable":
					f.denied["BootOrder"] = true
					valid = false
				case "missing_entry":
					valid = false
				}
				for _, id := range ids {
					var b [2]byte
					binary.LittleEndian.PutUint16(b[:], id)
					f.values["BootOrder"] = append(f.values["BootOrder"], b[:]...)
					f.values[fmt.Sprintf("Boot%04X", id)] = option(1)
				}
				if orderMode == "odd" {
					f.values["BootOrder"] = []byte{4}
				}
				if orderMode == "empty" {
					f.values["BootOrder"] = nil
				}
				if orderMode == "missing_entry" {
					delete(f.values, "Boot0004")
				}
				if pending == "present" {
					f.values["BootNext"] = []byte{4, 0}
				}
				if pending == "unreadable" {
					f.denied["BootNext"] = true
					valid = false
				}
				wantSecure := "unknown"
				switch secure {
				case "enabled":
					f.values["SecureBoot"] = []byte{1}
					wantSecure = "enabled"
				case "disabled":
					f.values["SecureBoot"] = []byte{0}
					wantSecure = "disabled"
				case "malformed":
					f.values["SecureBoot"] = []byte{1, 0}
				case "unreadable":
					f.denied["SecureBoot"] = true
				}
				entries, gotPending, gotSecure, err := readBootEntries(f)
				inventoryCases++
				if valid {
					inventorySuccess++
					if err != nil || len(entries) != len(ids) || gotPending != (pending == "present") || gotSecure != wantSecure {
						t.Fatalf("inventory %s/%s/%s: %v %v %q %d", orderMode, pending, secure, err, gotPending, gotSecure, len(entries))
					}
				} else if err == nil {
					t.Fatalf("accepted invalid inventory %s/%s", orderMode, pending)
				}
				if f.writes != 0 || f.removes != 0 {
					t.Fatal("read-only inventory mutated firmware")
				}
			}
		}
	}
	for _, entry := range []uint16{0, 4, 65535} {
		for _, direct := range []bool{false, true} {
			for _, pre := range []string{"absent", "present", "unreadable"} {
				for _, writeMode := range []string{"success", "foreign_same", "foreign_different", "owned_error", "owned_error_absent", "owned_error_different", "refused"} {
					for _, verify := range []string{"same", "absent", "different", "unreadable"} {
						for _, rebootMode := range []string{"success", "declined", "declined_foreign", "declined_absent"} {
							for _, removeMode := range []string{"success", "failure", "unconfirmed"} {
								f := &pass9TxFirmware{pre: pre, writeMode: writeMode, verify: verify, removeMode: removeMode}
								calls := 0
								want := []byte{byte(entry), byte(entry >> 8)}
								err := restartOnce(f, Plan{Direct: direct, Entry: entry}, func() error {
									calls++
									switch rebootMode {
									case "success":
										return nil
									case "declined_foreign":
										f.state = []byte{89, 0}
									case "declined_absent":
										f.state = nil
									}
									return errors.New("fake restart declined")
								})
								txCases++
								expectedSuccess := direct && pre == "absent" && writeMode == "success" && verify == "same" && rebootMode == "success"
								if (err == nil) != expectedSuccess {
									t.Fatalf("unexpected success entry=%d direct=%v pre=%s write=%s verify=%s reboot=%s removal=%s err=%v", entry, direct, pre, writeMode, verify, rebootMode, removeMode, err)
								}
								if expectedSuccess {
									txSuccess++
									if calls != 1 || !bytes.Equal(f.state, want) || f.removes != 0 {
										t.Fatal("positive restart contract lost")
									}
								} else {
									refusals++
								}
								if !direct || pre != "absent" {
									if f.writes != 0 || calls != 0 || f.removes != 0 {
										t.Fatal("mutated without verified plan and initial absence")
									}
								}
								if direct && pre == "absent" && (writeMode == "foreign_same" || writeMode == "foreign_different") {
									foreignPreserved++
									if f.removes != 0 || calls != 0 || f.state == nil {
										t.Fatal("removed foreign writer request")
									}
								}
								if calls != 0 && !(direct && pre == "absent" && writeMode == "success" && verify == "same") {
									t.Fatal("restarted before own exact write readback")
								}
								if f.removes != 0 && bytes.Equal(f.state, []byte{89, 0}) {
									t.Fatal("attempted removal of different foreign request")
								}
							}
						}
					}
				}
			}
		}
	}
	if inventoryCases != 150 || inventorySuccess != 40 || txCases != 6048 || txSuccess != 9 || foreignPreserved != 288 {
		t.Fatalf("matrix coverage changed: inv=%d/%d tx=%d/%d foreign=%d", inventoryCases, inventorySuccess, txCases, txSuccess, foreignPreserved)
	}
	data, _ := json.MarshalIndent(map[string]any{"inventory_cases": inventoryCases, "inventory_success_controls": inventorySuccess, "transaction_cases": txCases, "restart_success_controls": txSuccess, "foreign_request_preservation_controls": foreignPreserved, "transaction_refusals": refusals, "native_callbacks": 0, "mismatches": 0}, "", "  ")
	if err := os.WriteFile("/workspace/beamo-tools/audit-pass9-20261021/boot/firmware-contract-metrics.json", append(data, '\n'), 0600); err != nil {
		t.Fatal(err)
	}
}
