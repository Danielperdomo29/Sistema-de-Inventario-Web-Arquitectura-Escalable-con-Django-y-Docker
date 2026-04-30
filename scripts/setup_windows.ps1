# SETUP SCRIPT
Clear-Host
Write-Host "------------------------------------------" -ForegroundColor Cyan
Write-Host "   INSTALADOR AUTOMATICO - SMART INVENTORY" -ForegroundColor Cyan
Write-Host "------------------------------------------" -ForegroundColor Cyan

# 1. Python
Write-Host "[1/6] Verificando Python..." -ForegroundColor Yellow
if (!(Get-Command python -ErrorAction SilentlyContinue)) {
    Write-Host "Error: Python no instalado." -ForegroundColor Red
    exit
}

# 2. Venv
if (Test-Path "venv") {
    Write-Host "[2/6] venv existe." -ForegroundColor Gray
} else {
    Write-Host "[2/6] Creando venv..." -ForegroundColor Yellow
    python -m venv venv
}

# 3. Dependencies
Write-Host "[3/6] Instalando dependencias..." -ForegroundColor Yellow
& ".\venv\Scripts\Activate.ps1"
python -m pip install --upgrade pip
pip install -r requirements.txt

# 4. .env
if (!(Test-Path ".env")) {
    Write-Host "[4/6] Creando .env..." -ForegroundColor Yellow
    Copy-Item ".env.example" ".env"
} else {
    Write-Host "[4/6] .env detectado." -ForegroundColor Gray
}

# 5. DB
Write-Host "[5/6] Migraciones..." -ForegroundColor Yellow
try {
    python manage.py migrate
    Write-Host "Base de datos ok." -ForegroundColor Green
} catch {
    Write-Host "Error en migraciones." -ForegroundColor Red
}

# 6. Final
Write-Host "------------------------------------------" -ForegroundColor Cyan
Write-Host "   CONFIGURACION COMPLETADA" -ForegroundColor Cyan
Write-Host "------------------------------------------" -ForegroundColor Cyan
Write-Host "Para iniciar:"
Write-Host "1. .\venv\Scripts\activate" -ForegroundColor Green
Write-Host "2. python manage.py runserver" -ForegroundColor Green
Write-Host "------------------------------------------" -ForegroundColor Cyan
