@echo off
chcp 65001
title Building PDF Converter - Auto Detect
color 0A

echo ========================================
echo    Building PDF Converter EXE
echo ========================================

echo.
echo Step 1: Auto-detecting Python...

REM Вариант 1: Python из Local\Python\bin (ваш рабочий)
set "PYTHON1=C:\Users\%USERNAME%\AppData\Local\Python\bin\python.exe"

REM Вариант 2: Python из Local\Programs (стандартная установка)
set "PYTHON2=C:\Users\%USERNAME%\AppData\Local\Programs\Python\Python314\python.exe"

REM Вариант 3: Python из Program Files
set "PYTHON3=C:\Program Files\Python314\python.exe"

set "PYTHON_EXE="

for %%P in ("%PYTHON1%" "%PYTHON2%" "%PYTHON3%") do (
    if exist %%P (
        set "PYTHON_EXE=%%P"
        goto :found
    )
)

:found
if not defined PYTHON_EXE (
    echo ERROR: No Python installation found!
    echo Searched in:
    echo   %PYTHON1%
    echo   %PYTHON2%
    echo   %PYTHON3%
    pause
    exit /b 1
)

echo Found Python at: %PYTHON_EXE%
"%PYTHON_EXE%" --version

echo.
echo Step 2: Setting up PyInstaller...

REM Проверяем установлен ли PyInstaller
"%PYTHON_EXE%" -c "import pyinstaller" 2>nul
if errorlevel 1 (
    echo Installing PyInstaller...
    "%PYTHON_EXE%" -m pip install pyinstaller --user
) else (
    echo PyInstaller already installed.
)

echo.
echo Step 3: Building...

set "POPPLER=E:\Soft\poppler\Library\bin"

if not exist "%POPPLER%" (
    echo WARNING: Poppler not found!
    echo Building without poppler data...
    "%PYTHON_EXE%" -m pyinstaller --onefile --noconsole --name PDFConverter --hidden-import PIL._imaging --hidden-import PIL._imagingtk --hidden-import PIL._webp PDFConverter.py
) else (
    echo Using poppler from: %POPPLER%
    "%PYTHON_EXE%" -m pyinstaller --onefile --noconsole --name PDFConverter --add-data "%POPPLER%;poppler" --hidden-import PIL._imaging --hidden-import PIL._imagingtk --hidden-import PIL._webp --clean PDFConverter.py
)

echo.
if exist "dist\PDFConverter.exe" (
    echo ========================================
    echo    BUILD SUCCESSFUL!
    echo ========================================
    echo.
    
    REM Создаем простую портативную версию
    echo Creating simple distribution...
    mkdir "PDFConverter_Portable" 2>nul
    copy "dist\PDFConverter.exe" "PDFConverter_Portable\" >nul
    
    if exist "%POPPLER%" (
        mkdir "PDFConverter_Portable\poppler" 2>nul
        xcopy "%POPPLER%\*.*" "PDFConverter_Portable\poppler\" /Y /E >nul
        echo ✓ Included poppler in package
    )
    
    echo @echo off > "PDFConverter_Portable\START.bat"
    echo echo. >> "PDFConverter_Portable\START.bat"
    echo echo PDF Converter Portable >> "PDFConverter_Portable\START.bat"
    echo echo ====================== >> "PDFConverter_Portable\START.bat"
    echo echo. >> "PDFConverter_Portable\START.bat"
    echo start PDFConverter.exe >> "PDFConverter_Portable\START.bat"
    echo pause >> "PDFConverter_Portable\START.bat"
    
    for /f "tokens=*" %%i in ('powershell -Command "(Get-Item 'dist\PDFConverter.exe').Length / 1MB"') do (
        set "SIZE=%%i"
    )
    
    echo.
    echo ✓ EXE created: dist\PDFConverter.exe (%SIZE% MB)
    echo ✓ Portable version: PDFConverter_Portable\
    echo.
    echo READY TO DISTRIBUTE!
    
) else (
    echo ========================================
    echo    BUILD FAILED
    echo ========================================
    echo.
    echo Try running manually:
    echo "%PYTHON_EXE%" -m pyinstaller --onefile PDFConverter.py
)

echo.
pause