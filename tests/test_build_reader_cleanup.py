"""Reader ownership with exact helper AST and an entirely in-memory OS.

No product import, native descriptor, subprocess or physical input is used.
The same helper chain runs on Linux pytest and in the bounded stdlib replay.
"""
from __future__ import annotations

import ast
import builtins
from collections import Counter
import dataclasses
import hashlib
import json
from pathlib import Path, PurePosixPath
import stat
import sys
from types import SimpleNamespace


ROOT = Path(__file__).resolve().parents[1]
TRACE_ROWS = []
RM_NAMES = {
    '_RegularBinding', '_OutputSnapshot', '_metadata_values',
    '_validate_nonposix_parent', '_open_pinned_parent', '_named_metadata',
    '_require_parent_binding', '_open_bound_regular', '_open_regular_nofollow',
    '_read_descriptor', '_binding', '_read_regular_snapshot',
    '_hash_regular_snapshot', '_require_regular_binding', '_stat_fields',
    '_regular_fd_snapshot', '_regular_output_snapshot',
}
CI_NAMES = {
    '_OptionalImageInputMissing', '_metadata_values', '_open_evidence_directory', '_read_descriptor',
    '_regular_file_is_bound', '_read_regular_at', '_hash_regular_at',
    '_create_regular_at', '_write_bytes_at',
    '_require_evidence_directory', '_require_evidence_binding', '_name_exists',
    '_load_receipts_at', 'load_receipts', 'run_gate', 'collect_inventory', 'finalize',
    'print_summary', 'qemu_evidence_hashes', '_image_directory_fd', '_image_text',
    '_verify_execution_log',
    '_image_source_names',
}


def load_reader_ast(module, fs):
    source = ROOT / ('src/beamo_wipe/' + module + '.py')
    tree = ast.parse(source.read_bytes())
    names = RM_NAMES if module == 'release_manifest' else CI_NAMES
    selected = [node for node in tree.body
                if isinstance(node, (ast.FunctionDef, ast.ClassDef))
                and node.name in names | {'_close_reader_fds'}]
    assert names <= {node.name for node in selected}
    env = dict(os=fs, Path=fs.Path, stat=stat, hashlib=hashlib,
               dataclass=dataclasses.dataclass, json=json, __version__='0.2.14',
               KNOWN_GATES={'tests'}, __builtins__=dict(vars(builtins)))
    for node in tree.body:
        if isinstance(node, ast.Assign) and len(node.targets) == 1:
            target = node.targets[0]
            if isinstance(target, ast.Name) and target.id in {
                '_REGULAR_BIND_FIELDS', '_PARENT_BIND_FIELDS', '_SNAPSHOT_FIELDS',
                '_DIRECTORY_ID_FIELDS', '_FILE_ID_FIELDS',
            }:
                env[target.id] = ast.literal_eval(node.value)
    future = ast.parse('from __future__ import annotations').body
    exec(compile(ast.Module(body=future + selected, type_ignores=[]), str(source), 'exec'), env)  # noqa: S102
    return env


