# SPDX-FileCopyrightText: 2026 SG
# SPDX-License-Identifier: AGPL-3.0-only
"""
AI 가 만든 도트 밑그림 → 블서로그 실험체 도트 규격으로 정리 (docs/dot-guide, 도트 가이드 문서)

하는 일: 배경 지우기 → 캐릭터만 잘라서 칸에 맞게 줄이기 → 반투명 없애기 → 15색으로 묶기 →
         아래 가운데 정렬 (발끝은 맨 아래 1px 위) → 1배 PNG + 8배 확대 미리보기
그다음은 사람이 손으로: 외곽선 · 눈 · 손 · 무기 다듬기 (가이드의 검사 목록)

쓰는 법:
  python3 scripts/er-dot/clean_dot.py <AI 그림.png> <나올 이름.png> [--icon] [--size S|M|L] [--colors 15] [--no-lock] [--box]
  --icon      아이콘 (40×30, 위쪽을 잘라 써요)
  --size      키 등급: S 60px · M 68px (기본) · L 74px (칸은 80×80). --height N 으로 직접 줘도 돼요
  --no-lock   외곽선 2색 · 피부 3색을 팔레트 색으로 맞추지 않기 (기본은 맞춰요)
  --box       예전 줄이기 (평균). 기본은 큰 그림에서 15색으로 묶고 칸마다 제일 많은 색 (11-19), 어두운 선은 지켜요
  --no-outline 바깥 1px 외곽선(#1a1c2c)을 안 붙이기 (기본은 붙여요, 키는 외곽선까지 포함)
  --pre-colors 줄이기 전에 묶는 색 수 (기본 48, 마지막은 --colors)
배경: 투명이면 그대로, 아니면 테두리 색(중간값)을 배경으로 보고 지워요. 가장자리 번짐도 지워요
      (AI 에게 단색 배경을 부탁: 보통 #ff00ff, 보라 · 분홍 옷이면 #00ff00)
"""
import sys
from collections import Counter

from PIL import Image


SIZES = {"S": 60, "M": 68, "L": 74}
# 모든 실험체가 같이 쓰는 색 (docs/dot-guide/palette-15.png): 외곽선 2 + 피부 3
LOCK = [(0x1A, 0x1C, 0x2C), (0x3B, 0x3F, 0x5C), (0xFF, 0xE0, 0xC8), (0xF2, 0xB8, 0x96), (0xC9, 0x7E, 0x6A)]
LOCK_DIST = 30  # r·g·b 차이 합이 이 안이면 팔레트 색으로 바꿔요 (11-19: 48 이면 흰 머리가 피부색이 돼서 줄임)
DARK_LUMA = 70  # 이보다 어두우면 선으로 봐요 (줄일 때 지키기)


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


