@echo off
REM Launches start-all.ps1 regardless of the machine PowerShell execution policy.
REM Some systems set LocalMachine to AllSigned, which blocks unsigned local
REM scripts. -ExecutionPolicy Bypass applies to this process only and changes
REM nothing on the machine.
powershell.exe -NoProfile -ExecutionPolicy Bypass -File "%~dp0start-all.ps1" %*
if errorlevel 1 pause
