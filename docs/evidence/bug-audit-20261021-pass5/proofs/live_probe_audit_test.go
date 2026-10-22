// Supplemental fake-boundary audit; platformProbe control flow is unchanged.
package main

import (
    "context"
    "encoding/json"
    "os"
    "path/filepath"
    "strings"
    "testing"
)

const auditRoot = "/workspace/beamo-tools/audit-pass5-20261021/boot/live-fixture"

func TestPass5UnreadableLiveMarkerCannotOfferRestart(t *testing.T) {
    exe, err := os.Executable()
    if err != nil { t.Fatal(err) }
    mediaRoot := filepath.Dir(exe)
    write := func(path string, raw []byte) {
        if err := os.MkdirAll(filepath.Dir(path), 0700); err != nil { t.Fatal(err) }
        if err := os.WriteFile(path, raw, 0700); err != nil { t.Fatal(err) }
    }
    files := map[string][]byte{
        "START-HERE.html": []byte("fake guide"),
        "desktop-build.json": []byte("{}"),
        "live/filesystem.squashfs": []byte("fake squashfs bytes"),
        "EFI/BOOT/BOOTX64.EFI": []byte("MZfake loader"),
    }
    for name, raw := range files {
        path := filepath.Join(mediaRoot, name)
        if _, err := os.Lstat(path); !os.IsNotExist(err) { t.Fatalf("fixture path not absent:%s", path) }
        write(path, raw)
        t.Cleanup(func(){ _ = os.Remove(path) })
    }
    mount, _ := json.Marshal(map[string]any{"filesystems": []map[string]string{{"source":"/dev/sdb1", "target":mediaRoot}}})
    write(auditRoot+"/bin/findmnt", []byte("#!/bin/sh\nprintf '%s' '"+string(mount)+"'\n"))
    inventory := strings.ReplaceAll(linuxFixture, `"ptuuid":"12345678"`, `"ptuuid":"aaaaaaaa-bbbb-cccc-dddd-eeeeeeeeeeee"`)
    inventory = strings.ReplaceAll(inventory, `"partuuid":"12345678-01"`, `"partuuid":"00000001-0000-0000-0000-000000000000"`)
    write(auditRoot+"/bin/lsblk", []byte("#!/bin/sh\nprintf '%s' '"+inventory+"'\n"))
    for name, data := range map[string][]byte{"BootOrder":{4,0}, "Boot0004":option(1), "SecureBoot":{1}} {
        write(auditRoot+"/efi/efivars/"+name+"-"+efiGlobal, append([]byte{7,0,0,0}, data...))
    }
    for _, row := range []struct{name, cmdline string; exists, direct bool}{
        {"normal", "root=/dev/fake quiet", true, true},
        {"live", "boot=live quiet", true, false},
        {"unreadable", "", false, false},
    } {
        t.Run(row.name, func(t *testing.T){
            if row.exists { write(auditRoot+"/cmdline", []byte(row.cmdline)) } else { _ = os.Remove(auditRoot+"/cmdline") }
            snapshot := platformProbe(context.Background())
            plan := makePlan(snapshot)
            t.Logf("problem=%q direct=%v", snapshot.Problem, plan.Direct)
            if plan.Direct != row.direct { t.Fatalf("unknown live state offered direct restart: snapshot=%+v plan=%+v",snapshot,plan) }
        })
    }
}