class ReaderOS:
    name, sep, SEEK_SET = 'posix', '/', 0
    O_RDONLY, O_RDWR, O_CREAT, O_EXCL = 0, 2, 64, 128
    O_NONBLOCK, O_DIRECTORY, O_NOFOLLOW, O_CLOEXEC = 2048, 65536, 131072, 524288

    def __init__(self):
        self.nodes, self.live, self.acquired, self.borrowed = {}, {}, {}, set()
        self.events, self.rules, self.counts = [], [], Counter()
        self.next_fd = 10
        self.environ = {}
        self.path = SimpleNamespace(abspath=lambda value: '/' + str(value).lstrip('/'))
        fs = self

        class FakePath(PurePosixPath):
            def lstat(self):
                return fs.lstat(self)

        self.Path = FakePath
        for path in ('/', '/a', '/a/b'):
            self.put(path, mode=stat.S_IFDIR | 0o700)
        self.put('/a/b/item', b'abc\n')

    def put(self, path, data=b'', mode=stat.S_IFREG | 0o600):
        self.nodes[path] = dict(st_dev=1, st_ino=len(self.nodes) + 100,
                                st_mode=mode, st_uid=7, st_nlink=1,
                                st_size=len(data), st_mtime_ns=10, st_ctime_ns=11,
                                data=bytes(data))

    def info(self, path):
        if path not in self.nodes:
            raise FileNotFoundError(path)
        return SimpleNamespace(**{k: v for k, v in self.nodes[path].items() if k != 'data'})

    def fault(self, op, path, error, at=1, after=None):
        self.rules.append((op, path, at, error, after))

    def event(self, op, path, **details):
        self.counts[op, path] += 1
        self.events.append(dict(op=op, path=path, **details))
        for action, target, at, error, after in self.rules:
            if ((op, path, self.counts[op, path]) == (action, target, at)
                    and (after is None or self.counts[after])):
                raise error

    def key(self, path, dir_fd=None):
        value = str(path)
        return value if value.startswith('/') else str(PurePosixPath(self.live[dir_fd][0]) / value)

    def seed(self, path):
        fd = self.allocate(path)
        self.borrowed.add(fd)
        return fd

    def allocate(self, path):
        self.next_fd += 1
        self.live[self.next_fd] = [path, 0]
        self.acquired[self.next_fd] = path
        self.events.append(dict(op='acquire', path=path, fd=self.next_fd))
        return self.next_fd

    def open(self, path, flags, mode=0o644, *, dir_fd=None):
        key = self.key(path, dir_fd)
        self.event('open', key, flags=flags, dir_fd=dir_fd)
        if flags & self.O_CREAT:
            if key in self.nodes and flags & self.O_EXCL:
                raise FileExistsError(key)
            self.put(key, mode=stat.S_IFREG | mode)
        metadata = self.info(key)
        if flags & self.O_NOFOLLOW and stat.S_ISLNK(metadata.st_mode):
            raise OSError('nofollow refusal')
        if flags & self.O_DIRECTORY and not stat.S_ISDIR(metadata.st_mode):
            raise OSError('not directory')
        return self.allocate(key)

    def close(self, fd):
        self.events.append(dict(op='close-attempt', path=self.acquired[fd], fd=fd))
        assert fd in self.live and fd not in self.borrowed, ('unowned/retried close', fd)
        path, _ = self.live.pop(fd)
        self.event('close', path, fd=fd)

    def fstat(self, fd):
        path = self.live[fd][0]
        self.event('fstat', path, fd=fd)
        return self.info(path)

    def stat(self, path, *, dir_fd=None, follow_symlinks=True):
        key = self.key(path, dir_fd)
        self.event('stat', key, follow_symlinks=follow_symlinks)
        return self.info(key)

    def lstat(self, path):
        key = self.key(path)
        self.event('lstat', key)
        return self.info(key)

    def read(self, fd, count):
        path, offset = self.live[fd]
        self.event('read', path)
        data = self.nodes[path]['data'][offset:offset + count]
        self.live[fd][1] += len(data)
        return data

    def pread(self, fd, count, offset):
        path = self.live[fd][0]
        self.event('pread', path)
        return self.nodes[path]['data'][offset:offset + count]

    def lseek(self, fd, offset, whence):
        assert whence == self.SEEK_SET
        self.live[fd][1] = offset

    def write(self, fd, data):
        path = self.live[fd][0]
        self.event('write', path)
        self.nodes[path]['data'] += bytes(data)
        self.nodes[path]['st_size'] = len(self.nodes[path]['data'])
        return len(data)

    def fchmod(self, fd, mode):
        self.event('fchmod', self.live[fd][0])
        self.nodes[self.live[fd][0]]['st_mode'] = stat.S_IFREG | mode

    def fsync(self, fd):
        self.event('fsync', self.live[fd][0])

    def dup(self, fd):
        path = self.live[fd][0]
        self.event('dup', path)
        return self.allocate(path)

    def fdopen(self, fd, mode):
        assert mode == 'rb'
        fs = self

        class Stream:
            def __enter__(self):
                return self

            def __exit__(self, *args):
                fs.close(fd)

            def fileno(self):
                return fd

            def read(self, count):
                return fs.read(fd, count)

            def seek(self, offset):
                return fs.lseek(fd, offset, fs.SEEK_SET)

        return Stream()

    def mkdir(self, path, mode, *, dir_fd):
        key = self.key(path, dir_fd)
        if key in self.nodes:
            raise FileExistsError(key)
        self.put(key, mode=stat.S_IFDIR | mode)

    def listdir(self, directory_fd):
        path = self.live[directory_fd][0]
        self.event('listdir', path)
        prefix = path.rstrip('/') + '/'
        return [key[len(prefix):] for key in self.nodes
                if key.startswith(prefix) and '/' not in key[len(prefix):]]

    @staticmethod
    def fspath(path):
        return str(path)

    @staticmethod
    def getuid():
        return 7


def capture(call):
    try:
        return call(), None
    except BaseException as error:
        return None, error


def assert_ownership(fs, returned=()):
    expected = fs.borrowed | set(returned)
    assert set(fs.live) == expected, (fs.live, expected, fs.events)
    counts = Counter(e['fd'] for e in fs.events if e['op'] == 'close-attempt')
    assert all(count == 1 for count in counts.values()), counts
    assert set(counts) == set(fs.acquired) - expected
    assert not set(counts) & fs.borrowed
    TRACE_ROWS.append(dict(kind='ownership-checked', returned=list(returned), events=fs.events))


def setup_case(module, function):
    fs = ReaderOS()
    env = load_reader_ast(module, fs)
    path = fs.Path('/a/b/item')
    parent = tuple(getattr(fs.info('/a/b'), k) for k in ('st_dev', 'st_ino', 'st_mode', 'st_uid'))
    directory = fs.seed('/a/b') if module == 'ci_evidence' or function == '_require_parent_binding' else None
    binding = env['_binding'](path, fs.info(str(path)), parent) if module == 'release_manifest' else None
    if function == '_open_evidence_directory':
        def call():
            return env[function](path.parent)
    elif function == '_require_parent_binding':
        def call():
            return env[function](path, directory, parent)
    elif function == '_require_regular_binding':
        def call():
            return env[function](binding)
    elif function == '_regular_output_snapshot':
        def call():
            return env[function](path, 16)
    elif function in ('_read_regular_snapshot', '_read_regular_at'):
        call = (lambda: env[function](path, limit=16, what='fixture')) if module == 'release_manifest' else (lambda: env[function](directory, 'item', limit=16, what='fixture'))
    elif function == '_hash_regular_at':
        def call():
            return env[function](directory, 'item', what='fixture')
    elif function == '_create_regular_at':
        def call():
            return env[function](directory, 'new')
    elif function == '_write_bytes_at':
        def call():
            return env[function](directory, 'new', b'new bytes')
    else:
        def call():
            return env[function](path)
    return fs, env, call


def returned_fds(function, value):
    if function == '_open_pinned_parent':
        return () if value[1] is None else (value[1],)
    if function == '_open_bound_regular':
        return tuple(fd for fd in (value[1], value[3]) if fd is not None)
    if function in ('_open_evidence_directory', '_open_regular_nofollow', '_create_regular_at'):
        return (value,)
    return ()


