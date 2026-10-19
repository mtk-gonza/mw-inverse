$ErrorActionPreference = "Stop"
$root = Split-Path -Parent $PSScriptRoot
$godot = "D:\projects\Godot_v4.7.2-stable_win64\Godot_v4.7.2-stable_win64_console.exe"
$temp = Join-Path ([IO.Path]::GetTempPath()) ("mw-inverse-clean-" + [guid]::NewGuid().ToString("N"))
$clientCopy = Join-Path $temp "client"
try {
    New-Item -ItemType Directory -Force $clientCopy | Out-Null
    & robocopy (Join-Path $root "client") $clientCopy /E /XJ /XD (Join-Path $root "client\assets\reference-library") /NFL /NDL /NJH /NJS | Out-Null
    if ($LASTEXITCODE -gt 7) { throw "robocopy failed with exit code $LASTEXITCODE" }
    & $godot --headless --path $clientCopy --quit-after 3
    if ($LASTEXITCODE -ne 0) { throw "Godot clean smoke failed with exit code $LASTEXITCODE" }
    Write-Output "Clean client smoke: OK"
} finally {
    if (Test-Path $temp) { Remove-Item -Recurse -Force $temp }
}
