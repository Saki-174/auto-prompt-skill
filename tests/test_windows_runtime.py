"""Exercise the actual Windows bootstrapper and launcher without downloading Python."""
import json
import os
import shutil
import subprocess
import sys
import tempfile
import time
import unittest
try:
    import venv
except ModuleNotFoundError:
    venv = None
from pathlib import Path
from unittest.mock import patch
from test_install_release import ROOT, installer


class SelfCheckTransactionTests(unittest.TestCase):
    def test_failed_self_check_restores_upgrade_and_user_files(self):
        with tempfile.TemporaryDirectory() as folder:
            home = Path(folder)
            first = installer.install("plugin", home)
            (Path(first["path"]) / "user.txt").write_bytes(b"user preferences")
            before = installer.current_state(installer.locations(home, "plugin"))
            updated = installer.source_files("plugin")
            updated["skills/auto-prompt/SKILL.md"] += b"\nUpdated package\n"
            with patch.object(installer, "source_files", return_value=updated), patch.object(installer, "check_windows_launcher", side_effect=ValueError("self-check failed")):
                with self.assertRaisesRegex(ValueError, "self-check failed"):
                    installer.install("plugin", home, check_launcher=True)
            self.assertEqual(installer.current_state(installer.locations(home, "plugin")), before)

    def test_repeated_install_still_checks_without_changing_files(self):
        with tempfile.TemporaryDirectory() as folder:
            home = Path(folder)
            installer.install("skill", home)
            before = installer.current_state(installer.locations(home, "skill"))
            with patch.object(installer, "check_windows_launcher", side_effect=ValueError("self-check failed")) as check:
                with self.assertRaisesRegex(ValueError, "self-check failed"):
                    installer.install("skill", home, check_launcher=True)
                check.assert_called_once()
            self.assertEqual(installer.current_state(installer.locations(home, "skill")), before)


