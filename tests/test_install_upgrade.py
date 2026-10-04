import copy
import json
import os
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
from test_install_release import installer


class UpgradeTests(unittest.TestCase):
    def test_upgrade_preserves_user_files_catalog_fields_and_rollback(self):
        with tempfile.TemporaryDirectory() as folder:
            home = Path(folder)
            first = installer.install("plugin", home)
            target = Path(first["path"])
            (target / "user").mkdir()
            (target / "user/preferences.md").write_text("My own prompt preferences.", encoding="utf-8")
            catalog = Path(first["marketplace"])
            data = json.loads(catalog.read_text(encoding="utf-8"))
            data["plugins"][0]["customPolicy"] = {"enabledByUser": False}
            data["plugins"].append({"name": "unrelated", "source": "./unchanged"})
            catalog.write_text(json.dumps(data), encoding="utf-8")
            before = installer.current_state(installer.locations(home, "plugin"))
            updated = installer.source_files("plugin")
            updated["skills/auto-prompt/SKILL.md"] += b"\nNew package instructions.\n"
            with patch.object(installer, "source_files", return_value=updated):
                second = installer.install("plugin", home)
                repeated = installer.install("plugin", home)
            self.assertFalse(repeated["changed"])
            self.assertIsNone(repeated["transaction"])
            self.assertEqual((target / "user/preferences.md").read_text(), "My own prompt preferences.")
            after_catalog = json.loads(catalog.read_text(encoding="utf-8"))
            self.assertEqual(after_catalog["plugins"], data["plugins"])
            self.assertTrue(Path(second["backup"]).is_dir())
            installer.rollback(home, second["transaction"])
            self.assertEqual(installer.current_state(installer.locations(home, "plugin")), before)

    def test_managed_customization_blocks_update_without_replacing_anything(self):
        with tempfile.TemporaryDirectory() as folder:
            home = Path(folder)
            first = installer.install("plugin", home)
            target = Path(first["path"])
            manifest = target / "skills/auto-prompt/SKILL.md"
            manifest.write_bytes(manifest.read_bytes() + b"\nMy custom instruction.\n")
            before = installer.current_state(installer.locations(home, "plugin"))
            with self.assertRaisesRegex(ValueError, "customized program files"):
                installer.install("plugin", home)
            self.assertEqual(installer.current_state(installer.locations(home, "plugin")), before)

    def test_program_collision_with_user_file_stops_without_loss(self):
        with tempfile.TemporaryDirectory() as folder:
            home = Path(folder)
            first = installer.install("plugin", home)
            target = Path(first["path"])
            (target / "user.txt").write_bytes(b"user-owned")
            updated = installer.source_files("plugin")
            updated["user.txt"] = b"new program-owned"
            before = installer.current_state(installer.locations(home, "plugin"))
            with patch.object(installer, "source_files", return_value=updated):
                with self.assertRaisesRegex(ValueError, "user.txt"):
                    installer.install("plugin", home)
            self.assertEqual(installer.current_state(installer.locations(home, "plugin")), before)

    def test_failures_after_program_or_catalog_write_restore_all_owned_state(self):
        for failed_key in ("catalog", "runtime"):
            with self.subTest(failed_key=failed_key), tempfile.TemporaryDirectory() as folder:
                home = Path(folder)
                paths = installer.locations(home, "plugin")
                paths["catalog"].parent.mkdir(parents=True)
                paths["catalog"].write_bytes(b'{"name":"mine","plugins":[{"name":"keep","source":"./keep"}]}')
                before = installer.current_state(paths)
                real_write = installer.write_atomic
                def fail(path, data):
                    if path == paths[failed_key]:
                        raise PermissionError("injected write failure")
                    return real_write(path, data)
                with patch.object(installer, "write_atomic", side_effect=fail):
                    with self.assertRaises(PermissionError):
                        installer.install("plugin", home)
                self.assertEqual(installer.current_state(paths), before)
                journal = next((home / ".codex/auto-prompt/transactions").glob("*/transaction.json"))
                self.assertEqual(json.loads(journal.read_text())["status"], "rolled_back")

    def test_empty_install_rollback_and_repeat(self):
        with tempfile.TemporaryDirectory() as folder:
            home = Path(folder)
            paths = installer.locations(home, "plugin")
            before = installer.current_state(paths)
            result = installer.install("plugin", home)
            self.assertTrue(installer.rollback(home, result["transaction"])["changed"])
            self.assertEqual(installer.current_state(paths), before)
            self.assertFalse(installer.rollback(home, result["transaction"])["changed"])

    def test_rollback_refuses_later_user_or_other_plugin_edits(self):
        for key in ("target", "catalog", "runtime"):
            with self.subTest(key=key), tempfile.TemporaryDirectory() as folder:
                home = Path(folder)
                result = installer.install("plugin", home)
                paths = installer.locations(home, "plugin")
                path = paths[key] / "later.txt" if key == "target" else paths[key]
                path.write_bytes(path.read_bytes() + b"\n " if path.exists() else b"my later file")
                before = installer.current_state(paths)
                with self.assertRaisesRegex(ValueError, "changed since"):
                    installer.rollback(home, result["transaction"])
                self.assertEqual(installer.current_state(paths), before)

    def test_interrupted_partial_transaction_can_restore(self):
        with tempfile.TemporaryDirectory() as folder:
            home = Path(folder)
            first = installer.install("plugin", home)
            paths = installer.locations(home, "plugin")
            transaction = home / ".codex/auto-prompt/transactions" / first["transaction"]
            journal_path = transaction / "transaction.json"
            journal = json.loads(journal_path.read_text())
            journal["status"] = "applying"
            journal_path.write_text(json.dumps(journal), encoding="utf-8")
            paths["runtime"].unlink()  # A crash before runtime registration, after program/catalog.
            installer.rollback(home, first["transaction"])
            self.assertEqual(installer.current_state(paths), journal["before"])

    def test_modified_backup_is_not_restored(self):
        with tempfile.TemporaryDirectory() as folder:
            home = Path(folder)
            installer.install("skill", home)
            updated = installer.source_files("skill")
            updated["SKILL.md"] += b"\nUpdate.\n"
            with patch.object(installer, "source_files", return_value=updated):
                second = installer.install("skill", home)
            (Path(second["backup"]) / "SKILL.md").write_bytes(b"altered backup")
            with self.assertRaisesRegex(ValueError, "backup"):
                installer.rollback(home, second["transaction"])

    def test_duplicate_config_keys_and_lock_and_unsafe_journal_are_rejected(self):
        with tempfile.TemporaryDirectory() as folder:
            home = Path(folder)
            catalog = home / ".agents/plugins/marketplace.json"
            catalog.parent.mkdir(parents=True)
            catalog.write_bytes(b'{"name":"one","name":"two","plugins":[]}')
            with self.assertRaisesRegex(ValueError, "duplicate JSON"):
                installer.install("plugin", home)
            with self.assertRaisesRegex(ValueError, "transaction ID"):
                installer.rollback(home, "../../outside")
            with installer.install_lock(home):
                with self.assertRaisesRegex(ValueError, "install.lock"):
                    installer.install("plugin", home)

    def test_symlink_destination_is_rejected(self):
        with tempfile.TemporaryDirectory() as folder:
            home = Path(folder) / "home"
            external = Path(folder) / "external"
            external.mkdir()
            (external / "keep.txt").write_bytes(b"unchanged")
            home.mkdir()
            link = home / ".codex"
            try:
                link.symlink_to(external, target_is_directory=True)
            except OSError as error:
                if os.name != "nt":
                    self.skipTest("symlink creation unavailable: " + str(error))
                quote = lambda value: "'" + str(value).replace("'", "''") + "'"
                result = subprocess.run(["powershell.exe", "-NoProfile", "-Command",
                                         "New-Item -ItemType Junction -Path " + quote(link) + " -Target " + quote(external) + " | Out-Null"], capture_output=True)
                if result.returncode:
                    self.skipTest("Windows junction creation unavailable")
            try:
                with self.assertRaisesRegex(ValueError, "linked/reparse"):
                    installer.install("plugin", home)
                self.assertEqual((external / "keep.txt").read_bytes(), b"unchanged")
            finally:
                if link.is_symlink():
                    link.unlink()
                else:
                    link.rmdir()  # Remove only the tested junction, not its target.

    def test_locked_old_directory_is_not_rewritten_when_no_mutation_happened(self):
        with tempfile.TemporaryDirectory() as folder:
            home = Path(folder)
            first = installer.install("plugin", home)
            target = Path(first["path"])
            before = installer.current_state(installer.locations(home, "plugin"))
            updated = installer.source_files("plugin")
            updated["skills/auto-prompt/SKILL.md"] += b"\nUpdated instructions.\n"
            rename = Path.rename
            def locked(path, destination):
                if path == target:
                    raise PermissionError("old directory locked")
                return rename(path, destination)
            with patch.object(installer, "source_files", return_value=updated), patch.object(Path, "rename", new=locked), patch.object(installer, "restore_files", wraps=installer.restore_files) as restore:
                with self.assertRaises(PermissionError):
                    installer.install("plugin", home)
                restore.assert_not_called()
            self.assertEqual(installer.current_state(installer.locations(home, "plugin")), before)

    def test_runtime_version_is_verified_not_just_file_existence(self):
        data = json.loads(installer.runtime_data(sys.executable))
        self.assertEqual(data["version"], list(sys.version_info[:3]))
        with patch.object(installer.subprocess, "run") as run:
            run.return_value.returncode = 1
            with self.assertRaisesRegex(ValueError, "incompatible"):
                installer.runtime_data(sys.executable)


if __name__ == "__main__":
    unittest.main()
