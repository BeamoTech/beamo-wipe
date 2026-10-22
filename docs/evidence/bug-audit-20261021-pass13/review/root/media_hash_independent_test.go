package main

import (
    "context"
    "os"
    "path/filepath"
    "testing"
)

type rootMediaContextPass13 struct {
    context.Context
    calls int
    mutate func()
}
func (c *rootMediaContextPass13) Err() error {
    c.calls++
    if c.calls == 4 { c.mutate() }
    return nil
}

func TestRootMediaDigestFreshnessPass13(t *testing.T) {
    for _, mutation := range []string{"normal", "same-size", "mode"} {
        t.Run(mutation, func(t *testing.T) {
            p := filepath.Join(t.TempDir(), "owned-file")
            if err := os.WriteFile(p, []byte("old-content"), 0600); err != nil { t.Fatal(err) }
            before, err := os.Stat(p); if err != nil {t.Fatal(err)}
            c := &rootMediaContextPass13{Context:context.Background(),mutate:func(){
                if mutation == "same-size" {
                    if err := os.WriteFile(p, []byte("new-content"),0600);err!=nil{t.Fatal(err)}
                    if err := os.Chtimes(p,before.ModTime(),before.ModTime());err!=nil{t.Fatal(err)}
                } else if mutation == "mode" {if err:=os.Chmod(p,0644);err!=nil{t.Fatal(err)}}
            }}
            digest, err := mediaDigest(c,p,100)
            if (err == nil) != (mutation == "normal") { t.Fatalf("mutation=%s digest=%x err=%v calls=%d",mutation,digest,err,c.calls) }
        })
    }
}