@unittest.skipUnless(os.name == "nt", "actual Windows PowerShell 5.1 required")
class WindowsRuntimeTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.temp = tempfile.TemporaryDirectory(prefix="ap-win-")
        cls.root = Path(cls.temp.name)
        cls.ps = Path(os.environ["SystemRoot"]) / "System32/WindowsPowerShell/v1.0/powershell.exe"
        cls.env = {k:v for k,v in os.environ.items() if k.lower() not in ("psmodulepath", "path")}
        cls.env["PATH"] = str(cls.ps.parent) + os.pathsep + str(Path(os.environ["SystemRoot"]) / "System32")
        # A real interpreter with a non-ASCII path, deliberately absent from PATH.
        runtime = cls.root / "中文 Python"
        if venv is not None:
            venv.EnvBuilder(with_pip=False).create(runtime)
            cls.python = runtime / "Scripts/python.exe"
        elif list(Path(sys.executable).parent.glob("python*._pth")):
            # Official embeddable distributions omit venv. Copy that isolated runtime.
            shutil.copytree(Path(sys.executable).parent, runtime)
            cls.python = runtime / "python.exe"
        else:
            raise RuntimeError("Windows runtime tests need venv or an official embeddable runtime")

    @classmethod
    def tearDownClass(cls):
        cls.temp.cleanup()

    def setup_home(self, name, *args):
        home = self.root / name
        result = subprocess.run([str(self.ps), "-NoProfile", "-ExecutionPolicy", "Bypass", "-File", str(ROOT / "Install-Windows.ps1"),
                                 "-HomeDirectory", str(home), "-Offline", *map(str, args)],
                                env=self.env, capture_output=True, timeout=90)
        return home, result

    def test_unicode_home_and_runtime_in_both_modes_and_repeat_reuse(self):
        for mode in ("plugin", "skill"):
            with self.subTest(mode=mode):
                name = "中文 用户 " + mode
                home, first = self.setup_home(name, "-Mode", mode, "-PythonPath", self.python)
                self.assertEqual(first.returncode, 0, first.stderr)
                receipt = json.loads(first.stdout)
                self.assertEqual(receipt["selfTest"]["status"], "passed")
                home, repeat = self.setup_home(name, "-Mode", mode)
                self.assertEqual(repeat.returncode, 0, repeat.stderr)
                receipt = json.loads(repeat.stdout)
                self.assertFalse(receipt["changed"])
                self.assertEqual(receipt["selfTest"]["status"], "passed")
                self.assertEqual(Path(receipt["runtime"]["python"]), self.python)
                self.assertFalse((home / ".codex/auto-prompt/runtimes").exists())

    def test_invalid_missing_and_incompatible_registration_fail_cleanly_offline(self):
        for kind, value in (("malformed", b"{"), ("missing", installer.encoded({"schema":1,"python":str(self.root/"missing.exe")})),
                            ("incompatible", installer.encoded({"schema":1,"python":str(self.ps)}))):
            with self.subTest(kind=kind):
                home = self.root / kind
                receipt = home / ".codex/auto-prompt/runtime.json"
                receipt.parent.mkdir(parents=True)
                receipt.write_bytes(value)
                _, result = self.setup_home(kind)
                self.assertEqual(result.returncode, 2)
                self.assertIn(b"No compatible Python", result.stderr)
                self.assertEqual(receipt.read_bytes(), value)
                self.assertFalse((home / ".codex/plugins/local-auto-prompt-skill").exists())
                # Explicit compatible input takes precedence over a stale registration.
                _, repaired = self.setup_home(kind, "-PythonPath", self.python)
                self.assertEqual(repaired.returncode, 0, repaired.stderr)
                self.assertEqual(json.loads(repaired.stdout)["selfTest"]["status"], "passed")

    def test_cmd_summary_and_ps7_parent_environment(self):
        home = self.root / "cmd user"
        env = dict(self.env, PSModulePath=str(self.root / "nonexistent-ps7-module-path"))
        command = 'cmd.exe /d /c ""' + str(ROOT / 'Install-Windows.cmd') + '" -HomeDirectory "' + str(home) + '" -PythonPath "' + str(self.python) + '" -Offline < nul"'
        result = subprocess.run(command, env=env, capture_output=True, timeout=90)
        self.assertEqual(result.returncode, 0, result.stderr)
        text = result.stdout.decode("utf-8")
        self.assertIn("严格脚本自检：通过", text)
        self.assertIn("客户端待启用", text)
        self.assertIn("恢复事务 ID", text)

    def test_actual_bad_launcher_fails_before_transaction_commit(self):
        home = self.root / "broken-launcher"
        program = installer.source_files("plugin")
        program["skills/auto-prompt/scripts/Run-Strict.ps1"] = b"exit 17\n"
        with patch.object(installer, "source_files", return_value=program):
            with self.assertRaisesRegex(ValueError, "self-check failed"):
                installer.install("plugin", home, self.python, check_launcher=True)
        self.assertEqual(installer.current_state(installer.locations(home, "plugin")), {"target":None,"catalog":None,"runtime":None})

    def wait_file(self, path, process):
        deadline = time.monotonic() + 20
        while not path.exists():
            if process.poll() is not None or time.monotonic() >= deadline:
                self.fail("runtime lock worker exited or timed out")
            time.sleep(0.05)

    def test_runtime_preparation_is_serialized_and_rechecks_after_wait(self):
        folder = self.root / "concurrent"
        folder.mkdir()
        script = folder / "worker.ps1"
        script.write_text(r'''
param([string]$Package,[string]$HomeDirectory,[string]$PythonPath,[string]$Worker,[string]$Barrier)
$ErrorActionPreference='Stop'
. (Join-Path $Package 'scripts\runtime.ps1')
$original=(Get-Item Function:Get-APPythonUnlocked).ScriptBlock
function Get-APPythonUnlocked {
    param([string]$HomeDirectory,[string]$PackageRoot,[string]$PythonPath,[string]$RuntimeArchive,[switch]$DedicatedRuntime,[switch]$Offline)
    [IO.File]::WriteAllText((Join-Path $Barrier ('entered-'+$Worker)),'entered')
    if ($Worker -eq 'first') {
        $deadline=[DateTime]::UtcNow.AddSeconds(20)
        while (-not (Test-Path (Join-Path $Barrier 'release'))) {
            if ([DateTime]::UtcNow -gt $deadline) { throw 'Worker barrier timeout' }
            Start-Sleep -Milliseconds 50
        }
    }
    & $original @PSBoundParameters
}
[IO.File]::WriteAllText((Join-Path $Barrier ('started-'+$Worker)),'started')
$runtime=Get-APPython -HomeDirectory $HomeDirectory -PackageRoot $Package -PythonPath $PythonPath -Offline
$runtime | ConvertTo-Json -Compress
''',encoding="utf-8-sig")
        children=[]
        try:
            for worker in ("first","second"):
                child=subprocess.Popen([str(self.ps),"-NoProfile","-ExecutionPolicy","Bypass","-File",str(script),
                                        str(ROOT),str(folder/"user"),str(self.python),worker,str(folder)],
                                       env=self.env,stdout=subprocess.PIPE,stderr=subprocess.PIPE)
                children.append(child)
                self.wait_file(folder/("entered-first" if worker=="first" else "started-second"),child)
            time.sleep(0.5)
            self.assertFalse((folder/"entered-second").exists(),"second bootstrap entered while first held the runtime lock")
            (folder/"release").write_bytes(b"release")
            for child in children:
                stdout,stderr=child.communicate(timeout=30)
                self.assertEqual(child.returncode,0,stderr)
                self.assertEqual(Path(json.loads(stdout)["python"]),self.python)
            self.assertTrue((folder/"entered-second").exists())
            self.assertFalse((folder/"user/.codex/auto-prompt/runtime.prepare.lock").exists())
        finally:
            for child in children:
                if child.poll() is None:
                    child.kill(); child.communicate(timeout=10)

    def test_runtime_lock_is_released_when_holder_is_terminated(self):
        folder=self.root/"killed-lock"
        folder.mkdir()
        script=folder/"holder.ps1"
        script.write_text(r'''
param([string]$Package,[string]$HomeDirectory,[string]$Ready)
$ErrorActionPreference='Stop'
. (Join-Path $Package 'scripts\runtime.ps1')
$guard=Enter-APRuntimeLock $HomeDirectory
[IO.File]::WriteAllText($Ready,'ready')
Start-Sleep -Seconds 60
''',encoding="utf-8-sig")
        child=subprocess.Popen([str(self.ps),"-NoProfile","-ExecutionPolicy","Bypass","-File",str(script),
                                str(ROOT),str(folder/"user"),str(folder/"ready")],env=self.env,
                               stdout=subprocess.PIPE,stderr=subprocess.PIPE)
        try:
            self.wait_file(folder/"ready",child)
        finally:
            if child.poll() is None: child.kill()
            child.communicate(timeout=10)
        # No manual lock deletion: the next real installer must acquire it itself.
        result=subprocess.run([str(self.ps),"-NoProfile","-ExecutionPolicy","Bypass","-File",str(ROOT/"Install-Windows.ps1"),
                               "-HomeDirectory",str(folder/"user"),"-PythonPath",str(self.python),"-Offline"],
                              env=self.env,capture_output=True,timeout=60)
        self.assertEqual(result.returncode,0,result.stderr)
        self.assertEqual(json.loads(result.stdout)["selfTest"]["status"],"passed")


if __name__ == "__main__":
    unittest.main()
