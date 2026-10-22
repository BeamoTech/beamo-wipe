package main

import (
 "encoding/binary"
 "strings"
 "testing"
)

func TestPass12ContradictoryJSONAuthorizesPlan(t *testing.T) {
 for _,tc:=range []struct{name, body string; direct bool}{
  {"positive-USB",linuxFixture,true},
  {"refused-SATA",strings.Replace(linuxFixture,`"tran":"usb"`,`"tran":"sata"`,1),false},
  {"contradictory-duplicate-transport",strings.Replace(linuxFixture,`"tran":"usb"`,`"tran":"sata","tran":"usb"`,1),false},
  {"contradictory-duplicate-path",strings.Replace(linuxFixture,`"path":"/dev/sdb1"`,`"path":"/dev/sdc1","path":"/dev/sdb1"`,1),false},
 }{t.Run(tc.name,func(t *testing.T){
  id,routes,err:=linuxMedia([]byte(tc.body),"/dev/sdb1")
  s:=Snapshot{UEFI:true,Layout:"fake-layout",MediaID:id,Partitions:routes,Entries:map[uint16][]byte{}}
  if err==nil {b:=option(1);b[48],b[49]=1,1;binary.LittleEndian.PutUint32(b[32:],0x12345678);s.Entries[4]=b}else{s.Problem="media"}
  p:=makePlanForHost(s,"linux")
  checks,_:=explainReadiness(s,p)
  if p.Direct!=tc.direct{t.Fatalf("actual plan Direct=%t, USBcheck=%s routecheck=%s err=%v want=%t",p.Direct,checks[0].State,checks[2].State,err,tc.direct)}
 })}
}
