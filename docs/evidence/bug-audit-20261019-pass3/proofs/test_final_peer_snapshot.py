"""Final runner rediscovery must preserve the inventory-bound consent."""
from dataclasses import replace
import pytest
from beamo_wipe.demo import discovery_for_scenario
from beamo_wipe.models import MethodId
from beamo_wipe.safety import SafetyError, assert_ready_to_wipe, confirm_spec, listed_disks
from beamo_wipe.nwipe_runner import _recheck_identity_under_lock
from beamo_wipe.wizard import Wizard

@pytest.mark.parametrize('change',('unchanged','add','remove','replace'))
def test_last_rescan_respects_inventory_authorization(tmp_path,monkeypatch,change):
 monkeypatch.setenv('BEAMO_WIPE_DRY_RUN','1')
 monkeypatch.setattr('beamo_wipe.safety.default_log_dir',lambda:tmp_path)
 monkeypatch.setattr('beamo_wipe.safety.assert_not_boot',lambda *_a,**_k:None)
 monkeypatch.setattr('beamo_wipe.safety.assert_existing_is_block_device',lambda *_a,**_k:None)
 monkeypatch.setattr('beamo_wipe.safety.block_rdev',lambda p:8 if p=='/dev/sda' else 16)
 initial=discovery_for_scenario('happy')
 target=initial.selectable[0]
 peer=replace(target,path='/dev/sde',name='sde',serial='PEER-A',wwn='50014ee2aa000091',size_bytes=512_000_000_000,size_gb_label='512',model='Peer A',raw_model='Peer A',layout_id='peer-a')
 initial=replace(initial,disks=(*initial.disks,peer),selectable=(*initial.selectable,peer))
 spec=confirm_spec(target,listed_disks(initial))
 request=assert_ready_to_wipe(owner_ok=True,disk=target,discovery=initial,typed_token=spec.token,countdown_complete=True,method=MethodId.EVERYDAY)
 if change=='add':
  new=replace(peer,path='/dev/sdf',name='sdf',serial='PEER-C',wwn='50014ee2aa000092')
  fresh=replace(initial,disks=(*initial.disks,new),selectable=(*initial.selectable,new))
 elif change=='remove':
  fresh=replace(initial,disks=tuple(d for d in initial.disks if d.path!=peer.path),selectable=tuple(d for d in initial.selectable if d.path!=peer.path))
 elif change=='replace':
  new=replace(peer,serial='PEER-B',wwn='50014ee2aa000093',model='Peer B',raw_model='Peer B',layout_id='peer-b')
  fresh=replace(initial,disks=tuple(new if d.path==peer.path else d for d in initial.disks),selectable=tuple(new if d.path==peer.path else d for d in initial.selectable))
 else:fresh=initial
 # Independently show that the wizard's current authorization key regards
 # the exact same mutation as stale while the final runner guard allows it.
 before=Wizard(initial,object());before.selected=target
 after=Wizard(fresh,object());after.selected=target
 assert (before._operation_key()==after._operation_key())==(change=='unchanged')
 monkeypatch.setattr('beamo_wipe.discover.discover',lambda:fresh)
 if change=='unchanged':_recheck_identity_under_lock(request)
 else:
  with pytest.raises(SafetyError,match='identity|inventory|authorization'):
   _recheck_identity_under_lock(request)
