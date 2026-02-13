@echo off
chcp 65001
echo Checking Python installations...
echo.

echo 1. Checking 'py' command:
py --version
where py

echo.
echo 2. Checking 'python' command:
python --version 2>nul || echo python not found
where python 2>nul || echo Not found

echo.
echo 3. Checking PyInstaller:
py -c "import pyinstaller; print('PyInstaller found via py')" 2>nul || echo PyInstaller not found via py
python -c "import pyinstaller; print('PyInstaller found via python')" 2>nul || echo PyInstaller not found via python

echo.
echo 4. Python paths in PATH:
echo %PATH% | python -c "import sys; [print(p) for p in sys.path if 'python' in p.lower()]" 2>nul || echo Could not check

pause