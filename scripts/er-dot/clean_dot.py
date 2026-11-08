# SPDX-FileCopyrightText: 2026 SG
# SPDX-License-Identifier: AGPL-3.0-only
"""
AI 가 만든 도트 밑그림 → 블서로그 실험체 도트 규격으로 정리 (docs/dot-guide, 도트 가이드 문서)

하는 일: 배경 지우기 → 캐릭터만 잘라서 칸에 맞게 줄이기 → 반투명 없애기 → 15색으로 묶기 →
         아래 가운데 정렬 (발끝은 맨 아래 1px 위) → 1배 PNG + 8배 확대 미리보기
그다음은 사람이 손으로: 외곽선 · 눈 · 손 · 무기 다듬기 (가이드의 검사 목록)

쓰는 법:
  python3 scripts/er-dot/clean_dot.py <AI 그림.png> <나올 이름.png> [--icon] [--colors 15] [--height 72]
  --icon      아이콘 (40×30, 위쪽을 잘라 써요)
  --height N  전투 그림 캐릭터 키 (기본 72px, 칸은 80×80)
배경: 투명이면 그대로, 아니면 네 귀퉁이 색을 배경으로 보고 지워요 (AI 에게 단색 배경, 예: #ff00ff 를 부탁하면 깔끔해요)
"""
import sys
from collections import Counter

from PIL import Image


def arg(name, default):
    return type(default)(sys.argv[sys.argv.index(name) + 1]) if name in sys.argv else default


def remove_background(im: Image.Image, tol: int = 40) -> Image.Image:
    im = im.convert("RGBA")
    a = im.getchannel("A")
    if a.getextrema()[0] < 250:  # 이미 투명 배경
        return im
    w, h = im.size
    corners = [im.getpixel(p)[:3] for p in ((0, 0), (w - 1, 0), (0, h - 1), (w - 1, h - 1))]
    bg = Counter(corners).most_common(1)[0][0]
    px = im.load()
    for y in range(h):
        for x in range(w):
            r, g, b, _ = px[x, y]
            if abs(r - bg[0]) + abs(g - bg[1]) + abs(b - bg[2]) <= tol:
                px[x, y] = (0, 0, 0, 0)
    return im


def fit(im: Image.Image, max_w: int, max_h: int) -> Image.Image:
    box = im.getchannel("A").point(lambda v: 255 if v >= 128 else 0).getbbox()
    if box:
        im = im.crop(box)
    s = min(max_w / im.width, max_h / im.height)
    size = (max(1, round(im.width * s)), max(1, round(im.height * s)))
    # 줄일 때는 BOX (AI 그림의 픽셀 격자가 어긋나 있어도 평균으로 깔끔하게)
    return im.resize(size, Image.BOX)


def quantize(im: Image.Image, colors: int) -> Image.Image:
    alpha = im.getchannel("A").point(lambda v: 255 if v >= 128 else 0)  # 반투명 없애기
    rgb = Image.new("RGB", im.size, (0, 0, 0))
    rgb.paste(im.convert("RGB"), mask=alpha)
    q = rgb.quantize(colors=colors + 1, method=Image.Quantize.MEDIANCUT, dither=Image.Dither.NONE).convert("RGB")
    out = q.convert("RGBA")
    out.putalpha(alpha)
    # 투명 자리 색은 0 으로 (색 수 세기에 안 들어가게) + 혼자 떨어진 점 지우기 (위아래양옆에 이웃이 없는 점)
    px = out.load()
    w, h = out.size
    lone = [(x, y) for y in range(h) for x in range(w) if px[x, y][3]
            and not any(0 <= x + dx < w and 0 <= y + dy < h and px[x + dx, y + dy][3] for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)))]
    for y in range(h):
        for x in range(w):
            if px[x, y][3] == 0:
                px[x, y] = (0, 0, 0, 0)
    for x, y in lone:
        px[x, y] = (0, 0, 0, 0)
    return out


def main():
    if len(sys.argv) < 3:
        sys.exit(__doc__)
    src, dst = sys.argv[1], sys.argv[2]
    icon = "--icon" in sys.argv
    colors = arg("--colors", 15)
    im = remove_background(Image.open(src))
    if icon:
        cw, ch = 40, 30
        part = fit(im, 10_000, 10_000)
        part = part.crop((0, 0, part.width, min(part.height, round(part.width * 0.9))))  # 머리 ~ 가슴
        part = fit(part, cw, ch - 1)
        canvas = Image.new("RGBA", (cw, ch), (0, 0, 0, 0))
        canvas.alpha_composite(part, ((cw - part.width) // 2, ch - part.height))
    else:
        cw = ch = 80
        part = fit(im, cw, arg("--height", 72))
        canvas = Image.new("RGBA", (cw, ch), (0, 0, 0, 0))
        canvas.alpha_composite(part, ((cw - part.width) // 2, ch - 1 - part.height))
    out = quantize(canvas, colors)
    out.save(dst)
    used = len({p[:3] for p in out.get_flattened_data() if p[3]}) if hasattr(out, "get_flattened_data") else len({p[:3] for p in out.getdata() if p[3]})
    zoom = dst.rsplit(".", 1)[0] + "-zoom8.png"
    out.resize((cw * 8, ch * 8), Image.NEAREST).save(zoom)
    print(f"{dst}: {cw}×{ch}, 색 {used}개 (투명 빼고), 확대 미리보기 {zoom}")


if __name__ == "__main__":
    main()
