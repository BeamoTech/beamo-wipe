"""Minimal read-only FAT12/16/32 reader over an in-memory volume (bytes).

`Fat(volume, sparse=None)`: `sparse` may be a callable(offset, length)->bytes
for volumes held only in part; it must raise KeyError for bytes not held.
"""
import struct


class Fat:
    def __init__(self, volume, read=None):
        self._read = read or (lambda off, n: volume[off:off + n])
        bs = self._read(0, 512)
        self.bps, self.spc = struct.unpack_from("<H", bs, 11)[0], bs[13]
        reserved, nfats = struct.unpack_from("<H", bs, 14)[0], bs[16]
        root_entries, total16 = struct.unpack_from("<HH", bs, 17)
        fatsz16 = struct.unpack_from("<H", bs, 22)[0]
        total32 = struct.unpack_from("<I", bs, 32)[0]
        fatsz = fatsz16 or struct.unpack_from("<I", bs, 36)[0]
        total = total16 or total32
        root_secs = (root_entries * 32 + self.bps - 1) // self.bps
        self.fat_off = reserved * self.bps
        self.fat_bytes = fatsz * self.bps
        self.root_off = (reserved + nfats * fatsz) * self.bps
        self.root_len = root_secs * self.bps
        self.data_off = self.root_off + self.root_len
        clusters = (total - (reserved + nfats * fatsz + root_secs)) // self.spc
        self.kind = 12 if clusters < 4085 else 16 if clusters < 65525 else 32
        self.root_cluster = struct.unpack_from("<I", bs, 44)[0] if self.kind == 32 else None
        self.csize = self.bps * self.spc
        self.info = {"fat": self.kind, "bytes_per_sector": self.bps, "sectors_per_cluster": self.spc,
                     "clusters": clusters, "fat_offset": self.fat_off, "data_offset": self.data_off}
        self._fat = None

    def fat(self):
        if self._fat is None:
            self._fat = self._read(self.fat_off, self.fat_bytes)
        return self._fat

    def next_cluster(self, c):
        f = self.fat()
        if self.kind == 12:
            v = struct.unpack_from("<H", f, c + c // 2)[0]
            v = v >> 4 if c & 1 else v & 0xFFF
            return None if v >= 0xFF8 else v
        if self.kind == 16:
            v = struct.unpack_from("<H", f, c * 2)[0]
            return None if v >= 0xFFF8 else v
        v = struct.unpack_from("<I", f, c * 4)[0] & 0x0FFFFFFF
        return None if v >= 0x0FFFFFF8 else v

    def chain(self, first):
        out, c = [], first
        while c is not None and c >= 2 and len(out) < 1 << 22:
            out.append(c)
            c = self.next_cluster(c)
        return out

    def cluster_offset(self, c):
        return self.data_off + (c - 2) * self.csize

    def read_chain(self, first, size=None):
        parts = [self._read(self.cluster_offset(c), self.csize) for c in self.chain(first)]
        data = b"".join(parts)
        return data if size is None else data[:size]

    def entries(self, cluster):
        raw = (self._read(self.root_off, self.root_len) if cluster is None
               else self.read_chain(cluster))
        out, lfn = {}, []
        for i in range(0, len(raw), 32):
            e = raw[i:i + 32]
            if e[0] == 0:
                break
            if e[0] == 0xE5:
                lfn = []
                continue
            if e[11] == 0x0F:
                lfn.insert(0, (e[1:11] + e[14:26] + e[28:32]).decode("utf-16-le", "ignore")
                           .split("\x00")[0])
                continue
            short = e[0:8].decode("latin-1").rstrip()
            ext = e[8:11].decode("latin-1").rstrip()
            name = "".join(lfn) or (short + ("." + ext if ext else ""))
            lfn = []
            if e[11] & 0x08:
                continue
            hi = struct.unpack_from("<H", e, 20)[0] if self.kind == 32 else 0
            first = (hi << 16) | struct.unpack_from("<H", e, 26)[0]
            out[name] = {"dir": bool(e[11] & 0x10), "cluster": first,
                         "size": struct.unpack_from("<I", e, 28)[0]}
        return out

    def _walk(self, path):
        cluster = self.root_cluster
        node = None
        for part in [p for p in path.split("/") if p]:
            ents = self.entries(cluster)
            key = next((k for k in ents if k.lower() == part.lower()), None)
            if key is None:
                return None
            node = ents[key]
            cluster = node["cluster"]
        return node

    def listdir(self, path):
        node = self._walk(path)
        if node is None or not node["dir"]:
            return None
        return sorted(k for k in self.entries(node["cluster"]) if k not in (".", ".."))

    def read(self, path):
        node = self._walk(path)
        if node is None or node["dir"]:
            return None
        return self.read_chain(node["cluster"], node["size"])

    def file_clusters(self, path):
        node = self._walk(path)
        return None if node is None else (node, self.chain(node["cluster"]))
