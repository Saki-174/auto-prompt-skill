[CmdletBinding()]
param(
    [ValidateSet('plugin','skill')][string]$Mode = 'plugin',
    [string]$HomeDirectory = $env:USERPROFILE,
    [string]$PythonPath,
    [string]$RuntimeArchive,
    [switch]$DedicatedRuntime,
    [switch]$Offline,
    [string]$Rollback
)
$ErrorActionPreference = 'Stop'
[Console]::OutputEncoding = New-Object System.Text.UTF8Encoding($false)
$OutputEncoding = [Console]::OutputEncoding
try {
    . (Join-Path $PSScriptRoot 'scripts\runtime.ps1')
    $HomeDirectory = [IO.Path]::GetFullPath($HomeDirectory)
    Assert-APPlainPath $HomeDirectory
    $runtime = Get-APPython -HomeDirectory $HomeDirectory -PackageRoot $PSScriptRoot -PythonPath $PythonPath -RuntimeArchive $RuntimeArchive -DedicatedRuntime:$DedicatedRuntime -Offline:$Offline
    $arguments = @('-I', (Join-Path $PSScriptRoot 'scripts\install.py'), '--mode', $Mode, '--home', $HomeDirectory, '--python', $runtime.python)
    if ($Rollback) { $arguments += @('--rollback', $Rollback) }
    & $runtime.python @arguments
    if ($LASTEXITCODE -ne 0) { throw "Installer failed (exit $LASTEXITCODE). Read the conflict/recovery message above." }
    exit 0
} catch {
    [Console]::Error.WriteLine("Auto Prompt setup: " + $_.Exception.Message)
    exit 2
}
