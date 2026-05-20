@echo off
REM Installation script for pyvm (Python Version Manager)
REM Works on Windows

echo ==================================================
echo   Installing Python Version Manager (pyvm)
echo ==================================================
echo.

REM Check if pip is available
where pip >nul 2>nul
if %errorlevel% neq 0 (
    where pip3 >nul 2>nul
    if %errorlevel% neq 0 (
        echo ERROR: pip is not installed.
        echo Please install Python from https://www.python.org/downloads/
        echo Make sure to check "Add Python to PATH" during installation.
        pause
        exit /b 1
    ) else (
        set PIP_CMD=pip3
    )
) else (
    set PIP_CMD=pip
)

echo Installing pyvm and dependencies...
echo.

REM Install in editable mode (handles all deps from pyproject.toml)
%PIP_CMD% install -e .

if %errorlevel% equ 0 (
    echo.
    echo ==================================================
    echo   Installation successful!
    echo ==================================================
    echo.
    echo You can now use the 'pyvm' command:
    echo   pyvm          - Check Python version
    echo   pyvm check    - Check Python version
    echo   pyvm update   - Update Python
    echo   pyvm info     - Show system info
    echo   pyvm --help   - Show help
    echo.
    echo Note: You may need to restart your command prompt
    echo       for the changes to take effect.
    echo.
) else (
    echo.
    echo Installation failed.
    echo Please check the error messages above.
    pause
    exit /b 1
)

pause
