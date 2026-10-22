package main

import (
 "context"
 "fmt"
 "os"
 "os/exec"
 "path/filepath"
 "strings"
 "testing"
 "time"
)

func TestPass11OutputCancellationHelper(t *testing.T) {
 role := os.Getenv("BEAMO_PASS11_OUTPUT_ROLE")
 switch role {
 case "grandchild":
  if err := os.WriteFile(os.Getenv("BEAMO_PASS11_OUTPUT_MARKER"), []byte("started"), 0600); err != nil { os.Exit(21) }
  time.Sleep(900 * time.Millisecond)
  fmt.Print("owned descendant completed")
  os.Exit(0)
 case "parent":
  child := exec.Command(os.Args[0], "-test.run=^TestPass11OutputCancellationHelper$")
  child.Env = append(os.Environ(), "BEAMO_PASS11_OUTPUT_ROLE=grandchild")
  child.Stdout, child.Stderr = os.Stdout, os.Stderr
  if child.Start() != nil { os.Exit(22) }
  _ = child.Wait()
  os.Exit(0)
 case "direct":
  if err := os.WriteFile(os.Getenv("BEAMO_PASS11_OUTPUT_MARKER"), []byte("started"), 0600); err != nil { os.Exit(23) }
  time.Sleep(900 * time.Millisecond)
  os.Exit(0)
 case "complete":
  fmt.Print("normal bounded output")
  os.Exit(0)
 }
}

func TestPass11OutputCancellationProbe(t *testing.T) {
 for _, role := range []string{"complete", "direct", "parent"} {
  t.Run(role, func(t *testing.T) {
   marker := filepath.Join(t.TempDir(), "started")
   ctx, cancel := context.WithCancel(context.Background())
   defer cancel()
   command := exec.CommandContext(ctx, os.Args[0], "-test.run=^TestPass11OutputCancellationHelper$")
   command.Env = append(os.Environ(), "BEAMO_PASS11_OUTPUT_ROLE=" + role, "BEAMO_PASS11_OUTPUT_MARKER=" + marker)
   type result struct { data []byte; err error }
   done := make(chan result, 1)
   go func() { data, err := boundedOutput(command, 1024); done <- result{data, err} }()
   if role == "complete" {
    got := <-done
    if got.err != nil || string(got.data) != "normal bounded output" { t.Fatalf("normal output: %q %v", got.data, got.err) }
    return
   }
   deadline := time.Now().Add(5*time.Second)
   for {
    if data, err := os.ReadFile(marker); err == nil && strings.Contains(string(data), "started") { break }
    if time.Now().After(deadline) { t.Fatal("owned helper did not start") }
    time.Sleep(time.Millisecond)
   }
   started := time.Now()
   cancel()
   got := <-done
   elapsed := time.Since(started)
   if got.err == nil { t.Fatal("canceled output accepted as successful") }
   t.Logf("context cancellation to return: %s", elapsed)
   if elapsed > 250*time.Millisecond { t.Fatalf("cancellation waited for inherited descendant output: %s", elapsed) }
  })
 }
}
