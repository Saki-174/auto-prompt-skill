[CmdletBinding()]
param(
    [string]$RuntimeArchive,
    [string]$LegacyBundle,
    [string]$PreviousBundle,
    [string]$RecentBundle,
    [switch]$AllowDownload,
    [Parameter(Mandatory=$true)][string]$OutputDirectory
)
$ErrorActionPreference = 'Stop'
$root = Split-Path -Parent $PSScriptRoot
$runtimeLock = Get-Content -LiteralPath (Join-Path $root 'scripts/runtime-lock.json') -Raw -Encoding UTF8 | ConvertFrom-Json
$expectedVersion = (Get-Content (Join-Path $root 'plugin.json') -Raw -Encoding UTF8 | ConvertFrom-Json).version
$evidence = Join-Path ([IO.Path]::GetFullPath($OutputDirectory)) ('run-' + [guid]::NewGuid().ToString('N'))
[void][IO.Directory]::CreateDirectory($evidence)
$checks = New-Object Collections.Generic.List[object]
$ps5 = Join-Path $env:SystemRoot 'System32\WindowsPowerShell\v1.0\powershell.exe'
$pathBefore = @([Environment]::GetEnvironmentVariable('PATH','User'), [Environment]::GetEnvironmentVariable('PATH','Machine'))
function Check([bool]$Condition, [string]$Name) {
    $checks.Add([pscustomobject]@{name=$Name; passed=$Condition})
    if (-not $Condition) { throw "FAILED: $Name" }
}
function Setup([string[]]$Arguments, [int]$ExpectedExit=0) {
    $previousPreference = $ErrorActionPreference
    try {
        $ErrorActionPreference = 'Continue'
        $log = @(& $ps5 -NoProfile -ExecutionPolicy Bypass -File (Join-Path $root 'Install-Windows.ps1') @Arguments 2>&1)
        $code = $LASTEXITCODE
    } finally { $ErrorActionPreference = $previousPreference }
    $text = ($log | ForEach-Object { $_.ToString() }) -join [Environment]::NewLine
    $logPath = Join-Path $evidence ('setup-' + [guid]::NewGuid().ToString('N') + '.txt')
    [IO.File]::WriteAllText($logPath, $text, (New-Object Text.UTF8Encoding($false)))
    if ($code -ne $ExpectedExit) { throw "Setup exit $code, expected $ExpectedExit. $text" }
    if ($code -eq 0) { return ($text | ConvertFrom-Json) }
    return $text
}
function Snapshot([string]$HomeDirectory, [string]$Mode='plugin') {
    $relative = if ($Mode -eq 'plugin') { '.codex\plugins\local-auto-prompt-skill' } else { '.agents\skills\auto-prompt' }
    $target = Join-Path $HomeDirectory $relative
    $files = @{}
    foreach ($item in Get-ChildItem -LiteralPath $target -Recurse -File) {
        $files[$item.FullName.Substring($target.Length + 1)] = (Get-FileHash -LiteralPath $item.FullName).Hash
    }
    $catalog = Join-Path $HomeDirectory '.agents\plugins\marketplace.json'
    $catalogHash = if (Test-Path $catalog) { (Get-FileHash -LiteralPath $catalog).Hash } else { $null }
    return @{files=$files; catalog=$catalogHash}
}
$passed = $false
$failure = $null
try {
    if (-not $RuntimeArchive -and -not $AllowDownload) { throw 'Supply -RuntimeArchive or explicitly choose -AllowDownload.' }
    $fresh = Join-Path $evidence 'empty-user'
    $argsFresh = @('-HomeDirectory',$fresh,'-DedicatedRuntime')
    if ($RuntimeArchive) { $argsFresh += @('-Offline','-RuntimeArchive',[IO.Path]::GetFullPath($RuntimeArchive)) }
    $first = Setup $argsFresh
    Check ($first.selfTest.status -eq 'passed') 'installer verifies the real strict launcher before success'
    $runtimeFile = Join-Path $fresh '.codex\auto-prompt\runtime.json'
    $runtime = Get-Content -LiteralPath $runtimeFile -Raw -Encoding UTF8 | ConvertFrom-Json
    Check ($runtime.python.StartsWith($fresh)) 'empty home gets a dedicated runtime'
    Check (($runtime.version -join '.') -eq $runtimeLock.version) 'fixed Python version'
    Check (Test-Path (Join-Path (Split-Path $runtime.python) 'LICENSE.txt')) 'upstream runtime license retained'
    $runtimeHash = (Get-FileHash -LiteralPath $runtime.python).Hash
    $fixture = (Get-Content -LiteralPath (Join-Path $root 'tests\fixtures\legacy.json') -Raw -Encoding UTF8 | ConvertFrom-Json).cases[0]
    $inputFile = Join-Path $evidence 'input.json'
    [IO.File]::WriteAllText($inputFile, ($fixture.input | ConvertTo-Json -Depth 10), (New-Object Text.UTF8Encoding($false)))
    $runner = Join-Path $first.path 'skills\auto-prompt\scripts\Run-Strict.ps1'
    $outputs = @((Join-Path $evidence 'strict-1.txt'),(Join-Path $evidence 'strict-2.txt'))
    foreach ($output in $outputs) {
        & $ps5 -NoProfile -ExecutionPolicy Bypass -File $runner -HomeDirectory $fresh -InputPath $inputFile -OutputPath $output
        Check ($LASTEXITCODE -eq 0) 'installed strict launcher executes'
        Check ((Get-FileHash -LiteralPath $output).Hash.ToLowerInvariant() -eq $fixture.sha256) 'installed output matches legacy fixture'
    }
    $second = Setup @('-HomeDirectory',$fresh,'-DedicatedRuntime','-Offline')
    Check ($second.selfTest.status -eq 'passed') 'repeat installation reruns launcher self-check'
    Check (-not $second.changed -and $null -eq $second.transaction) 'repeat installation is idempotent'
    $reuse = Join-Path $evidence 'reuse-user'
    $reuseResult = Setup @('-HomeDirectory',$reuse,'-PythonPath',$runtime.python,'-Offline')
    $reuseRuntime = Get-Content (Join-Path $reuse '.codex\auto-prompt\runtime.json') -Raw -Encoding UTF8 | ConvertFrom-Json
    Check ($reuseRuntime.python -eq $runtime.python) 'compatible runtime reused'
    Check (-not (Test-Path (Join-Path $reuse '.codex\auto-prompt\runtimes'))) 'no redundant runtime prepared'
    $archive = if ($RuntimeArchive) { [IO.Path]::GetFullPath($RuntimeArchive) } else { Join-Path $fresh ('.codex\auto-prompt\downloads\' + $runtimeLock.filename) }
    $incompatible = Join-Path $evidence 'incompatible-user'
    # A known executable unable to satisfy the Python probe exercises the rejection branch.
    $badResult = Setup @('-HomeDirectory',$incompatible,'-PythonPath',$ps5,'-Offline','-RuntimeArchive',$archive)
    $newRuntime = Get-Content (Join-Path $incompatible '.codex\auto-prompt\runtime.json') -Raw -Encoding UTF8 | ConvertFrom-Json
    Check ($newRuntime.python.StartsWith($incompatible)) 'failed compatibility probe prepares dedicated runtime'
    $corrupt = Join-Path $evidence 'corrupt.zip'
    [IO.File]::WriteAllBytes($corrupt,[byte[]](1,2,3,4))
    $corruptHome = Join-Path $evidence 'corrupt-user'
    $badMessage = Setup @('-HomeDirectory',$corruptHome,'-DedicatedRuntime','-Offline','-RuntimeArchive',$corrupt) 2
    Check ($badMessage -match 'checksum mismatch') 'corrupt runtime is rejected with recovery message'
    Check (-not (Test-Path (Join-Path $corruptHome '.codex\plugins\local-auto-prompt-skill'))) 'checksum failure installs no program'
    $offlineHome = Join-Path $evidence 'offline-user'
    $offlineMessage = Setup @('-HomeDirectory',$offlineHome,'-DedicatedRuntime','-Offline') 2
    Check ($offlineMessage -match 'No compatible Python') 'offline missing runtime fails clearly'
    if ($LegacyBundle) {
        Check ((Get-FileHash -LiteralPath $LegacyBundle).Hash.ToLowerInvariant() -eq 'fdf4d98179062f490d180ce4ba59013fb37d071f4cd56d4ae3a14d02ca343d94') 'v1.0.0 bundle integrity'
        Add-Type -AssemblyName System.IO.Compression.FileSystem
        $legacySource = Join-Path $evidence 'legacy-source'
        [IO.Compression.ZipFile]::ExtractToDirectory([IO.Path]::GetFullPath($LegacyBundle),$legacySource)
        $legacy = Join-Path $evidence 'legacy-user'
        & $runtime.python -I (Join-Path $legacySource 'auto-prompt-skill\scripts\install.py') --home $legacy | Out-Null
        Check ($LASTEXITCODE -eq 0) 'real v1.0.0 installation prepared'
        $target = Join-Path $legacy '.codex\plugins\local-auto-prompt-skill'
        [void][IO.Directory]::CreateDirectory((Join-Path $target 'user'))
        [IO.File]::WriteAllText((Join-Path $target 'user\keep.txt'),'custom preference')
        $catalogPath = Join-Path $legacy '.agents\plugins\marketplace.json'
        $catalog = Get-Content $catalogPath -Raw -Encoding UTF8 | ConvertFrom-Json
        $catalog.plugins += [pscustomobject]@{name='unrelated'; source='./keep'}
        [IO.File]::WriteAllText($catalogPath,($catalog | ConvertTo-Json -Depth 10),(New-Object Text.UTF8Encoding($false)))
        $before = Snapshot $legacy
        $upgrade = Setup @('-HomeDirectory',$legacy,'-PythonPath',$runtime.python,'-Offline')
        Check ($upgrade.version -eq $expectedVersion) 'upgrade installs current package version'
        Check ((Get-Content (Join-Path $target 'user\keep.txt') -Raw) -eq 'custom preference') 'custom file preserved during real upgrade'
        $newCatalog = Get-Content $catalogPath -Raw -Encoding UTF8 | ConvertFrom-Json
        Check (@($newCatalog.plugins | Where-Object name -eq 'unrelated').Count -eq 1) 'unrelated plugin preserved'
        $rolled = Setup @('-HomeDirectory',$legacy,'-PythonPath',$runtime.python,'-Offline','-Rollback',$upgrade.transaction)
        $after = Snapshot $legacy
        Check ($before.catalog -eq $after.catalog) 'rollback restores exact old catalog bytes'
        Check (($before.files.Count -eq $after.files.Count) -and (@($before.files.Keys | Where-Object { $before.files[$_] -ne $after.files[$_] }).Count -eq 0)) 'rollback restores exact v1.0.0 and user files'
        Check (-not (Test-Path (Join-Path $legacy '.codex\auto-prompt\runtime.json'))) 'rollback removes newly added runtime pointer'
    }
    foreach ($prior in @(
        [pscustomobject]@{path=$PreviousBundle; version='1.0.1'; sha256='56dfd2f786f3bc0f674edfe1f22b6bd40d8a8cb4d6faa0c168b346574b2c05f9'},
        [pscustomobject]@{path=$RecentBundle; version='1.0.2'; sha256='92023ff94488cba53c76917dd7b075bcf3baa6638e01ec7d502f96a4ac60d8dd'}
    )) {
        if (-not $prior.path) { continue }
        Check ((Get-FileHash -LiteralPath $prior.path).Hash.ToLowerInvariant() -eq $prior.sha256) ("v" + $prior.version + " bundle integrity")
        Add-Type -AssemblyName System.IO.Compression.FileSystem
        $previousSource = Join-Path $evidence ('previous-source-' + $prior.version)
        [IO.Compression.ZipFile]::ExtractToDirectory([IO.Path]::GetFullPath($prior.path),$previousSource)
        foreach ($mode in @('plugin','skill')) {
            $previousUser = Join-Path $evidence ('previous-' + $prior.version + '-' + $mode)
            & $runtime.python -I (Join-Path $previousSource 'auto-prompt-skill\scripts\install.py') --home $previousUser --mode $mode | Out-Null
            Check ($LASTEXITCODE -eq 0) "real v$($prior.version) $mode installation prepared"
            $relative = if ($mode -eq 'plugin') { '.codex\plugins\local-auto-prompt-skill' } else { '.agents\skills\auto-prompt' }
            $target = Join-Path $previousUser $relative
            [IO.File]::WriteAllText((Join-Path $target 'preferences.txt'),'user-owned preference')
            $before = Snapshot $previousUser $mode
            $oldRuntimeHash = (Get-FileHash (Join-Path $previousUser '.codex\auto-prompt\runtime.json')).Hash
            $upgrade = Setup @('-HomeDirectory',$previousUser,'-Mode',$mode,'-PythonPath',$runtime.python,'-Offline')
            Check ($upgrade.selfTest.status -eq 'passed') "v$($prior.version) $mode upgrade self-check passed"
            Check ($upgrade.version -eq $expectedVersion -and $upgrade.changed) "v$($prior.version) $mode upgrade installs current version"
            Check ((Get-Content (Join-Path $target 'preferences.txt') -Raw) -eq 'user-owned preference') "$mode upgrade preserves custom file"
            $again = Setup @('-HomeDirectory',$previousUser,'-Mode',$mode,'-PythonPath',$runtime.python,'-Offline')
            Check (-not $again.changed) "$mode upgraded installation is idempotent"
            $rolled = Setup @('-HomeDirectory',$previousUser,'-Mode',$mode,'-PythonPath',$runtime.python,'-Offline','-Rollback',$upgrade.transaction)
            $after = Snapshot $previousUser $mode
            Check ($before.catalog -eq $after.catalog) "$mode rollback restores prior catalog"
            Check (($before.files.Count -eq $after.files.Count) -and (@($before.files.Keys | Where-Object { $before.files[$_] -ne $after.files[$_] }).Count -eq 0)) "$mode rollback restores exact v$($prior.version) and user files"
            Check ((Get-FileHash (Join-Path $previousUser '.codex\auto-prompt\runtime.json')).Hash -eq $oldRuntimeHash) "$mode rollback preserves prior runtime registration"
        }
    }
    # Two real bootstrap processes prepare the same empty dedicated runtime.
    $parallelHome = Join-Path $evidence 'parallel-user'
    $workerPath = Join-Path $evidence 'runtime-worker.ps1'
    $workerSource = @'
param([string]$PackageRoot,[string]$HomeDirectory,[string]$Archive)
$ErrorActionPreference='Stop'
. (Join-Path $PackageRoot 'scripts\runtime.ps1')
Get-APPython -HomeDirectory $HomeDirectory -PackageRoot $PackageRoot -RuntimeArchive $Archive -DedicatedRuntime -Offline | ConvertTo-Json -Compress
'@
    [IO.File]::WriteAllText($workerPath,$workerSource,(New-Object Text.UTF8Encoding($true)))
    $workers = @()
    $runtimePaths = @()
    try {
        foreach ($number in @(1,2)) {
            $child = New-Object Diagnostics.Process
            $child.StartInfo = New-Object Diagnostics.ProcessStartInfo
            $child.StartInfo.FileName = $ps5
            $child.StartInfo.Arguments = (@('-NoProfile','-ExecutionPolicy','Bypass','-File',$workerPath,$root,$parallelHome,$archive) | ForEach-Object { '"'+$_+'"' }) -join ' '
            $child.StartInfo.UseShellExecute = $false
            $child.StartInfo.CreateNoWindow = $true
            $child.StartInfo.RedirectStandardOutput = $true
            $child.StartInfo.RedirectStandardError = $true
            $child.StartInfo.EnvironmentVariables.Remove('PSModulePath')
            [void]$child.Start()
            $workers += @{process=$child; stdout=$child.StandardOutput.ReadToEndAsync(); stderr=$child.StandardError.ReadToEndAsync()}
        }
        foreach ($worker in $workers) {
            if (-not $worker.process.WaitForExit(45000)) { throw 'Concurrent runtime worker timed out' }
            Check ($worker.process.ExitCode -eq 0) 'concurrent dedicated runtime bootstrap succeeds'
            $runtimePaths += ($worker.stdout.Result | ConvertFrom-Json).python
        }
        Check ($runtimePaths[0] -eq $runtimePaths[1]) 'concurrent workers reuse exactly the same dedicated interpreter'
        $parallelTarget = Split-Path $runtimePaths[0]
        Check (@(Get-ChildItem -LiteralPath $parallelTarget -Directory -Recurse | Where-Object Name -match '\.stage-').Count -eq 0) 'runtime contains no nested staging directories'
        Check (-not (Test-Path (Join-Path $parallelHome '.codex\auto-prompt\runtime.prepare.lock'))) 'runtime preparation lock released after workers finish'
    } finally {
        foreach ($worker in $workers) {
            if (-not $worker.process.HasExited) { $worker.process.Kill(); $worker.process.WaitForExit() }
            $worker.process.Dispose()
        }
    }
    Check ((Get-FileHash -LiteralPath $runtime.python).Hash -eq $runtimeHash) 'reused interpreter not modified'
    $pathAfter = @([Environment]::GetEnvironmentVariable('PATH','User'),[Environment]::GetEnvironmentVariable('PATH','Machine'))
    Check (($pathBefore[0] -ceq $pathAfter[0]) -and ($pathBefore[1] -ceq $pathAfter[1])) 'global user and machine PATH unchanged'
    $passed = $true
} catch {
    $failure = $_.Exception.Message
} finally {
    $report = @{passed=$passed; failure=$failure; version=$expectedVersion; powershell=$PSVersionTable.PSVersion.ToString(); os=[Environment]::OSVersion.VersionString; checks=$checks.ToArray(); legacyChecked=[bool]$LegacyBundle; previousChecked=[bool]$PreviousBundle; recentChecked=[bool]$RecentBundle; dedicatedDownloadRequested=[bool]$AllowDownload; scope='Isolated user directories on this Windows host; not a clean VM or ChatGPT UI acceptance.'}
    $reportPath = Join-Path $evidence 'windows-acceptance.json'
    [IO.File]::WriteAllText($reportPath,($report | ConvertTo-Json -Depth 10),(New-Object Text.UTF8Encoding($false)))
    Write-Output $reportPath
}
if (-not $passed) { throw $failure }
