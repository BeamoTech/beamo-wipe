#!/bin/bash
set -euo pipefail
export DEBIAN_FRONTEND=noninteractive
apt-get -o Acquire::https::CaInfo=/run/beamo-ca-bundle.crt update -qq
apt-get -o Acquire::https::CaInfo=/run/beamo-ca-bundle.crt install -y -qq --no-install-recommends python3 python3-tk python3-gi gir1.2-gtk-3.0 python3-pip python3-setuptools python3-qrcode python3-pil xvfb xauth x11-utils libxtst6 dbus-x11 fonts-dejavu-core ca-certificates > /evidence/apt-install.log 2>&1
PIP_CERT=/run/beamo-ca-bundle.crt python3 -m pip install --break-system-packages -q pytest==9.0.3 cryptography==50.0.1 qrcode==8.2 > /evidence/pip-install.log 2>&1
python3 --version
python3 -c 'import tkinter as t; from gi.repository import GLib; print("Tcl", t.TclVersion, "Tk", t.TkVersion); print("GLib", GLib.MAJOR_VERSION,GLib.MINOR_VERSION,GLib.MICRO_VERSION)'
dpkg-query -W python3-tk libtk8.6 libtcl8.6 libgtk-3-0 python3-gi > /evidence/installed-versions.txt
touch /evidence/READY
exec sleep infinity
