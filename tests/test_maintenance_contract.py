"""Catch runtime/CI version drift without fetching or installing dependencies."""
import ast
import importlib.util
import json
import re
import unittest
from pathlib import Path
from urllib.parse import urlsplit

ROOT = Path(__file__).resolve().parent.parent
spec = importlib.util.spec_from_file_location("maintenance_policy", ROOT / "skills/auto-prompt/scripts/runtime_policy.py")
policy = importlib.util.module_from_spec(spec)
spec.loader.exec_module(policy)


class MaintenanceContractTests(unittest.TestCase):
    def test_locked_runtime_matches_policy_and_official_download_coordinates(self):
        lock = json.loads((ROOT / "scripts/runtime-lock.json").read_text(encoding="utf-8"))
        version = tuple(int(p) for p in lock["version"].split("."))
        self.assertTrue(policy.supported(version), "locked runtime falls below reuse policy")
        self.assertEqual(lock["platform"], "windows-x64")
        self.assertEqual(lock["filename"], "python-" + lock["version"] + "-embed-amd64.zip")
        url = urlsplit(lock["url"])
        self.assertEqual((url.scheme, url.netloc), ("https", "www.python.org"))
        self.assertEqual(url.path, "/ftp/python/" + lock["version"] + "/" + lock["filename"])
        self.assertFalse(url.query or url.fragment)
        self.assertRegex(lock["sha256"], r"^[0-9a-f]{64}$")

    def test_explicit_ci_versions_meet_policy_and_include_locked_runtime(self):
        workflow = (ROOT / ".github/workflows/ci.yml").read_text(encoding="utf-8")
        matrix = re.search(r"(?m)^\s+python:\s*(\[[^\n]+\])\s*$", workflow)
        self.assertIsNotNone(matrix, "CI must declare exact maintained Python versions")
        versions = ast.literal_eval(matrix.group(1))
        self.assertTrue(versions)
        for version in versions:
            self.assertRegex(version, r"^3\.\d+\.\d+$")
            self.assertTrue(policy.supported(tuple(int(p) for p in version.split("."))), version)
        lock = json.loads((ROOT / "scripts/runtime-lock.json").read_text(encoding="utf-8"))
        self.assertIn(lock["version"], versions, "CI must cover the default dedicated runtime")
