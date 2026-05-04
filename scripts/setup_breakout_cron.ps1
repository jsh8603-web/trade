# 변동성 돌파 cron 등록 (PC128 Windows Task Scheduler)
#
# 사용:
#   PowerShell 관리자 권한으로 실행:
#     .\scripts\setup_breakout_cron.ps1
#
#   해제:
#     .\scripts\setup_breakout_cron.ps1 -Remove
#
# 등록 작업:
#   1) CoinTrading_Breakout_Trade — 매일 10:00 (매수/24h 청산)
#   2) CoinTrading_Breakout_Monitor — 매 15분 (손절 감시, 보유 시만 처리)

param(
    [switch]$Remove
)

$ErrorActionPreference = "Stop"
$ProjectDir = Split-Path -Parent $PSScriptRoot
$PythonExe = Join-Path $ProjectDir ".venv\Scripts\python.exe"

if (-not (Test-Path $PythonExe)) {
    Write-Error ".venv\Scripts\python.exe not found. Run: python -m venv .venv && .venv\Scripts\pip install -r requirements.txt"
    exit 1
}

$TaskTrade = "CoinTrading_Breakout_Trade"
$TaskMonitor = "CoinTrading_Breakout_Monitor"

if ($Remove) {
    Write-Host "변동성 돌파 cron 해제 중..."
    foreach ($name in @($TaskTrade, $TaskMonitor)) {
        if (Get-ScheduledTask -TaskName $name -ErrorAction SilentlyContinue) {
            Unregister-ScheduledTask -TaskName $name -Confirm:$false
            Write-Host "  해제: $name"
        }
    }
    Write-Host "완료"
    exit 0
}

Write-Host "변동성 돌파 cron 등록 중..."
Write-Host "  PROJECT_DIR: $ProjectDir"
Write-Host "  PYTHON: $PythonExe"

# 기존 작업 제거 (재등록 안전)
foreach ($name in @($TaskTrade, $TaskMonitor)) {
    if (Get-ScheduledTask -TaskName $name -ErrorAction SilentlyContinue) {
        Unregister-ScheduledTask -TaskName $name -Confirm:$false
    }
}

# 1) Trade — 매일 10:00
$traderScript = Join-Path $ProjectDir "scripts\breakout_trader.py"
$logTrade = Join-Path $ProjectDir "logs\breakout\cron_trade.log"
$traderArg = "-NoProfile -ExecutionPolicy Bypass -Command `"& '$PythonExe' '$traderScript' *>> '$logTrade'`""
$actionTrade = New-ScheduledTaskAction -Execute "powershell.exe" -Argument $traderArg -WorkingDirectory $ProjectDir
$triggerTrade = New-ScheduledTaskTrigger -Daily -At "10:00am"
$settings = New-ScheduledTaskSettingsSet -StartWhenAvailable -DontStopIfGoingOnBatteries -AllowStartIfOnBatteries

Register-ScheduledTask -TaskName $TaskTrade -Action $actionTrade -Trigger $triggerTrade `
    -Settings $settings -Description "변동성 돌파 매수/24h 청산 — 매일 10:00 KST" | Out-Null
Write-Host "  등록: $TaskTrade (매일 10:00)"

# 2) Monitor — 매 15분 (손절 감시)
$monitorScript = Join-Path $ProjectDir "scripts\breakout_monitor.py"
$logMon = Join-Path $ProjectDir "logs\breakout\cron_monitor.log"
$monitorArg = "-NoProfile -ExecutionPolicy Bypass -Command `"& '$PythonExe' '$monitorScript' *>> '$logMon'`""
$actionMonitor = New-ScheduledTaskAction -Execute "powershell.exe" -Argument $monitorArg -WorkingDirectory $ProjectDir

# 매 15분 (00, 15, 30, 45) — 시작 시각은 자정, 무한 반복
$startTime = (Get-Date).Date  # 오늘 자정
$triggerMonitor = New-ScheduledTaskTrigger -Once -At $startTime `
    -RepetitionInterval (New-TimeSpan -Minutes 15) `
    -RepetitionDuration ([TimeSpan]::FromDays(3650))

Register-ScheduledTask -TaskName $TaskMonitor -Action $actionMonitor -Trigger $triggerMonitor `
    -Settings $settings -Description "변동성 돌파 손절 감시 — 매 15분 (보유 시만 처리)" | Out-Null
Write-Host "  등록: $TaskMonitor (매 15분)"

Write-Host ""
Write-Host "완료. 등록된 작업 확인:"
Get-ScheduledTask -TaskName "CoinTrading_Breakout_*" | Select-Object TaskName, State, @{N="Next";E={(Get-ScheduledTaskInfo $_).NextRunTime}}

Write-Host ""
Write-Host "[안내]"
Write-Host "  로그: logs\breakout\YYYYMMDD.log (매매 이력)"
Write-Host "       logs\breakout\cron_trade.log / cron_monitor.log (PowerShell 출력)"
Write-Host "  state: data\breakout_state.json"
Write-Host "  현재 모드: BREAKOUT_DRY_RUN=true (.env) — 실거래 없음, 알림만"
Write-Host "  실거래 전환: .env에서 BREAKOUT_DRY_RUN=false 로 변경"
Write-Host "  완전 정지: .env에서 BREAKOUT_ENABLED=false 또는 EMERGENCY_STOP=true"
