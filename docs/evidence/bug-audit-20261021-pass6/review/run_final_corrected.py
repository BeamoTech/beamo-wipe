from pathlib import Path
import json,subprocess,sys
r=Path(__file__).parent;w=r.parent;wrapper='/workspace/beamo-tools/beamo-dev'
def run(name,*args,expected=0):
 p=subprocess.run(['python3',str(r/'run_group.py'),name,*args]);assert p.returncode==expected,(name,p.returncode)
display=[wrapper,'dbus-run-session','--','xvfb-run','-a','-n','765','-s','-screen 0 1600x1000x24 -dpi 72','python3','-m','pytest','-W','error','-p','no:cacheprovider','-q']
new=['tests/test_mount_visibility_pass6_20261021.py','tests/test_cancel_delivery_receipt_pass6_20261021.py','tests/test_tk_callback_ownership_pass6_20261021.py','tests/test_curses_review_paint_pass6_20261021.py']
run('final-new-regressions',*display,*new,'--junitxml='+str(r/'final-new-regressions.xml'))
probes=[w/'discovery/test_hidden_descendant_mount_probe.py',w/'ui/test_tk_poll_interruption_candidate.py',w/'ui/test_tk_stop_render_failure_candidate.py',w/'ui/test_curses_write_failure_candidate.py',w/'runner/test_cancel_inner_poll_probe.py',r/'test_curses_clipped_review_probe.py']
run('final-original-probes',*display,'-o','addopts=','-o','pythonpath=src',*map(str,probes),'--junitxml='+str(r/'final-original-probes.xml'))
run('final-ui-exact-original',wrapper,'env','BEAMO_WIPE_DRY_RUN=1','dbus-run-session','--','xvfb-run','-a','-n','766','-s','-screen 0 1600x1000x24 -dpi 72','python3','-m','pytest','-p','no:cacheprovider','-c',str(r/'pytest-ui-original.ini'),'-q',str(r/'ui-final-tests-original'),'--junitxml='+str(r/'final-ui-exact-original.xml'),expected=1)
modules=json.loads((r/'ui-adjacent-selection.json').read_text())
run('final-ui-adjacent',*display,*modules,'--junitxml='+str(r/'final-ui-adjacent.xml'))
for phase in ('lint','preview','negative'):run('final-'+phase,wrapper,'env','BEAMO_GATE_CHILD=1','bash','scripts/ci-hosted.sh',phase)
run('final-tests',wrapper,'env','BEAMO_GATE_CHILD=1','BEAMO_GATE_JUNIT='+str(r/'final-tests.xml'),'bash','scripts/ci-hosted.sh','tests')
