from pathlib import Path
from PIL import ImageGrab
from beamo_wipe.demo import make_demo_wizard
from beamo_wipe.models import Screen
from beamo_wipe.ui.tk_wizard import TkWizard

out = Path('/tmp/pass9-ui')
w = make_demo_wizard()
a = TkWizard(w)
a.root.geometry('1000x760+0+0')
def capture(name):
    a._draw()
    for _ in range(3):
        a.root.update_idletasks()
        a.root.update()
    ImageGrab.grab().save(out / (name + '.png'))
    print(name, w.screen.name, flush=True)
capture('01-splash')
w.skip_intro()
capture('02-owner')
w.set_owner(True)
w.continue_owner()
capture('03-pick')
w.select_disk(w.selectable[0].path)
w.continue_pick()
capture('04-confirm')
w.set_confirm_input(w.confirm.token)
w.continue_confirm()
capture('05-method')
w.continue_method()
capture('06-review')
assert w.screen == Screen.LAST_CHANCE
assert not w.erase_enabled
w._erase_until = 0
w.confirm_erase()
assert w.screen == Screen.WORKING
capture('07-working')
w.request_stop()
capture('08-stop-confirm')
w.confirm_stop(w.stop_confirmation, asynchronous=False)
assert w.screen == Screen.DONE
capture('09-interrupted')
assert w.wipe_result is not None
assert not w.wipe_result.ok
a._teardown()