OPERATIONS = (
    ('release_manifest', '_open_pinned_parent', 'fstat', '/a/b'),
    ('release_manifest', '_require_parent_binding', 'fstat', '/a/b'),
    ('release_manifest', '_open_bound_regular', 'fstat', '/a/b/item'),
    ('release_manifest', '_open_regular_nofollow', 'fstat', '/a/b/item'),
    ('release_manifest', '_read_regular_snapshot', 'read', '/a/b/item'),
    ('release_manifest', '_hash_regular_snapshot', 'read', '/a/b/item'),
    ('release_manifest', '_require_regular_binding', 'stat', '/a/b/item'),
    ('release_manifest', '_regular_output_snapshot', 'pread', '/a/b/item'),
    ('ci_evidence', '_open_evidence_directory', 'fstat', '/a/b'),
    ('ci_evidence', '_read_regular_at', 'read', '/a/b/item'),
    ('ci_evidence', '_hash_regular_at', 'read', '/a/b/item'),
    ('ci_evidence', '_create_regular_at', 'fchmod', '/a/b/new'),
    ('ci_evidence', '_write_bytes_at', 'write', '/a/b/new'),
)


def test_reader_normal_returns_and_transfer_controls():
    for module, function, _op, _path in OPERATIONS:
        fs, _env, call = setup_case(module, function)
        value, error = capture(call)
        assert error is None, (module, function, error)
        assert_ownership(fs, returned_fds(function, value))
        if function in ('_read_regular_snapshot', '_read_regular_at'):
            assert (value[0] if isinstance(value, tuple) else value) == b'abc\n'
        if function in ('_hash_regular_snapshot', '_hash_regular_at'):
            assert (value[0] if isinstance(value, tuple) else value) == hashlib.sha256(b'abc\n').hexdigest()
        if function == '_hash_regular_snapshot':
            assert value[1] == 4 and value[2].path == fs.Path('/a/b/item')
        if function == '_regular_output_snapshot':
            assert value.contents == b'abc\n' and value.kind == 'regular'
        if function == '_write_bytes_at':
            assert value is None and fs.nodes['/a/b/new']['data'] == b'new bytes'


def test_reader_primary_identity_and_each_cleanup_error():
    for module, function, op, path in OPERATIONS:
        for primary_type in (KeyboardInterrupt, SystemExit, ValueError):
            for close_type in (OSError, KeyboardInterrupt, SystemExit):
                fs, _env, call = setup_case(module, function)
                primary = primary_type('primary ' + function)
                fs.fault(op, path, primary)
                for target in ('/', '/a', '/a/b', '/a/b/item', '/a/b/new'):
                    # Traversal closes before the primary must succeed. The final
                    # /a/b close is the first close of that path on failure.
                    if target in ('/a/b', '/a/b/item', '/a/b/new'):
                        fs.fault('close', target, close_type('secondary ' + target),
                                 after=(op, path))
                _value, error = capture(call)
                TRACE_ROWS.append(dict(module=module, function=function,
                                       primary=primary_type.__name__, close=close_type.__name__,
                                       preserved=error is primary, live=list(fs.live), events=fs.events))
                assert error is primary, (module, function, error, primary)
                assert_ownership(fs)


def test_directory_pending_close_failure_is_not_retried():
    for module, function in (('release_manifest', '_open_pinned_parent'),
                             ('ci_evidence', '_open_evidence_directory')):
        for close_type in (OSError, KeyboardInterrupt, SystemExit):
            fs, _env, call = setup_case(module, function)
            primary = close_type('current directory close')
            fs.fault('close', '/', primary)
            fs.fault('close', '/a', SystemExit('pending directory close'))
            _value, error = capture(call)
            assert error is primary or (isinstance(error, RuntimeError) and error.__cause__ is primary), (module, function, '/', error)
            assert_ownership(fs)


def test_reader_standalone_cleanup_errors_inside_active_outer_exception():
    for module, function, _op, _path in OPERATIONS:
        # Returning an owner is intentionally not a close operation.
        if function in ('_open_pinned_parent', '_open_evidence_directory', '_open_bound_regular', '_create_regular_at'):
            continue
        for target in ('/a/b', '/a/b/item'):
            if function == '_require_parent_binding' and target != '/a/b':
                continue
            if function == '_open_regular_nofollow' and target == '/a/b/item':
                continue  # Its leaf is returned to the caller.
            if module == 'ci_evidence' and target == '/a/b':
                continue  # The directory is borrowed here.
            fs, _env, call = setup_case(module, function)
            if function == '_write_bytes_at':
                target = '/a/b/new'
            primary = OSError('standalone close')
            # Parent checks reopen /a/b while leaf is still owned. For wrappers
            # the first /a/b close is that internal check; it must also fail shut.
            fs.fault('close', target, primary)
            try:
                raise ValueError('unrelated outer exception')
            except ValueError:
                _value, error = capture(call)
            assert error is primary or (isinstance(error, RuntimeError) and error.__cause__ is primary), (module, function, target, error)
            assert_ownership(fs)


