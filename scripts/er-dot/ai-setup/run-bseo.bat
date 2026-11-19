@echo off
REM SPDX-FileCopyrightText: 2026 SG
REM SPDX-License-Identifier: AGPL-3.0-only
REM bseorogue: start ComfyUI for dot work (12GB VRAM, models on a slow disk) - docs 4-29
REM  --disable-dynamic-vram : load models into RAM once (64GB RAM), no disk-backed paging
REM  --disable-assets       : no rescanning of the fan kit (28k files) after every image
REM  --disable-auto-launch  : do not open a browser
REM  --port 8189           : own port, so it can start even while run_nvidia_gpu.bat (8188) is still open
title ComfyUI (bseorogue)
cd /d "%~dp0"
if not exist python_embeded\python.exe cd /d E:\AI\ComfyUI_windows_portable
.\python_embeded\python.exe -s ComfyUI\main.py --windows-standalone-build --disable-assets --disable-dynamic-vram --high-ram --disable-auto-launch --port 8189
pause
