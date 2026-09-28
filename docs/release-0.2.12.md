# Beamo Wipe 0.2.12

This patch release restores the live USB recovery menu after a single terminal
EOF (for example, Ctrl-D). If terminal reads keep failing, the menu keeps its
warning visible and checks again at a slower pace without relaunching the
wizard. A closed non-terminal input still exits the supervisor. Recovery
continues to warn that an earlier erase may still be running.

An uncertain child-cleanup result now directs the owner to support in the
wizard's supported languages. It does not become a successful erase result or
permit application-requested shutdown while the process may still run.

The release also includes the merged draft-release verification correction:
the publisher looks up a GitHub draft by its numeric release ID before checking
uploaded asset hashes. It does not change the disk engine or its arguments.

The engine remains pinned to nwipe 0.42. The supported hardware and storage
claims remain those in [claims](claims.md) and the
[compatibility matrix](compatibility-matrix.md). Safe local tests use fake
devices and stubbed power commands. Release qualification includes exact-source
Blacksmith Linux, amd64 image, isolated KVM/USB boot, and native Windows gates.
These checks do not establish physical-machine compatibility.

The signed release manifest identifies the tagged source and measured ISO/USB
bytes. The previous signed v0.2.11 release remains the rollback target; its
artifacts are unchanged.