def test_reader_acquisition_line_interrupts_own_root_pending_and_leaf():
    for module, function, _op, _path in OPERATIONS:
        for target in ('/', '/a', '/a/b', '/a/b/item', '/a/b/new'):
            for error_type in (KeyboardInterrupt, SystemExit):
                fs, env, call = setup_case(module, function)
                primary = error_type('line after acquisition')
                injected = []
                previous = sys.gettrace()
                code = env[function].__code__

                def trace(frame, event, _arg):
                    if frame.f_code is code and event == 'line' and not injected:
                        if any(path == target and fd not in fs.borrowed for fd, (path, _offset) in fs.live.items()):
                            injected.append(frame.f_lineno)
                            raise primary
                    return trace

                try:
                    sys.settrace(trace)
                    value, error = capture(call)
                finally:
                    sys.settrace(previous)
                if injected:
                    assert error is primary, (module, function, target, error)
                    assert_ownership(fs)
                else:
                    assert error is None
                    assert_ownership(fs, returned_fds(function, value))


def test_readers_keep_absence_links_size_identity_and_exclusive_refusals():
    for module, function in (('release_manifest', '_regular_output_snapshot'),
                             ('release_manifest', '_read_regular_snapshot'),
                             ('release_manifest', '_hash_regular_snapshot'),
                             ('ci_evidence', '_read_regular_at'),
                             ('ci_evidence', '_hash_regular_at')):
        for kind in ('absent', 'symlink', 'fifo', 'metadata', 'oversize'):
            if function == '_hash_regular_snapshot' and kind == 'metadata':
                continue  # This API binds metadata; it does not count stream bytes.
            if kind == 'oversize' and 'hash' in function:
                continue
            fs, _env, call = setup_case(module, function)
            if kind == 'absent':
                del fs.nodes['/a/b/item']
            elif kind in ('symlink', 'fifo'):
                fs.nodes['/a/b/item']['st_mode'] = stat.S_IFLNK if kind == 'symlink' else stat.S_IFIFO
            elif kind == 'metadata':
                fs.nodes['/a/b/item']['st_size'] = 99
            else:
                fs.nodes['/a/b/item']['data'] = b'x' * 17
                fs.nodes['/a/b/item']['st_size'] = 17
            value, error = capture(call)
            if function == '_regular_output_snapshot' and kind == 'absent':
                assert value is None and error is None
            else:
                assert error is not None, (module, function, kind)
            assert_ownership(fs)
    for function in ('_create_regular_at', '_write_bytes_at'):
        fs, _env, call = setup_case('ci_evidence', function)
        fs.put('/a/b/new', b'foreign')
        _value, error = capture(call)
        assert isinstance(error, FileExistsError)
        assert fs.nodes['/a/b/new']['data'] == b'foreign'
        assert_ownership(fs)


def test_ci_readers_refuse_hardlinks_and_rm_preserves_nonposix_contract():
    for function in ('_read_regular_at', '_hash_regular_at'):
        fs, _env, call = setup_case('ci_evidence', function)
        fs.nodes['/a/b/item']['st_nlink'] = 2
        _value, error = capture(call)
        assert isinstance(error, RuntimeError)
        assert_ownership(fs)
    for function in ('_open_pinned_parent', '_read_regular_snapshot', '_hash_regular_snapshot'):
        fs, _env, call = setup_case('release_manifest', function)
        fs.name = 'nt'
        value, error = capture(call)
        assert error is None
        assert_ownership(fs, returned_fds(function, value))


def caller_case(function):
    fs = ReaderOS()
    env = load_reader_ast('ci_evidence', fs)
    del fs.nodes['/a/b/item']
    path = fs.Path('/a/b')

    def deny(*args, **kwargs):
        raise AssertionError('forbidden process/product operation')

    env['subprocess'] = SimpleNamespace(check_output=deny, Popen=deny)
    env['_image_source_names'] = deny
    if function == '_require_evidence_binding':
        directory = fs.seed(str(path))
        def call():
            return env[function](path, directory)
        fault = ('fstat', str(path), 2)
    elif function == 'load_receipts':
        def call():
            return env[function](path)
        fault = ('listdir', str(path), 1)
    elif function == 'run_gate':
        def call():
            return env[function]('tests', ['FORBIDDEN'], root=path, evidence_dir=path, build_id='local')
        fault = ('fstat', str(path), 3)
    elif function == 'collect_inventory':
        def call():
            return env[function](path, path / 'inventory', 'fake-commit')
        fault = ('fstat', str(path), 3)
    else:
        assert function == 'finalize'
        for target in ('/a/b/dist', '/a/b/dist/evidence'):
            fs.put(target, mode=stat.S_IFDIR | 0o700)
        prior = dict(source={'commit': 'fake-commit'}, build={'release_build_id': 'local'})
        rm = SimpleNamespace(verify_build_manifest=lambda *a, **kw: json.dumps(prior).encode(),
                             git_commit=lambda: 'fake-commit',
                             require_verified_prior_checksum_list=lambda *a, **kw: object(),
                             generate_manifest=deny, write_manifest=deny, verify_manifest=deny,
                             _atomic_write=deny)
        def fake_import(name, *args, **kwargs):
            assert name == 'beamo_wipe', name
            return SimpleNamespace(release_manifest=rm)

        env['__builtins__']['__import__'] = fake_import
        env['_unique_json_fields'] = dict
        def call():
            return env[function](path)
        fault = ('listdir', '/a/b/dist/evidence', 3)
    return fs, env, call, fault


