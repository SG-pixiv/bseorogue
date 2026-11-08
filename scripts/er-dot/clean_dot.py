# SPDX-FileCopyrightText: 2026 SG
# SPDX-License-Identifier: AGPL-3.0-only
"""
AI 가 만든 도트 밑그림 → 블서로그 실험체 도트 규격으로 정리 (docs/dot-guide, 도트 가이드 문서)

하는 일: 배경 지우기 → 캐릭터만 잘라서 칸에 맞게 줄이기 → 반투명 없애기 → 15색으로 묶기 →
         아래 가운데 정렬 (발끝은 맨 아래 1px 위) → 1배 PNG + 8배 확대 미리보기
그다음은 사람이 손으로: 외곽선 · 눈 · 손 · 무기 다듬기 (가이드의 검사 목록)

쓰는 법:
  python3 scripts/er-dot/clean_dot.py <AI 그림.png> <나올 이름.png> [--icon] [--size S|M|L] [--colors 15] [--no-lock]
  --icon      아이콘 (40×30, 위쪽을 잘라 써요)
  --size      키 등급: S 60px · M 68px (기본) · L 74px (칸은 80×80). --height N 으로 직접 줘도 돼요
  --no-lock   외곽선 2색 · 피부 3색을 팔레트 색으로 맞추지 않기 (기본은 맞춰요)
배경: 투명이면 그대로, 아니면 네 귀퉁이 색을 배경으로 보고 지워요. 가장자리 번짐도 지워요
      (AI 에게 단색 배경을 부탁: 보통 #ff00ff, 보라 · 분홍 옷이면 #00ff00)
"""
import sys
from collections import Counter

from PIL import Image


SIZES = {"S": 60, "M": 68, "L": 74}
# 모든 실험체가 같이 쓰는 색 (docs/dot-guide/palette-15.png): 외곽선 2 + 피부 3
LOCK = [(0x1A, 0x1C, 0x2C), (0x3B, 0x3F, 0x5C), (0xFF, 0xE0, 0xC8), (0xF2, 0xB8, 0x96), (0xC9, 0x7E, 0x6A)]
LOCK_DIST = 48  # r·g·b 차이 합이 이 안이면 팔레트 색으로 바꿔요


def lock_colors(im: Image.Image) -> Image.Image:
    px = im.load()
    w, h = im.size
    cache = {}
    for y in range(h):
        for x in range(w):
            r, g, b, a = px[x, y]
            if not a:
                continue
            if (r, g, b) not in cache:
                d, c = min((abs(r - c[0]) + abs(g - c[1]) + abs(b - c[2]), c) for c in LOCK)
                cache[(r, g, b)] = c if d <= LOCK_DIST else (r, g, b)
            px[x, y] = (*cache[(r, g, b)], 255)
    return im


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
    remove_fringe(im, bg)
    return im


def chroma(c):
    m = sum(c[:3]) / 3
    return [c[0] - m, c[1] - m, c[2] - m]


def remove_fringe(im: Image.Image, bg, depth: int = 8):
    """가장자리에 남은 배경색 번짐(예: 분홍 테두리) 지우기: 투명 칸에서 안쪽으로 depth 칸까지, 배경과 같은 쪽 색이면 지워요"""
    bc = chroma(bg)
    bn = sum(v * v for v in bc) ** 0.5
    if bn < 60:  # 흰색 · 회색처럼 색이 옅은 배경은 건너뛰어요
        return
    px = im.load()
    w, h = im.size
    near = {}

    def bgish(x, y):
        if (x, y) not in near:
            cc = chroma(px[x, y])
            cn = sum(v * v for v in cc) ** 0.5
            near[(x, y)] = cn > 30 and sum(a * b for a, b in zip(cc, bc)) / (cn * bn) > 0.85
        return near[(x, y)]

    steps = ((1, 0), (-1, 0), (0, 1), (0, -1))
    edge = [(x, y) for y in range(h) for x in range(w) if px[x, y][3] and any(
        not (0 <= x + dx < w and 0 <= y + dy < h) or not px[x + dx, y + dy][3] for dx, dy in steps)]
    front = [p for p in edge if bgish(*p)]
    for _ in range(depth):
        if not front:
            break
        for x, y in front:
            px[x, y] = (0, 0, 0, 0)
        nxt = set()
        for x, y in front:
            for dx, dy in steps:
                q = (x + dx, y + dy)
                if 0 <= q[0] < w and 0 <= q[1] < h and px[q][3] and bgish(*q):
                    nxt.add(q)
        front = list(nxt)


def pixels(im: Image.Image):
    return im.get_flattened_data() if hasattr(im, "get_flattened_data") else im.getdata()


def crop_bbox(im: Image.Image) -> Image.Image:
    box = im.getchannel("A").point(lambda v: 255 if v >= 128 else 0).getbbox()
    return im.crop(box) if box else im


def fit(im: Image.Image, max_w: int, max_h: int) -> Image.Image:
    im = crop_bbox(im)
    s = min(max_w / im.width, max_h / im.height)
    size = (max(1, round(im.width * s)), max(1, round(im.height * s)))
    # 줄일 때는 BOX (AI 그림의 픽셀 격자가 어긋나 있어도 평균으로 깔끔하게)
    return im.resize(size, Image.BOX)


def quantize(im: Image.Image, colors: int) -> Image.Image:
    alpha = im.getchannel("A").point(lambda v: 255 if v >= 128 else 0)  # 반투명 없애기
    # 투명 자리는 그림에 제일 많은 색으로 채워서 색 한 칸을 먹지 않게
    opaque = [p[:3] for p, a in zip(pixels(im.convert("RGB")), pixels(alpha)) if a]
    fill = Counter(opaque).most_common(1)[0][0] if opaque else (0, 0, 0)
    rgb = Image.new("RGB", im.size, fill)
    rgb.paste(im.convert("RGB"), mask=alpha)
    q = rgb.quantize(colors=colors, method=Image.Quantize.MEDIANCUT, dither=Image.Dither.NONE).convert("RGB")
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
        part = crop_bbox(im)
        part = part.crop((0, 0, part.width, min(part.height, round(part.width * 0.9))))  # 머리 ~ 가슴
        part = fit(part, cw, ch - 1)
        canvas = Image.new("RGBA", (cw, ch), (0, 0, 0, 0))
        canvas.alpha_composite(part, ((cw - part.width) // 2, ch - part.height))
    else:
        cw = ch = 80
        part = fit(im, cw, arg("--height", SIZES[arg("--size", "M").upper()]))
        canvas = Image.new("RGBA", (cw, ch), (0, 0, 0, 0))
        canvas.alpha_composite(part, ((cw - part.width) // 2, ch - 1 - part.height))
    out = quantize(canvas, colors)
    if "--no-lock" not in sys.argv:
        out = lock_colors(out)
    out.save(dst)
    used = len({p[:3] for p in pixels(out) if p[3]})
    zoom = dst.rsplit(".", 1)[0] + "-zoom8.png"
    out.resize((cw * 8, ch * 8), Image.NEAREST).save(zoom)
    print(f"{dst}: {cw}×{ch}, 색 {used}개 (투명 빼고), 확대 미리보기 {zoom}")


if __name__ == "__main__":
    main()
