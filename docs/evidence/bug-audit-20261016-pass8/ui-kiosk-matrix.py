import itertools,json,tempfile
from pathlib import Path
from test_kiosk_recovery import run_kiosk,launches
count=0
with tempfile.TemporaryDirectory(prefix='beamo-pass8-ui-kiosk-') as base:
 for g,c,e,choice,accepted in itertools.product((0,1,3,127),(0,1,127),(0,1,2,127,255),('4','5'),(False,True)):
  p=Path(base)/str(count);p.mkdir()
  action='reboot' if choice=='4' else 'poweroff'
  token=('RESTART' if choice=='4' else 'SHUTDOWN') if accepted else 'INVALID'
  result,calls=run_kiosk(p,inputs=f'{choice}\n{token}\n',graphical=g,console=c,engine=e,power=0)
  assert result.returncode==0,(g,c,e,choice,accepted,result.stderr)
  power=launches(calls,'systemctl')
  assert len(power)==int(accepted and e==1),(g,c,e,choice,accepted,calls)
  if power:assert power==[f'systemctl --no-block {action}']
  assert len(launches(calls,'startx'))<=3 and len(launches(calls,'beamo-wipe'))<=3
  assert 'This screen cannot identify disks or confirm an erase result.' in result.stdout
  if accepted and e!=1:assert 'Power request blocked' in result.stdout
  count+=1
print(json.dumps({'fully_stubbed_kiosk_exit_power_token_cases':count,'unexpected_host_actions':0},indent=2))
