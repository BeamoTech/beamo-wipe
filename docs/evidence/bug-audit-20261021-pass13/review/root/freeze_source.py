"""Freeze only after root has reproduced, reviewed, and replayed repairs."""
from pathlib import Path
import datetime
import hashlib
import json
import subprocess

repo=Path('/workspace/beamo-wipe')
r=Path(__file__).parent
start=json.loads((r/'starting-source-sha256.json').read_text())
changed={'desktop/media.go','scripts/build_desktop.py','src/beamo_wipe/ci_evidence.py',
 'src/beamo_wipe/evidence.py','src/beamo_wipe/sound.py','src/beamo_wipe/ui/accessible_wizard.py'}
cases={'tests/test_ci_log_snapshot_pass13_20261021.py':36,
 'tests/test_evidence_publication_pass13_20261021.py':63,
 'tests/test_sound_cancelled_spawn_pass13_20261021.py':20,
 'tests/test_accessible_main_lifetime_pass13.py':32,
 'developer_tests/test_desktop_manifest_interrupt_pass13_20261021.py':19}
new={*cases,'desktop/media_snapshot_pass13_20261021_test.go'}
assert subprocess.check_output(['git','rev-parse','HEAD'],cwd=repo,text=True).strip()=='7fcd706b44c0d63cf5f2959bcd235968e8300274'
source={name:hashlib.sha256((repo/name).read_bytes()).hexdigest() for name in sorted(set(start)|new)}
assert {name for name,old in start.items() if source[name]!=old}==changed
assert len(source)==831
(r/'final-source-sha256.json').write_text(json.dumps(source,indent=2,sort_keys=True)+'\n')
freeze={'baseline_commit':'7fcd706b44c0d63cf5f2959bcd235968e8300274',
 'frozen_at_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),
 'client_timezone':'America/Chicago','source_files':831,
 'source_manifest_sha256':hashlib.sha256((r/'final-source-sha256.json').read_bytes()).hexdigest(),
 'new_case_breakdown':cases,'new_python_cases':170,
 'new_go_test_pattern':'^TestMediaDigestFinalSnapshotPass13$',
 'new_go_leaf_cases':7,'new_go_named_pass_events':8,
 'go_full_expected_named_pass_events':467,
 'expected_canonical_main_passes':11967,'expected_canonical_main_ids':11995,
 'expected_canonical_unique_python_passes':11968,'unchanged_python_skips':28,
 'changed_paths':sorted(changed|new),'verified_root_causes':6,
 'all_existing_test_files_byte_identical':True,'old_assertions_preserved':True,
 'all_source_ownership_released':True,'actual_native_device_engine_power_guest_actions':False}
(r/'final-freeze.json').write_text(json.dumps(freeze,indent=2)+'\n')
print(json.dumps(freeze,indent=2))
