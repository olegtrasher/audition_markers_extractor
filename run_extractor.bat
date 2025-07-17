@echo off
chcp 65001
title Извлечение маркеров из SESX файлов

echo ========================================
echo    Извлечение маркеров из SESX файлов
echo ========================================
echo.

REM Запускаем скрипт
python markers_extractor.py

echo.
echo Нажмите любую клавишу для выхода...
pause >nul 