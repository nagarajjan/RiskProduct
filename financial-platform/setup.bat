@echo off
setlocal

echo Checking for Python 3.13...
where python >nul 2>nul
if %errorlevel% neq 0 (
    echo Python not found. Please install Python 3.13 from python.org and ensure it's in your PATH.
    goto :end
)

python --version | findstr "3.13." >nul 2>nul
if %errorlevel% neq 0 (
    echo Warning: Python 3.13 not found. Using the default Python installation.
    echo To use Python 3.13, ensure it is in your PATH.
)

echo Creating and activating virtual environment...
python -m venv venv
call venv\Scripts\activate.bat

echo Installing dependencies...
pip install langchain openai faiss-cpu pandas Flask mcp Flask-Cors python-dotenv

echo Environment setup complete.
echo You can now start the servers.

:end
endlocal
