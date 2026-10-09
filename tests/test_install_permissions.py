"""Actual NTFS ACL regressions; assertions use .NET independently of installer."""
import json
import os
import re
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from test_install_release import installer
from test_install_recovery import CRASH_UPGRADE


PS = r"""
$ErrorActionPreference='Stop'
$p=$args[0]; $operation=$args[1]
$isDirectory=(Get-Item -LiteralPath $p).PSIsContainer
if($operation -ne 'get') {
  $sid=[Security.Principal.WindowsIdentity]::GetCurrent().User.Value
  $flags=if($isDirectory){'OICI'}else{''}
  $d='D:P(A;'+$flags+';FA;;;'+$sid+')'
  if($operation -eq 'broad'){$d+='(A;'+$flags+';GRGX;;;WD)'}
  if($operation -eq 'changed'){$d+='(A;'+$flags+';FA;;;SY)'}
  $a=if($isDirectory){[Security.AccessControl.DirectorySecurity]::new()}else{[Security.AccessControl.FileSecurity]::new()}
  $a.SetSecurityDescriptorSddlForm($d,[Security.AccessControl.AccessControlSections]::Access)
  if($isDirectory){[IO.Directory]::SetAccessControl($p,$a)}else{[IO.File]::SetAccessControl($p,$a)}
}
$a=Get-Acl -LiteralPath $p
$a.GetSecurityDescriptorSddlForm([Security.AccessControl.AccessControlSections]::Access -bor [Security.AccessControl.AccessControlSections]::Owner -bor [Security.AccessControl.AccessControlSections]::Group)
"""


