"""Data preservation, bounded parsing, error privacy and runtime-policy regressions."""
import importlib.util
import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from test_render_prompt import renderer, SCRIPT
from test_install_release import installer, ROOT

policy_spec = importlib.util.spec_from_file_location("runtime_policy", ROOT / "skills/auto-prompt/scripts/runtime_policy.py")
policy = importlib.util.module_from_spec(policy_spec)
policy_spec.loader.exec_module(policy)


class SecurityRegressionTests(unittest.TestCase):
    def invoke(self, *args, input=None):
        return subprocess.run([sys.executable, "-B", str(SCRIPT), *map(str, args)], input=input, capture_output=True, timeout=20)

    def test_input_aliases_are_rejected_without_changing_bytes(self):
        for kind in ("same", "hardlink", "symlink"):
            with self.subTest(kind=kind), tempfile.TemporaryDirectory() as folder:
                source = Path(folder) / "input.json"
                source.write_bytes(b'{"rawPrompt":"Keep source intact"}')
                alias = source if kind == "same" else Path(folder) / "alias.txt"
                if kind == "hardlink":
                    os.link(source, alias)
                elif kind == "symlink":
                    try:
                        alias.symlink_to(source)
                    except OSError as error:
                        if getattr(error, "winerror", None) == 1314:
                            self.skipTest("Windows symbolic-link privilege unavailable")
                        raise
                original = source.read_bytes()
                result = self.invoke("--input", source, "--output", alias)
                self.assertEqual(result.returncode, 2, result.stderr)
                self.assertEqual(source.read_bytes(), original)
                self.assertEqual(result.stdout, b"")

    def test_normal_output_replaces_entry_without_truncating_hardlink_peer(self):
        with tempfile.TemporaryDirectory() as folder:
            output, peer = Path(folder) / "output.txt", Path(folder) / "peer.txt"
            output.write_bytes(b"peer content")
            os.link(output, peer)
            result = self.invoke("--raw-prompt", "A request", "--output", output)
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertEqual(peer.read_bytes(), b"peer content")
            self.assertEqual(output.read_bytes(), renderer.render_prompt({"rawPrompt":"A request"}).encode("utf-8"))

    def test_failed_replace_keeps_destination_and_removes_temporary_file(self):
        with tempfile.TemporaryDirectory() as folder:
            target = Path(folder) / "output.txt"
            target.write_bytes(b"original output")
            with patch.object(renderer.os, "replace", side_effect=OSError("synthetic replace failure")):
                with self.assertRaises(OSError):
                    renderer.write_output(target, b"new output")
            self.assertEqual(target.read_bytes(), b"original output")
            self.assertEqual(set(Path(folder).iterdir()), {target})

    def test_untrusted_key_names_are_not_echoed(self):
        marker = "SYNTHETIC_SECRET_IN_KEY_82a0"
        cases = [json.dumps({"rawPrompt":"valid", marker:"value"}).encode(),
                 ('{"rawPrompt":"valid","' + marker + '":1,"' + marker + '":2}').encode()]
        for data in cases:
            result = self.invoke("--input", "-", input=data)
            self.assertEqual(result.returncode, 2)
            self.assertEqual(result.stdout, b"")
            self.assertNotIn(marker.encode(), result.stderr)
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / "input.json"
            path.write_bytes(cases[1])
            with self.assertRaises(ValueError) as failure:
                installer.load_json(path)
            self.assertNotIn(marker, str(failure.exception))
            catalog = installer.locations(Path(folder), "plugin")["catalog"]
            catalog.parent.mkdir(parents=True)
            catalog.write_bytes(cases[1])
            result = subprocess.run([sys.executable, "-B", str(ROOT / "scripts/install.py"), "--home", folder],
                                    capture_output=True, timeout=20)
            self.assertEqual(result.returncode, 2)
            self.assertEqual(result.stdout, b"")
            log = Path(folder) / "synthetic-error.log"
            log.write_bytes(result.stderr)
            self.assertNotIn(marker.encode(), log.read_bytes())

    def test_byte_limit_accepts_boundary_rejects_above_before_parsing(self):
        for transport in ("stdin", "file"):
            for extra in (0, 1):
                with self.subTest(transport=transport, extra=extra), tempfile.TemporaryDirectory() as folder:
                    body = b'{"rawPrompt":"valid"}'
                    body += b" " * (renderer.MAX_INPUT_BYTES + extra - len(body))
                    path = Path(folder) / "input.json"
                    path.write_bytes(body)
                    result = self.invoke("--input", "-" if transport == "stdin" else path,
                                         input=body if transport == "stdin" else None)
                    self.assertEqual(result.returncode, 0 if extra == 0 else 2, result.stderr)
                    if extra:
                        self.assertEqual(result.stdout, b"")
                        self.assertIn(b"exceeds 1048576 bytes", result.stderr)

    def test_target_length_and_deep_json_fail_cleanly(self):
        self.assertIn("x" * 256, renderer.render_prompt({"rawPrompt":"valid", "targetAgent":"x" * 256}))
        with self.assertRaisesRegex(ValueError, "targetAgent exceeds"):
            renderer.render_prompt({"rawPrompt":"valid", "targetAgent":"x" * 257})
        with self.assertRaises(ValueError):
            renderer.render_prompt({"rawPrompt":"valid", "targetAgent":"🧩" * 129})
        result = self.invoke("--input", "-", input=(b"[" * 3000 + b"0" + b"]" * 3000))
        self.assertEqual(result.returncode, 2)
        self.assertEqual(result.stdout, b"")
        self.assertNotIn(b"Traceback", result.stderr)

    def test_switch_window_preserves_latest_active_user_and_program_files(self):
        for mode in ("plugin", "skill"):
            for when in ("before-rename", "after-rename"):
                with self.subTest(mode=mode, when=when), tempfile.TemporaryDirectory() as folder:
                    home = Path(folder)
                    installer.install(mode, home)
                    paths = installer.locations(home, mode)
                    before = installer.current_state(paths)
                    changed = installer.source_files(mode)
                    key = "skills/auto-prompt/SKILL.md" if mode == "plugin" else "SKILL.md"
                    changed[key] += b"\nCandidate upgrade\n"
                    rename = Path.rename
                    injected = []
                    def concurrent_edit(path, destination):
                        is_switch = path == paths["target"] and Path(destination).name == "displaced"
                        if is_switch and when == "before-rename":
                            (path / "user.txt").write_bytes(b"latest independent content")
                            (path / key).write_bytes(b"latest program edit")
                            injected.append(True)
                        result = rename(path, destination)
                        if is_switch and when == "after-rename":
                            (Path(destination) / "user.txt").write_bytes(b"latest independent content")
                            (Path(destination) / key).write_bytes(b"latest program edit")
                            injected.append(True)
                        return result
                    with patch.object(installer, "source_files", return_value=changed), patch.object(Path, "rename", new=concurrent_edit):
                        with self.assertRaisesRegex(ValueError, "directory changed during switch"):
                            installer.install(mode, home)
                    self.assertEqual(injected, [True])
                    self.assertEqual((paths["target"] / "user.txt").read_bytes(), b"latest independent content")
                    self.assertEqual((paths["target"] / key).read_bytes(), b"latest program edit")
                    now = installer.current_state(paths)
                    self.assertEqual(now["catalog"], before["catalog"])
                    self.assertEqual(now["runtime"], before["runtime"])
                    conflicts = [p for p in (home / ".codex/auto-prompt/transactions").glob("*/transaction.json")
                                 if installer.load_json(p)["status"] == "recovery_conflict"]
                    self.assertEqual(len(conflicts), 1)
                    with self.assertRaises(ValueError):
                        installer.rollback(home, conflicts[0].parent.name)
                    self.assertEqual(installer.current_state(paths), now)

    def test_runtime_patch_policy_boundary(self):
        for minor, patch_floor in policy.MINIMUM_PATCH.items():
            self.assertTrue(policy.supported((*minor, patch_floor)))
            self.assertTrue(policy.supported((*minor, patch_floor + 1)))
            self.assertFalse(policy.supported((*minor, patch_floor - 1)))
        for version in ((3,9,25), (3,10,22), (3,15,0), (2,7,18)):
            self.assertFalse(policy.supported(version))

    def test_unreadable_moved_tree_is_restored_without_using_stale_backup(self):
        with tempfile.TemporaryDirectory() as folder:
            home = Path(folder)
            installer.install("plugin", home)
            paths = installer.locations(home, "plugin")
            before = installer.current_state(paths)
            changed = installer.source_files("plugin")
            changed["skills/auto-prompt/SKILL.md"] += b"\nCandidate upgrade\n"
            tree_bytes = installer.tree_bytes
            def unavailable(path):
                if path.name == "displaced":
                    (path / "user.txt").write_bytes(b"latest content")
                    raise OSError("synthetic snapshot failure")
                return tree_bytes(path)
            with patch.object(installer, "source_files", return_value=changed), patch.object(installer, "tree_bytes", side_effect=unavailable):
                with self.assertRaisesRegex(ValueError, "directory changed during switch"):
                    installer.install("plugin", home)
            self.assertEqual((paths["target"] / "user.txt").read_bytes(), b"latest content")
            now = installer.current_state(paths)
            for key in ("catalog", "runtime"):
                self.assertEqual(now[key], before[key])

    def test_invalid_utf8_does_not_echo_input(self):
        result = self.invoke("--input", "-", input=b"\xffSYNTHETIC_PRIVATE_BYTES")
        self.assertEqual(result.returncode, 2)
        self.assertNotIn(b"SYNTHETIC_PRIVATE_BYTES", result.stderr)
        self.assertNotIn(b"Traceback", result.stderr)


if __name__ == "__main__":
    unittest.main()
