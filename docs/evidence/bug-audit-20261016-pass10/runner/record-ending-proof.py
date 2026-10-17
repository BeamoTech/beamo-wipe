from pathlib import Path
from beamo_wipe import nwipe_runner as module
from beamo_wipe.models import MethodId, WipeRequest

class Exited:
    returncode = 0
    def poll(self):
        return self.returncode

root = Path('/tmp/pass10-runner')
for ending in ('\n', '\r\n', '\r\r\n'):
    for large in (False, True):
        padding = ('ordinary detail ' + 'x' * 65500 + '\n') * 17 if large else ''
        text = padding + module.NWIPE_DRIVE_STATUS_HEADER + ending + ' sda | Erased | 120MB/s | 00:01:00 | FAKE/DISK\n'
        logfile = root / 'fake-current.log'
        logfile.write_bytes(text.encode())
        runner = module.NwipeRunner()
        runner._proc = Exited()
        request = WipeRequest('/dev/sda', MethodId.EVERYDAY, '/dev/sr0', str(logfile))
        result = runner.poll(request)
        direct = module.completion_for_method(0, text, request.device, request.method)
        print({'ending':repr(ending),'bytes':len(text),'large':large,'direct':direct,'runner':(result.ok,result.summary,result.reason),'projection_ready':runner._assessment_ready,'unchanged_file':logfile.read_bytes()==text.encode()})
