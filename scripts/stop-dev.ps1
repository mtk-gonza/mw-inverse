$connections = Get-NetTCPConnection -LocalPort 24500 -State Listen -ErrorAction SilentlyContinue
foreach ($connection in $connections) {
    Stop-Process -Id $connection.OwningProcess -Force
    Write-Host "Servidor detenido: PID $($connection.OwningProcess)"
}
