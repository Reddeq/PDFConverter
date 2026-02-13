import os
import sys
import subprocess
import shutil
from pathlib import Path

def get_python_exe():
    """Get the correct Python executable"""
    # Попробуем разные варианты
    python_commands = ['python', 'py', 'python3']
    
    for cmd in python_commands:
        try:
            # Проверяем, есть ли команда
            result = subprocess.run([cmd, '--version'], 
                                  capture_output=True, text=True)
            if result.returncode == 0:
                # Получаем полный путь
                if sys.platform == 'win32':
                    where_result = subprocess.run(['where', cmd], 
                                                 capture_output=True, text=True)
                else:
                    where_result = subprocess.run(['which', cmd], 
                                                 capture_output=True, text=True)
                
                if where_result.returncode == 0:
                    python_path = where_result.stdout.strip().split('\n')[0]
                    print(f"✓ Found Python: {python_path}")
                    return python_path
        except:
            continue
    
    # Если не нашли, используем текущий
    return sys.executable

def install_pyinstaller(python_exe):
    """Install PyInstaller using specific Python"""
    print(f"\nInstalling PyInstaller using: {python_exe}")
    
    cmd = [python_exe, '-m', 'pip', 'install', 'pyinstaller', '--user']
    
    try:
        result = subprocess.run(cmd, capture_output=True, text=True)
        if result.returncode == 0:
            print("✓ PyInstaller installed")
            return True
        else:
            print(f"✗ Failed to install PyInstaller: {result.stderr}")
            return False
    except Exception as e:
        print(f"✗ Error installing PyInstaller: {e}")
        return False

def build_exe(python_exe):
    """Build the executable"""
    print("\n" + "="*60)
    print("Building PDFConverter.exe")
    print("="*60)
    
    # Путь к poppler
    poppler_path = r"E:\Soft\poppler\Library\bin"
    
    if not os.path.exists(poppler_path):
        print(f"✗ Poppler not found at: {poppler_path}")
        
        # Ищем в других местах
        possible_paths = [
            r"C:\poppler\Library\bin",
            r"D:\poppler\Library\bin",
            os.path.join(os.path.expanduser("~"), "poppler", "Library", "bin")
        ]
        
        for path in possible_paths:
            if os.path.exists(path):
                poppler_path = path
                print(f"✓ Found poppler at: {poppler_path}")
                break
        else:
            print("✗ Poppler not found anywhere!")
            return False
    
    # Команда сборки
    cmd = [
        python_exe,
        '-m', 'pyinstaller',
        '--onefile',
        '--noconsole',
        '--name=PDFConverter',
        f'--add-data={poppler_path};poppler',
        '--hidden-import=PIL._imaging',
        '--hidden-import=PIL._imagingtk',
        '--hidden-import=PIL._webp',
        '--hidden-import=pdf2image',
        '--clean',
        'PDFConverter.py'
    ]
    
    print(f"\nRunning PyInstaller...")
    print(f"Command: {' '.join(cmd[:5])} ...")
    
    try:
        # Запускаем сборку
        process = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            encoding='utf-8',
            errors='replace'
        )
        
        # Выводим вывод в реальном времени
        while True:
            output = process.stdout.readline()
            if output == '' and process.poll() is not None:
                break
            if output:
                print(output.strip())
        
        # Получаем результат
        return_code = process.poll()
        
        if return_code == 0:
            print("\n✓ Build successful!")
            return True
        else:
            print("\n✗ Build failed!")
            # Читаем stderr
            stderr_output = process.stderr.read()
            if stderr_output:
                print("Errors:", stderr_output[-1000:])
            return False
            
    except Exception as e:
        print(f"✗ Error during build: {e}")
        import traceback
        traceback.print_exc()
        return False

def create_portable_package():
    """Create portable package"""
    print("\n" + "="*60)
    print("Creating portable package")
    print("="*60)
    
    dist_dir = Path("dist")
    portable_dir = dist_dir / "PDFConverter_Portable"
    
    # Очищаем старую папку
    if portable_dir.exists():
        shutil.rmtree(portable_dir)
    
    portable_dir.mkdir(parents=True, exist_ok=True)
    
    # Копируем EXE
    exe_src = dist_dir / "PDFConverter.exe"
    if exe_src.exists():
        exe_dst = portable_dir / "PDFConverter.exe"
        shutil.copy2(exe_src, exe_dst)
        print(f"✓ Copied: {exe_dst}")
        
        # Создаем README
        readme_content = """PDF Converter - Portable Edition
===============================

This is a standalone application. No installation required!

HOW TO USE:
1. Run PDFConverter.exe
2. Select PDF folder (files must contain '-ru-en-P1' in names)
3. Select reference images folder
4. Click Convert

FEATURES:
• Converts PDF to images
• Matches reference dimensions exactly
• Preserves DPI/resolution
• Supports multiple formats (PNG, JPEG, BMP, TIFF)
• User-friendly interface

System requirements:
• Windows 7 or later
• 50 MB free disk space

Enjoy!
"""
        
        (portable_dir / "README.txt").write_text(readme_content, encoding='utf-8')
        print("✓ Created README.txt")
        
        # BAT файл для запуска
        bat_content = """@echo off
chcp 65001
echo PDF Converter Portable
echo ======================
echo.
echo Starting application...
echo.
PDFConverter.exe
pause
"""
        
        (portable_dir / "Start.bat").write_text(bat_content, encoding='utf-8')
        print("✓ Created Start.bat")
        
        # Показываем результат
        exe_size = exe_src.stat().st_size / 1024 / 1024
        print(f"\n✓ Package created successfully!")
        print(f"  Location: {portable_dir}")
        print(f"  EXE size: {exe_size:.2f} MB")
        
        return True
    else:
        print(f"✗ EXE file not found: {exe_src}")
        return False

def main():
    """Main function"""
    print("="*70)
    print("PDF Converter - Build Tool")
    print("="*70)
    
    # Получаем правильный Python
    python_exe = get_python_exe()
    print(f"\nUsing Python: {python_exe}")
    
    # Проверяем/устанавливаем PyInstaller
    try:
        # Проверяем, установлен ли уже PyInstaller
        check_cmd = [python_exe, '-c', 'import pyinstaller; print("OK")']
        result = subprocess.run(check_cmd, capture_output=True, text=True)
        
        if "OK" in result.stdout:
            print("✓ PyInstaller already installed")
        else:
            if not install_pyinstaller(python_exe):
                return
    except:
        if not install_pyinstaller(python_exe):
            return
    
    # Собираем EXE
    if build_exe(python_exe):
        # Создаем портативную версию
        create_portable_package()
        
        print("\n" + "="*70)
        print("BUILD COMPLETE!")
        print("="*70)
        print("\nYour portable application is ready!")
        print("\nTo distribute:")
        print("1. Copy the 'dist\\PDFConverter_Portable' folder")
        print("2. Send it to any Windows computer")
        print("3. Run PDFConverter.exe - no installation needed!")
    else:
        print("\n" + "="*70)
        print("BUILD FAILED")
        print("="*70)
    
    print("\n" + "="*70)
    input("Press Enter to exit...")

if __name__ == "__main__":
    main()