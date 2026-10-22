package main

import (
 "context"
 "encoding/json"
 "errors"
 "fmt"
 "math/rand"
 "net/http/httptest"
 "os"
 "strings"
 "testing"
 "time"
)

func TestPass8ReadinessActionModel(t *testing.T) {
 // All platform/firmware callbacks below are fake. HTTP handlers are invoked
 // through ResponseRecorder; no socket, native probe, elevation or restart runs.
 const sessions = 200
 const actions = 80
 probes, restarts, refused, invalid, requests := 0, 0, 0, 0, 0
 for seed := int64(0); seed < sessions; seed++ {
  rng := rand.New(rand.NewSource(802026+seed))
  a := testApp()
  a.p = Plan{}
  a.current = planView(a.p, false)
  var next Snapshot
  a.probe = func(context.Context) Snapshot { probes++; return next }
  authorized := false
  var expected string
  failRestart := false
  a.restart = func(_ context.Context, got string) error {
   if !authorized || expected == "" || got != expected || !a.busy || a.p.Direct || a.current.Ready {
    t.Fatalf("seed=%d: mutation escaped model authorization: authorized=%t expected=%q got=%q busy=%t plan=%+v", seed, authorized, expected, got, a.busy, a.p)
   }
   restarts++
   if failRestart { return errors.New("fake permission refusal") }
   return nil
  }
  for index := 0; index < actions; index++ {
   kind := rng.Intn(11)
   oldRevision, oldReady, oldRestarts, oldProbes := a.revision, a.p.Direct, restarts, probes
   authorized = false
   wantStatus := 200
   path, body := "/api/state", `{}`
   var cancelContext context.Context
   switch kind {
   case 0, 1:
    next = Snapshot{Layout: strings.Repeat("c",64), UEFI:true, MediaID:fmt.Sprintf("fake-usb-%d-%d",seed,index), Partitions:[]string{"gpt:00000001-0000-0000-0000-000000000000:1:2048:4096"}, Entries:map[uint16][]byte{4:option(1)}}
    if kind == 1 { next.Problem = "media" }
    path = "/api/check"
   case 2:
    path = "/api/restart"
    body = fmt.Sprintf(`{"confirm":true,"revision":%d}`,a.revision)
    if oldReady {
     expected, authorized, failRestart = a.p.Fingerprint, true, rng.Intn(2)==0
     if failRestart { wantStatus = 503 }
    } else { wantStatus = 409; refused++ }
   case 3:
    path, body, wantStatus = "/api/restart",fmt.Sprintf(`{"confirm":false,"revision":%d}`,a.revision),409
    refused++
   case 4:
    path, body, wantStatus = "/api/restart",fmt.Sprintf(`{"confirm":true,"revision":%d}`,a.revision+1),409
    refused++
   case 5:
    path, body, wantStatus = "/api/restart",fmt.Sprintf(`{"confirm":false,"confirm":true,"revision":%d}`,a.revision),400
    invalid++
   case 6:
    // State polling cannot repeat a probe or turn readiness on.
   case 7:
    path, body, wantStatus = "/api/restart",fmt.Sprintf(`{"confirm":true,"revision":%d}`,a.revision),403
    refused++
   case 8, 9:
    path = "/api/check"
    if kind == 8 {
     ctx,cancel := context.WithCancel(context.Background()); cancel(); cancelContext = ctx
    } else {
     ctx,cancel := context.WithDeadline(context.Background(),time.Now().Add(-time.Second));defer cancel();cancelContext = ctx
    }
   case 10:
    a.busy = true
    path, body, wantStatus = "/api/restart",fmt.Sprintf(`{"confirm":true,"revision":%d}`,a.revision),409
    refused++
   }
   r := httptest.NewRequest("POST","http://"+a.host+path,strings.NewReader(body))
   r.Header.Set("Origin","http://"+a.host);r.Header.Set("X-Beamo-Token",a.token);r.Header.Set("Content-Type","application/json")
   if kind == 7 { r.Header.Set("X-Beamo-Token","incorrect-fake-token") }
   if cancelContext != nil { r = r.WithContext(cancelContext) }
   w := httptest.NewRecorder();a.serve(w,r);requests++
   if w.Code != wantStatus { t.Fatalf("seed=%d action=%d kind=%d: status=%d want=%d body=%s",seed,index,kind,w.Code,wantStatus,w.Body.String()) }
   if kind == 10 { a.busy = false }
   if a.busy { t.Fatalf("seed=%d kind=%d: stranded busy state",seed,kind) }
   switch kind {
   case 0, 1, 8, 9:
    if a.revision != oldRevision+1 || a.current.Revision != a.revision || a.p.Direct != (kind==0) || a.current.Ready != a.p.Direct {
     t.Fatalf("seed=%d kind=%d: incoherent check state %+v",seed,kind,a.current)
    }
    wantProbes := oldProbes
    if kind==0 || kind==1 { wantProbes++ }
    if probes!=wantProbes || restarts!=oldRestarts { t.Fatal("check escaped read-only provider boundary") }
   case 2:
    delta:=0
    if oldReady { delta=1 }
    if restarts!=oldRestarts+delta || probes!=oldProbes || a.p.Direct || a.current.Ready || a.revision!=oldRevision+uint64(delta) { t.Fatal("restart did not consume exactly one current plan") }
   default:
    if restarts!=oldRestarts || probes!=oldProbes || a.revision!=oldRevision || a.p.Direct!=oldReady { t.Fatal("non-mutating/refused request changed state") }
   }
  }
  if request(a,"/api/close",`{}`).Code!=200 { t.Fatal("normal close refused") }
  select { case <-a.close: default:t.Fatal("close did not retire owned app") }
 }
 // A complete Windows fixture never enables the firmware restart path.
 for n:=0;n<1000;n++ {
  s:=Snapshot{Layout:strings.Repeat("c",64),UEFI:true,MediaID:fmt.Sprintf("fake-%d",n),Partitions:[]string{"gpt:00000001-0000-0000-0000-000000000000:1:2048:4096"},Entries:map[uint16][]byte{4:option(1)}}
  p:=makePlanForHost(s,"windows")
  if p.Direct || p.Fingerprint!="" || p.Problem!="windows-manual" { t.Fatal("Windows policy escaped manual path") }
 }
 result:=map[string]any{"seed_base":802026,"sessions":sessions,"public_action_requests":requests,"probes":probes,"authorized_fake_restarts":restarts,"refused_requests":refused,"malformed_duplicate_requests":invalid,"windows_manual_policy_cases":1000,"native_callbacks":0,"failures":0}
 raw,err:=json.MarshalIndent(result,"","  ");if err!=nil{t.Fatal(err)}
 if err:=os.WriteFile("/workspace/beamo-tools/audit-pass8-20261021/boot/readiness-sequence-model.json",append(raw,'\n'),0600);err!=nil{t.Fatal(err)}
 fmt.Println(string(raw))
}
