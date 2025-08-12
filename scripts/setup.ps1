param(
  [string]$RepoZipUrl = "https://github.com/cbarria/gorilla/archive/refs/heads/main.zip",
  [string]$InstallPath = "$env:USERPROFILE\gorilla",
  [switch]$Run
)

$ErrorActionPreference = 'Stop'

function Write-Info($msg) { Write-Host "$msg" -ForegroundColor Cyan }
function Write-Ok($msg) { Write-Host "$msg" -ForegroundColor Green }
function Write-Warn($msg) { Write-Host "$msg" -ForegroundColor Yellow }

try {
  Write-Info "Descargando repo..."
  $tempRoot = Join-Path $env:TEMP ("gorilla-" + [System.Guid]::NewGuid().ToString('N'))
  New-Item -ItemType Directory -Path $tempRoot | Out-Null

  $zipPath = Join-Path $tempRoot "gorilla.zip"
  Invoke-WebRequest -UseBasicParsing -Uri $RepoZipUrl -OutFile $zipPath

  Write-Info "Extrayendo..."
  Expand-Archive -Path $zipPath -DestinationPath $tempRoot -Force

  $extracted = Get-ChildItem -Directory $tempRoot | Where-Object { $_.Name -like 'gorilla-*' } | Select-Object -First 1
  if (-not $extracted) { throw "No se pudo encontrar carpeta extraída." }

  if (Test-Path $InstallPath) {
    Write-Warn "Eliminando instalación previa en $InstallPath"
    Remove-Item -Recurse -Force $InstallPath
  }

  Move-Item -Path $extracted.FullName -Destination $InstallPath

  Write-Info "Creando entorno virtual..."
  Push-Location $InstallPath
  & python -m venv .venv
  $venvPy = Join-Path $InstallPath ".venv\Scripts\python.exe"
  if (-not (Test-Path $venvPy)) { throw "No se encontró Python del venv: $venvPy" }

  Write-Info "Instalando dependencias..."
  & $venvPy -m pip install --upgrade pip | Out-Null
  & $venvPy -m pip install -r requirements.txt

  if ($Run) {
    Write-Info "Lanzando el juego..."
    & $venvPy .\src\gorilla.py
  }

  Pop-Location
  Write-Ok "Instalado en $InstallPath"
  Write-Info "Para ejecutar manualmente:" 
  Write-Host ". .\\.venv\\Scripts\\Activate.ps1; python .\\src\\gorilla.py" -ForegroundColor Yellow
}
catch {
  Write-Host "Error: $($_.Exception.Message)" -ForegroundColor Red
  exit 1
}


