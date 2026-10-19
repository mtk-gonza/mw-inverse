param(
    [string]$GodotPath = "D:\projects\Godot_v4.7.2-stable_win64\Godot_v4.7.2-stable_win64.exe"
)

$root = Split-Path -Parent $PSScriptRoot
$server = Start-Process -FilePath "python" -ArgumentList "server\main.py" -WorkingDirectory $root -PassThru
Start-Process -FilePath $GodotPath -ArgumentList "--path `"$root\client`"" -WorkingDirectory $root

Write-Host "Servidor iniciado con PID $($server.Id) en 127.0.0.1:24500"
Write-Host "Cliente Godot iniciado desde $root\client"
