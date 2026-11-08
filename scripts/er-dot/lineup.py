# SPDX-FileCopyrightText: 2026 SG
# SPDX-License-Identifier: AGPL-3.0-only
"""
실험체 도트 나란히 보기 (도트 가이드 문서의 "다섯 명마다 나란히 검수")

80×80 전투 그림을 한 줄로 세우고 발밑 선 · 키 등급 선(S 60 · M 68 · L 74)을 그어서
키 · 외곽선 굵기 · 밝기가 서로 맞는지 한눈에 봐요.

쓰는 법:
  python3 scripts/er-dot/lineup.py <폴더 또는 PNG 여러 개> [-o 나올 이름.png]
  → 1배 그림과 4배 확대 그림(-zoom4.png)이 나와요. 아이콘(_icon)은 빼요.
"""
import sys
from pathlib import Path

from PIL import Image, ImageDraw

CELL, GAP = 80, 4
BG, CELL_BG = (40, 42, 54, 255), (58, 61, 77, 255)
LINES = {79: (255, 255, 255, 140), 80 - 1 - 60: (120, 200, 255, 90), 80 - 1 - 68: (120, 255, 160, 90), 80 - 1 - 74: (255, 180, 120, 90)}


def main():
    args = [a for a in sys.argv[1:] if a != "-o"]
    out = Path(sys.argv[sys.argv.index("-o") + 1]) if "-o" in sys.argv else Path("lineup.png")
    args = [a for a in args if Path(a) != out]
    files = []
    for a in args:
        p = Path(a)
        files += sorted(p.glob("*.png")) if p.is_dir() else [p]
    files = [f for f in files if "_icon" not in f.stem and "zoom" not in f.stem and f.resolve() != out.resolve()]
    if not files:
        sys.exit(__doc__)
    w = GAP + len(files) * (CELL + GAP)
    h = GAP * 2 + CELL
    sheet = Image.new("RGBA", (w, h), BG)
    d = ImageDraw.Draw(sheet)
    for i, f in enumerate(files):
        x0 = GAP + i * (CELL + GAP)
        d.rectangle((x0, GAP, x0 + CELL - 1, GAP + CELL - 1), fill=CELL_BG)
        for y, c in LINES.items():
            d.line((x0, GAP + y, x0 + CELL - 1, GAP + y), fill=c)
        im = Image.open(f).convert("RGBA")
        if im.size != (CELL, CELL):
            print(f"  주의: {f.name} 크기가 {im.width}×{im.height} (80×80 아님)")
        sheet.alpha_composite(im.crop((0, 0, CELL, CELL)), (x0, GAP))
    sheet.save(out)
    big = sheet.resize((w * 4, h * 4), Image.NEAREST)
    d = ImageDraw.Draw(big)
    for i, f in enumerate(files):
        d.text(((GAP + i * (CELL + GAP)) * 4 + 6, GAP * 4 + 4), f.stem, fill=(255, 255, 255, 230))
    zoom = out.with_name(out.stem + "-zoom4.png")
    big.save(zoom)
    print(f"{out} ({len(files)}명), 확대 {zoom}")
    print("선: 흰색 = 발밑 · 파랑 = S 60 · 초록 = M 68 · 주황 = L 74")


if __name__ == "__main__":
    main()
