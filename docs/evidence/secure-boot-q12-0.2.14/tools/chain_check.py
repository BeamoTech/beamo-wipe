"""Offline: shim policy sections and leaf->anchor checks on extracted files."""
import hashlib
import json
import sys
sys.path.insert(0, '.')
import pe_sig
from cryptography import x509
out = {}
shim = pe_sig.inspect_pe(open('extracted/EFI_boot_bootx64.efi', 'rb').read())
lay = shim['layout']
out['shim_sections'] = [s['name'] for s in lay['sections']]
out['shim_sbat'] = shim['sbat']
out['shim_sbatlevel'] = shim['sbatlevel']
vc = shim['vendor_cert']
ca = vc.pop('_cert')
out['shim_vendor_cert'] = vc
out['debian_ca'] = {'subject': ca.subject.rfc4514_string(), 'not_before': ca.not_valid_before_utc.isoformat(), 'not_after': ca.not_valid_after_utc.isoformat()}
anchors = {'Debian Secure Boot CA (shim .vendor_cert)': ca}
for f, label in [('ms-uefi-ca-2011.crt', 'Microsoft Corporation UEFI CA 2011'), ('ms-uefi-ca-2023.crt', 'Microsoft UEFI CA 2023')]:
    b = open(f, 'rb').read()
    anchors[label] = x509.load_der_x509_certificate(b)
    out.setdefault('anchor_der_sha256', {})[label] = hashlib.sha256(b).hexdigest()
out['leaf_issuance'] = {}
for name in ['EFI_boot_bootx64.efi', 'EFI_boot_grubx64.efi', 'live_vmlinuz-6.12.115+deb12-amd64']:
    info = pe_sig.inspect_pe(open('extracted/' + name, 'rb').read())
    rows = []
    for s in info['signatures']:
        leaf = s['_signer_cert']
        hits = []
        for label, a in anchors.items():
            try:
                leaf.verify_directly_issued_by(a)
                hits.append(label)
            except Exception:
                pass
        rows.append({'leaf': leaf.subject.rfc4514_string(), 'leaf_directly_issued_by': hits})
    out['leaf_issuance'][name] = rows
json.dump(out, open('q12-chain-0.2.14.json', 'w'), indent=2)
print(json.dumps(out, indent=1))
