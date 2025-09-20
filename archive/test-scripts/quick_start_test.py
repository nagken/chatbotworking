import subprocess
import sys
import os

# Set working directory
os.chdir(r'c:\cvssep9')

# Command to run
cmd = [
    r'C:\Program Files\Python\311\python.exe',
    '-m', 'uvicorn',
    'app.main:app',
    '--host', '0.0.0.0',
    '--port', '8000',
    '--reload'
]

print(f"Running: {' '.join(cmd)}")
print(f"Working directory: {os.getcwd()}")

try:
    result = subprocess.run(cmd, capture_output=True, text=True, timeout=10)
    print(f"Return code: {result.returncode}")
    print(f"STDOUT: {result.stdout}")
    print(f"STDERR: {result.stderr}")
except subprocess.TimeoutExpired:
    print("Server started successfully (timeout after 10 seconds)")
except Exception as e:
    print(f"Error: {e}")
