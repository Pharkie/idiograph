@echo off
REM Idiograph's command line from source, Windows: the venv's python running cli.py, from wherever
REM it is called. The venv is the one beside this file, as run.bat's first run makes it, and else the
REM one two folders up, at the root of the repo the folder sits in. See docs\agents.md.
setlocal
set "HERE=%~dp0"
set "PY=python"
if exist "%HERE%..\..\.venv\Scripts\python.exe" set "PY=%HERE%..\..\.venv\Scripts\python.exe"
if exist "%HERE%.venv\Scripts\python.exe" set "PY=%HERE%.venv\Scripts\python.exe"
"%PY%" "%HERE%cli.py" %*
exit /b %errorlevel%
