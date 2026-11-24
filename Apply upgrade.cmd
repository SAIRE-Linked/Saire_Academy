@echo off
setlocal
set "PROJECT=%USERPROFILE%\Documents\Saire_Academy"
if exist "%PROJECT%\.saire_acad_env\Scripts\python.exe" (
  "%PROJECT%\.saire_acad_env\Scripts\python.exe" "%~dp0apply_upgrade.py" "%PROJECT%" --apply
) else (
  python "%~dp0apply_upgrade.py" "%PROJECT%" --apply
)
pause
