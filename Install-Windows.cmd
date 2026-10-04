@echo off
powershell.exe -NoProfile -ExecutionPolicy Bypass -File "%~dp0Install-Windows.ps1" %*
if errorlevel 1 (
  echo Installation failed. See the message above and README.md.
) else (
  echo Restart ChatGPT desktop or Codex, choose the local marketplace and install Auto Prompt Skill.
)
pause
