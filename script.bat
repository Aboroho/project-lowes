@echo off
:loop

python scrap.py
set exit_code=%ERRORLEVEL%

REM Check if the exit code matches 1
if %exit_code% equ 1 (
    echo Python program exited with code 1, closing...
    exit /b
) else (
    echo Python program restarting...
)

goto loop
