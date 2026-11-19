@echo off
REM SPDX-FileCopyrightText: 2026 SG
REM SPDX-License-Identifier: AGPL-3.0-only
chcp 65001 >nul
title bseorogue AI setup 2 - FLUX 3 Image Klein models
set PYTHONIOENCODING=utf-8
set COMFY=E:\AI\ComfyUI_windows_portable
if not exist "%COMFY%\python_embeded\python.exe" (echo Run 1-comfyui.bat first & pause & exit /b 1)
"%COMFY%\python_embeded\python.exe" -s "%~dp0get_models.py"
if errorlevel 1 (echo. & echo Something went wrong - see log-2.txt & pause & exit /b 1)
echo.
echo Models ready. Starting ComfyUI in a new window (keep that window open)...
start "ComfyUI" /D "%COMFY%" run_nvidia_gpu.bat
pause
