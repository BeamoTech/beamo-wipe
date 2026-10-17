import sys,pytest
sys.path.insert(0,'/tmp/beamo-pass8-projection-original-z703gq6z')
import beamo_wipe.nwipe_runner as runner
print("ORIGINAL_RUNNER",runner.__file__,flush=True)
raise SystemExit(pytest.main(["-q","tests/test_runner_projection_progress_order_pass8.py","--junitxml=/tmp/beamo-pass8-discovery-projection-original.xml"]))
