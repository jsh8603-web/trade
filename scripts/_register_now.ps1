$python = "D:\Projects\claude-coin-trading-main\.venv\Scripts\python.exe"
$script = "D:\Projects\claude-coin-trading-main\scripts\training_scheduler.py"
$wd = "D:\Projects\claude-coin-trading-main"

# Tier1: 6시간마다
$a1 = New-ScheduledTaskAction -Execute $python -Argument "-u `"$script`" tier1" -WorkingDirectory $wd
$t1 = New-ScheduledTaskTrigger -Once -At '00:00' -RepetitionInterval (New-TimeSpan -Hours 6) -RepetitionDuration (New-TimeSpan -Days 365)
$s1 = New-ScheduledTaskSettingsSet -AllowStartIfOnBatteries -DontStopIfGoingOnBatteries -StartWhenAvailable -ExecutionTimeLimit (New-TimeSpan -Minutes 30) -MultipleInstances IgnoreNew
Register-ScheduledTask -TaskName 'CoinTrading_RL_tier1' -Description 'RL Tier1 Quick 6h' -Action $a1 -Trigger $t1 -Settings $s1 -Force | Out-Null
Write-Host '[OK] tier1 - 6시간마다'

# Tier2: 매일 03:00
$a2 = New-ScheduledTaskAction -Execute $python -Argument "-u `"$script`" tier2" -WorkingDirectory $wd
$t2 = New-ScheduledTaskTrigger -Daily -At '03:00'
$s2 = New-ScheduledTaskSettingsSet -AllowStartIfOnBatteries -DontStopIfGoingOnBatteries -StartWhenAvailable -ExecutionTimeLimit (New-TimeSpan -Minutes 30) -MultipleInstances IgnoreNew
Register-ScheduledTask -TaskName 'CoinTrading_RL_tier2' -Description 'RL Tier2 Daily 03:00' -Action $a2 -Trigger $t2 -Settings $s2 -Force | Out-Null
Write-Host '[OK] tier2 - 매일 03:00'

# Tier3: 매주 일요일 04:00
$a3 = New-ScheduledTaskAction -Execute $python -Argument "-u `"$script`" tier3" -WorkingDirectory $wd
$t3 = New-ScheduledTaskTrigger -Weekly -DaysOfWeek Sunday -At '04:00'
$s3 = New-ScheduledTaskSettingsSet -AllowStartIfOnBatteries -DontStopIfGoingOnBatteries -StartWhenAvailable -ExecutionTimeLimit (New-TimeSpan -Minutes 60) -MultipleInstances IgnoreNew
Register-ScheduledTask -TaskName 'CoinTrading_RL_tier3' -Description 'RL Tier3 Weekly Sun 04:00' -Action $a3 -Trigger $t3 -Settings $s3 -Force | Out-Null
Write-Host '[OK] tier3 - 매주 일요일 04:00'

Write-Host ''
Write-Host '=== 등록 확인 ==='
Get-ScheduledTask -TaskName 'CoinTrading_RL_*' | Format-Table TaskName, State -AutoSize
