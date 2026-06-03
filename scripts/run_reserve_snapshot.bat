@echo off
REM 길1 forward-OOS reserve vintage 일일 적재 (schtasks daily 대상, 2026-06-03 btn-Inv)
REM CM Community API live fetch → sys_time=오늘 vintage 동결 → reserve-pit-snapshots.parquet 누적
set PYTHONUTF8=1
set PYTHONIOENCODING=utf-8
cd /d D:\projects\Inv
set LOG=D:\projects\Inv\logs\reserve_snapshot.log
echo [%date% %time%] capture start >> "%LOG%"
"C:\Users\jsh86\AppData\Local\Programs\Python\Python312\python.exe" -m core.data.reserve_snapshot capture >> "%LOG%" 2>&1
echo [%date% %time%] capture done (exit %ERRORLEVEL%) >> "%LOG%"
