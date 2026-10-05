@echo off
setlocal
rem Do not pass PowerShell 7 module paths to Windows PowerShell 5.1.
set "PSModulePath="
powershell.exe -NoProfile -ExecutionPolicy Bypass -File "%~dp0Install-Windows.ps1" -Interactive %*
set "AP_EXIT=%errorlevel%"
if not "%AP_EXIT%"=="0" (
  echo Setup failed. Read the message above and docs\install.md before retrying.
)
pause
exit /b %AP_EXIT%