@unittest.skipUnless(os.name == "nt", "requires Windows file ACLs")
class WindowsPermissionTests(unittest.TestCase):
    def security(self, path, operation="get"):
        ps = Path(os.environ["SystemRoot"]) / "System32/WindowsPowerShell/v1.0/powershell.exe"
        env = dict(os.environ)
        env["PSMODULEPATH"] = str(Path(os.environ["SystemRoot"]) / "System32/WindowsPowerShell/v1.0/Modules")
        with tempfile.TemporaryDirectory() as folder:
            script = Path(folder) / "acl.ps1"
            script.write_text(PS, encoding="utf-8")
            output = subprocess.check_output([str(ps), "-NoProfile", "-File", str(script), str(path), operation], env=env, timeout=20)
        # AI/AR are inheritance bookkeeping; compare owner/group, protection
        # and the full ACEs including inherited flags without using capture().
        return re.sub(r"D:[^()]*", lambda m: m[0].replace("AI", "").replace("AR", ""), output.decode().strip())

    def setup_private(self, home, mode):
        self.security(home, "broad")
        installer.install(mode, home)
        paths = installer.locations(home, mode)
        folder = paths["target"] / "private-directory"
        folder.mkdir()
        self.security(folder, "private")
        (folder / "empty").mkdir()
        user = folder / "private.txt"
        user.write_bytes(b"synthetic private preferences")
        self.security(user, "private")
        for key in ("catalog", "runtime"):
            if paths[key] is not None:
                self.security(paths[key], "private")
        tracked = [folder, folder / "empty", user, paths["runtime"]]
        if paths["catalog"] is not None:
            tracked.append(paths["catalog"])
        return paths, {p: self.security(p) for p in tracked}

    def upgrade(self, home, mode, fail=False):
        program = installer.source_files(mode)
        program["SKILL.md" if mode == "skill" else "skills/auto-prompt/SKILL.md"] += b"\nACL regression revision\n"
        runtime = json.loads(installer.runtime_data(sys.executable)); runtime["revision"] = "acl-test"
        paths = installer.locations(home, mode)
        catalog = installer.catalog_update(paths["catalog"], home, paths["target"]) if mode == "plugin" else None
        if catalog:
            catalog["revision"] = "acl-test"
        with patch.object(installer, "source_files", return_value=program), \
                patch.object(installer, "runtime_data", return_value=installer.encoded(runtime)), \
                patch.object(installer, "catalog_update", return_value=catalog), \
                patch.object(installer, "check_windows_launcher", side_effect=OSError("synthetic launcher failure") if fail else None):
            return installer.install(mode, home, check_launcher=fail)

    def assert_private_backup(self, transaction):
        for path in [transaction, *transaction.joinpath("before").rglob("*")]:
            self.assertNotIn(";;;WD)", self.security(path), path.name)

    def test_upgrade_backup_and_explicit_rollback_keep_permissions_and_content(self):
        for mode in ("plugin", "skill"):
            with self.subTest(mode=mode), tempfile.TemporaryDirectory() as folder:
                home = Path(folder); paths, snapshots = self.setup_private(home, mode)
                before = installer.current_state(paths)
                receipt = self.upgrade(home, mode)
                transaction = home / ".codex/auto-prompt/transactions" / receipt["transaction"]
                self.assert_private_backup(transaction)
                for path, security in snapshots.items():
                    self.assertEqual(self.security(path), security, path.name)
                self.assertEqual((paths["target"] / "private-directory/private.txt").read_bytes(), b"synthetic private preferences")
                installer.rollback(home, receipt["transaction"])
                self.assertEqual(installer.current_state(paths), before)
                for path, security in snapshots.items():
                    self.assertEqual(self.security(path), security, path.name)
                self.assertFalse(installer.rollback(home, receipt["transaction"])["changed"])

    def test_failed_upgrade_restores_original_permissions(self):
        for mode in ("plugin", "skill"):
            with self.subTest(mode=mode), tempfile.TemporaryDirectory() as folder:
                home = Path(folder); paths, snapshots = self.setup_private(home, mode)
                before = installer.current_state(paths)
                with self.assertRaisesRegex(OSError, "synthetic launcher failure"):
                    self.upgrade(home, mode, fail=True)
                self.assertEqual(installer.current_state(paths), before)
                for path, security in snapshots.items():
                    self.assertEqual(self.security(path), security, path.name)

    def test_atomic_config_permissions_are_correct_before_replace(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder); self.security(root, "broad")
            path = root / "config.json"; path.write_bytes(b"old")
            original = self.security(path, "private")
            replace = installer.os.replace
            def checked_replace(source, destination):
                self.assertEqual(self.security(source), original)
                self.assertEqual(Path(source).read_bytes(), b"new synthetic config")
                return replace(source, destination)
            with patch.object(installer.os, "replace", side_effect=checked_replace):
                installer.write_atomic(path, b"new synthetic config")
            self.assertEqual(self.security(path), original)

    def test_permission_only_later_edit_stops_rollback(self):
        for key in ("target", "catalog", "runtime"):
            with self.subTest(key=key), tempfile.TemporaryDirectory() as folder:
                home = Path(folder); paths, _ = self.setup_private(home, "plugin")
                receipt = self.upgrade(home, "plugin")
                path = paths[key] / "private-directory/private.txt" if key == "target" else paths[key]
                changed = self.security(path, "changed")
                content = installer.current_state(paths)
                with self.assertRaisesRegex(ValueError, "changed since installation"):
                    installer.rollback(home, receipt["transaction"])
                self.assertEqual(self.security(path), changed)
                self.assertEqual(installer.current_state(paths), content)

    def test_permission_only_backup_edit_stops_rollback(self):
        with tempfile.TemporaryDirectory() as folder:
            home = Path(folder); paths, _ = self.setup_private(home, "skill")
            receipt = self.upgrade(home, "skill")
            backup = Path(receipt["backup"]) / "private-directory/private.txt"
            self.security(backup, "broad")
            before = installer.current_state(paths)
            with self.assertRaisesRegex(ValueError, "backup"):
                installer.rollback(home, receipt["transaction"])
            self.assertEqual(installer.current_state(paths), before)

    def test_permission_restore_failure_leaves_active_install_unchanged(self):
        with tempfile.TemporaryDirectory() as folder:
            home = Path(folder); paths, snapshots = self.setup_private(home, "plugin")
            before = installer.current_state(paths)
            with patch.object(installer.permissions, "apply", side_effect=OSError("synthetic ACL access denied")):
                with self.assertRaisesRegex(OSError, "ACL access denied"):
                    self.upgrade(home, "plugin")
            self.assertEqual(installer.current_state(paths), before)
            for path, security in snapshots.items():
                self.assertEqual(self.security(path), security)

    def test_legacy_transaction_with_existing_files_refuses_unknown_acl_restore(self):
        with tempfile.TemporaryDirectory() as folder:
            home = Path(folder); paths, _ = self.setup_private(home, "skill")
            receipt = self.upgrade(home, "skill")
            path = home / ".codex/auto-prompt/transactions" / receipt["transaction"] / "transaction.json"
            journal = installer.load_json(path); journal["schema"] = 1; del journal["permissions"]
            path.write_bytes(installer.encoded(journal))
            before = installer.current_state(paths)
            with self.assertRaisesRegex(ValueError, "no original ACL evidence"):
                installer.rollback(home, receipt["transaction"])
            self.assertEqual(installer.current_state(paths), before)

    def test_private_transaction_is_created_before_copying(self):
        with tempfile.TemporaryDirectory() as folder:
            home = Path(folder); self.setup_private(home, "plugin")
            copy = installer.shutil.copytree
            def inspect(source, destination, *args, **kwargs):
                if Path(destination).name == "target":
                    self.assertNotIn(";;;WD)", self.security(Path(destination).parent.parent))
                return copy(source, destination, *args, **kwargs)
            with patch.object(installer.shutil, "copytree", side_effect=inspect):
                self.upgrade(home, "plugin")

    def test_actual_process_exit_restores_private_acl(self):
        with tempfile.TemporaryDirectory() as folder:
            home = Path(folder); paths, snapshots = self.setup_private(home, "plugin")
            before = installer.current_state(paths)
            process = subprocess.run([sys.executable, "-B", "-c", CRASH_UPGRADE, installer.__file__, str(home)], capture_output=True, timeout=30)
            self.assertEqual(process.returncode, 91, process.stderr.decode(errors="replace"))
            (home / ".codex/auto-prompt/install.lock").unlink()  # Confirmed child exit.
            tx = next(p.parent for p in (home / ".codex/auto-prompt/transactions").glob("*/transaction.json")
                      if installer.load_json(p)["status"] == "applying")
            installer.rollback(home, tx.name)
            self.assertEqual(installer.current_state(paths), before)
            for path, security in snapshots.items():
                self.assertEqual(self.security(path), security)

    def test_permission_change_during_directory_switch_is_preserved(self):
        with tempfile.TemporaryDirectory() as folder:
            home = Path(folder); paths, _ = self.setup_private(home, "skill")
            rename = Path.rename
            changed = []
            def concurrent(path, destination):
                result = rename(path, destination)
                if path == paths["target"]:
                    changed.append(self.security(Path(destination) / "private-directory/private.txt", "changed"))
                return result
            with patch.object(Path, "rename", new=concurrent):
                with self.assertRaisesRegex(ValueError, "directory changed during switch"):
                    self.upgrade(home, "skill")
            self.assertEqual(self.security(paths["target"] / "private-directory/private.txt"), changed[0])

    def test_filesystem_without_enforced_dacl_is_rejected_before_data_write(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            # Simulate a filesystem that accepts creation but ignores DACLs.
            with patch.object(installer.permissions, "capture", return_value={"sddl": "O:SYG:SY"}):
                with self.assertRaisesRegex(ValueError, "filesystem did not enforce private transaction ACL"):
                    installer.permissions.mkdir_private(root / "transaction")
                with self.assertRaisesRegex(ValueError, "filesystem did not enforce private temporary ACL"):
                    installer.permissions.private_file(root / "temporary")
            self.assertEqual((root / "temporary").read_bytes(), b"")
            self.assertEqual(list((root / "transaction").iterdir()), [])


if __name__ == "__main__":
    unittest.main()
