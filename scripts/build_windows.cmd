@echo off
rem cmd.exe is not subject to PowerShell's AllSigned / Restricted policy.
rem This only bypasses policy for this one script; it does not change the machine.
cd /d "%~dp0\.."
powershell.exe -NoProfile -ExecutionPolicy Bypass -File "%~dp0build_windows.ps1" %*
exit /b %ERRORLEVEL%
