# SPDX-License-Identifier: GPL-3.0-or-later
"""NVMe namespace failover, using only owned sysfs directories/files/links.

The collision and replacement cases are synthetic integrity controls, not
claims that Linux can reuse a live subsystem's reserved controller number.
"""

from pathlib import Path

import pytest

from beamo_wipe import safety


class _Sysfs:
    def __init__(self, tmp_path, monkeypatch):
        self.root = tmp_path / "sys"
        self.subsystem = self.path("devices/virtual/nvme-subsystem/nvme-subsys0")
        self.subsystem.mkdir(parents=True)
        self.link("class/nvme-subsystem/nvme-subsys0", self.subsystem)
        self.namespace = self.subsystem / "nvme0n1"
        self.namespace.mkdir()
        self.link("block/nvme0n1", self.namespace)
        (self.namespace / "device").symlink_to(self.subsystem, target_is_directory=True)
        # The target's /dev name is lexical test input, never host inventory.
        realpath = safety.os.path.realpath

        def owned_realpath(path, *args, **kwargs):
            if str(path) in {"/dev/nvme0n1", "/dev/nvme0n2"}:
                return str(path)
            return realpath(path, *args, **kwargs)

        monkeypatch.setattr(safety.os.path, "realpath", owned_realpath)
        monkeypatch.setattr(safety, "Path", self.kernel_path)
        monkeypatch.setattr(safety, "is_preview_env", lambda: False)

    def path(self, relative):
        return self.root / relative

    def kernel_path(self, raw):
        assert str(raw).startswith("/sys/")
        return self.root / str(raw)[len("/sys/"):]

    def link(self, relative, target):
        path = self.path(relative)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.symlink_to(target, target_is_directory=True)
        return path

    def controller(self, number, transport):
        name = f"nvme{number}"
        controller = self.path(f"devices/pci0000:00/0000:00:{number:02d}.0/nvme/{name}")
        controller.mkdir(parents=True)
        (controller / "transport").write_text(transport, encoding="ascii")
        self.link(f"class/nvme/{name}", controller)
        (self.subsystem / name).symlink_to(controller, target_is_directory=True)
        return controller

    def use_direct_namespace(self, controller, name="nvme0n1"):
        self.path(f"block/{self.namespace.name}").unlink()
        (self.namespace / "device").unlink()
        self.namespace.rmdir()
        self.namespace = controller / name
        self.namespace.mkdir()
        (self.namespace / "device").symlink_to(controller, target_is_directory=True)
        self.link(f"block/{name}", self.namespace)

    def remove_controller(self, number):
        name = f"nvme{number}"
        class_link = self.path(f"class/nvme/{name}")
        controller = class_link.resolve(strict=True)
        # Model disappearance of the controller, not just a missing attribute.
        class_link.unlink()
        (self.subsystem / name).unlink()
        (controller / "transport").unlink()
        controller.rmdir()
        assert not class_link.is_symlink()
        assert not (self.subsystem / name).is_symlink()
        assert not controller.exists()


@pytest.fixture
def sysfs(tmp_path, monkeypatch):
    return _Sysfs(tmp_path, monkeypatch)


@pytest.fixture
def surviving(sysfs):
    sysfs.controller(0, "pcie\n")
    sysfs.controller(1, "pcie\n")
    sysfs.remove_controller(0)
    return sysfs


def _check(name="nvme0n1"):
    safety.assert_local_device_transport(f"/dev/{name}")


def _refuses(name="nvme0n1"):
    with pytest.raises(safety.SafetyError, match="NVMe"):
        _check(name)


def test_surviving_local_controller_accepts_namespace_head(surviving):
    device = surviving.kernel_path("/sys/block/nvme0n1/device")
    assert device.resolve(strict=True) == surviving.subsystem
    assert not surviving.path("class/nvme/nvme0").exists()
    members = sorted(p.name for p in surviving.subsystem.iterdir() if p.is_symlink())
    assert members == ["nvme1"]
    _check()


def test_multiple_surviving_pcie_controllers_are_accepted(surviving):
    surviving.controller(2, "pcie\n")
    _check()


@pytest.mark.parametrize(
    "transport",
    ["pcie\n", " PCIE \n", "tcp\n", "rdma\n", "fc\n", "loop\n", "", "unknown\n"],
)
def test_direct_transport_keeps_existing_decision(sysfs, monkeypatch, transport):
    controller = sysfs.controller(0, transport)
    sysfs.use_direct_namespace(controller)

    def unexpected_fallback(*args):
        pytest.fail("A readable direct transport must not use the fallback")

    # No namespace-parent or subsystem scan is needed for the direct path.
    monkeypatch.setattr(
        safety, "_assert_local_nvme_subsystem", unexpected_fallback, raising=False
    )
    if transport.strip().casefold() == "pcie":
        _check()
    else:
        with pytest.raises(safety.SafetyError, match="remote or unknown"):
            _check()


