import os,subprocess,tempfile
files=['test_startup_diagnostics.py','test_session_recovery.py','test_privacy_sharing_copy.py','test_sharing_semantic_collision_regression.py','test_verification_evidence.py','test_gate_receipt_skip_kind_counts_pass7.py','test_export_hardware_padding_regression.py','test_report_destination_unicode_pass29.py']
with tempfile.TemporaryDirectory(prefix='beamo-pass8-primary-runtime-') as runtime:
    env={**os.environ,'PATH':'/tmp/beamo-audit-go.oeGvle/go/bin:/tmp/beamo-wipe-audit-python/bin:'+os.environ['PATH'],'PYTHONPATH':'src','XDG_RUNTIME_DIR':runtime,'BEAMO_WIPE_DRY_RUN':'1'}
    with open('/tmp/beamo-pass8-primary-baseline.txt','w') as log:
        result=subprocess.run(['dbus-run-session','--','xvfb-run','-a','-s','-screen 0 1600x1000x24 -dpi 72','python3','-m','pytest',*['tests/'+p for p in files],'--junitxml=/tmp/beamo-pass8-primary-baseline.xml'],env=env,stdout=log,stderr=subprocess.STDOUT)
    raise SystemExit(result.returncode)
