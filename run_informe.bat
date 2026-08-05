@echo off
REM Genera el informe PDF, las figuras y las exportaciones de la practica.
cd /d "%~dp0"
echo.
echo Generando informe de la Practica Calificada 02...
echo.
python main.py
echo.
echo Informe disponible en: informe\INFORME_PRACTICA_02.pdf
if exist "informe\INFORME_PRACTICA_02.pdf" start "" "informe\INFORME_PRACTICA_02.pdf"
pause
