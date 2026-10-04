[CmdletBinding()]
param(
    [ValidateSet('plugin', 'skill')]
    [string]$Mode = 'plugin'
)
$ErrorActionPreference = 'Stop'
$pythonCandidates = @()
foreach ($pythonName in @('python', 'python3')) {
    $found = Get-Command $pythonName -ErrorAction SilentlyContinue
    if ($found -and $found.Source -notmatch 'WindowsApps') { $pythonCandidates += $found.Source }
}
# Use a host-provided runtime when present; no download or Python installation.
$bundledPython = Join-Path $env:USERPROFILE '.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe'
if (Test-Path -LiteralPath $bundledPython) { $pythonCandidates += $bundledPython }
$foundPy = Get-Command py -ErrorAction SilentlyContinue
if ($pythonCandidates.Count -gt 0) {
    & $pythonCandidates[0] (Join-Path $PSScriptRoot 'scripts\install.py') --mode $Mode
} elseif ($foundPy) {
    & $foundPy.Source -3 (Join-Path $PSScriptRoot 'scripts\install.py') --mode $Mode
} else {
    throw 'Python 3.9+ is required by this installer. See README for manual installation without Python.'
}
if ($LASTEXITCODE -ne 0) { throw "Auto Prompt installer exited with code $LASTEXITCODE" }
