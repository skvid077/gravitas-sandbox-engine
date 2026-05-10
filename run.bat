@echo off
if not exist venv (
    python -m venv venv
)

call venv\Scripts\activate
pip install -r requirements.txt
set PYTHONPATH=%PYTHONPATH%;%cd%\src
python main.py
pause
