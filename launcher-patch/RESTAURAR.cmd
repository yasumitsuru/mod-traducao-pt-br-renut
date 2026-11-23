@echo off
chcp 65001 >nul
setlocal
echo.
echo  Traducao PT-BR do launcher do reNut - restaurar
echo  Remove somente a copia renut.ptbr.exe gerada pelo patch.
echo.
set /p RENUT="Pasta do reNut (ou caminho do renut.exe): "
if "%RENUT%"=="" goto fim
where py >nul 2>nul
if errorlevel 1 (set "PY=python") else (set "PY=py -3")
%PY% -I "%~dp0aplicar.py" reverter --renut "%RENUT%"
:fim
echo.
pause