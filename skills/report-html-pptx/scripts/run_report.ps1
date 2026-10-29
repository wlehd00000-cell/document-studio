param(
    [Parameter(Mandatory=$true, Position=0)][ValidateSet('scaffold','refresh','inventory','convert','render','contract','workflow','state')][string]$Action,
    [string]$PythonPath,
    [string[]]$CandidatePythonPath,
    [switch]$CheckOnly,
    [Parameter(ValueFromRemainingArguments=$true)][string[]]$ReportArguments
)
$ErrorActionPreference = 'Stop'
switch ($Action) {
    'scaffold' { $scriptPath = Join-Path $PSScriptRoot 'scaffold_report.py' }
    'refresh' { $scriptPath = Join-Path $PSScriptRoot 'refresh_report.py' }
    'inventory' { $scriptPath = Join-Path $PSScriptRoot 'inventory_sources.py' }
    'convert' { $scriptPath = Join-Path $PSScriptRoot '..\..\html-to-pptx\convert.py' }
    'render' { $scriptPath = Join-Path $PSScriptRoot 'render_text_flow.py' }
    'contract' { $scriptPath = Join-Path $PSScriptRoot 'production_contract.py' }
    'workflow' { $scriptPath = Join-Path $PSScriptRoot 'workflow.py' }
    'state' { $scriptPath = Join-Path $PSScriptRoot 'project_state.py' }
}
if (-not (Test-Path -LiteralPath $scriptPath -PathType Leaf)) { throw "Required skill script is missing: $scriptPath" }
$candidates = @()
if ($PythonPath) {
    $candidates = @($PythonPath)
} else {
    $candidates += $CandidatePythonPath
    if ($env:GS_PYTHON_PATH) { $candidates += $env:GS_PYTHON_PATH }
    $candidates += Join-Path ([Environment]::GetFolderPath('UserProfile')) '.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe'
    $taskCodexRoot = if ($env:CODEX_HOME) { $env:CODEX_HOME } else { Join-Path ([Environment]::GetFolderPath('UserProfile')) '.codex' }
    $candidates += Join-Path $taskCodexRoot 'runtimes\demo-report\Scripts\python.exe'
    $candidates += Join-Path $taskCodexRoot 'runtimes\demo-report\python.exe'
    $candidates += [IO.Path]::GetFullPath((Join-Path $PSScriptRoot '..\..\..\runtimes\demo-report\Scripts\python.exe'))
    $candidates += [IO.Path]::GetFullPath((Join-Path $PSScriptRoot '..\..\..\runtimes\demo-report\python.exe'))
    $candidates += [IO.Path]::GetFullPath((Join-Path $PSScriptRoot '..\..\runtime\python.exe'))
    $pythonCommand = Get-Command python -ErrorAction SilentlyContinue
    if ($pythonCommand -and $pythonCommand.Source -notmatch 'WindowsApps') { $candidates += $pythonCommand.Source }
}
$runtimePath = $null
$diagnostics = @()
$probe = @'
import importlib, importlib.util, json, sys
from pathlib import Path
if sys.version_info < (3, 11):
    raise SystemExit('Python 3.11+ required')
action = sys.argv[1]
modules = ['pptx', 'lxml', 'fontTools', 'playwright', 'PIL', 'yaml'] if action == 'convert' else (['playwright'] if action == 'render' else [])
missing = [m for m in modules if importlib.util.find_spec(m) is None]
if missing:
    raise SystemExit('Missing packages: ' + ', '.join(missing))
for name in modules:
    try: importlib.import_module(name)
    except Exception as error: raise SystemExit('Package import failed: ' + name + ' / ' + str(error).splitlines()[0])
if action in ('convert', 'render'):
    from playwright.sync_api import sync_playwright
    with sync_playwright() as p:
        override = sys.argv[3] if len(sys.argv) > 3 else ''
        executable = override or p.chromium.executable_path
        if not Path(executable).is_file():
            raise SystemExit('Chromium executable is unavailable')
        if sys.argv[2] == 'deep':
            try:
                browser = p.chromium.launch(headless=True, executable_path=override or None)
                browser.close()
            except Exception as error:
                raise SystemExit(str(error).splitlines()[0])
print(json.dumps({'ready': True, 'action': action,
    'pymupdf_available': importlib.util.find_spec('fitz') is not None,
    'scope': 'Generation tools; actual output rendering and delivery QA follow separately'}))
'@
$probeAction = $Action
if ($ReportArguments -contains '--check-against' -or $ReportArguments -contains '--help') { $probeAction = 'inspect' }
$probeDepth = if ($CheckOnly) { 'deep' } else { 'available' }
$browserOverride = ''
if ($Action -in @('render','convert') -and $ReportArguments) {
    $browserFlagIndex = [Array]::IndexOf($ReportArguments, '--browser-path')
    if ($browserFlagIndex -ge 0 -and $browserFlagIndex + 1 -lt $ReportArguments.Count) { $browserOverride = $ReportArguments[$browserFlagIndex + 1] }
}
foreach ($candidate in ($candidates | Where-Object { $_ } | Select-Object -Unique)) {
    if (Test-Path -LiteralPath $candidate -PathType Leaf) {
        try {
            $probeOutput = & $candidate -X utf8 -c $probe $probeAction $probeDepth $browserOverride 2>&1
            if ($LASTEXITCODE -eq 0) { $runtimePath = $candidate; break }
            $diagnostics += "$candidate : $($probeOutput | Where-Object { -not [string]::IsNullOrWhiteSpace($_.ToString()) } | Select-Object -Last 1)"
        } catch { $diagnostics += "$candidate : $($_.Exception.Message)" }
    }
}
if (-not $runtimePath) { throw "No available runtime satisfies action '$Action'. Check existing host dependencies and permitted alternatives; no installation was performed. $($diagnostics -join ' | ')" }
if ($CheckOnly) {
    [pscustomobject]@{status='ready'; action=$Action; runtime=$runtimePath} | ConvertTo-Json -Compress
    exit 0
}
& $runtimePath -X utf8 $scriptPath @ReportArguments
if ($LASTEXITCODE -ne 0) { throw "Report action failed with exit code $LASTEXITCODE" }
