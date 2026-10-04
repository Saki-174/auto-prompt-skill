import hashlib
import importlib.util
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SCRIPT = ROOT / "skills/auto-prompt/scripts/render_prompt.py"
spec = importlib.util.spec_from_file_location("renderer", SCRIPT)
renderer = importlib.util.module_from_spec(spec)
spec.loader.exec_module(renderer)


class RendererTests(unittest.TestCase):
    def test_legacy_outputs_match_exact_utf8_hashes(self):
        fixtures = json.loads((ROOT / "tests/fixtures/legacy.json").read_text(encoding="utf-8"))
        for fixture in fixtures["cases"]:
            with self.subTest(input=fixture["input"]):
                actual = renderer.render_prompt(fixture["input"]).encode("utf-8")
                self.assertEqual(hashlib.sha256(actual).hexdigest(), fixture["sha256"])

    def test_rejects_invalid_inputs_without_dropping_constraints(self):
        invalid = [
            [], {}, {"rawPrompt": " \r\n\t "}, {"rawPrompt": None},
            {"rawPrompt": "ok", "requirements": []},
            {"rawPrompt": "ok", "targetAgent": "Codex\nChatGPT"},
            {"rawPrompt": "ok", "profile": "unknown"},
            {"rawPrompt": "ok", "strictMode": False},
            {"rawPrompt": "ok", "strictMode": 1},
            {"rawPrompt": "ok", "enableDeepReasoning": "true"},
            {"rawPrompt": "ok", "requirements": "使用日语输出。"},
            {"rawPrompt": "ok", "unexpectedConstraint": "must preserve"},
            {"rawPrompt": "a" * 20001},
            {"rawPrompt": "🧩" * 10001},
            {"rawPrompt": "ok", "requirements": "a" * 8001},
        ]
        for payload in invalid:
            with self.subTest(payload_type=type(payload).__name__):
                with self.assertRaises(ValueError):
                    renderer.render_prompt(payload)

    def test_strict_mode_does_not_reinterpret_or_expand_user_text(self):
        raw = "保留 $requirements ${target_agent} {context} 和 🧩。\n我没有提供版本。"
        constraints = "只改我的文档。保持中文。"
        payload = {"rawPrompt": raw, "requirements": constraints, "profile": "general"}
        text = renderer.render_prompt(payload)
        self.assertIn(raw, text)
        self.assertIn(constraints, text)
        self.assertNotIn("Codex", text)
        self.assertEqual(renderer.render_prompt(payload), text)

    def test_legacy_deep_reasoning_flag_has_no_effect_in_strict_mode(self):
        payload = {"rawPrompt": "整理资料。", "profile": "general"}
        self.assertEqual(renderer.render_prompt(payload), renderer.render_prompt(dict(payload, enableDeepReasoning=True)))

    def test_cli_json_matches_text_and_works_outside_repo(self):
        payload = {"targetAgent": "ChatGPT Work", "rawPrompt": "整理资料。", "profile": "general"}
        with tempfile.TemporaryDirectory() as folder:
            result = subprocess.run([sys.executable, str(SCRIPT), "--input", "-", "--format", "json"], input=json.dumps(payload).encode("utf-8"), capture_output=True, cwd=folder)
        self.assertEqual(result.returncode, 0, result.stderr.decode("utf-8"))
        data = json.loads(result.stdout)
        self.assertEqual(data["optimizedPrompt"], renderer.render_prompt(payload))
        self.assertEqual(data["model"], "strict-deterministic-v1")

    def test_duplicate_json_keys_fail(self):
        result = subprocess.run([sys.executable, str(SCRIPT), "--input", "-"], input=b'{"rawPrompt":"one","rawPrompt":"two"}', capture_output=True)
        self.assertEqual(result.returncode, 2)
        self.assertEqual(result.stdout, b"")

    def test_output_does_not_overwrite_input_file(self):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / "input.json"
            original = b'{"rawPrompt":"test"}'
            path.write_bytes(original)
            result = subprocess.run([sys.executable, str(SCRIPT), "--input", str(path), "--output", str(path)], capture_output=True)
            self.assertEqual(result.returncode, 2)
            self.assertEqual(path.read_bytes(), original)


if __name__ == "__main__":
    unittest.main()
