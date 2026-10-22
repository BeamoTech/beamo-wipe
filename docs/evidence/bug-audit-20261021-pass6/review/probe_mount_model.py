"""Compare mount ancestry proofs with an independent simulated mount sequence."""
from pathlib import Path
import hashlib
import json
import random

from beamo_wipe.discover import mountinfo_mount_is_visible

root = Path(__file__).resolve().parent
rng = random.Random(612026)
paths = ('/tmp', '/tmp/beamo-wipe', '/tmp/beamo-wipe/nested', '/run',
         '/run/live', '/run/live/medium', '/media', '/media/external', '/opt/shared')
checks = visible = hidden = ambiguous = 0
failures = []
for trial in range(2000):
    rows = [(1, 0, '/')]
    active = {1: '/'}
    for _ in range(rng.randrange(2, 16)):
        path = rng.choice(paths)
        parents = [(mid, point) for mid, point in active.items()
                   if point == '/' or path == point or path.startswith(point + '/')]
        parent = max(parents, key=lambda item: len(item[1]))[0]
        mid = rng.randrange(2, 10000000)
        while any(item[0] == mid for item in rows):
            mid = rng.randrange(2, 10000000)
        rows.append((mid, parent, path))
        # A new mount hides older mounts at/below its pathname. Its parent
        # is the mount reached immediately before the operation, including
        # an existing mount at the same pathname when stacking.
        active = {old: point for old, point in active.items()
                  if point != path and not point.startswith(path + '/')}
        active[mid] = path
    rng.shuffle(rows)
    table = ''.join(f'{mid} {parent} 0:{index+1} / {point} rw - tmpfs tmpfs rw\n'
                    for index, (mid, parent, point) in enumerate(rows))
    for path in paths:
        candidates = [mid for mid, _parent, point in rows if point == path]
        if len(candidates) != 1:
            # Existing public policy deliberately refuses same-path ambiguity.
            assert mountinfo_mount_is_visible(table, path) is False
            ambiguous += 1
            continue
        expected = candidates[0] in active
        observed = mountinfo_mount_is_visible(table, path)
        checks += 1
        visible += expected
        hidden += not expected
        if observed != expected:
            failures.append({'trial': trial, 'path': path, 'expected': expected,
                             'observed': observed, 'mountinfo': table})
record = {'seed': 612026, 'simulated_mount_sequences': 2000,
          'unique_path_visibility_checks': checks, 'visible': visible,
          'hidden': hidden, 'absent_or_same_path_ambiguous_refusals': ambiguous,
          'mismatches': failures,
          'source_sha256': hashlib.sha256(Path('/workspace/beamo-wipe/src/beamo_wipe/discover.py').read_bytes()).hexdigest(),
          'actual_mount_or_device_actions': 0}
(root / 'mount-model.json').write_text(json.dumps(record, indent=2) + '\n')
print(json.dumps({key: value for key, value in record.items() if key != 'mismatches'}))
assert not failures, failures[:2]