def test_proved_callers_preserve_primary_and_all_owned_directory_closes():
    for function in ('_require_evidence_binding', 'load_receipts', 'run_gate', 'collect_inventory', 'finalize'):
        for primary_type in (OSError, KeyboardInterrupt, SystemExit):
            for close_type in (OSError, KeyboardInterrupt, SystemExit):
                fs, _env, call, (op, path, at) = caller_case(function)
                primary = primary_type('caller boundary refusal')
                fs.fault(op, path, primary, at)
                for close_at in (1, 2):
                    fs.fault('close', path, close_type('caller directory close'),
                             close_at if function != 'finalize' else close_at + 2,
                             after=(op, path))
                _value, error = capture(call)
                TRACE_ROWS.append(dict(function=function, primary=primary_type.__name__,
                                       close=close_type.__name__, preserved=error is primary,
                                       live=list(fs.live), events=fs.events))
                assert error is primary, (function, error, primary)
                assert_ownership(fs)


def test_evidence_directory_wrapper_transfer_interrupt_and_close_controls():
    for error_type in (KeyboardInterrupt, SystemExit):
        fs = ReaderOS()
        env = load_reader_ast('ci_evidence', fs)
        function = env['_require_evidence_directory']
        primary = error_type('wrapper acquisition line')
        injected = []
        previous = sys.gettrace()

        def trace(frame, event, _arg):
            if frame.f_code is function.__code__ and event == 'line' and fs.live and not injected:
                injected.append(frame.f_lineno)
                raise primary
            return trace

        try:
            sys.settrace(trace)
            _value, error = capture(lambda: function(fs.Path('/a/b')))
        finally:
            sys.settrace(previous)
        assert error is primary and injected
        assert not (set(fs.live) - fs.borrowed), (injected, fs.live)
        assert_ownership(fs)
    for fail in (False, True):
        fs = ReaderOS()
        env = load_reader_ast('ci_evidence', fs)
        error = OSError('standalone wrapper close')
        if fail:
            fs.fault('close', '/a/b', error)
        value, caught = capture(lambda: env['_require_evidence_directory'](fs.Path('/a/b')))
        assert caught is (error if fail else None) and value is None
        assert_ownership(fs)


def retained_case(function):
    fs = ReaderOS()
    env = load_reader_ast('ci_evidence', fs)
    env['print'] = lambda *args, **kwargs: None
    path = fs.Path('/a/b')
    if function in ('print_summary', 'qemu_evidence_hashes'):
        def call():
            return env[function](path)
        fault, close = ('listdir', str(path)), str(path)
    elif function == '_image_text':
        def call():
            return env[function](fs.Path('/a'), fs.Path('b/item'), required=True, limit=16)
        fault, close = ('read', '/a/b/item'), str(path)
    else:
        assert function == '_verify_execution_log'
        parent = fs.seed(str(path))
        def call():
            return env[function](path / 'item', parent, fs.info('/a/b/item'), 4, hashlib.sha256(b'abc\n').hexdigest())
        fault, close = ('read', '/a/b/item'), '/a/b/item'
    return fs, env, call, fault, close


def test_retained_reader_callers_preserve_refusal_cause_and_cleanup():
    for function in ('print_summary', 'qemu_evidence_hashes', '_image_text', '_verify_execution_log'):
        for primary_type in (OSError, KeyboardInterrupt, SystemExit):
            for cleanup_type in (OSError, KeyboardInterrupt, SystemExit):
                fs, _env, call, (op, path), close = retained_case(function)
                primary = primary_type('retained reader refusal')
                fs.fault(op, path, primary)
                fs.fault('close', close, cleanup_type('retained cleanup'), after=(op, path))
                _value, error = capture(call)
                TRACE_ROWS.append(dict(function=function, primary=primary_type.__name__,
                                       close=cleanup_type.__name__, preserved=error is primary,
                                       cause_preserved=error is not None and error.__cause__ is primary,
                                       live=list(fs.live), events=fs.events))
                assert error is primary or (isinstance(error, RuntimeError) and error.__cause__ is primary)
                assert_ownership(fs)


def test_retained_reader_normal_contracts_and_directory_transfers():
    for function in ('print_summary', 'qemu_evidence_hashes', '_image_text', '_verify_execution_log'):
        fs, _env, call, _fault, _close = retained_case(function)
        value, error = capture(call)
        assert error is None, (function, error)
        if function == 'qemu_evidence_hashes':
            assert value == {'item': hashlib.sha256(b'abc\n').hexdigest()}
        elif function == '_image_text':
            assert value == 'abc\n'
        else:
            assert value is None
        assert_ownership(fs)
    for at in (0, 1, 3):
        fs = ReaderOS()
        env = load_reader_ast('ci_evidence', fs)
        primary = OSError('old or retained-root close')
        if at:
            fs.fault('close', '/a', primary, at)
        value, error = capture(lambda: env['_image_directory_fd'](fs.Path('/a'), fs.Path('b')))
        assert error is (primary if at else None)
        assert_ownership(fs, () if at else (value,))


def test_image_directory_root_pending_and_successor_line_interrupts():
    for target in ('/a', '/a/b'):
        for minimum_live in (1, 2):
            for error_type in (KeyboardInterrupt, SystemExit):
                fs = ReaderOS()
                env = load_reader_ast('ci_evidence', fs)
                function = env['_image_directory_fd']
                primary = error_type('image owner transfer')
                previous = sys.gettrace()
                injected = []

                def trace(frame, event, _arg):
                    if frame.f_code is function.__code__ and event == 'line' and not injected:
                        if len(fs.live) >= minimum_live and any(p == target for p, _ in fs.live.values()):
                            injected.append(frame.f_lineno)
                            raise primary
                    return trace

                try:
                    sys.settrace(trace)
                    value, error = capture(lambda: function(fs.Path('/a'), fs.Path('b')))
                finally:
                    sys.settrace(previous)
                assert injected and error is primary, (target, minimum_live, error)
                assert_ownership(fs)


