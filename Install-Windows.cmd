@echo off
powershell.exe -NoProfile -ExecutionPolicy Bypass -File "%~dp0Install-Windows.ps1" %*
set "AP_EXIT=%errorlevel%"
if not "%AP_EXIT%"=="0" (
  echo Setup failed. Read the message above and docs\install.md before retrying.
) else (
  echo Files and catalog are ready. Complete install or refresh in ChatGPT, then start a new local chat.
)
pause
exit /b %AP_EXIT%
