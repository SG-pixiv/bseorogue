# SPDX-FileCopyrightText: 2026 SG
# SPDX-License-Identifier: AGPL-3.0-only
# 블서로그 AI 도트 환경 1단계: ComfyUI 포터블 (NVIDIA) 을 E:\AI 에 설치
# 하는 일: E 공간 · 그래픽 카드 확인 → GitHub 공식 최신 ComfyUI 포터블 받기 → 7-Zip 공식 7zr.exe 로 E:\AI 에 풀기 → 확인
# C 드라이브에는 아무것도 저장하지 않아요. 기록은 이 폴더의 log-1.txt
$ErrorActionPreference = 'Stop'
$ProgressPreference = 'SilentlyContinue'
[Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12
# 파이썬 · 7zr 이 오류 줄(stderr)을 써도 스크립트가 멈추지 않게
function Run($exe) { $old = $ErrorActionPreference; $ErrorActionPreference = 'Continue'; try { & $exe @args 2>&1 | ForEach-Object { "$_" } } finally { $ErrorActionPreference = $old } }
$Root = 'E:\AI'
$Dl = Join-Path $Root '_download'
$Log = Join-Path $PSScriptRoot 'log-1.txt'
New-Item -ItemType Directory -Force -Path $Dl | Out-Null
function Say($t) { Write-Host $t; Add-Content -Path $Log -Value $t -Encoding UTF8 }
Set-Content -Path $Log -Value ("시작 " + (Get-Date -Format 'yyyy-MM-dd HH:mm:ss')) -Encoding UTF8
try {
  $e = Get-PSDrive E
  Say ("E 남은 공간: {0:N1} GB" -f ($e.Free / 1GB))
  if ($e.Free -lt 40GB) { Say "!! E 공간이 40GB 보다 적어요 (ComfyUI 7GB + 모델 약 23GB)" }
  Say ("윈도우: " + [System.Environment]::OSVersion.VersionString)
  try { Say ("그래픽: " + ((& nvidia-smi --query-gpu=name,driver_version,memory.total --format=csv,noheader) -join ' ')) } catch { Say "!! nvidia-smi 실행 실패" }

  $Dest = Join-Path $Root 'ComfyUI_windows_portable'
  if (Test-Path (Join-Path $Dest 'run_nvidia_gpu.bat')) {
    Say "이미 풀려 있어요: $Dest (받기 · 풀기 건너뜀)"
  } else {
    $rel = Invoke-RestMethod 'https://api.github.com/repos/Comfy-Org/ComfyUI/releases/latest' -Headers @{ 'User-Agent' = 'bseorogue-ai-setup' }
    Say ("ComfyUI 최신: " + $rel.tag_name + " (" + $rel.published_at + ")")
    foreach ($a in $rel.assets) { Say ("  파일 {0}  {1:N2} GB" -f $a.name, ($a.size / 1GB)) }
    $asset = $rel.assets | Where-Object { $_.name -eq 'ComfyUI_windows_portable_nvidia.7z' } | Select-Object -First 1
    if (-not $asset) { $asset = $rel.assets | Where-Object { $_.name -like '*portable_nvidia*.7z' } | Select-Object -First 1 }
    if (-not $asset) { throw "NVIDIA 포터블 파일을 못 찾았어요" }
    $z = Join-Path $Dl $asset.name
    Say ("받는 중: " + $asset.name + " → " + $z)
    & curl.exe -L --retry 5 --retry-delay 3 -C - -o $z $asset.browser_download_url
    if ((Get-Item $z).Length -ne $asset.size) { throw ("받은 크기가 달라요: " + (Get-Item $z).Length + " / " + $asset.size) }
    Say "받기 끝 (크기 맞음)"
    $sz = Join-Path $Dl '7zr.exe'
    if (-not (Test-Path $sz)) { & curl.exe -L --retry 5 -o $sz 'https://www.7-zip.org/a/7zr.exe' }
    Say "푸는 중 (몇 분 걸려요)..."
    & $sz x $z ("-o" + $Root) -y -bso0 -bsp1
    if ($LASTEXITCODE -ne 0) { throw "풀기 실패 (7zr 코드 $LASTEXITCODE)" }
    $inner = Get-ChildItem $Root -Directory | Where-Object { Test-Path (Join-Path $_.FullName 'run_nvidia_gpu.bat') } | Select-Object -First 1
    if (-not $inner) { throw "풀었는데 run_nvidia_gpu.bat 이 없어요" }
    if ($inner.FullName -ne $Dest) { Rename-Item $inner.FullName 'ComfyUI_windows_portable' }
    Say "풀기 끝: $Dest"
    Add-Type -AssemblyName Microsoft.VisualBasic
    [Microsoft.VisualBasic.FileIO.FileSystem]::DeleteFile($z, 'OnlyErrorDialogs', 'SendToRecycleBin')
    Say "받은 압축 파일은 휴지통으로 보냈어요 (휴지통을 비우면 약 2GB 생겨요)"
  }
  $py = Join-Path $Dest 'python_embeded\python.exe'
  $ver = Get-Content (Join-Path $Dest 'ComfyUI\comfyui_version.py') -ErrorAction SilentlyContinue | Select-String '__version__'
  Say ("ComfyUI 버전: " + $ver)
  $chk = Run $py -c "import sys,torch;print('python',sys.version.split()[0],'| torch',torch.__version__,'| cuda',torch.version.cuda,'| gpu',torch.cuda.is_available(),torch.cuda.get_device_name(0) if torch.cuda.is_available() else '')" 2>&1
  Say ("파이썬 확인: " + ($chk -join ' '))
  $hf = Run $py -c "import huggingface_hub;print(huggingface_hub.__version__)" 2>&1
  Say ("huggingface_hub: " + ($hf -join ' '))
  $e = Get-PSDrive E
  Say ("끝. E 남은 공간: {0:N1} GB" -f ($e.Free / 1GB))
  Say "DONE"
} catch {
  Say ("!! 멈춤: " + $_.Exception.Message)
  Say "FAILED"
}
