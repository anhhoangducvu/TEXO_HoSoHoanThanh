@echo off
chcp 65001 >nul
cd /d "%~dp0"
echo === TEXO - Kiem tra Ho so chat luong du an ===
python -m pip install -q -r requirements.txt
python -m streamlit run app.py
pause
