"""Unknown Linux live state must stop the real launcher probe before inventory.

Only fixed OS I/O boundaries are replaced in a private Go overlay. Regular
temporary files stand in for media/EFI and tiny scripts print fake inventories.
The production probe, media readers, boot parser, plan and view are exercised.
"""

import json
import os
from pathlib import Path
import shutil
import subprocess
import sys

import pytest


ROOT = Path(__file__).resolve().parents[1]
GO_PROBE = r"""
package main

import (
    "context"
    "encoding/json"
    "errors"
    "io/fs"
    "os"
    "path/filepath"
    "strings"
    "syscall"
    "testing"
)

const auditRoot = AUDIT_ROOT
var auditMode string

func auditUname(info *syscall.Utsname) error {
    if auditMode == "platform-error" { return errors.New("fake uname error") }
    name := "x86_64"
    if auditMode == "platform-other" { name = "aarch64" }
    for i, ch := range []byte(name) { info.Machine[i] = int8(ch) }
    return nil
}

func auditReadSmall(path string, limit int64) ([]byte, error) {
    if auditMode == "denied" { return nil, fs.ErrPermission }
    return readSmall(path, limit)
}

func TestLinuxLiveRuntimePass5(t *testing.T) {
    exe, err := os.Executable()
    if err != nil { t.Fatal(err) }
    mediaRoot := filepath.Dir(exe)
    write := func(path string, raw []byte) {
        t.Helper()
        if err := os.MkdirAll(filepath.Dir(path), 0700); err != nil { t.Fatal(err) }
        if err := os.WriteFile(path, raw, 0700); err != nil { t.Fatal(err) }
    }
    shellQuote := func(s string) string { return "'"+strings.ReplaceAll(s,"'","'\"'\"'")+"'" }
    for name, raw := range map[string][]byte{
        "START-HERE.html": []byte("fake guide"),
        "desktop-build.json": []byte("{}"),
        "live/filesystem.squashfs": []byte("fake squashfs"),
        "EFI/BOOT/BOOTX64.EFI": []byte("MZfake loader"),
    } {
        path := filepath.Join(mediaRoot, name)
        if _, err := os.Lstat(path); !os.IsNotExist(err) { t.Fatalf("fixture path not absent:%s",path) }
        write(path,raw)
        t.Cleanup(func(){ _ = os.Remove(path) })
    }
    trace := auditRoot+"/commands"
    mount, _ := json.Marshal(map[string]any{"filesystems":[]map[string]string{{"source":"/dev/sdb1","target":mediaRoot}}})
    inventory := strings.ReplaceAll(linuxFixture, `"ptuuid":"12345678"`, `"ptuuid":"aaaaaaaa-bbbb-cccc-dddd-eeeeeeeeeeee"`)
    inventory = strings.ReplaceAll(inventory, `"partuuid":"12345678-01"`, `"partuuid":"00000001-0000-0000-0000-000000000000"`)
    for name, data := range map[string]string{"findmnt":string(mount),"lsblk":inventory} {
        write(auditRoot+"/bin/"+name,[]byte("#!/bin/sh\nprintf '%s\\n' "+shellQuote(name)+" >> "+shellQuote(trace)+"\nprintf '%s' "+shellQuote(data)+"\n"))
    }
    for name, data := range map[string][]byte{"BootOrder":{4,0},"Boot0004":option(1),"SecureBoot":{1}} {
        write(auditRoot+"/efi/efivars/"+name+"-"+efiGlobal,append([]byte{7,0,0,0},data...))
    }
    for _, row := range []struct{name,cmdline,problem string; direct bool}{
        {"normal","root=/dev/fake quiet","",true},
        {"empty","","",true},
        {"at-limit",strings.Repeat(" ",16384),"",true},
        {"live","boot=live quiet","live",false},
        {"live-last","quiet boot=live","live",false},
        {"missing","","runtime",false},
        {"directory","","runtime",false},
        {"symlink","","runtime",false},
        {"fifo","","runtime",false},
        {"oversized","","runtime",false},
        {"ancestor-link","","runtime",false},
        {"denied","","runtime",false},
        {"platform-error","","platform",false},
        {"platform-other","","platform",false},
        {"legacy","","legacy",false},
    } {
        t.Run(row.name,func(t *testing.T){
            auditMode=row.name
            runtimeDir:=auditRoot+"/runtime"
            _ = os.RemoveAll(runtimeDir)
            if err:=os.MkdirAll(runtimeDir,0700);err!=nil{t.Fatal(err)}
            path:=runtimeDir+"/cmdline"
            switch row.name {
            case "missing","legacy","platform-error","platform-other":
            case "directory":
                if err:=os.Mkdir(path,0700);err!=nil{t.Fatal(err)}
            case "symlink":
                target:=auditRoot+"/outside-cmdline"
                write(target,[]byte("boot=live"))
                if err:=os.Symlink(target,path);err!=nil{t.Fatal(err)}
            case "ancestor-link":
                outside:=auditRoot+"/outside-runtime"
                write(outside+"/cmdline",[]byte("boot=live"))
                if err:=os.Remove(runtimeDir);err!=nil{t.Fatal(err)}
                if err:=os.Symlink(outside,runtimeDir);err!=nil{t.Fatal(err)}
            case "fifo":
                if err:=syscall.Mkfifo(path,0600);err!=nil{t.Fatal(err)}
            case "oversized": write(path,[]byte("boot=live"+strings.Repeat(" ",16385)))
            default: write(path,[]byte(row.cmdline))
            }
            if row.name=="legacy" {
                if err:=os.Rename(auditRoot+"/efi",auditRoot+"/held-efi");err!=nil{t.Fatal(err)}
                defer func(){ if err:=os.Rename(auditRoot+"/held-efi",auditRoot+"/efi");err!=nil{t.Fatal(err)} }()
            }
            _ = os.Remove(trace)
            snapshot:=platformProbe(context.Background())
            plan:=makePlan(snapshot)
            view:=planView(plan,false)
            t.Logf("problem=%q direct=%v",snapshot.Problem,plan.Direct)
            if snapshot.Problem!=row.problem || plan.Direct!=row.direct || view.Ready!=row.direct {
                t.Fatalf("wrong runtime result: problem=%q direct=%v ready=%v",snapshot.Problem,plan.Direct,view.Ready)
            }
            calls,_:=os.ReadFile(trace)
            if !row.direct && len(calls)!=0 { t.Fatalf("runtime refusal reached inventory:%s",calls) }
            if row.direct && string(calls)!="findmnt\nlsblk\n" {t.Fatalf("normal probe missed inventory:%q",calls)}
            if row.problem=="runtime" {
                if len(snapshot.Entries)!=0 || snapshot.MediaID!="" { t.Fatal("unknown runtime reached media or firmware") }
                for _,check:=range view.Checks {if check.State!="unverified" {t.Fatalf("unknown runtime claimed readiness:%+v",check)}}
                if strings.Contains(view.Detail,"already in the Beamo USB") {t.Fatal("unknown runtime labeled confirmed live")}
                if !strings.Contains(view.Detail,"Keep the computer on") {t.Fatal("unknown runtime lost safe next step")}
                if view.Title!="Keep this computer on" {t.Fatal("unknown runtime offered boot instructions as its title")}
            }
        })
    }
}
"""


