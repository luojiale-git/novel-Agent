# ============================================================
# 天机 - 一键启动脚本 (Ollama 模式)
# ============================================================
Write-Host "╔══════════════════════════════════════════════╗" -ForegroundColor Cyan
Write-Host "║     天机 - 一键启动 (Ollama 模式)            ║" -ForegroundColor Cyan
Write-Host "╚══════════════════════════════════════════════╝" -ForegroundColor Cyan
Write-Host ""

# ---- Step 1: 创建模型目录 ----
Write-Host "[1/5] 创建模型目录 D:\ollama\models ..." -ForegroundColor Yellow
New-Item -ItemType Directory -Path "D:\ollama\models" -Force | Out-Null
Write-Host "  ✔ 已创建" -ForegroundColor Green

# ---- Step 2: 设置环境变量（模型存 D 盘） ----
Write-Host "[2/5] 设置 OLLAMA_MODELS 环境变量 ..." -ForegroundColor Yellow
[Environment]::SetEnvironmentVariable("OLLAMA_MODELS", "D:\ollama\models", "User")
Write-Host "  ✔ 已设置（模型文件将下载到 D:\ollama\models）" -ForegroundColor Green

# ---- Step 3: 检查/安装 Ollama ----
Write-Host "[3/5] 检查 Ollama 安装状态 ..." -ForegroundColor Yellow
$ollamaPath = Get-Command "ollama" -ErrorAction SilentlyContinue
if (-not $ollamaPath) {
    Write-Host "  ⚠ Ollama 未安装，正在下载安装包 ..." -ForegroundColor Yellow
    $installer = "$env:TEMP\OllamaSetup.exe"
    try {
        Invoke-WebRequest -Uri "https://ollama.com/download/OllamaSetup.exe" -OutFile $installer -UseBasicParsing
        Write-Host "  ✔ 下载完成，正在静默安装（请稍候）..." -ForegroundColor Green
        Start-Process -FilePath $installer -ArgumentList "/S" -Wait
        Write-Host "  ✔ 安装完成" -ForegroundColor Green
    }
    catch {
        Write-Host "  ✘ 下载安装包失败：$_" -ForegroundColor Red
        Write-Host "  请手动安装：https://ollama.com" -ForegroundColor Red
        exit 1
    }
}
else {
    Write-Host "  ✔ Ollama 已安装：$($ollamaPath.Source)" -ForegroundColor Green
}

# ---- Step 4: 启动 Ollama 服务并拉取模型 ----
Write-Host "[4/5] 启动 Ollama 服务 ..." -ForegroundColor Yellow
$ollamaRunning = $false
try {
    $resp = Invoke-WebRequest -Uri "http://localhost:11434" -Method GET -UseBasicParsing -TimeoutSec 5
    $ollamaRunning = $true
}
catch {
    Write-Host "  ⚠ Ollama 服务未启动，正在启动 ..." -ForegroundColor Yellow
    try {
        Start-Process -FilePath "ollama" -ArgumentList "serve" -WindowStyle Hidden
        Start-Sleep -Seconds 3
        $ollamaRunning = $true
    }
    catch {
        Write-Host "  ✘ 启动失败，请手动启动 Ollama（系统托盘图标）" -ForegroundColor Red
        Write-Host "  然后重新运行此脚本" -ForegroundColor Red
        exit 1
    }
}

if ($ollamaRunning) {
    Write-Host "  ✔ Ollama 服务运行中" -ForegroundColor Green
    Write-Host "  拉取模型 qwen2:7b（首次约 4GB，需要几分钟）..." -ForegroundColor Yellow
    ollama pull qwen2:7b
    Write-Host "  ✔ 模型已就绪" -ForegroundColor Green
}

# ---- Step 5: 安装 Python 依赖 ----
Write-Host "[5/5] 安装 Python 依赖 ..." -ForegroundColor Yellow
$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $scriptDir
pip install -r requirements.txt
Write-Host "  ✔ 依赖已安装" -ForegroundColor Green

# ---- 完成 ----
Write-Host ""
Write-Host "╔══════════════════════════════════════════════╗" -ForegroundColor Cyan
Write-Host "║  全部就绪！启动命令：                       ║" -ForegroundColor Cyan
Write-Host "║                                              ║" -ForegroundColor Cyan
Write-Host "║  cd D:\crow5\智能体\天机                    ║" -ForegroundColor Cyan
Write-Host "║  python main.py                             ║" -ForegroundColor Cyan
Write-Host "║                                              ║" -ForegroundColor Cyan
Write-Host "╚══════════════════════════════════════════════╝" -ForegroundColor Cyan

pause
