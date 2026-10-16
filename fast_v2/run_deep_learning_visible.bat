@echo off
setlocal
set "STUDY_AI_PROFILE=settings.deep_learning.json"
call "%~dp0run_fast_solver_visible.bat" %*
endlocal
