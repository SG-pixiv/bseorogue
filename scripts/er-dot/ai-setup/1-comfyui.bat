@echo off
REM SPDX-FileCopyrightText: 2026 SG
REM SPDX-License-Identifier: AGPL-3.0-only
chcp 65001 >nul
title bseorogue AI setup 1 - ComfyUI
powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp01-comfyui.ps1"
echo.
echo You can close this window.
pause