def test_reader_oserror_mappings_retain_original_cause_after_cleanup_fault():
    for module, function, op, path in OPERATIONS:
        fs, _env, call = setup_case(module, function)
        primary = OSError('original IO boundary')
        fs.fault(op, path, primary)
        for target in ('/a/b', '/a/b/item', '/a/b/new'):
            fs.fault('close', target, SystemExit('secondary cleanup'), after=(op, path))
        _value, error = capture(call)
        assert error is primary or (isinstance(error, RuntimeError) and error.__cause__ is primary), (function, error)
        assert_ownership(fs)


def test_failed_close_never_closes_a_reused_peer_number():
    for module, function in (('release_manifest', '_open_pinned_parent'),
                             ('ci_evidence', '_open_evidence_directory'),
                             ('ci_evidence', '_image_directory_fd')):
        fs = ReaderOS()
        env = load_reader_ast(module, fs)
        primary = OSError('release then reuse before close reports EIO')
        fs.fault('close', '/a' if function == '_image_directory_fd' else '/', primary)
        original_close = fs.close
        reused = []

        def reuse_close(fd):
            try:
                original_close(fd)
            except OSError as error:
                if error is primary and not reused:
                    reused.append(fd)
                    fs.live[fd] = ['/peer-sentinel', 0]
                raise

        fs.close = reuse_close
        path = fs.Path('/a/b/item')
        if function == '_image_directory_fd':
            def call():
                return env[function](fs.Path('/a'), fs.Path('b'))
        elif function == '_open_evidence_directory':
            def call():
                return env[function](path.parent)
        else:
            def call():
                return env[function](path)
        _value, error = capture(call)
        assert error is primary or (isinstance(error, RuntimeError) and error.__cause__ is primary)
        assert len(reused) == 1 and fs.live == {reused[0]: ['/peer-sentinel', 0]}
        attempts = Counter(e['fd'] for e in fs.events if e['op'] == 'close-attempt')
        assert all(count == 1 for count in attempts.values())


def test_image_text_absence_and_standalone_cleanup_do_not_hide_failure():
    for absent in (False, True):
        for cleanup_type in (None, OSError, FileNotFoundError, KeyboardInterrupt, SystemExit):
            fs = ReaderOS()
            env = load_reader_ast('ci_evidence', fs)
            if absent:
                del fs.nodes['/a/b/item']
            cleanup = cleanup_type('standalone parent close') if cleanup_type else None
            if cleanup is not None:
                fs.fault('close', '/a/b', cleanup)
            value, error = capture(lambda: env['_image_text'](
                fs.Path('/a'), fs.Path('b/item'), required=False, limit=16))
            assert error is cleanup
            if error is None:
                assert value == (None if absent else 'abc\n')
            assert_ownership(fs)


def test_retained_binding_and_leaf_transfer_faults_reach_the_owned_caller():
    failures = []
    for function, op, at in (('_require_parent_binding', 'fstat', 2),
                             ('_require_regular_binding', 'stat', 2),
                             ('_open_regular_nofollow', 'close', 2)):
        fs, _env, call = setup_case('release_manifest', function)
        target = '/a/b/item' if op == 'stat' else '/a/b'
        primary = ValueError('retained binding body') if op != 'close' else OSError('parent transfer close')
        fs.fault(op, target, primary, at)
        if op != 'close':
            fs.fault('close', '/a/b', OSError('secondary retained parent close'),
                     1 if function == '_require_parent_binding' else 2,
                     after=(op, target))
            fs.fault('close', '/a/b/item', OSError('secondary retained leaf close'),
                     after=(op, target))
        _value, error = capture(call)
        TRACE_ROWS.append(dict(kind='exact-caller-boundary', function=function, op=op,
                               occurrence=at, preserved=error is primary,
                               cause_preserved=error is not None and error.__cause__ is primary,
                               events=fs.events))
        try:
            assert error is primary or (isinstance(error, RuntimeError) and error.__cause__ is primary)
            assert_ownership(fs)
        except AssertionError:
            failures.append(function)
    assert not failures, failures


def test_snapshot_success_attempts_leaf_and_retained_parent_close_once_each():
    for function in ('_read_regular_snapshot', '_hash_regular_snapshot'):
        for target, at in (('/a/b/item', 1), ('/a/b', 2)):
            for close_type in (OSError, KeyboardInterrupt, SystemExit):
                fs, _env, call = setup_case('release_manifest', function)
                primary = close_type('standalone snapshot close')
                fs.fault('close', target, primary, at)
                _value, error = capture(call)
                assert error is primary, (function, target, error)
                assert_ownership(fs)


def optional_inventory_case(function, absent, required=False):
    fs = ReaderOS()
    env = load_reader_ast('ci_evidence', fs)
    for target in ('/a/etc', '/a/etc/apt'):
        fs.put(target, mode=stat.S_IFDIR | 0o700)
    if not absent:
        fs.put('/a/etc/apt/sources.list.d', mode=stat.S_IFDIR | 0o700)
        fs.put('/a/etc/apt/sources.list.d/item.list', b'abc\n')
    if function == '_image_text':
        def call():
            return env[function](fs.Path('/a'), fs.Path('missing/item'), required=required, limit=16)
    else:
        def call():
            return env[function](fs.Path('/a'))
    return fs, env, call


