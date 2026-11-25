# Gera o executavel portatil sanitizado (sem caminhos da maquina de desenvolvimento).
# Uso:  powershell -ExecutionPolicy Bypass -File installer\build-portatil.ps1 [-Versao 1.0.0]
param([string] $Versao = "")
$ErrorActionPreference = 'Stop'
$nome = if ($Versao) { "Instalador-reNut-PTBR-v$Versao.exe" } else { 'Instalador-reNut-PTBR.exe' }

$installer = $PSScriptRoot
$raiz = Split-Path -Parent $installer
$cargoHome = Join-Path $env:USERPROFILE '.cargo'
$destino = Join-Path $raiz 'dist\instalador'

# Os caminhos absolutos sao remapeados em tempo de compilacao: o binario nao publica
# o nome do usuario nem a pasta do projeto. O /Brepro troca a data e o GUID do PE por
# valores derivados do conteudo: duas compilacoes do mesmo codigo geram o mesmo SHA-256.
$flags = @(
    "-C", "target-feature=+crt-static",
    "-C", "link-arg=/Brepro",
    "--remap-path-prefix=$raiz=projeto",
    "--remap-path-prefix=$cargoHome=registro",
    "--remap-path-prefix=$env:USERPROFILE=usuario"
) -join [char]0x1f
$env:CARGO_ENCODED_RUSTFLAGS = $flags

Push-Location $raiz
try {
    cargo build --release --locked -p instalador-renut-ptbr --bin instalador-renut-ptbr
    if ($LASTEXITCODE -ne 0) { throw "cargo build falhou" }
    New-Item -ItemType Directory -Force -Path $destino | Out-Null
    Copy-Item (Join-Path $raiz 'target\release\instalador-renut-ptbr.exe') `
        (Join-Path $destino $nome) -Force
    $arquivo = Join-Path $destino $nome
    $sha = (Get-FileHash $arquivo -Algorithm SHA256).Hash.ToLower()
    "$sha  $nome" | Out-File (Join-Path $destino 'SHA256SUMS.txt') -Encoding ascii
    $bytes = [System.IO.File]::ReadAllBytes($arquivo)
    $texto = [System.Text.Encoding]::ASCII.GetString($bytes)
    foreach ($proibido in @($raiz, $env:USERPROFILE, $cargoHome)) {
        if ($texto.Contains($proibido)) {
            throw "O binario ainda contem o caminho local: $proibido"
        }
    }
    $tamanho = (Get-Item $arquivo).Length
    Write-Host "OK: $arquivo"
    Write-Host "Tamanho: $tamanho bytes"
    Write-Host "SHA-256: $sha"
}
finally {
    Pop-Location
}