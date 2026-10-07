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

CRASH_RESTORE = r'''
import importlib.util, json, os, sys
from pathlib import Path
from unittest.mock import patch
spec = importlib.util.spec_from_file_location("installer", sys.argv[1])
m = importlib.util.module_from_spec(spec); spec.loader.exec_module(m)
home, tx, point = Path(sys.argv[2]), sys.argv[3], sys.argv[4]
paths = m.locations(home, "plugin")
rename, copy, replace, write = Path.rename, m.shutil.copytree, m.os.replace, m.write_atomic
def crash_rename(path, destination):
    result = rename(path, destination)
    if ((point == "moved" and Path(destination).name == "restore-displaced")
            or (point == "installed" and path.name == "restore-stage")):
        os._exit(93)
    return result
def crash_copy(source, destination, *args, **kwargs):
    if point == "copy" and Path(destination).name == "restore-stage":
        Path(destination).mkdir()
        (Path(destination) / "partial.txt").write_bytes(b"incomplete restoration")
        os._exit(93)
    return copy(source, destination, *args, **kwargs)
def crash_replace(source, destination):
    for key in ("catalog", "runtime"):
        if Path(destination) == paths[key] and point == key + "-before": os._exit(93)
    result = replace(source, destination)
    for key in ("catalog", "runtime"):
        if Path(destination) == paths[key] and point == key + "-after": os._exit(93)
    return result
def crash_write(path, data):
    if point == "journal" and path.name == "transaction.json": os._exit(93)
    result = write(path, data)
    if point == "ready" and path.name == "restore.json" and json.loads(data)["phase"] == "ready": os._exit(93)
    return result
with patch.object(Path,"rename",new=crash_rename), patch.object(m.shutil,"copytree",new=crash_copy), \
        patch.object(m.os,"replace",new=crash_replace), patch.object(m,"write_atomic",new=crash_write):
    m.rollback(home, tx)
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


class RestorationTests(unittest.TestCase):
    def upgrade(self, home):
        paths = installer.locations(home, "plugin")
        paths["catalog"].parent.mkdir(parents=True)
        paths["catalog"].write_bytes(b'{"name":"mine","plugins":[{"name":"other","source":"./other"}]}')
        installer.install("plugin", home)
        (paths["target"] / "user.txt").write_bytes(b"keep preferences")
        before = installer.current_state(paths)
        updated = installer.source_files("plugin")
        updated["skills/auto-prompt/SKILL.md"] += b"\nNew revision\n"
        catalog = installer.catalog_update(paths["catalog"], home, paths["target"])
        catalog["revision"] = "new"
        runtime = installer.load_json(paths["runtime"])
        runtime["revision"] = "new"
        with patch.object(installer,"source_files",return_value=updated), \
                patch.object(installer,"catalog_update",return_value=catalog), \
                patch.object(installer,"runtime_data",return_value=installer.encoded(runtime)):
            result = installer.install("plugin", home)
        return paths, before, result["transaction"]

    def crash(self, home, transaction, point):
        result = subprocess.run([sys.executable,"-B","-c",CRASH_RESTORE,installer.__file__,str(home),transaction,point],
                                capture_output=True,timeout=30)
        self.assertEqual(result.returncode,93,result.stderr.decode(errors="replace"))
        (home / ".codex/auto-prompt/install.lock").unlink()  # The child is confirmed dead.

    def test_actual_exit_during_restore_copy_and_each_rename_is_retryable(self):
        for point in ("copy","ready","moved","installed","journal"):
            with self.subTest(point=point), tempfile.TemporaryDirectory() as folder:
                home = Path(folder)
                paths, before, tx = self.upgrade(home)
                after = installer.current_state(paths)
                self.crash(home,tx,point)
                if point in ("copy","ready"):
                    # Other resources may already have been atomically restored.
                    current = installer.current_state(paths)
                    self.assertEqual(current["target"],after["target"])
                    for key in ("catalog","runtime"):
                        self.assertIn(current[key],(before[key],after[key]))
                installer.rollback(home,tx)
                self.assertEqual(installer.current_state(paths),before)
                self.assertEqual((paths["target"] / "user.txt").read_bytes(),b"keep preferences")
                self.assertFalse(installer.rollback(home,tx)["changed"])

    def test_shared_files_remain_complete_before_and_after_atomic_restore(self):
        for key in ("catalog","runtime"):
            for when in ("before","after"):
                with self.subTest(key=key,when=when), tempfile.TemporaryDirectory() as folder:
                    home = Path(folder)
                    paths, before, tx = self.upgrade(home)
                    after = installer.current_state(paths)
                    self.crash(home,tx,key+"-"+when)
                    self.assertIsInstance(installer.load_json(paths[key]),dict)
                    self.assertIn(installer.current_state(paths)[key],(before[key],after[key]))
                    installer.rollback(home,tx)
                    self.assertEqual(installer.current_state(paths),before)

    def test_copy_error_keeps_current_program_and_can_retry(self):
        with tempfile.TemporaryDirectory() as folder:
            home = Path(folder)
            paths,before,tx = self.upgrade(home)
            current_target = installer.current_state(paths)["target"]
            with patch.object(installer.shutil,"copytree",side_effect=OSError("restore copy failed")):
                with self.assertRaisesRegex(OSError,"restore copy failed"):
                    installer.rollback(home,tx)
            self.assertEqual(installer.current_state(paths)["target"],current_target)
            installer.rollback(home,tx)
            self.assertEqual(installer.current_state(paths),before)

    def test_rename_gap_requires_intact_restoration_evidence_and_backup(self):
        for tampered in ("restore-stage","restore-displaced","before/target","restore.json"):
            with self.subTest(tampered=tampered), tempfile.TemporaryDirectory() as folder:
                home = Path(folder)
                paths,_,tx = self.upgrade(home)
                self.crash(home,tx,"moved")
                transaction = home / ".codex/auto-prompt/transactions" / tx
                if tampered == "restore.json":
                    receipt = installer.load_json(transaction / tampered)
                    receipt["original"] = {"unexpected":"changed"}
                    (transaction / tampered).write_bytes(installer.encoded(receipt))
                else:
                    (transaction / tampered / "user.txt").write_bytes(b"external edit")
                unchanged = installer.current_state(paths)
                with self.assertRaises(ValueError):
                    installer.rollback(home,tx)
                self.assertEqual(installer.current_state(paths),unchanged)

    def test_later_user_file_in_rename_gap_is_not_removed(self):
        with tempfile.TemporaryDirectory() as folder:
            home = Path(folder)
            paths,_,tx = self.upgrade(home)
            self.crash(home,tx,"moved")
            paths["target"].mkdir()
            (paths["target"] / "user.txt").write_bytes(b"later user work")
            unchanged = installer.current_state(paths)
            with self.assertRaisesRegex(ValueError,"changed since"):
                installer.rollback(home,tx)
            self.assertEqual(installer.current_state(paths),unchanged)

    def test_failed_install_restoration_copy_can_be_finished_by_rollback(self):
        with tempfile.TemporaryDirectory() as folder:
            home = Path(folder)
            installer.install("plugin",home)
            paths = installer.locations(home,"plugin")
            before = installer.current_state(paths)
            updated = installer.source_files("plugin")
            updated["skills/auto-prompt/SKILL.md"] += b"\nNew revision\n"
            copy = installer.shutil.copytree
            def fail_restore(source,destination,*args,**kwargs):
                if Path(destination).name == "restore-stage":
                    raise OSError("restore copy failed")
                return copy(source,destination,*args,**kwargs)
            with patch.object(installer,"source_files",return_value=updated), \
                    patch.object(installer,"check_windows_launcher",side_effect=ValueError("launcher failed")), \
                    patch.object(installer.shutil,"copytree",new=fail_restore):
                with self.assertRaisesRegex(ValueError,"restore copy failed"):
                    installer.install("plugin",home,check_launcher=True)
            journal = next(p for p in (home / ".codex/auto-prompt/transactions").glob("*/transaction.json")
                           if installer.load_json(p)["status"] == "recovery_conflict")
            self.assertTrue(paths["target"].exists())
            installer.rollback(home,journal.parent.name)
            self.assertEqual(installer.current_state(paths),before)

    def test_foreign_edit_after_resource_restoration_is_not_reported_as_success(self):
        with tempfile.TemporaryDirectory() as folder:
            home = Path(folder)
            paths,_,tx = self.upgrade(home)
            recover = installer.recover_attempt
            foreign = b'{"name":"mine","plugins":[{"name":"later-plugin","source":"./later"}]}'
            def foreign_manager(*args,**kwargs):
                recover(*args,**kwargs)
                paths["catalog"].write_bytes(foreign)
            with patch.object(installer,"recover_attempt",side_effect=foreign_manager):
                with self.assertRaisesRegex(ValueError,"changed during rollback"):
                    installer.rollback(home,tx)
            self.assertEqual(paths["catalog"].read_bytes(),foreign)


if __name__ == "__main__":
    unittest.main()
