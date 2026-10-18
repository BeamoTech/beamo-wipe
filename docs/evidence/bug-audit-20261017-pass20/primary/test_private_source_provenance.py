from pathlib import Path
import json

def test_private_source_provenance(request):
    from beamo_wipe.ui import tk_wizard
    from beamo_wipe import build_identity
    expected=Path('/tmp/pass20-primary/private-graph/src').resolve()
    actual={module.__name__:str(Path(module.__file__).resolve()) for module in (tk_wizard,build_identity)}
    request.node.user_properties.append(('source_provenance',json.dumps(actual)))
    assert all(Path(path).is_relative_to(expected) for path in actual.values()), actual
