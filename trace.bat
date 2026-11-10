@echo off
REM Trace's command line from source, Windows: the venv's python running cli.py as Trace, from
REM wherever it is called. The venv is found as idiograph.bat finds it. See docs\agents-trace.md.
setlocal
set "HERE=%~dp0"
set "PY=python"
if exist "%HERE%..\..\.venv\Scripts\python.exe" set "PY=%HERE%..\..\.venv\Scripts\python.exe"
if exist "%HERE%.venv\Scripts\python.exe" set "PY=%HERE%.venv\Scripts\python.exe"
"%PY%" "%HERE%cli.py" --app trace %*
exit /b %errorlevel%