def test_optional_missing_parent_requires_successful_cleanup():
    failures = []
    for function in ('_image_text', '_image_source_names'):
        for close_at in (1, 2):
            for cleanup_type in (OSError, FileNotFoundError, KeyboardInterrupt, SystemExit):
                fs, _env, call = optional_inventory_case(function, absent=True)
                cleanup = cleanup_type('optional parent missing cleanup')
                # Both current duplicate and retained root remain owned when a
                # relative component open reports absence.
                close_path = '/a/etc/apt' if function == '_image_source_names' and close_at == 1 else '/a'
                fs.fault('close', close_path, cleanup, 1 if close_path != '/a' else close_at)
                value, error = capture(call)
                TRACE_ROWS.append(dict(kind='optional-missing-cleanup', function=function,
                                       close_at=close_at, close_type=cleanup_type.__name__,
                                       surfaced=type(error).__name__ if error else None,
                                       events=fs.events, live=list(fs.live)))
                try:
                    assert error is cleanup or (isinstance(error, RuntimeError) and error.__cause__ is cleanup)
                    assert value is None
                    assert_ownership(fs)
                except AssertionError:
                    failures.append((function, close_at, cleanup_type.__name__))
    assert not failures, failures


def test_optional_inventory_clean_absence_and_required_missing_contracts():
    for function in ('_image_text', '_image_source_names'):
        fs, _env, call = optional_inventory_case(function, absent=True)
        value, error = capture(call)
        assert error is None and value == (None if function == '_image_text' else [])
        assert_ownership(fs)
    for cleanup_type in (None, OSError, KeyboardInterrupt):
        fs, _env, call = optional_inventory_case('_image_text', absent=True, required=True)
        primary = FileNotFoundError('required missing parent')
        fs.fault('open', '/a/missing', primary)
        if cleanup_type:
            fs.fault('close', '/a', cleanup_type('secondary required cleanup'), 1)
            fs.fault('close', '/a', cleanup_type('secondary retained root cleanup'), 2)
        _value, error = capture(call)
        assert isinstance(error, RuntimeError) and error.__cause__ is primary
        assert_ownership(fs)


def test_source_names_preserves_list_failure_and_standalone_cleanup():
    failures = []
    target = '/a/etc/apt/sources.list.d'
    for primary_type in (OSError, KeyboardInterrupt, SystemExit, ValueError):
        for cleanup_type in (OSError, KeyboardInterrupt, SystemExit):
            fs, _env, call = optional_inventory_case('_image_source_names', absent=False)
            primary, cleanup = primary_type('list failure'), cleanup_type('list parent cleanup')
            fs.fault('listdir', target, primary)
            fs.fault('close', target, cleanup, after=('listdir', target))
            _value, error = capture(call)
            try:
                assert error is primary or (isinstance(error, RuntimeError) and error.__cause__ is primary)
                assert_ownership(fs)
            except AssertionError:
                failures.append((primary_type.__name__, cleanup_type.__name__))
    assert not failures, failures
    for primary in (None, FileNotFoundError('optional list absence')):
        for cleanup_type in (None, OSError, FileNotFoundError, KeyboardInterrupt):
            fs, _env, call = optional_inventory_case('_image_source_names', absent=False)
            if primary:
                fs.fault('listdir', target, primary)
            cleanup = cleanup_type('standalone names close') if cleanup_type else None
            if cleanup:
                fs.fault('close', target, cleanup)
            value, error = capture(call)
            assert error is cleanup
            if error is None:
                assert value == ([] if primary else ['item.list'])
            assert_ownership(fs)


def image_leaf_case(required=False):
    fs = ReaderOS()
    env = load_reader_ast('ci_evidence', fs)

    def call():
        return env['_image_text'](fs.Path('/a'), fs.Path('b/item'), required=required, limit=16)

    return fs, env, call


def test_named_leaf_absence_after_double_read_requires_successful_cleanup():
    failures = []
    for required in (False, True):
        for cleanup_type in (None, OSError, FileNotFoundError, KeyboardInterrupt, SystemExit):
            fs, _env, call = image_leaf_case(required)
            primary = FileNotFoundError(2, 'named leaf disappeared after both reads')
            fs.fault('stat', '/a/b/item', primary)
            cleanup = cleanup_type(5, 'leaf close after named absence') if cleanup_type else None
            if cleanup is not None:
                fs.fault('close', '/a/b/item', cleanup, after=('stat', '/a/b/item'))
            value, error = capture(call)
            TRACE_ROWS.append(dict(kind='named-leaf-absence', required=required,
                                   cleanup=cleanup_type.__name__ if cleanup_type else None,
                                   surfaced=type(error).__name__ if error else None,
                                   value=value, events=fs.events))
            assert fs.counts['read', '/a/b/item'] == 4
            assert fs.counts['fstat', '/a/b/item'] == 3
            assert fs.counts['open', '/a/b/item'] == 1
            assert fs.counts['stat', '/a/b/item'] == 1
            assert_ownership(fs)
            try:
                if required:
                    assert isinstance(error, RuntimeError) and error.__cause__ is primary
                elif isinstance(cleanup, (KeyboardInterrupt, SystemExit)):
                    assert error is cleanup
                elif cleanup is not None:
                    assert error is cleanup or (isinstance(error, RuntimeError) and error.__cause__ is cleanup)
                else:
                    assert error is None and value is None
            except AssertionError:
                failures.append((required, cleanup_type.__name__ if cleanup_type else None))
    assert not failures, failures