@pytest.mark.parametrize("transport", ["tcp\n", "rdma\n", "fc\n", "loop\n", "", "unknown\n"])
def test_surviving_remote_or_unknown_controller_is_refused(surviving, transport):
    controller = surviving.path("class/nvme/nvme1").resolve(strict=True)
    (controller / "transport").write_text(transport, encoding="ascii")
    _refuses()


@pytest.mark.parametrize("transport", ["tcp\n", "rdma\n", "", "unknown\n"])
def test_one_local_member_cannot_hide_another_transport(surviving, transport):
    surviving.controller(2, transport)
    _refuses()


def test_no_remaining_controller_membership_is_refused(surviving):
    surviving.remove_controller(1)
    _refuses()


def test_missing_original_transport_is_not_controller_removal(sysfs):
    original = sysfs.controller(0, "pcie\n")
    sysfs.controller(1, "pcie\n")
    (original / "transport").unlink()
    assert sysfs.path("class/nvme/nvme0").is_symlink()
    assert (sysfs.subsystem / "nvme0").is_symlink()
    _refuses()


def test_unreadable_original_member_cannot_be_skipped(sysfs, monkeypatch):
    sysfs.controller(0, "pcie\n")
    sysfs.controller(1, "pcie\n")
    original = Path.read_text

    def read(path, *args, **kwargs):
        if path.name == "transport" and "nvme0" in path.parts:
            raise PermissionError("original member remains unreadable")
        return original(path, *args, **kwargs)

    monkeypatch.setattr(Path, "read_text", read)
    _refuses()


def test_dangling_original_subsystem_member_is_refused(surviving):
    (surviving.subsystem / "nvme0").symlink_to(
        surviving.path("devices/removed/nvme0"), target_is_directory=True
    )
    _refuses()


@pytest.mark.parametrize(
    "missing", ["device", "subsystem-class", "controller-class", "transport"]
)
def test_incomplete_surviving_sysfs_is_refused(surviving, missing):
    paths = {
        "device": surviving.namespace / "device",
        "subsystem-class": surviving.path("class/nvme-subsystem/nvme-subsys0"),
        "controller-class": surviving.path("class/nvme/nvme1"),
        "transport": surviving.path("class/nvme/nvme1/transport"),
    }
    paths[missing].unlink()
    _refuses()


def test_dangling_namespace_parent_is_refused(surviving):
    device = surviving.namespace / "device"
    device.unlink()
    device.symlink_to(
        surviving.path("devices/removed/nvme-subsys0"), target_is_directory=True
    )
    _refuses()


@pytest.mark.parametrize("name", ["nvme-subsys9", "nvme-subsys0"])
def test_matching_number_alone_cannot_establish_subsystem_membership(surviving, name):
    other = surviving.path(f"devices/unrelated/{name}")
    other.mkdir(parents=True)
    (other / "nvme1").symlink_to(
        surviving.path("class/nvme/nvme1").resolve(strict=True), target_is_directory=True
    )
    device = surviving.namespace / "device"
    device.unlink()
    device.symlink_to(other, target_is_directory=True)
    _refuses()


def test_subsystem_member_must_be_the_matching_class_controller(surviving):
    other = surviving.controller(2, "pcie\n")
    member = surviving.subsystem / "nvme1"
    member.unlink()
    member.symlink_to(other, target_is_directory=True)
    _refuses()


def test_same_named_unrelated_class_controller_is_refused(surviving):
    other = surviving.path("devices/unrelated/nvme1")
    other.mkdir(parents=True)
    (other / "transport").write_text("pcie\n", encoding="ascii")
    class_link = surviving.path("class/nvme/nvme1")
    class_link.unlink()
    class_link.symlink_to(other, target_is_directory=True)
    _refuses()


def test_controller_directory_cannot_replace_membership_link(surviving):
    member = surviving.subsystem / "nvme1"
    member.unlink()
    member.mkdir()
    (member / "transport").write_text("pcie\n", encoding="ascii")
    _refuses()


