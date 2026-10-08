# PowerShell 5.1+, Windows x64. No global Python, PATH or registry changes.
Set-StrictMode -Version Latest

function Assert-APPlainPath([string]$Path) {
    $itemPath = [IO.Path]::GetFullPath($Path)
    while ($itemPath) {
        if (Test-Path -LiteralPath $itemPath) {
            $item = Get-Item -LiteralPath $itemPath -Force
            if (($item.Attributes -band [IO.FileAttributes]::ReparsePoint) -ne 0) {
                throw "Linked/reparse path is unsupported: $itemPath"
            }
        }
        $parent = [IO.Directory]::GetParent($itemPath)
        if ($null -eq $parent) { break }
        $itemPath = $parent.FullName
    }
}
function Assert-APOwned([string]$HomeDirectory, [string]$Path) {
    $base = [IO.Path]::GetFullPath($HomeDirectory).TrimEnd('\') + '\'
    $full = [IO.Path]::GetFullPath($Path)
    if (-not $full.StartsWith($base, [StringComparison]::OrdinalIgnoreCase)) {
        throw "Path is outside the selected home: $full"
    }
    Assert-APPlainPath $full
}
function Test-APPython([string]$PythonPath, [string]$PolicyPath) {
    if (-not $PythonPath -or -not (Test-Path -LiteralPath $PythonPath -PathType Leaf)) { return $null }
    if ([IO.Path]::GetExtension($PythonPath) -ne '.exe') { return $null }
    $process = New-Object Diagnostics.Process
    $process.StartInfo = New-Object Diagnostics.ProcessStartInfo
    $process.StartInfo.FileName = $PythonPath
    $process.StartInfo.Arguments = '-I "' + $PolicyPath + '"'
    $process.StartInfo.UseShellExecute = $false
    $process.StartInfo.CreateNoWindow = $true
    $process.StartInfo.RedirectStandardOutput = $true
    $process.StartInfo.RedirectStandardError = $true
    try {
        [void]$process.Start()
        $stdout = $process.StandardOutput.ReadToEndAsync()
        $stderr = $process.StandardError.ReadToEndAsync()
        if (-not $process.WaitForExit(15000)) { $process.Kill(); $process.WaitForExit(); return $null }
        if ($process.ExitCode -ne 0) { return $null }
        $result = $stdout.Result | ConvertFrom-Json
        if (-not $result.python -or $result.version.Count -ne 3) { return $null }
        return $result
    } catch { return $null }
    finally { $process.Dispose() }
}
function Enter-APRuntimeLock([string]$HomeDirectory) {
    $path = Join-Path $HomeDirectory '.codex\auto-prompt\runtime.prepare.lock'
    Assert-APOwned $HomeDirectory $path
    [void][IO.Directory]::CreateDirectory([IO.Path]::GetDirectoryName($path))
    $deadline = [DateTime]::UtcNow.AddSeconds(30)
    while ($true) {
        try {
            # The OS releases the handle and removes the lock even on process termination.
            $handle = [IO.FileStream]::new($path, [IO.FileMode]::OpenOrCreate, [IO.FileAccess]::ReadWrite,
                [IO.FileShare]::None, 4096, [IO.FileOptions]::DeleteOnClose)
            return $handle
        } catch [IO.IOException] {
            if ([DateTime]::UtcNow -ge $deadline) {
                throw 'Runtime preparation is busy or its lock is unavailable. Wait for the other installer to finish, then retry; do not remove a live lock.'
            }
            Start-Sleep -Milliseconds 100
        }
    }
}
function Get-APPython {
    param(
        [string]$HomeDirectory,
        [string]$PackageRoot,
        [string]$PythonPath,
        [string]$RuntimeArchive,
        [switch]$DedicatedRuntime,
        [switch]$Offline
    )
    $guard = Enter-APRuntimeLock $HomeDirectory
    try { Get-APPythonUnlocked @PSBoundParameters }
    finally { $guard.Dispose() }
}
function Get-APPythonUnlocked {
    param(
        [string]$HomeDirectory,
        [string]$PackageRoot,
        [string]$PythonPath,
        [string]$RuntimeArchive,
        [switch]$DedicatedRuntime,
        [switch]$Offline
    )
    if ($env:OS -ne 'Windows_NT') { throw 'Automatic runtime preparation is Windows x64 only; see docs/install.md.' }
    # ARM64 may emulate x64; do not claim native support without its own acceptance.
    $architecture = if ($env:PROCESSOR_ARCHITEW6432) { $env:PROCESSOR_ARCHITEW6432 } else { $env:PROCESSOR_ARCHITECTURE }
    if ($architecture -ne 'AMD64') { throw "Automatic runtime preparation has not been validated on $architecture." }
    $lock = Get-Content -LiteralPath (Join-Path $PackageRoot 'scripts\runtime-lock.json') -Raw | ConvertFrom-Json
    $policy = Join-Path $PackageRoot 'skills\auto-prompt\scripts\runtime_policy.py'
    if ($lock.platform -ne 'windows-x64' -or $lock.url -notmatch '^https://www\.python\.org/ftp/python/' -or $lock.sha256 -notmatch '^[a-f0-9]{64}$') {
        throw 'Invalid runtime lock. Obtain an intact candidate package.'
    }
    $state = Join-Path $HomeDirectory '.codex\auto-prompt'
    $target = Join-Path $state ("runtimes\python-" + $lock.version + "-x64")
    Assert-APOwned $HomeDirectory $target
    $probe = Test-APPython (Join-Path $target 'python.exe') $policy
    if ($probe -and ($probe.version -join '.') -eq $lock.version) { return $probe }
    if (-not $DedicatedRuntime) {
        $candidates = @()
        if ($PythonPath) {
            $candidates += $PythonPath
        } else {
            # Reuse a previous explicit/host interpreter even when it is off PATH.
            $receipt = Join-Path $state 'runtime.json'
            Assert-APOwned $HomeDirectory $receipt
            if (Test-Path -LiteralPath $receipt -PathType Leaf) {
                try {
                    $registered = Get-Content -LiteralPath $receipt -Raw -Encoding UTF8 | ConvertFrom-Json
                    if ($registered.schema -eq 1 -and $registered.python -is [string] -and [IO.Path]::IsPathRooted($registered.python)) {
                        $candidates += $registered.python
                    }
                } catch { Write-Verbose 'Invalid runtime registration; continue runtime discovery.' }
            }
            # Then discover host/PATH runtimes. Do not invoke py/pymanager or Store aliases:
            # these launchers can install or update a shared runtime behind our back.
            $candidates += (Join-Path $HomeDirectory '.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe')
            foreach ($name in @('python.exe', 'python3.exe')) {
                $command = Get-Command $name -CommandType Application -ErrorAction SilentlyContinue
                if ($command -and $command.Source -notmatch 'WindowsApps') { $candidates += $command.Source }
            }
        }
        foreach ($candidate in $candidates) {
            $probe = Test-APPython $candidate $policy
            if ($probe) { return $probe }
        }
    }
    if ($RuntimeArchive) {
        $archive = [IO.Path]::GetFullPath($RuntimeArchive)
    } else {
        $archive = Join-Path $state ("downloads\" + $lock.filename)
        Assert-APOwned $HomeDirectory $archive
        if (-not (Test-Path -LiteralPath $archive)) {
            if ($Offline) { throw "No compatible Python or cached runtime. Download $($lock.url) on a connected machine, then rerun with -RuntimeArchive <zip-path>." }
            [void][IO.Directory]::CreateDirectory([IO.Path]::GetDirectoryName($archive))
            $part = $archive + '.partial-' + [guid]::NewGuid().ToString('N')
            Assert-APOwned $HomeDirectory $part
            try {
                [Net.ServicePointManager]::SecurityProtocol = [Net.ServicePointManager]::SecurityProtocol -bor [Net.SecurityProtocolType]::Tls12
                Invoke-WebRequest -UseBasicParsing -Uri $lock.url -OutFile $part -TimeoutSec 120 -MaximumRedirection 0
                $downloadHash = (Get-FileHash -LiteralPath $part -Algorithm SHA256).Hash.ToLowerInvariant()
                if ($downloadHash -ne $lock.sha256) { throw 'Downloaded Python checksum does not match the pinned SHA-256.' }
                [IO.File]::Move($part, $archive)
            } catch {
                throw "Runtime download failed: $($_.Exception.Message) Retry after fixing connectivity, or use -RuntimeArchive <official-zip>. No install success has been recorded."
            } finally {
                if (Test-Path -LiteralPath $part) { Assert-APOwned $HomeDirectory $part; Remove-Item -LiteralPath $part }
            }
        }
    }
    $actual = (Get-FileHash -LiteralPath $archive -Algorithm SHA256).Hash.ToLowerInvariant()
    if ($actual -ne $lock.sha256) { throw "Runtime checksum mismatch at $archive. Keep it for inspection; supply a fresh official archive with -RuntimeArchive. Expected $($lock.sha256)." }
    Add-Type -AssemblyName System.IO.Compression.FileSystem
    $stage = $target + '.stage-' + [guid]::NewGuid().ToString('N')
    Assert-APOwned $HomeDirectory $stage
    [void][IO.Directory]::CreateDirectory($stage)
    try {
        $zip = [IO.Compression.ZipFile]::OpenRead($archive)
        try {
            foreach ($entry in $zip.Entries) {
                $path = Join-Path $stage $entry.FullName
                Assert-APOwned $stage $path
                if ([IO.Path]::GetFullPath($path).Length -ge 260) { throw 'Runtime extraction path is too long for Windows PowerShell 5.1. Retry with a shorter -HomeDirectory; do not change global Windows settings.' }
                if (($entry.FullName -split '[\\/]') -contains '..') { throw 'Unsafe runtime ZIP member.' }
                if ((($entry.ExternalAttributes -shr 16) -band 61440) -eq 40960) { throw 'Runtime ZIP symlinks are unsupported.' }
            }
        } finally { $zip.Dispose() }
        [IO.Compression.ZipFile]::ExtractToDirectory($archive, $stage)
        $probe = Test-APPython (Join-Path $stage 'python.exe') $policy
        if (-not $probe -or ($probe.version -join '.') -ne $lock.version -or -not (Test-Path -LiteralPath (Join-Path $stage 'LICENSE.txt'))) {
            throw 'Extracted runtime validation failed; existing runtime retained.'
        }
        $backup = $null
        if (Test-Path -LiteralPath $target) {
            $backup = $target + '.backup-' + [guid]::NewGuid().ToString('N')
            Assert-APOwned $HomeDirectory $backup
            [IO.Directory]::Move($target, $backup)
        }
        try { [IO.Directory]::Move($stage, $target) }
        catch {
            if ($backup) { [IO.Directory]::Move($backup, $target) }
            throw
        }
        $probe = Test-APPython (Join-Path $target 'python.exe') $policy
        if (-not $probe) { throw 'Runtime failed its final probe. Rerun installation; retained runtime backups are under runtimes/.' }
        return $probe
    } finally {
        if (Test-Path -LiteralPath $stage) {
            Assert-APOwned $HomeDirectory $stage
            foreach ($child in Get-ChildItem -LiteralPath $stage -Recurse -Force) { Assert-APOwned $HomeDirectory $child.FullName }
            Remove-Item -LiteralPath $stage -Recurse -Force
        }
    }
}
