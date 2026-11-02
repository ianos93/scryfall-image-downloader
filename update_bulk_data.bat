@echo off
rem Double-click to rebuild data\prints_index.json and data\bulk_manifest.json.
setlocal
cd /d "%~dp0"

set "PY="
where py >nul 2>nul && set "PY=py -3"
if not defined PY (
  where python >nul 2>nul && set "PY=python"
)
if not defined PY (
  echo Python 3.7 or newer is needed and was not found.
  echo Get it from https://www.python.org/downloads/ and tick "Add python.exe to PATH".
  goto end
)

%PY% update_bulk_data.py
if errorlevel 1 echo.& echo The update did not finish. See the message above.

:end
echo.
pause
