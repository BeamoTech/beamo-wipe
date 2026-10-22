"""Write/checksum API trace using owned regular files and an injected link boundary."""
import hashlib,json,os,tempfile
from pathlib import Path
from unittest.mock import patch
from beamo_wipe import evidence

with tempfile.TemporaryDirectory(prefix='pass13-publish-api-') as temporary:
    directory=Path(temporary)
    original_link=os.link
    swaps=[]
    def alter_before_publication(source,destination,*args,**kwargs):
        if destination.endswith('.json'):
            fd=os.open(source,os.O_RDWR,dir_fd=kwargs['src_dir_fd'])
            try:
                original=os.read(fd,1<<20)
                changed=original.replace(b'"owner-provided"',b'"foreign-bytes"')
                assert changed != original
                os.lseek(fd,0,os.SEEK_SET)
                os.ftruncate(fd,0)
                os.write(fd,changed)
                swaps.append(dict(before_sha256=hashlib.sha256(original).hexdigest(),after_sha256=hashlib.sha256(changed).hexdigest()))
            finally: os.close(fd)
        return original_link(source,destination,*args,**kwargs)
    with patch.dict(os.environ,{'BEAMO_WIPE_DRY_RUN':'1'}),patch('os.link',alter_before_publication):
        path=evidence.write_evidence_atomic({'sentinel':'owner-provided'},log_dir=directory,device_path='/dev/fake',target_device='/dev/fake')
    print(json.dumps(dict(api_returned=True,payload=json.loads(path.read_bytes()),checksum_verified=evidence.verify_evidence_checksum(path),mutations=swaps),sort_keys=True))
