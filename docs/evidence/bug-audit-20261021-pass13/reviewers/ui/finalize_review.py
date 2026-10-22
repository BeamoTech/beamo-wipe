from pathlib import Path
from hashlib import sha256
import json, subprocess
root=Path(__file__).parent
repo=Path('/workspace/beamo-wipe')
paths=['src/beamo_wipe/wizard.py','src/beamo_wipe/app.py','src/beamo_wipe/ui/tk_wizard.py','src/beamo_wipe/ui/accessible_wizard.py','src/beamo_wipe/ui/console_wizard.py','src/beamo_wipe/ui/sound_dialog.py','src/beamo_wipe/startup_stages.py','helper/index.html']
sources={path:sha256((repo/path).read_bytes()).hexdigest() for path in paths}
(root/'reviewed-source-sha256.json').write_text(json.dumps(sources,indent=2)+'\n')
report={'baseline':'7fcd706b44c0d63cf5f2959bcd235968e8300274','branch':'fix/safety-audit-20261019',
 'status':'bounded review complete; proved GTK candidate awaits root independent validation and ownership',
 'repository_edits':[], 'findings':[{'id':'GTK-main-view-lifetime','status':'PROVED on baseline; product untouched',
 'source':'src/beamo_wipe/ui/accessible_wizard.py','functions':['AccessibleWizard.__init__','AccessibleWizard.run'],
 'trigger':'Initial render/show or timer installation throws; or Gtk.main raises/returns externally.',
 'observed':'Owned visible GTK window survives all four paths; installed poll timer survives both loop paths.',
 'proof':'lifetime-before.status.json','failures':4,'positive_controls':1,'native_callbacks':0,
 'minimal_fix_caution':'Initialize retirement fields before fallible GTK setup; clean on construction and every run exit; quit only owned Gtk.main level, preserving peer/nested loops.'}],
 'focused_checks':json.loads((root/'focused-ui.status.json').read_text()),
 'finite_model':json.loads((root/'shutdown_overlay_epoch_model.json').read_text()),
 'source_sha256':sources,
 'safety':{'actual_engine':False,'native_inventory':False,'device_operations':False,'network_remote':False,'Docker_build':False,'firmware_power_guest':False,
 'private72dpi':True,'preserved_peer_displays':[':1',':99'],'private_XDG_and_DBus':True,'child_umask':'022'},
 'limits':'Supporting focused/model counts overlap canonical coverage. No native/physical/browser acceptance claim. Initial model missing-fake-selector setup failure is retained separately and excluded from success counts.'}
(root/'review-report.json').write_text(json.dumps(report,indent=2)+'\n')
manifest={path.name:sha256(path.read_bytes()).hexdigest() for path in sorted(root.iterdir()) if path.is_file() and path.name!='artifact-sha256.json'}
(root/'artifact-sha256.json').write_text(json.dumps(manifest,indent=2)+'\n')
print(json.dumps({'source_files':len(sources),'artifacts':len(manifest),'proof':'4fail/1control','focused':'683pass/0fail/0skip','model':'108scenarios/1926events/0mismatch/0native'}))
