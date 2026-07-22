@echo off
title Mutual Fund RAG Chatbot - Phase 8 Voice I/O

echo Checking virtual environments...
if exist .venv\Scripts\activate.bat goto ACTIVATE_DOT_VENV
if exist venv\Scripts\activate.bat goto ACTIVATE_VENV
goto START_APP

:ACTIVATE_DOT_VENV
echo Activating virtual environment .venv...
call .venv\Scripts\activate.bat
goto START_APP

:ACTIVATE_VENV
echo Activating virtual environment venv...
call venv\Scripts\activate.bat
goto START_APP

:START_APP
echo Starting Streamlit app...
py -m streamlit run phase_6_streamlit_app/app.py
if %ERRORLEVEL% EQU 0 goto END

echo.
echo Streamlit execution using 'py' failed. Trying 'python' launcher...
python -m streamlit run phase_6_streamlit_app/app.py
if %ERRORLEVEL% EQU 0 goto END

echo.
echo Streamlit execution using 'python' failed. Trying direct 'streamlit' command...
streamlit run phase_6_streamlit_app/app.py
if %ERRORLEVEL% EQU 0 goto END

echo.
echo Error: Failed to start Streamlit app. Please ensure streamlit is installed in your python environment.
pause

:END

