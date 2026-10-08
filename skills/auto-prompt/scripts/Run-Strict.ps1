[CmdletBinding()]
param(
    [Parameter(Mandatory=$true)][string]$InputPath,
    [string]$OutputPath,
    [ValidateSet('text','json')][string]$Format = 'text',
    [string]$HomeDirectory = $env:USERPROFILE
)
$ErrorActionPreference = 'Stop'
[Console]::OutputEncoding = New-Object System.Text.UTF8Encoding($false)
$OutputEncoding = [Console]::OutputEncoding
try {
    $receipt = Join-Path $HomeDirectory '.codex\auto-prompt\runtime.json'
    if (-not (Test-Path -LiteralPath $receipt)) { throw 'Runtime registration missing. Run Install-Windows.cmd, or use a compatible host Python with render_prompt.py.' }
    $runtime = Get-Content -LiteralPath $receipt -Raw -Encoding UTF8 | ConvertFrom-Json
    if ($runtime.schema -ne 1 -or -not (Test-Path -LiteralPath $runtime.python -PathType Leaf)) {
        throw 'Registered Python is unavailable. Rerun Install-Windows.cmd to repair the project runtime.'
    }
    $probe = & $runtime.python -I (Join-Path $PSScriptRoot 'runtime_policy.py')
    if ($LASTEXITCODE -ne 0) { throw 'Registered Python is incompatible. Rerun Install-Windows.cmd.' }
    $arguments = @('-I', (Join-Path $PSScriptRoot 'render_prompt.py'), '--input', $InputPath, '--format', $Format)
    if ($OutputPath) { $arguments += @('--output', $OutputPath) }
    & $runtime.python @arguments
    exit $LASTEXITCODE
} catch {
    [Console]::Error.WriteLine("Auto Prompt strict runner: " + $_.Exception.Message)
    exit 2
}
