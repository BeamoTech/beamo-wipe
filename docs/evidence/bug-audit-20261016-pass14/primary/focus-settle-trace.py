from types import SimpleNamespace
import json
import pytest
from beamo_wipe.models import Screen
from test_tk_focus_reveal_pass14 import fake_effects, _app, _visible  # noqa: F401

@pytest.mark.parametrize('screen,language,size', [(Screen.OWNER,'fr','standard'),(Screen.KEYBOARD,'de','large'),(Screen.KEYBOARD,'en','extra'),(Screen.OWNER,'en','extra'),(Screen.OWNER,'fr','extra')])
def test_geometry(screen,language,size):
 app=_app(screen,language,size)
 def state():
  c=app._body_canvas;f=app.root.focus_get()
  return dict(top=f.winfo_rooty()-c.winfo_rooty(),height=f.winfo_height(),viewport=c.winfo_height(),bbox=c.bbox('all'),yview=c.yview(),visible=_visible(app))
 try:
  before=state()
  app._on_body_focus(SimpleNamespace(widget=app.root.focus_get()))
  app.root.update()
  after=state()
  print(json.dumps(dict(screen=screen.name,language=language,size=size,before=before,after=after)))
 finally:app._teardown()