def test_existing_image_cleanup_errors_cannot_be_normalized_as_absence():
    failures = []
    for function in ('optional-text', 'required-text', 'source-names'):
        targets = (('/a', 1), ('/a', 3), ('/a/b/item', 1)) if function != 'source-names' else (
            ('/a', 1), ('/a', 3), ('/a/etc/apt/sources.list.d', 1))
        for target, occurrence in targets:
            for cleanup_type in (OSError, FileNotFoundError, KeyboardInterrupt, SystemExit):
                if function == 'source-names':
                    fs, _env, call = optional_inventory_case('_image_source_names', absent=False)
                else:
                    fs, _env, call = image_leaf_case(required=function == 'required-text')
                cleanup = cleanup_type(5, 'existing image owned close failure')
                fs.fault('close', target, cleanup, occurrence)
                value, error = capture(call)
                TRACE_ROWS.append(dict(kind='existing-image-cleanup', function=function,
                                       target=target, occurrence=occurrence, cleanup=cleanup_type.__name__,
                                       surfaced=type(error).__name__ if error else None, events=fs.events))
                assert fs.counts['close', target] >= occurrence
                assert_ownership(fs)
                try:
                    assert value is None
                    if isinstance(cleanup, (KeyboardInterrupt, SystemExit)):
                        assert error is cleanup
                    else:
                        assert error is cleanup or (isinstance(error, RuntimeError) and error.__cause__ is cleanup)
                except AssertionError:
                    failures.append((function, target, occurrence, cleanup_type.__name__))
    assert not failures, failures


def test_optional_leaf_absence_before_open_and_after_read_keeps_parent_cleanup_visible():
    for operation in ('open', 'stat'):
        for required in (False, True):
            for cleanup_type in (None, OSError, FileNotFoundError, KeyboardInterrupt, SystemExit):
                fs, _env, call = image_leaf_case(required)
                primary = FileNotFoundError(2, 'operation-level leaf absence')
                fs.fault(operation, '/a/b/item', primary)
                cleanup = cleanup_type(5, 'owned parent close after leaf absence') if cleanup_type else None
                if cleanup is not None:
                    fs.fault('close', '/a/b', cleanup, after=(operation, '/a/b/item'))
                value, error = capture(call)
                if required:
                    assert isinstance(error, RuntimeError) and error.__cause__ is primary
                elif cleanup is not None:
                    assert error is cleanup
                else:
                    assert error is None and value is None
                if operation == 'open':
                    assert not any(e['op'] == 'acquire' and e['path'] == '/a/b/item' for e in fs.events)
                    assert fs.counts['read', '/a/b/item'] == 0
                else:
                    assert fs.counts['read', '/a/b/item'] == 4
                assert_ownership(fs)


def test_strict_leaf_and_directory_absence_preserve_primary_with_secondary_cleanup():
    for function in ('_read_regular_at', '_image_directory_fd'):
        for cleanup_type in (OSError, FileNotFoundError, KeyboardInterrupt, SystemExit):
            fs = ReaderOS()
            env = load_reader_ast('ci_evidence', fs)
            primary = FileNotFoundError(2, 'strict operation-level absence')
            cleanup = cleanup_type(5, 'strict secondary cleanup')
            if function == '_read_regular_at':
                parent_fd = fs.seed('/a/b')
                fs.fault('stat', '/a/b/item', primary)
                fs.fault('close', '/a/b/item', cleanup)

                def call():
                    return env[function](parent_fd, 'item', limit=16, what='strict fixture')
            else:
                fs.fault('open', '/a/missing', primary)
                fs.fault('close', '/a', cleanup, 1)
                fs.fault('close', '/a', cleanup, 2)

                def call():
                    return env[function](fs.Path('/a'), fs.Path('missing'))
            _value, error = capture(call)
            assert error is primary
            assert_ownership(fs)


def test_image_fatal_operation_preserves_primary_over_each_cleanup_type():
    for required in (False, True):
        for operation in ('read', 'stat'):
            for primary_type in (OSError, KeyboardInterrupt, SystemExit, ValueError):
                for cleanup_type in (OSError, FileNotFoundError, KeyboardInterrupt, SystemExit):
                    fs, _env, call = image_leaf_case(required)
                    primary = primary_type(5, 'fatal image operation')
                    cleanup = cleanup_type(5, 'secondary leaf and parent cleanup')
                    fs.fault(operation, '/a/b/item', primary)
                    fs.fault('close', '/a/b/item', cleanup, after=(operation, '/a/b/item'))
                    fs.fault('close', '/a/b', cleanup, after=(operation, '/a/b/item'))
                    _value, error = capture(call)
                    if primary_type is OSError:
                        assert isinstance(error, RuntimeError) and error.__cause__ is primary
                    else:
                        assert error is primary
                    assert_ownership(fs)


def test_source_names_operation_absence_and_fatal_primary_provenance():
    target = '/a/etc/apt/sources.list.d'
    for primary_type in (None, FileNotFoundError, OSError, KeyboardInterrupt, SystemExit, ValueError):
        for cleanup_type in (None, OSError, FileNotFoundError, KeyboardInterrupt, SystemExit):
            fs, _env, call = optional_inventory_case('_image_source_names', absent=False)
            fs.put(target + '/z.sources', b'text')
            fs.put(target + '/ignored.txt', b'text')
            primary = primary_type(5 if primary_type is OSError else 2, 'source list operation') if primary_type else None
            cleanup = cleanup_type(5, 'source list final cleanup') if cleanup_type else None
            if primary is not None:
                fs.fault('listdir', target, primary)
            if cleanup is not None:
                fs.fault('close', target, cleanup)
            value, error = capture(call)
            if primary_type in (None, FileNotFoundError):
                assert error is cleanup
                if cleanup is None:
                    assert value == ([] if primary is not None else ['item.list', 'z.sources'])
            else:
                if primary_type is OSError:
                    assert isinstance(error, RuntimeError) and error.__cause__ is primary
                else:
                    assert error is primary
            assert_ownership(fs)