def remove_background(im: Image.Image, tol: int = 40, flood_tol: int = 110) -> Image.Image:
    """배경 지우기. 배경색 = 테두리 픽셀의 중간값 (11-19: AI 그림은 귀퉁이가 어둡게 번져서 귀퉁이 색만 보면 틀려요).
    ① 테두리에서 이어진 곳은 넉넉하게(flood_tol) ② 캐릭터 사이에 갇힌 배경은 가깝게(tol) 지워요"""
    im = im.convert("RGBA")
    a = im.getchannel("A")
    if a.getextrema()[0] < 250:  # 이미 투명 배경
        return im
    w, h = im.size
    px = im.load()
    border = [(x, 0) for x in range(w)] + [(x, h - 1) for x in range(w)] + [(0, y) for y in range(h)] + [(w - 1, y) for y in range(h)]
    cols = [px[p][:3] for p in border]
    bg = tuple(sorted(c[i] for c in cols)[len(cols) // 2] for i in range(3))

    def dist(p):
        r, g, b, _ = px[p]
        return abs(r - bg[0]) + abs(g - bg[1]) + abs(b - bg[2])

    seen = set()
    stack = [p for p in border if dist(p) <= flood_tol]
    while stack:
        p = stack.pop()
        if p in seen:
            continue
        seen.add(p)
        x, y = p
        for q in ((x + 1, y), (x - 1, y), (x, y + 1), (x, y - 1)):
            if 0 <= q[0] < w and 0 <= q[1] < h and q not in seen and dist(q) <= flood_tol:
                stack.append(q)
    for p in seen:
        px[p] = (0, 0, 0, 0)
    for y in range(h):
        for x in range(w):
            if px[x, y][3] and dist((x, y)) <= tol:
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


def fit(im: Image.Image, max_w: int, max_h: int, colors: int = 15) -> Image.Image:
    im = crop_bbox(im)
    s = min(max_w / im.width, max_h / im.height)
    size = (max(1, round(im.width * s)), max(1, round(im.height * s)))
    if "--box" in sys.argv:  # 예전 방식: 평균으로 줄이기 (색이 뭉개져요)
        return im.resize(size, Image.BOX)
    # 11-19: 큰 그림에서 먼저 색을 묶고 → 칸마다 제일 많은 색으로 줄이기 (평균이 아니라 색이 또렷해요)
    # 큰 그림에서 15색으로 바로 묶으면 넓은 옷 색이 색을 다 먹어서 얼굴 · 단추 같은 작은 색이 사라져요 →
    # 넉넉하게(--pre-colors, 기본 48) 묶어서 줄이고, 마지막에 작은 그림에서 15색으로 (main 의 quantize)
    return downsample_mode(quantize(im, max(colors, arg("--pre-colors", 48)), lone=False), size)


def downsample_mode(im: Image.Image, size) -> Image.Image:
    """칸(작은 그림 한 픽셀이 덮는 큰 그림 영역)마다 제일 많은 색. 투명이 절반 넘으면 투명"""
    W, H = im.size
    tw, th = size
    px = im.load()
    out = Image.new("RGBA", size, (0, 0, 0, 0))
    op = out.load()
    for ty in range(th):
        y0, y1 = ty * H // th, max(ty * H // th + 1, (ty + 1) * H // th)
        for tx in range(tw):
            x0, x1 = tx * W // tw, max(tx * W // tw + 1, (tx + 1) * W // tw)
            cnt = Counter(px[x, y] if px[x, y][3] else None for y in range(y0, y1) for x in range(x0, x1))
            total = (y1 - y0) * (x1 - x0)
            if cnt.get(None, 0) * 2 > total:
                continue
            cnt.pop(None, None)
            # 11-19: 어두운 색들을 합쳐 칸의 절반 이상이면 그중 제일 많은 어두운 색 (선 · 머리가 여러 어두운 색으로 갈라져도 지켜요)
            # (1/4 로 했더니 유키처럼 옷이 어두우면 얼굴까지 까매졌어요)
            opaque = sum(cnt.values())
            dark = [(n, c) for c, n in cnt.items() if c[0] * 0.3 + c[1] * 0.59 + c[2] * 0.11 < DARK_LUMA]
            if dark and sum(n for n, _ in dark) * 2 >= opaque:
                op[tx, ty] = max(dark)[1]
            else:
                op[tx, ty] = cnt.most_common(1)[0][0]
    return out


def add_outline(im: Image.Image, color=None) -> Image.Image:
    """캐릭터 바깥 1px 외곽선 (가이드: #1a1c2c). 투명 칸 중 위아래양옆에 캐릭터가 있는 칸을 칠해요"""
    color = (*(color or LOCK[0]), 255)
    out = Image.new("RGBA", (im.width + 2, im.height + 2), (0, 0, 0, 0))
    out.alpha_composite(im, (1, 1))
    px = out.load()
    w, h = out.size
    edge = [(x, y) for y in range(h) for x in range(w) if not px[x, y][3]
            and any(0 <= x + dx < w and 0 <= y + dy < h and px[x + dx, y + dy][3] for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)))]
    for x, y in edge:
        px[x, y] = color
    return out


def quantize(im: Image.Image, colors: int, lone: bool = True) -> Image.Image:
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
    lone_px = [(x, y) for y in range(h) for x in range(w) if lone and px[x, y][3]
            and not any(0 <= x + dx < w and 0 <= y + dy < h and px[x + dx, y + dy][3] for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)))]
    for y in range(h):
        for x in range(w):
            if px[x, y][3] == 0:
                px[x, y] = (0, 0, 0, 0)
    if lone:
        for x, y in lone_px:
            px[x, y] = (0, 0, 0, 0)
    return out


def main():
    if len(sys.argv) < 3:
        sys.exit(__doc__)
    src, dst = sys.argv[1], sys.argv[2]
    icon = "--icon" in sys.argv
    colors = arg("--colors", 15)
    line = 0 if "--no-outline" in sys.argv else 1
    im = remove_background(Image.open(src))
    if icon:
        cw, ch = 40, 30
        part = crop_bbox(im)
        part = part.crop((0, 0, part.width, min(part.height, round(part.width * 0.9))))  # 머리 ~ 가슴
        part = fit(part, cw - 2 * line, ch - 1 - 2 * line, colors)
        if line:
            part = add_outline(part)
        canvas = Image.new("RGBA", (cw, ch), (0, 0, 0, 0))
        canvas.alpha_composite(part, ((cw - part.width) // 2, ch - part.height))
    else:
        cw = ch = 80
        part = fit(im, cw - 2 * line, arg("--height", SIZES[arg("--size", "M").upper()]) - 2 * line, colors)
        if line:
            part = add_outline(part)
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
