import hashlib
import importlib.util
import json
import tempfile
import unittest
import zipfile
from pathlib import Path

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

    def test_skill_update_keeps_recoverable_backup(self):
        with tempfile.TemporaryDirectory() as folder:
            result = installer.install("skill", Path(folder))
            target = Path(result["path"])
            manifest = target / "SKILL.md"
            manifest.write_text(manifest.read_text(encoding="utf-8") + "\nOld local custom rule.\n", encoding="utf-8")
            second = installer.install("skill", Path(folder))
            self.assertIn("Old local custom rule", (Path(second["backup"]) / "SKILL.md").read_text(encoding="utf-8"))
            self.assertNotIn("Old local custom rule", manifest.read_text(encoding="utf-8"))


class ReleaseTests(unittest.TestCase):
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
