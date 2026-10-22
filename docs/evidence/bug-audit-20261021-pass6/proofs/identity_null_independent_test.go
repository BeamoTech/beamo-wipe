package main

import (
 "fmt"
 "path/filepath"
 "strings"
 "testing"
)

func TestRootBuildIdentityDirtyType(t *testing.T) {
 oldCommit, oldDirty := sourceCommit, sourceDirty
 t.Cleanup(func(){ sourceCommit, sourceDirty = oldCommit, oldDirty })
 sourceCommit, sourceDirty = strings.Repeat("a",40), "false"
 for _, tc := range []struct{name, raw, status string; manufactured bool}{
  {"null_refuses", "null", "unavailable", false},
  {"clean_control", "false", "production", true},
  {"dirty_control", "true", "source mismatch", false},
 } {
  t.Run(tc.name,func(t *testing.T){
   directory := mediaFixture(t)
   fixtureFile(t,directory,"build-identity.json",fmt.Sprintf(`{"source_commit":"%s","source_sha256":"%s","build_id":"12345678-1234-1234-1234-123456789abc","source_dirty":%s}`,sourceCommit,strings.Repeat("b",64),tc.raw))
   result:=loadUSBIdentity(filepath.Join(directory,"Start Beamo Wipe Linux"))
   if result.Status!=tc.status || result.Manufactured!=tc.manufactured {
    t.Fatalf("%s gave status=%s manufactured=%v",tc.raw,result.Status,result.Manufactured)
   }
  })
 }
}
