"""Keep successful race injection distinct from a native OS denying it."""

from contextlib import contextmanager
import stat
import sys


def _snapshot(path):
    metadata = path.lstat()
    return (
        metadata.st_dev,
        metadata.st_ino,
        metadata.st_mode,
        metadata.st_size,
        metadata.st_mtime_ns,
        path.read_bytes() if stat.S_ISREG(metadata.st_mode) else None,
    )


class NativeMutation:
    def __init__(self, request):
        self.request = request
        self.denied = None
        self.attempted = False

    @contextmanager
    def operation(self, *winerrors, unchanged=()):
        before = [_snapshot(path) for path in unchanged]
        self.attempted = True
        try:
            yield
        except OSError as exc:
            if sys.platform == "win32" and exc.winerror in winerrors:
                assert [_snapshot(path) for path in unchanged] == before
                self.denied = exc
                self.request.node.user_properties.append(
                    ("fixture_mutation", f"native-denied-winerror-{exc.winerror}")
                )
            raise

    def was_denied(self, caught):
        assert self.attempted, "The mutation callback was not reached"
        if self.denied is not None:
            assert caught.value is self.denied, "The original denial was swallowed"
            return True
        self.request.node.user_properties.append(("fixture_mutation", "performed"))
        return False
