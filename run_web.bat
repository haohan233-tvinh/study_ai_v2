@echo off
setlocal
set "STUDY_AI_PROFILE=settings.web.json"
call "%~dp0fast_v2\run_fast_solver.bat" %*
endlocal
