"""Regression cases for external edits and an actual process exit mid-upgrade."""
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from test_install_release import installer


CRASH_UPGRADE = r'''
import importlib.util, os, sys
from pathlib import Path
from unittest.mock import patch
spec = importlib.util.spec_from_file_location("installer", sys.argv[1])
installer = importlib.util.module_from_spec(spec)
spec.loader.exec_module(installer)
home = Path(sys.argv[2])
target = installer.locations(home, "plugin")["target"]
updated = installer.source_files("plugin")
updated["skills/auto-prompt/SKILL.md"] += b"\nUpgrade instructions.\n"
rename = Path.rename
def crash(path, destination):
    result = rename(path, destination)
    if path == target:
        os._exit(91)
    return result
with patch.object(installer, "source_files", return_value=updated), patch.object(Path, "rename", new=crash):
    installer.install("plugin", home)
'''


class RecoveryTests(unittest.TestCase):
    def changed_program(self):
        updated = installer.source_files("plugin")
        updated["skills/auto-prompt/SKILL.md"] += b"\nUpgrade instructions.\n"
        return updated

    def test_external_catalog_edit_survives_failed_upgrade_without_catalog_write(self):
        with tempfile.TemporaryDirectory() as folder:
            home = Path(folder)
            installer.install("plugin", home)
            paths = installer.locations(home, "plugin")
            before = installer.current_state(paths)
            catalog = json.loads(paths["catalog"].read_bytes())
            catalog["plugins"].append({"name": "other-plugin", "source": "./other"})
            foreign = installer.encoded(catalog)
            rename = Path.rename
            def concurrent_edit(path, destination):
                result = rename(path, destination)
                if Path(destination) == paths["target"]:
                    paths["catalog"].write_bytes(foreign)
                return result
            with patch.object(installer, "source_files", return_value=self.changed_program()), patch.object(Path, "rename", new=concurrent_edit):
                with self.assertRaisesRegex(ValueError, "post-install verification"):
                    installer.install("plugin", home)
            self.assertEqual(paths["catalog"].read_bytes(), foreign)
            self.assertEqual(installer.current_state(paths), dict(before, catalog=installer.digest(foreign)))

    def test_external_edit_before_planned_catalog_write_is_not_overwritten(self):
        with tempfile.TemporaryDirectory() as folder:
            home = Path(folder)
            paths = installer.locations(home, "plugin")
            paths["catalog"].parent.mkdir(parents=True)
            paths["catalog"].write_bytes(b'{"name":"mine","plugins":[]}')
            foreign = b'{"name":"mine","plugins":[{"name":"other","source":"./other"}]}'
            rename = Path.rename
            def concurrent_edit(path, destination):
                result = rename(path, destination)
                if Path(destination) == paths["target"]:
                    paths["catalog"].write_bytes(foreign)
                return result
            with patch.object(Path, "rename", new=concurrent_edit):
                with self.assertRaisesRegex(ValueError, "before writing catalog"):
                    installer.install("plugin", home)
            self.assertEqual(paths["catalog"].read_bytes(), foreign)
            self.assertFalse(paths["target"].exists())
            self.assertFalse(paths["runtime"].exists())

    def test_external_edit_after_our_write_is_preserved_and_conflict_reported(self):
        for key in ("target", "catalog", "runtime"):
            with self.subTest(key=key), tempfile.TemporaryDirectory() as folder:
                home = Path(folder)
                paths = installer.locations(home, "plugin")
                real_write = installer.write_atomic
                def edit_after_runtime(path, data):
                    real_write(path, data)
                    if path == paths["runtime"]:
                        foreign = paths[key] / "user.txt" if key == "target" else paths[key]
                        foreign.write_bytes(b"user-owned subsequent edit")
                with patch.object(installer, "write_atomic", side_effect=edit_after_runtime):
                    with self.assertRaisesRegex(ValueError, "recovery preserved later edits to: " + key):
                        installer.install("plugin", home)
                foreign = paths[key] / "user.txt" if key == "target" else paths[key]
                self.assertEqual(foreign.read_bytes(), b"user-owned subsequent edit")
                journal_path = next((home / ".codex/auto-prompt/transactions").glob("*/transaction.json"))
                self.assertEqual(installer.load_json(journal_path)["status"], "recovery_conflict")
                unchanged = installer.current_state(paths)
                with self.assertRaisesRegex(ValueError, "changed since"):
                    installer.rollback(home, journal_path.parent.name)
                self.assertEqual(installer.current_state(paths), unchanged)

    def test_write_that_succeeds_then_raises_is_recovered(self):
        with tempfile.TemporaryDirectory() as folder:
            home = Path(folder)
            paths = installer.locations(home, "plugin")
            real_write = installer.write_atomic
            def fail_after_write(path, data):
                real_write(path, data)
                if path == paths["catalog"]:
                    raise OSError("failure after atomic write")
            with patch.object(installer, "write_atomic", side_effect=fail_after_write):
                with self.assertRaisesRegex(OSError, "after atomic write"):
                    installer.install("plugin", home)
            self.assertEqual(installer.current_state(paths), {key: None for key in paths})

    def crash_upgrade(self, home):
        installer.install("plugin", home)
        paths = installer.locations(home, "plugin")
        (paths["target"] / "user.txt").write_bytes(b"preserve my preferences")
        before = installer.current_state(paths)
        process = subprocess.run([sys.executable, "-B", "-c", CRASH_UPGRADE, installer.__file__, str(home)], capture_output=True, timeout=30)
        self.assertEqual(process.returncode, 91, process.stderr.decode(errors="replace"))
        # This child has exited, so only its isolated project's lock can be removed.
        (home / ".codex/auto-prompt/install.lock").unlink()
        transaction = next(p.parent for p in (home / ".codex/auto-prompt/transactions").glob("*/transaction.json")
                           if installer.load_json(p)["status"] == "applying")
        self.assertFalse(paths["target"].exists())
        return paths, before, transaction

    def test_actual_process_exit_between_directory_renames_can_roll_back(self):
        with tempfile.TemporaryDirectory() as folder:
            home = Path(folder)
            paths, before, transaction = self.crash_upgrade(home)
            self.assertTrue(installer.rollback(home, transaction.name)["changed"])
            self.assertEqual(installer.current_state(paths), before)
            self.assertFalse(installer.rollback(home, transaction.name)["changed"])

    def test_missing_target_requires_intact_stage_displaced_and_backup(self):
        for tampered in ("stage", "displaced", "before/target", "status"):
            with self.subTest(tampered=tampered), tempfile.TemporaryDirectory() as folder:
                home = Path(folder)
                paths, _, transaction = self.crash_upgrade(home)
                if tampered == "status":
                    journal = installer.load_json(transaction / "transaction.json")
                    journal["status"] = "committed"
                    (transaction / "transaction.json").write_bytes(installer.encoded(journal))
                else:
                    (transaction / tampered / "user.txt").write_bytes(b"unexpected edit")
                current = installer.current_state(paths)
                with self.assertRaises(ValueError):
                    installer.rollback(home, transaction.name)
                self.assertEqual(installer.current_state(paths), current)


if __name__ == "__main__":
    unittest.main()