@pytest.mark.parametrize(
    "failure",
    [
        PermissionError("denied"),
        OSError("read failed"),
        UnicodeDecodeError("ascii", b"\xff", 0, 1, "non-ASCII"),
    ],
)
def test_unreadable_surviving_transport_is_refused(surviving, monkeypatch, failure):
    original = Path.read_text

    def read(path, *args, **kwargs):
        if path.name == "transport" and "nvme1" in path.parts:
            raise failure
        return original(path, *args, **kwargs)

    monkeypatch.setattr(Path, "read_text", read)
    _refuses()


def test_unreadable_membership_is_refused(surviving, monkeypatch):
    original = Path.iterdir

    def entries(path):
        if path == surviving.subsystem:
            raise PermissionError("cannot enumerate members")
        return original(path)

    monkeypatch.setattr(Path, "iterdir", entries)
    _refuses()


@pytest.mark.parametrize(
    "change", ["namespace", "controller", "add-local-member", "transport"]
)
def test_observed_replacement_during_transport_read_is_refused(
    surviving, monkeypatch, change
):
    original = Path.read_text
    changed = False

    def read(path, *args, **kwargs):
        nonlocal changed
        value = original(path, *args, **kwargs)
        if path.name != "transport" or "nvme1" not in path.parts or changed:
            return value
        changed = True
        if change == "namespace":
            other = surviving.path("devices/replacement/nvme-subsys0")
            other.mkdir(parents=True)
            device = surviving.namespace / "device"
            device.unlink()
            device.symlink_to(other, target_is_directory=True)
        elif change == "controller":
            other = surviving.path("devices/replacement/nvme1")
            other.mkdir(parents=True)
            (other / "transport").write_text("pcie\n", encoding="ascii")
            for link in (
                surviving.subsystem / "nvme1",
                surviving.path("class/nvme/nvme1"),
            ):
                link.unlink()
                link.symlink_to(other, target_is_directory=True)
        elif change == "add-local-member":
            surviving.controller(2, "pcie\n")
        else:
            path.write_text("tcp\n", encoding="ascii")
        return value

    monkeypatch.setattr(Path, "read_text", read)
    _refuses()
    assert changed


@pytest.fixture
def private_namespace(surviving):
    # Without a unique NSID guarantee, Linux keeps the namespace below its
    # controller even with multipath enabled. The name uses the subsystem ID.
    controller = surviving.path("class/nvme/nvme1").resolve(strict=True)
    surviving.use_direct_namespace(controller, "nvme0n2")
    return surviving


@pytest.mark.parametrize("extra_local", [False, True])
def test_surviving_private_pcie_namespace_is_accepted(private_namespace, extra_local):
    if extra_local:
        private_namespace.controller(2, "pcie\n")
    device = private_namespace.kernel_path("/sys/block/nvme0n2/device")
    controller = private_namespace.path("class/nvme/nvme1").resolve(strict=True)
    assert device.resolve(strict=True) == controller
    assert device.resolve(strict=True) != private_namespace.subsystem
    assert (private_namespace.subsystem / "nvme1").resolve(strict=True) == controller
    assert not private_namespace.path("class/nvme/nvme0").exists()
    _check("nvme0n2")


@pytest.mark.parametrize("transport", ["tcp\n", "rdma\n", "fc\n", "loop\n", "", "unknown\n"])
def test_private_remote_or_unknown_parent_is_refused(private_namespace, transport):
    (private_namespace.namespace.parent / "transport").write_text(
        transport, encoding="ascii"
    )
    _refuses("nvme0n2")


@pytest.mark.parametrize("transport", ["tcp\n", "rdma\n", "fc\n", "loop\n", "", "unknown\n"])
def test_private_local_parent_cannot_hide_other_transport(private_namespace, transport):
    private_namespace.controller(2, transport)
    _refuses("nvme0n2")


@pytest.mark.parametrize(
    "missing", ["device", "subsystem-class", "controller-class", "member", "transport"]
)
def test_incomplete_private_namespace_sysfs_is_refused(private_namespace, missing):
    if missing == "member":
        private_namespace.controller(2, "pcie\n")
    paths = {
        "device": private_namespace.namespace / "device",
        "subsystem-class": private_namespace.path("class/nvme-subsystem/nvme-subsys0"),
        "controller-class": private_namespace.path("class/nvme/nvme1"),
        "member": private_namespace.subsystem / "nvme1",
        "transport": private_namespace.namespace.parent / "transport",
    }
    paths[missing].unlink()
    _refuses("nvme0n2")


def test_private_namespace_cannot_skip_unreadable_original_member(private_namespace):
    original = private_namespace.controller(0, "pcie\n")
    (original / "transport").unlink()
    _refuses("nvme0n2")


