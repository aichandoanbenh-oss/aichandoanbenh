param(
    [ValidateSet('Auto','CPU','CUDA')][string]$Device = 'Auto',
    [switch]$SkipBrowser,
    [switch]$CheckOnly
)
$ErrorActionPreference = 'Stop'
Set-Location -LiteralPath $PSScriptRoot
$pythonExe = Join-Path $PSScriptRoot '.venv\Scripts\python.exe'
function Run-Native {
    param([string]$Executable, [string[]]$Arguments)
    & $Executable @Arguments
    if ($LASTEXITCODE -ne 0) { throw "Command failed ($LASTEXITCODE): $Executable $($Arguments -join ' ')" }
}
function Find-Python312 {
    $launcher = Get-Command py.exe -ErrorAction SilentlyContinue
    if ($launcher) {
        $found = & $launcher.Source -3.12 -c 'import sys; print(sys.executable)' 2>$null
        if ($LASTEXITCODE -eq 0 -and $found) { return [string]($found | Select-Object -Last 1) }
    }
    foreach ($candidate in @("$env:LOCALAPPDATA\Programs\Python\Python312\python.exe", "$env:ProgramFiles\Python312\python.exe")) {
        if (Test-Path -LiteralPath $candidate) { return $candidate }
    }
    return $null
}
New-Item -ItemType Directory -Force -Path 'reports' | Out-Null
Start-Transcript -Path 'reports/setup-latest.log' -Force | Out-Null
try {
    if ($CheckOnly) {
        if (!(Test-Path -LiteralPath $pythonExe)) { throw 'Missing .venv. Run setup.bat first.' }
        Run-Native $pythonExe @('scripts/check_setup.py')
    } else {
        if (!(Test-Path -LiteralPath $pythonExe)) {
            $basePython = Find-Python312
            if (!$basePython) {
                Write-Host 'Installing Python 3.12.10 (current Windows user)...'
                [Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12
                New-Item -ItemType Directory -Force -Path 'data/setup' | Out-Null
                $installer = Join-Path $PSScriptRoot 'data/setup/python-3.12.10-amd64.exe'
                Invoke-WebRequest 'https://www.python.org/ftp/python/3.12.10/python-3.12.10-amd64.exe' -OutFile $installer
                $signature = Get-AuthenticodeSignature -LiteralPath $installer
                if ($signature.Status -ne 'Valid' -or $signature.SignerCertificate.Subject -notmatch 'Python Software Foundation') { throw 'Python installer signature validation failed.' }
                $process = Start-Process -FilePath $installer -ArgumentList '/quiet','InstallAllUsers=0','PrependPath=1','Include_test=0','Include_pip=1' -WindowStyle Hidden -Wait -PassThru
                if ($process.ExitCode -notin @(0,3010)) { throw "Python installer failed: $($process.ExitCode)" }
                $basePython = Find-Python312
                if (!$basePython) { throw 'Python not found after installation. Reopen setup.bat.' }
            }
            Run-Native $basePython @('-m','venv','.venv')
        }
        Write-Host 'Checking existing virtual environment: Python 3.12, 64-bit required.'
        Run-Native $pythonExe @('-c','import sys; assert sys.version_info[:2] == (3,12); assert sys.maxsize > 2**32')
        $selectedDevice = $Device
        if ($selectedDevice -eq 'Auto') {
            $selectedDevice = 'CPU'
            $smi = Get-Command nvidia-smi.exe -ErrorAction SilentlyContinue
            if ($smi) {
                & $smi.Source --query-gpu=name --format=csv,noheader
                if ($LASTEXITCODE -eq 0) { $selectedDevice = 'CUDA' }
            }
        }
        $channel = if ($selectedDevice -eq 'CUDA') { 'cu124' } else { 'cpu' }
        Write-Host "Installing PyTorch 2.6.0 / torchvision 0.21.0 ($channel)..."
        Run-Native $pythonExe @('-m','pip','install','--upgrade','pip')
        Run-Native $pythonExe @('-m','pip','install',"torch==2.6.0+$channel","torchvision==0.21.0+$channel",'--index-url',"https://download.pytorch.org/whl/$channel")
        Run-Native $pythonExe @('-m','pip','install','-r','scripts/requirements-project.txt')
        if (!$SkipBrowser) { Run-Native $pythonExe @('-m','playwright','install','chromium') }
        Run-Native $pythonExe @('-m','pip','check')
        Run-Native $pythonExe @('scripts/check_setup.py')
        if ($selectedDevice -eq 'CUDA') {
            Run-Native $pythonExe @('scripts/check_setup.py','--require-cuda')
        }
        Write-Host 'SETUP COMPLETE. Read run.md. Double-click run_web.bat to start the web.' -ForegroundColor Green
        Write-Host 'Datasets, model weights, NVIDIA driver and Android JDK/SDK/Gradle are NOT downloaded by this installer.'
    }
} catch {
    Write-Host "SETUP FAILED: $($_.Exception.Message)" -ForegroundColor Red
    exit 1
} finally { Stop-Transcript | Out-Null }
