from pathlib import Path
import json,subprocess,sys
r=Path(__file__).parent
command=['env','BEAMO_ISOLATED_X11_TEST=1','BEAMO_WIPE_DRY_RUN=1','dbus-run-session','--','xvfb-run','-a','-n','179','-s','-screen 0 1600x1000x24 -dpi 72',sys.executable,'-m','pytest','-q','-W','error','-p','no:cacheprovider','-o','addopts=','--strict-markers','--junitxml='+str(r/'focused-ui.xml'),*json.loads((r/'selected-tests.json').read_text())]
raise SystemExit(subprocess.run([sys.executable,str(r/'run_group.py'),'focused-ui',*command],cwd='/workspace/beamo-wipe').returncode)
