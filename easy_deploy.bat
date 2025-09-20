@echo off
echo ===============================================
echo  CVS Pharmacy Knowledge Assist - Easy Deploy
echo ===============================================
echo.

cd /d "%~dp0"

echo 🔧 Creating production-ready deployment...
echo.

REM Create deployment package
echo Creating deployment directory...
if not exist "cvs_deployment" mkdir cvs_deployment
if not exist "cvs_deployment\app" mkdir cvs_deployment\app
if not exist "cvs_deployment\static" mkdir cvs_deployment\static
if not exist "cvs_deployment\GyaniNuxeo" mkdir cvs_deployment\GyaniNuxeo

echo.
echo 📦 Copying application files...

REM Copy core files
xcopy app cvs_deployment\app /E /I /Y >nul
xcopy static cvs_deployment\static /E /I /Y >nul
xcopy GyaniNuxeo cvs_deployment\GyaniNuxeo /E /I /Y >nul

REM Copy config files
copy requirements.txt cvs_deployment\ >nul

echo.
echo 🚀 Creating startup script...

REM Create simple startup script
echo @echo off > cvs_deployment\START_CVS_PHARMACY.bat
echo echo =============================================== >> cvs_deployment\START_CVS_PHARMACY.bat
echo echo  CVS Pharmacy Knowledge Assist >> cvs_deployment\START_CVS_PHARMACY.bat
echo echo =============================================== >> cvs_deployment\START_CVS_PHARMACY.bat
echo echo. >> cvs_deployment\START_CVS_PHARMACY.bat
echo cd /d "%%~dp0" >> cvs_deployment\START_CVS_PHARMACY.bat
echo echo 📦 Installing Python dependencies... >> cvs_deployment\START_CVS_PHARMACY.bat
echo pip install -r requirements.txt >> cvs_deployment\START_CVS_PHARMACY.bat
echo echo. >> cvs_deployment\START_CVS_PHARMACY.bat
echo echo 🚀 Starting CVS Pharmacy Knowledge Assist... >> cvs_deployment\START_CVS_PHARMACY.bat
echo echo    Server will be available at: http://localhost:8080 >> cvs_deployment\START_CVS_PHARMACY.bat
echo echo    Login: john.smith@cvshealth.com / password123 >> cvs_deployment\START_CVS_PHARMACY.bat
echo echo. >> cvs_deployment\START_CVS_PHARMACY.bat
echo echo 💡 Press Ctrl+C to stop the server >> cvs_deployment\START_CVS_PHARMACY.bat
echo echo =============================================== >> cvs_deployment\START_CVS_PHARMACY.bat
echo echo. >> cvs_deployment\START_CVS_PHARMACY.bat
echo python -m uvicorn app.main:app --host 0.0.0.0 --port 8080 --reload >> cvs_deployment\START_CVS_PHARMACY.bat
echo pause >> cvs_deployment\START_CVS_PHARMACY.bat

echo.
echo 📖 Creating documentation...

REM Create simple README
echo # CVS Pharmacy Knowledge Assist > cvs_deployment\README.txt
echo. >> cvs_deployment\README.txt
echo ## How to Run >> cvs_deployment\README.txt
echo 1. Double-click START_CVS_PHARMACY.bat >> cvs_deployment\README.txt
echo 2. Wait for "Application startup complete" >> cvs_deployment\README.txt
echo 3. Open: http://localhost:8080/static/index.html >> cvs_deployment\README.txt
echo. >> cvs_deployment\README.txt
echo ## Login >> cvs_deployment\README.txt
echo Email: john.smith@cvshealth.com >> cvs_deployment\README.txt
echo Password: password123 >> cvs_deployment\README.txt
echo. >> cvs_deployment\README.txt
echo ## Features >> cvs_deployment\README.txt
echo - Chat interface with document search >> cvs_deployment\README.txt
echo - 1880+ pharmacy documents indexed >> cvs_deployment\README.txt
echo - Works without database (fallback mode) >> cvs_deployment\README.txt
echo - CVS Pharmacy branding and content >> cvs_deployment\README.txt
echo. >> cvs_deployment\README.txt
echo ## Support >> cvs_deployment\README.txt
echo If issues, check that Python 3.11+ is installed >> cvs_deployment\README.txt

echo.
echo ✅ Deployment package created!
echo.
echo ===============================================
echo  🎉 Ready to Deploy!
echo ===============================================
echo.
echo 📁 Package Location: %cd%\cvs_deployment
echo.
echo 🚀 To deploy:
echo   1. Copy 'cvs_deployment' folder to target machine
echo   2. Run START_CVS_PHARMACY.bat
echo   3. Open http://localhost:8080/static/index.html
echo.
echo 🧪 To test now:
echo   cd cvs_deployment
echo   START_CVS_PHARMACY.bat
echo.
echo Press any key to continue...
pause >nul
