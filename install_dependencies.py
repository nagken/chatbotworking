#!/usr/bin/env python3
"""
Install dependencies for CVS Pharmacy Knowledge Assist
"""

import subprocess
import sys
import os

def run_pip_install(packages):
    """Install packages using pip"""
    python_path = r"C:\Program Files\Python\311\python.exe"
    
    for package in packages:
        print(f"Installing {package}...")
        try:
            result = subprocess.run([
                python_path, "-m", "pip", "install", package
            ], capture_output=True, text=True, check=True)
            print(f"✅ Successfully installed {package}")
        except subprocess.CalledProcessError as e:
            print(f"❌ Failed to install {package}: {e}")
            print(f"Error output: {e.stderr}")

def main():
    print("=" * 50)
    print("CVS Pharmacy Knowledge Assist - Dependency Installer")
    print("=" * 50)
    
    # Change to script directory
    script_dir = os.path.dirname(os.path.abspath(__file__))
    os.chdir(script_dir)
    
    # Critical packages that are often missing
    critical_packages = [
        "PyPDF2==3.0.1",
        "python-docx==0.8.11", 
        "fastapi==0.104.1",
        "uvicorn[standard]==0.24.0",
        "sqlalchemy==2.0.23",
        "pydantic==2.5.0",
        "python-dotenv==1.0.0",
        "jinja2==3.1.2",
        "aiofiles==23.2.1"
    ]
    
    print("Installing critical packages...")
    run_pip_install(critical_packages)
    
    print("\nInstalling all requirements from requirements.txt...")
    try:
        python_path = r"C:\Program Files\Python\311\python.exe"
        subprocess.run([
            python_path, "-m", "pip", "install", "-r", "requirements.txt"
        ], check=True)
        print("✅ All requirements installed successfully")
    except subprocess.CalledProcessError as e:
        print(f"❌ Some packages may have failed to install: {e}")
    
    print("\n" + "=" * 50)
    print("Installation complete!")
    print("You can now start the server with:")
    print("  start_localhost_only.bat")
    print("or")
    print('  "C:/Program Files/Python/311/python.exe" start_server_python.py')
    print("=" * 50)

if __name__ == "__main__":
    main()
