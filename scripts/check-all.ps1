$ErrorActionPreference = "Stop"
$root = Split-Path -Parent $PSScriptRoot
Push-Location $root
try {
    python -m unittest discover -s server -p "test_*.py"
    $pythonFiles = Get-ChildItem tools,server -Filter "*.py" -Recurse | ForEach-Object { $_.FullName }
    python -m py_compile @pythonFiles
    & "D:\projects\Godot_v4.7.2-stable_win64\Godot_v4.7.2-stable_win64_console.exe" --headless --path client --quit-after 3
    python tools\validate_reference_pack.py client\assets\reference-local client\assets\reference-local\manifest.json
} finally {
    Pop-Location
}
