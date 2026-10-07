import hashlib
import importlib.util
import json
import os
import subprocess
import tempfile
import unittest
import zipfile
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parent.parent


def module(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    result = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(result)
    return result


installer = module("installer", ROOT / "scripts/install.py")
release = module("release", ROOT / "scripts/build_release.py")


class InstallerTests(unittest.TestCase):
    def test_personal_marketplace_preserves_existing_plugins_and_is_idempotent(self):
        with tempfile.TemporaryDirectory() as folder:
            home = Path(folder)
            catalog = home / ".agents/plugins/marketplace.json"
            catalog.parent.mkdir(parents=True)
            original = {"name": "my-existing-tools", "interface": {"displayName": "My Tools"}, "custom": 12, "plugins": [{"name": "cyx-memory", "source": "./memory", "policy": {"installation": "AVAILABLE"}}]}
            catalog.write_text(json.dumps(original), encoding="utf-8")
            first = installer.install("plugin", home)
            data = json.loads(catalog.read_text(encoding="utf-8"))
            self.assertEqual(data["name"], original["name"])
            self.assertEqual(data["custom"], 12)
            self.assertEqual(data["plugins"][0], original["plugins"][0])
            self.assertEqual(Path(first["catalogBackup"]).read_text(encoding="utf-8"), json.dumps(original))
            second = installer.install("plugin", home)
            self.assertFalse(second["changed"])
            self.assertIsNone(second["catalogBackup"])
            self.assertEqual(len(json.loads(catalog.read_text(encoding="utf-8"))["plugins"]), 2)

    def test_conflicting_source_fails_before_mutation(self):
        with tempfile.TemporaryDirectory() as folder:
            home = Path(folder)
            catalog = home / ".agents/plugins/marketplace.json"
            catalog.parent.mkdir(parents=True)
            original = '{"name":"existing","plugins":[{"name":"auto-prompt-skill","source":"./someone-elses-plugin"}]}'
            catalog.write_text(original, encoding="utf-8")
            with self.assertRaises(ValueError):
                installer.install("plugin", home)
            self.assertEqual(catalog.read_text(encoding="utf-8"), original)
            self.assertFalse((home / ".codex/plugins/local-auto-prompt-skill").exists())

    def test_skill_update_preserves_modified_program_by_reporting_conflict(self):
        with tempfile.TemporaryDirectory() as folder:
            result = installer.install("skill", Path(folder))
            target = Path(result["path"])
            manifest = target / "SKILL.md"
            manifest.write_text(manifest.read_text(encoding="utf-8") + "\nOld local custom rule.\n", encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "customized program files"):
                installer.install("skill", Path(folder))
            self.assertIn("Old local custom rule", manifest.read_text(encoding="utf-8"))


class ReleaseTests(unittest.TestCase):
    def test_unsafe_source_names_fail_before_any_archive_is_written(self):
        for entry in ("../outside.md", str(ROOT / "README.md"), "C:/private.md", "./README.md"):
            with self.subTest(entry=entry), tempfile.TemporaryDirectory() as folder:
                output = Path(folder) / "release"
                with patch.object(release,"PUBLIC",release.PUBLIC+[entry]):
                    with self.assertRaisesRegex(ValueError,"release file name"):
                        release.build(output)
                self.assertFalse(output.exists())

    def linked_source(self, kind):
        with tempfile.TemporaryDirectory() as folder:
            base = Path(folder)
            source, external, output = base/"source",base/"external",base/"release"
            source.mkdir();external.mkdir()
            (source/"plugin.json").write_text('{"version":"1.0.2"}',encoding="utf-8")
            (source/"LICENSE").write_bytes(b"license")
            (source/"NOTICE").write_bytes(b"notice")
            marker=b"synthetic external text, never real private data"
            (external/"private.md").write_bytes(marker)
            linked = source/"references"
            try:
                try:
                    if kind == "junction":
                        if os.name != "nt": self.skipTest("junction requires Windows")
                        result=subprocess.run(["cmd.exe","/d","/c","mklink","/J",str(linked),str(external)],capture_output=True)
                        if result.returncode:self.skipTest("junction creation unavailable")
                    else:
                        linked.symlink_to(external,target_is_directory=True)
                except OSError as error:
                    self.skipTest("directory symlink creation unavailable: "+str(error))
                with patch.object(release,"ROOT",source), patch.object(release,"PUBLIC",["plugin.json","references/private.md"]), \
                        patch.object(release,"SKILL_FILES",[]):
                    with self.assertRaisesRegex(ValueError,"linked/reparse"):
                        release.build(output)
                self.assertFalse(output.exists(),"invalid late source must not create even an earlier archive")
                self.assertEqual((external/"private.md").read_bytes(),marker)
            finally:
                if linked.is_symlink():linked.unlink()
                elif linked.exists():linked.rmdir()  # Only this junction, never its target.

    def test_directory_symlink_source_is_rejected_before_writing(self):
        self.linked_source("symlink")

    def test_directory_junction_source_is_rejected_before_writing(self):
        self.linked_source("junction")

    def test_archives_reproduce_and_contain_only_the_public_allowlist(self):
        with tempfile.TemporaryDirectory() as folder:
            output = Path(folder)
            files = release.build(output)
            initial = {path.name: path.read_bytes() for path in files}
            release.build(output)
            self.assertEqual(initial, {path.name: path.read_bytes() for path in files})
            for path in files:
                if path.suffix != ".zip":
                    continue
                with zipfile.ZipFile(path) as bundle:
                    names = bundle.namelist()
                    self.assertEqual(len(names), len(set(names)))
                    self.assertEqual(len([n for n in names if n.endswith("/SKILL.md")]), 1)
                    for name in names:
                        self.assertFalse(name.startswith("/"))
                        self.assertNotIn("..", Path(name).parts)
                        self.assertNotIn(".git", Path(name).parts)
                        self.assertNotIn("node_modules", Path(name).parts)
                        self.assertFalse(name.endswith((".env", ".db", ".dpapi", ".pid", ".exe", ".pyc")))
                    self.assertIsNone(bundle.testzip())
                    if "-bundle" in path.name:
                        expected = {"auto-prompt-skill/" + entry for entry in release.PUBLIC}
                    elif "-plugin" in path.name:
                        expected = {"auto-prompt-skill/" + entry for entry in ["plugin.json", "LICENSE", "NOTICE"] + release.SKILL_FILES}
                    else:
                        expected = {"auto-prompt/" + str(Path(entry).relative_to("skills/auto-prompt")).replace("\\", "/") for entry in release.SKILL_FILES}
                    self.assertEqual(set(names), expected)
            for line in (output / "SHA256SUMS.txt").read_text(encoding="ascii").splitlines():
                digest, name = line.split("  ")
                self.assertEqual(hashlib.sha256((output / name).read_bytes()).hexdigest(), digest)


if __name__ == "__main__":
    unittest.main()
