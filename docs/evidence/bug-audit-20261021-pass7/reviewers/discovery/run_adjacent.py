from pathlib import Path
import json,subprocess,sys
r=Path(__file__).parent
cmd=[sys.executable,"-m","pytest","-p","no:cacheprovider","-q",*json.loads((r/"adjacent-selection.json").read_text()),"--junitxml="+str(r/"adjacent-baseline.xml")]
with (r/"adjacent-baseline.log").open("wb")as f:p=subprocess.run(cmd,stdout=f,stderr=subprocess.STDOUT)
(r/"adjacent-baseline.exit").write_text(str(p.returncode)+"\n")
print("Adjacent exit",p.returncode)
sys.exit(p.returncode)
