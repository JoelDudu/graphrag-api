# Pegar IP do WSL automaticamente
$wslIp = (wsl hostname -I).Trim()

# Remover regra antiga se existir
netsh interface portproxy delete v4tov4 listenport=7474 listenaddress=0.0.0.0

# Criar nova regra
netsh interface portproxy add v4tov4 listenport=7474 listenaddress=0.0.0.0 connectport=7474 connectaddress=$wslIp

Write-Host "Port forward criado para $wslIp"
netsh interface portproxy show all