def run_probe(tmp_path, source):
    """Build the real package with explicit, checked OS-boundary substitutions."""
    fixture = tmp_path / "fake system with spaces"
    replacements = {
        '"/sys/firmware/efi/efivars/"': json.dumps(str(fixture / "efi/efivars") + "/"),
        '"/sys/firmware/efi"': json.dumps(str(fixture / "efi")),
        '"/proc/cmdline"': json.dumps(str(fixture / "runtime/cmdline")),
        '"/usr/bin/findmnt"': json.dumps(str(fixture / "bin/findmnt")),
        '"/usr/bin/lsblk"': json.dumps(str(fixture / "bin/lsblk")),
        "syscall.Uname(&info)": "auditUname(&info)",
        'readSmall("/proc/cmdline", 16384)': 'auditReadSmall("/proc/cmdline", 16384)',
    }
    for original in replacements:
        assert original in source, original
    # Replace the call before its path; every other change is a fixed I/O path.
    call = 'readSmall("/proc/cmdline", 16384)'
    source = source.replace(call, replacements.pop(call))
    for original, replacement in replacements.items():
        source = source.replace(original, replacement)
    private_source = tmp_path / "platform_linux.go"
    private_source.write_text(source)
    probe = tmp_path / "live_runtime_test.go"
    probe.write_text(GO_PROBE.replace("AUDIT_ROOT", json.dumps(str(fixture))))
    overlay = tmp_path / "overlay.json"
    overlay.write_text(
        json.dumps(
            {
                "Replace": {
                    str(ROOT / "desktop/platform_linux.go"): str(private_source),
                    str(ROOT / "desktop/live_runtime_audit_test.go"): str(probe),
                }
            }
        )
    )
    env = os.environ.copy()
    for name in ("BEAMO_DESKTOP_NATIVE_INVENTORY_TEST", "GOOS", "GOARCH", "GOROOT"):
        env.pop(name, None)
    env.update(GOTOOLCHAIN="local", GOFLAGS="", GOENV="off", GOWORK="off")
    return subprocess.run(
        [
            os.environ.get("BEAMO_GO_BIN", "go"),
            "test",
            "-count=1",
            "-json",
            "-overlay=" + str(overlay),
            "-run=^TestLinuxLiveRuntimePass5$",
            "./...",
        ],
        cwd=ROOT / "desktop",
        env=env,
        capture_output=True,
        text=True,
        timeout=90,
    )


@pytest.mark.skipif(sys.platform != "linux", reason="Linux launcher I/O fixture")
def test_unknown_live_runtime_refuses_before_inventory(tmp_path):
    if not shutil.which(os.environ.get("BEAMO_GO_BIN", "go")):
        pytest.skip("Go unavailable")
    result = run_probe(tmp_path, (ROOT / "desktop/platform_linux.go").read_text())
    print(result.stdout)
    assert result.returncode == 0, result.stdout + result.stderr
    events = [json.loads(line) for line in result.stdout.splitlines()]
    names = {
        event["Test"]
        for event in events
        if event["Action"] == "pass" and "Test" in event
    }
    assert len(names) == 16  # One parent and all fifteen named scenarios.
    assert not any(event["Action"] in {"fail", "skip"} for event in events)
