@echo off
setlocal
set ROOT=%~dp0
if "%~1"=="" (
  echo sdd-gov
  echo   g check --budget
  echo   g check --changed
  echo   g context --task T-0001-01
  echo   g resume --spec 1
  echo   g plan --spec 1
  echo   g emit all
  echo   g emit registry --by-epic
  echo   g reserve --size 10 --owner "team"
  echo   g metrics --out .local/tmp/metrics.json
  echo   g metrics
  echo   g doctor
  echo   g upgrade --from ^<path^>
  exit /b 0
)
python "%ROOT%governance\scripts\govern.py" %* --root "%ROOT%"