def test_private_parent_class_without_expected_membership_is_refused(private_namespace):
    other = private_namespace.controller(2, "pcie\n")
    (private_namespace.subsystem / "nvme2").unlink()
    other_subsystem = private_namespace.path("devices/virtual/nvme-subsystem/nvme-subsys9")
    other_subsystem.mkdir()
    (other_subsystem / "nvme2").symlink_to(other, target_is_directory=True)
    device = private_namespace.namespace / "device"
    device.unlink()
    device.symlink_to(other, target_is_directory=True)
    assert private_namespace.path("class/nvme/nvme2").resolve(strict=True) == other
    _refuses("nvme0n2")


@pytest.mark.parametrize("mismatch", ["parent", "class", "member-and-class"])
def test_private_matching_number_cannot_prove_membership(private_namespace, mismatch):
    other = private_namespace.path("devices/unrelated/nvme1")
    other.mkdir(parents=True)
    (other / "transport").write_text("pcie\n", encoding="ascii")
    if mismatch == "parent":
        links = [private_namespace.namespace / "device"]
    elif mismatch == "class":
        links = [private_namespace.path("class/nvme/nvme1")]
    else:
        links = [
            private_namespace.path("class/nvme/nvme1"),
            private_namespace.subsystem / "nvme1",
        ]
    for link in links:
        link.unlink()
        link.symlink_to(other, target_is_directory=True)
    _refuses("nvme0n2")


def test_private_parent_requires_membership_symlink(private_namespace):
    member = private_namespace.subsystem / "nvme1"
    member.unlink()
    member.mkdir()
    (member / "transport").write_text("pcie\n", encoding="ascii")
    _refuses("nvme0n2")


@pytest.mark.parametrize(
    "change",
    [
        "namespace-to-subsystem",
        "namespace-to-other-member",
        "controller",
        "controller-inode",
        "subsystem-inode",
        "subsystem-class",
        "remove-member",
        "add-local-member",
        "transport",
    ],
)
def test_private_observed_replacement_is_refused(private_namespace, monkeypatch, change):
    original = Path.read_text
    changed = False
    if change == "namespace-to-other-member":
        private_namespace.controller(2, "pcie\n")

    def read(path, *args, **kwargs):
        nonlocal changed
        value = original(path, *args, **kwargs)
        if path.name != "transport" or "nvme1" not in path.parts or changed:
            return value
        changed = True
        if change in {"namespace-to-subsystem", "namespace-to-other-member"}:
            parent = private_namespace.subsystem
            if change == "namespace-to-other-member":
                parent = private_namespace.path("class/nvme/nvme2").resolve(strict=True)
            device = private_namespace.namespace / "device"
            device.unlink()
            device.symlink_to(parent, target_is_directory=True)
        elif change == "controller":
            other = private_namespace.path("devices/replacement/nvme1")
            other.mkdir(parents=True)
            (other / "transport").write_text("pcie\n", encoding="ascii")
            for link in (
                private_namespace.subsystem / "nvme1",
                private_namespace.path("class/nvme/nvme1"),
            ):
                link.unlink()
                link.symlink_to(other, target_is_directory=True)
        elif change == "controller-inode":
            controller = private_namespace.namespace.parent
            retired = controller.with_name("retired-nvme1")
            controller.rename(retired)
            controller.mkdir()
            (retired / private_namespace.namespace.name).rename(private_namespace.namespace)
            (controller / "transport").write_text("pcie\n", encoding="ascii")
        elif change == "subsystem-inode":
            subsystem = private_namespace.subsystem
            retired = subsystem.with_name("retired-nvme-subsys0")
            subsystem.rename(retired)
            subsystem.mkdir()
            for link in retired.iterdir():
                (subsystem / link.name).symlink_to(
                    link.resolve(strict=True), target_is_directory=True
                )
        elif change == "subsystem-class":
            other = private_namespace.path("devices/replacement/nvme-subsys0")
            other.mkdir(parents=True)
            (other / "nvme1").symlink_to(
                private_namespace.namespace.parent, target_is_directory=True
            )
            link = private_namespace.path("class/nvme-subsystem/nvme-subsys0")
            link.unlink()
            link.symlink_to(other, target_is_directory=True)
        elif change == "remove-member":
            (private_namespace.subsystem / "nvme1").unlink()
        elif change == "add-local-member":
            private_namespace.controller(2, "pcie\n")
        else:
            path.write_text("tcp\n", encoding="ascii")
        return value

    monkeypatch.setattr(Path, "read_text", read)
    _refuses("nvme0n2")
    assert changed
