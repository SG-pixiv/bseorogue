# SPDX-FileCopyrightText: 2026 SG
# SPDX-License-Identifier: AGPL-3.0-only
"""
블서로그 지역 배경 21곳 (루미아 섬) — 포켓로그 방식으로 코드로 그려요 (11-19 SG "1번으로 하고 20곳 제작 이후 병합까지")

포켓로그 원래 배경(pagefaultgames/pokerogue-assets)과 같은 구조예요:
  - <바이옴>_bg.png  320×180 배경: 하늘 색 띠(위가 진하고 지평선으로 밝게, 경계는 2줄 줄무늬) + 먼 풍경 + 땅 색 띠.
    그다음 '빠르게 지나가는 느낌'(SG 고른 ① 약하게): 가로로만 번지게(하늘 · 건물 9px, 땅 15px) + 먼 곳 옅은 안개 22%
    + 가로 속도선 16줄 → 14색. 아래 48칸은 전투 창에 가려요
  - <바이옴>_b.png   320×132 상대 발판 (포켓로그와 같은 자리 128×33, x 152 · y 57) + 소품 (발판 뒤에 세워 그림)
  - <바이옴>_a.png   320×132 내 발판 (120×30, x 44 · y 117, 위쪽만 보여요)
  - <바이옴>_b_1~3   투명 (소품은 _b 에 같이 그려서 늘 보여요)
  발판 = 두꺼운 테 + 윗면 무늬(지역마다) + 가장자리 어둡게. 그곳다움은 발판 · 소품 · 먼 풍경이 맡아요.

이터널 리턴 2026 기준 (공식 패치노트 · 스토리 모드 배경 그림 · 나무위키 지역 스크린샷의 색과 모양을 참고):
  - 시즌 11: 바지선(항구와 공장 사이 해상 작업장, 크레인 · 배럴), 자연 지역(숲 · 연못 · 절 · 양궁장 · 성당 · 묘지) 사과나무
    (가끔 황금사과), 학교 괘종시계, 경찰서 분실물 상자, 병원 의료 지원
  - 시즌 13: 연구소를 뺀 모든 지역에 음식 자판기 (공장은 2대)

포켓로그 지역(바이옴) 35곳을 루미아 섬 21곳에 나눠 붙였어요 (이름은 locales/ko/biomes.json, 역할군은
src/data/bseorogue/regions.ts). 같은 지역에 붙은 바이옴은 같은 그림을 써요.

쓰는 법 (저장소 맨 위에서): python3 -B scripts/er-ui/make_arenas.py [--preview docs/arenas-preview.png] [--only alley,forest]
그린 파일은 assets/.placeholders.json 에서 빠져요 (임시 그림 만들기가 덮어쓰지 않게).
"""
import json
import math
import random
import sys
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw

ROOT = Path(__file__).resolve().parents[2]
ARENA = ROOT / "assets" / "images" / "arenas"
MARK = ROOT / "assets" / ".placeholders.json"
W, H = 320, 180
HOR = 62  # 지평선
OL = (38, 34, 44)  # 외곽선

# 바이옴 → 지역 (locales/ko/biomes.json · src/data/bseorogue/regions.ts 와 같게)
# 바지선 = seabed, 호텔 = snowy_forest 는 11-12 에 임시로 붙인 자리예요 (SG가 바꾸면 세 곳을 같이)
BIOME_REGION = {
    "town": "alley", "slum": "alley", "plains": "archery", "grass": "stream", "tall_grass": "forest", "forest": "forest",
    "jungle": "forest", "snowy_forest": "hotel", "metropolis": "uptown", "sea": "harbor", "seabed": "barge",
    "swamp": "pond", "lake": "pond", "beach": "beach", "desert": "beach", "island": "beach", "mountain": "temple",
    "temple": "temple", "badlands": "gas", "cave": "warehouse", "ice_cave": "warehouse", "meadow": "school",
    "power_plant": "factory", "factory": "factory", "construction_site": "factory", "volcano": "fire",
    "graveyard": "cemetery", "wasteland": "cemetery", "dojo": "police", "ruins": "chapel", "fairy_cave": "hospital",
    "abyss": "lab", "space": "lab", "laboratory": "lab", "end": "lab", "default": "lab", "rockycoast": "harbor", "well": "pond",
}
NAMES = {"alley": "골목길", "archery": "양궁장", "stream": "개울", "forest": "숲", "uptown": "고급 주택가", "harbor": "항구",
         "pond": "연못", "beach": "모래사장", "temple": "절", "gas": "주유소", "warehouse": "창고", "school": "학교",
         "factory": "공장", "fire": "소방서", "cemetery": "묘지", "police": "경찰서", "chapel": "성당", "hospital": "병원",
         "lab": "연구소", "hotel": "호텔", "barge": "바지선"}

done: list[str] = []

# ── 색 ─────────────────────────────────────────────
SKY = {
    "day": [(112, 146, 196), (138, 168, 212), (164, 190, 226), (190, 210, 236), (214, 226, 242)],
    "sea": [(92, 146, 204), (118, 168, 218), (148, 190, 230), (180, 210, 240), (208, 228, 246)],
    "warm": [(120, 150, 196), (150, 172, 210), (184, 196, 222), (214, 214, 226), (236, 226, 220)],
    "grey": [(108, 116, 136), (126, 134, 152), (146, 154, 170), (168, 174, 188), (190, 194, 204)],
    "green": [(70, 108, 96), (88, 128, 110), (110, 148, 124), (134, 168, 140), (160, 188, 158)],
    "lab": [(48, 62, 88), (62, 80, 108), (80, 100, 128), (102, 124, 150), (128, 150, 172)],
    "dusk": [(84, 96, 140), (110, 118, 160), (146, 140, 176), (186, 164, 180), (220, 190, 180)],
}


def mix(a, b, t):
    return tuple(int(a[i] + (b[i] - a[i]) * t) for i in range(3))


def shade(c, k):
    return tuple(max(0, min(255, int(v * k))) for v in c[:3])


# ── 배경 도우미 ──────────────────────────────────────
def stripes(d, y0, y1, c_top, c_bot):
    """포켓로그 띠 경계: 위 색과 아래 색을 한 줄씩 번갈아"""
    d.rectangle([0, y0, W, y1], fill=c_bot)
    for k in (0, 2):
        d.line([(0, y0 + k), (W, y0 + k)], fill=c_top)


def sky(d, cols, hor=HOR):
    step = hor // len(cols)
    for i, c in enumerate(cols):
        y0, y1 = i * step, (hor if i == len(cols) - 1 else (i + 1) * step)
        if i == 0:
            d.rectangle([0, 0, W, y1], fill=c)
        else:
            stripes(d, y0, y1, cols[i - 1], c)


def ground(d, bands, hor=HOR):
    """bands: [(높이, 색), …] 지평선부터 아래로. 마지막은 끝까지"""
    y, prev = hor, None
    for i, (h, c) in enumerate(bands):
        y1 = H if i == len(bands) - 1 else y + h
        if prev is None:
            d.rectangle([0, y, W, y1], fill=c)
        else:
            stripes(d, y, y1, prev, c)
        y, prev = y1, c


def building(d, x0, x1, h, body, win=None, base=HOR, roof=None, step=6):
    d.rectangle([x0, base - h, x1, base], fill=body)
    d.line([(x0, base - h), (x1, base - h)], fill=shade(body, 0.9))
    if roof:
        d.polygon([(x0 - 2, base - h), ((x0 + x1) // 2, base - h - roof[0]), (x1 + 2, base - h)], fill=roof[1])
    if win:
        for wy in range(base - h + 4, base - 5, step):
            for wx in range(x0 + 3, x1 - 3, step):
                d.rectangle([wx, wy, wx + 2, wy + 2], fill=win)


def skyline(d, rng, color, win, hmin, hmax, x0=-4, x1=W, base=HOR):
    x = x0
    while x < x1:
        w = rng.randint(14, 30)
        h = rng.randint(hmin, hmax)
        d.rectangle([x, base - h, x + w, base], fill=color)
        for wy in range(base - h + 4, base - 4, 5):
            for wx in range(x + 3, x + w - 2, 5):
                if rng.random() < 0.5:
                    d.point((wx, wy), fill=win)
        x += w + rng.randint(0, 3)


def treeline(d, rng, color, hi, y=HOR, r=(6, 12), x0=-8, x1=W + 8, dark=None):
    x = x0
    while x < x1:
        rr = rng.randint(*r)
        cy = y - rng.randint(0, hi)
        d.ellipse([x - rr, cy - rr, x + rr, cy + rr], fill=color)
        if dark:
            d.ellipse([x - rr + 2, cy - rr // 3, x + rr - 1, cy + rr], fill=dark)
        x += rr + rng.randint(1, 5)
    d.rectangle([x0, y - 2, x1, y + 2], fill=dark or color)


def hills(d, rng, base, amp, color, step=16):
    pts = [(0, H)]
    for x in range(0, W + step, step):
        pts.append((x, base - rng.randint(0, amp)))
    pts.append((W, H))
    d.polygon(pts, fill=color)


def mountains(d, peaks, color, base=HOR):
    for x, h, w in peaks:
        d.polygon([(x - w, base), (x, base - h), (x + w, base)], fill=color)


def sea(d, y0, y1, c1, c2, rng):
    d.rectangle([0, y0, W, y1], fill=c1)
    for _ in range(26):
        x, y = rng.randint(0, W), rng.randint(y0 + 1, y1 - 1)
        d.line([(x, y), (x + rng.randint(4, 12), y)], fill=c2)


def poles(d, xs, color=(84, 88, 106), wire=(70, 74, 92), top=6):
    for px in xs:
        d.rectangle([px, top, px + 2, HOR + 2], fill=color)
        d.rectangle([px - 6, top + 6, px + 8, top + 7], fill=color)
    for a, b in zip(xs, xs[1:]):
        for y0, sag in ((top + 7, 10), (top + 10, 13)):
            d.line([(a + 1 + t * (b - a), y0 + sag * 4 * t * (1 - t)) for t in [i / 40 for i in range(41)]], fill=wire)


def speed_blur(img, k_sky=9, k_ground=15, haze_t=0.22, lines=16, colors=14, haze=(190, 210, 236)):
    """빠르게 지나가는 느낌 ① (SG 고름): 가로로만 번지게 + 먼 곳 안개 + 가로 속도선 → 적은 색"""
    a = np.asarray(img.convert("RGB")).astype(np.float32)
    out = a.copy()

    def hblur(rows, k):
        acc = np.zeros_like(a[rows])
        for s in range(-(k // 2), k // 2 + 1):
            acc += np.roll(a[rows], s, axis=1)
        return acc / k

    top, low = slice(0, HOR + 3), slice(HOR + 3, H)
    out[top] = hblur(top, k_sky) * (1 - haze_t) + np.array(haze, np.float32) * haze_t
    out[low] = hblur(low, k_ground)
    res = Image.fromarray(out.clip(0, 255).astype("uint8"))
    res = res.quantize(colors=colors, method=Image.MEDIANCUT, dither=Image.NONE).convert("RGB")
    dd = ImageDraw.Draw(res)
    rr = random.Random(11)
    for _ in range(lines):
        y = rr.randint(4, H - 50)
        x0 = rr.randint(-40, W)
        ln = rr.randint(18, 70) * (1 if y < HOR else 2)
        c = res.getpixel((max(0, min(W - 1, x0)), y))
        c = mix(c, (255, 255, 255), 0.35) if y < HOR else shade(c, 0.9)
        dd.line([(x0, y), (x0 + ln, y)], fill=c)
    return res


# ── 발판 ────────────────────────────────────────────
def platform(w, h, surface, seed, rim=((60, 54, 62), (78, 72, 80)), decor=None):
    """포켓로그 발판: 두꺼운 테 + 윗면 surface(x, y, u, v, rng) + 가장자리 어둡게 + decor(ImageDraw, w, h)"""
    rng = random.Random(seed)
    im = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    px = im.load()
    cx, cy, rx, ry = (w - 1) / 2, (h - 1) / 2, w / 2, h / 2
    for y in range(h):
        for x in range(w):
            e = ((x - cx) / rx) ** 2 + ((y - cy) / ry) ** 2
            if e > 1:
                continue
            ei = ((x - cx) / (rx - 4)) ** 2 + ((y - cy) / (ry - 2.5)) ** 2
            if ei > 1:
                px[x, y] = (rim[0] if e > 0.9 or y > cy else rim[1]) + (255,)
                continue
            c = surface(x, y, x / w, y / h, rng)
            if ei > 0.82:
                c = shade(c, 0.86)
            px[x, y] = tuple(c) + (255,)
    if decor:
        decor(ImageDraw.Draw(im), w, h, rng)
    return im


def speck(base, rng, alt, p=0.06):
    return alt[0] if rng.random() < p * 0.6 else alt[1] if rng.random() < p * 0.4 else base


def split(left, right, at=0.66, edge=(208, 208, 214)):
    def f(x, y, u, v, rng):
        s = at + 0.05 * (v - 0.5)
        if abs(u - s) < 0.012 and edge:
            return edge
        return right(x, y, u, v, rng) if u > s else left(x, y, u, v, rng)
    return f


def wavy_split(left, right, at=0.6, amp=0.06, edge=None):
    def f(x, y, u, v, rng):
        s = at + amp * math.sin(v * 7 + 1)
        if edge and abs(u - s) < 0.014:
            return edge
        return right(x, y, u, v, rng) if u > s else left(x, y, u, v, rng)
    return f


def s_asphalt(base=(92, 94, 106)):
    return lambda x, y, u, v, rng: speck(base, rng, (shade(base, 0.88), shade(base, 1.12)))


def s_crosswalk(base=(92, 94, 106)):
    def f(x, y, u, v, rng):
        xs = x + (v - 0.5) * 6
        if 0.12 < u < 0.56 and 0.18 < v < 0.84 and int(xs) % 8 < 4:
            return (226, 228, 232) if v < 0.7 else (196, 198, 206)
        return speck(base, rng, (shade(base, 0.88), shade(base, 1.12)))
    return f


def s_bricks(c1, c2, bw=7, bh=3):
    def f(x, y, u, v, rng):
        off = bw // 2 if (y // bh) % 2 else 0
        return c2 if (y % bh == 0 or (x + off) % bw == 0) else c1
    return f


def s_herring(c1, c2):
    def f(x, y, u, v, rng):
        return c2 if ((x + y) % 6 == 0 or (x - y) % 12 == 0) else c1
    return f


def s_tiles(c1, c2, step=8, ystep=4):
    def f(x, y, u, v, rng):
        xs = x + (v - 0.5) * 4
        return c2 if (int(xs) % step == 0 or y % ystep == 0) else c1
    return f


def s_grass(c1, c2, c3):
    def f(x, y, u, v, rng):
        r = rng.random()
        return c2 if r < 0.12 else c3 if r < 0.17 else c1
    return f


def s_sand(c1, c2):
    def f(x, y, u, v, rng):
        return c2 if (rng.random() < 0.1 or (y + x // 9) % 7 == 0) else c1
    return f


def s_water(c1, c2, c3):
    def f(x, y, u, v, rng):
        k = (x + int(3 * math.sin(y * 0.9))) % 11
        return c3 if k == 0 and y % 3 == 0 else c2 if (x // 6 + y) % 5 == 0 else c1
    return f


def s_planks(c1, c2, step=4):
    def f(x, y, u, v, rng):
        if y % step == 0:
            return c2
        return c2 if (x + (y // step) * 13) % 23 == 0 else (shade(c1, 0.95) if (y // step) % 2 else c1)
    return f


def s_metal(c1, c2, step=16):
    def f(x, y, u, v, rng):
        if x % step == 0 or y % 8 == 0:
            return c2
        if (x % step == 3 and y % 8 == 3) or (x % step == step - 3 and y % 8 == 3):
            return shade(c1, 1.25)
        return c1
    return f


def s_hazard(base):
    def f(x, y, u, v, rng):
        if 0.05 < u < 0.95 and (v < 0.2 or v > 0.86) and ((x + y) // 4) % 2 == 0:
            return (226, 186, 60)
        return speck(base, rng, (shade(base, 0.9), shade(base, 1.1)), 0.05)
    return f


def s_track(c1, line=(236, 230, 220)):
    def f(x, y, u, v, rng):
        ring = ((u - 0.5) * 2) ** 2 + ((v - 0.5) * 2) ** 2
        for r0 in (0.18, 0.42, 0.7):
            if abs(ring - r0) < 0.035:
                return line
        return speck(c1, rng, (shade(c1, 0.92), shade(c1, 1.08)), 0.05)
    return f


def s_stone(c1, c2, c3):
    """돌판 (불규칙 판석)"""
    cells = [(random.Random(i).uniform(0, 128), random.Random(i * 7 + 1).uniform(0, 33)) for i in range(26)]

    def f(x, y, u, v, rng):
        ds = sorted(((x - px) ** 2 + ((y - py) * 3.2) ** 2, i) for i, (px, py) in enumerate(cells))
        if math.sqrt(ds[1][0]) - math.sqrt(ds[0][0]) < 1.6:
            return c2
        return c3 if ds[0][1] % 3 == 0 else c1
    return f


def s_dirt(c1, c2):
    return lambda x, y, u, v, rng: c2 if rng.random() < 0.09 else c1


def s_glow(c1, c2, glow):
    def f(x, y, u, v, rng):
        if (x % 16 == 0) or (y % 8 == 0):
            return glow if (x // 16 + y // 8) % 3 == 0 else c2
        return c1
    return f


# ── 소품 (상대 발판 뒤 · 양옆에 세움) ──────────────────────
def vending(d, x, yb, body=(204, 70, 60)):
    y = yb - 24
    d.rectangle([x, y, x + 13, yb], fill=body, outline=OL)
    d.rectangle([x + 2, y + 2, x + 11, y + 11], fill=(246, 234, 176))
    for i, c in enumerate([(84, 160, 220), (236, 120, 60), (110, 180, 90), (230, 70, 90)]):
        d.rectangle([x + 3 + (i % 2) * 4, y + 3 + (i // 2) * 4, x + 5 + (i % 2) * 4, y + 5 + (i // 2) * 4], fill=c)
    d.rectangle([x + 3, y + 15, x + 10, y + 18], fill=(48, 40, 50))
    d.line([(x + 1, y + 1), (x + 1, yb - 1)], fill=mix(body, (255, 255, 255), 0.3))


def apple_tree(d, x, yb, gold=False):
    d.rectangle([x - 1, yb - 12, x + 2, yb], fill=(104, 72, 50), outline=OL)
    d.ellipse([x - 11, yb - 30, x + 12, yb - 9], fill=(74, 140, 74), outline=OL)
    d.ellipse([x - 7, yb - 28, x + 6, yb - 18], fill=(96, 164, 88))
    for ax, ay in ((-6, -16), (4, -22), (6, -13), (-2, -25)):
        d.rectangle([x + ax, yb + ay, x + ax + 2, yb + ay + 2], fill=(236, 196, 60) if gold else (214, 60, 60))


def bags(d, x, yb):
    for bx, c in ((x, (54, 56, 70)), (x + 8, (66, 68, 84))):
        d.ellipse([bx, yb - 9, bx + 10, yb], fill=c, outline=OL)


def cone(d, x, yb):
    d.polygon([(x, yb - 9), (x - 4, yb), (x + 4, yb)], fill=(236, 120, 52), outline=OL)
    d.line([(x - 2, yb - 4), (x + 2, yb - 4)], fill=(240, 240, 240))


def target(d, x, yb):
    d.line([(x - 6, yb), (x, yb - 10)], fill=(110, 80, 56), width=2)
    d.line([(x + 6, yb), (x, yb - 10)], fill=(110, 80, 56), width=2)
    for r, c in ((10, (240, 240, 236)), (8, (60, 60, 70)), (6, (70, 130, 210)), (4, (220, 70, 60)), (2, (246, 214, 70))):
        d.ellipse([x - r, yb - 22 - r, x + r, yb - 22 + r], fill=c, outline=OL if r == 10 else None)


def rocks(d, x, yb):
    d.ellipse([x, yb - 6, x + 10, yb], fill=(130, 132, 140), outline=OL)
    d.ellipse([x + 7, yb - 4, x + 14, yb], fill=(150, 152, 160), outline=OL)


def reeds(d, x, yb):
    for i in range(5):
        d.line([(x + i * 2, yb), (x + i * 2 + (i % 2), yb - 8 - (i * 3) % 5)], fill=(96, 130, 70))
        d.rectangle([x + i * 2, yb - 10 - (i * 3) % 5, x + i * 2 + 1, yb - 8 - (i * 3) % 5], fill=(120, 84, 56))


def lamp(d, x, yb):
    d.rectangle([x, yb - 26, x + 1, yb], fill=(60, 62, 74))
    d.rectangle([x - 2, yb - 30, x + 3, yb - 26], fill=(250, 226, 150), outline=OL)


def buoy(d, x, yb):
    d.ellipse([x - 6, yb - 12, x + 6, yb], fill=(226, 80, 60), outline=OL)
    d.rectangle([x - 6, yb - 7, x + 6, yb - 5], fill=(240, 240, 240))


def bollard(d, x, yb):
    d.rectangle([x - 3, yb - 7, x + 3, yb], fill=(58, 60, 70), outline=OL)
    d.rectangle([x - 5, yb - 9, x + 5, yb - 7], fill=(70, 72, 84), outline=OL)


def umbrella(d, x, yb, c=(230, 90, 80)):
    d.line([(x, yb), (x, yb - 22)], fill=(200, 200, 200))
    d.pieslice([x - 14, yb - 30, x + 14, yb - 14], 180, 360, fill=c, outline=OL)
    for k in (-7, 7):
        d.line([(x, yb - 22), (x + k, yb - 22)], fill=(250, 250, 250))


def lantern(d, x, yb):
    d.rectangle([x - 2, yb - 6, x + 2, yb], fill=(150, 146, 136), outline=OL)
    d.rectangle([x - 4, yb - 12, x + 4, yb - 6], fill=(170, 166, 156), outline=OL)
    d.rectangle([x - 2, yb - 10, x + 2, yb - 8], fill=(250, 210, 120))
    d.polygon([(x - 6, yb - 12), (x, yb - 17), (x + 6, yb - 12)], fill=(120, 116, 110), outline=OL)


def pump(d, x, yb):
    d.rectangle([x, yb - 20, x + 10, yb], fill=(226, 228, 232), outline=OL)
    d.rectangle([x + 2, yb - 17, x + 8, yb - 12], fill=(70, 120, 200))
    d.rectangle([x, yb - 22, x + 10, yb - 20], fill=(60, 110, 190), outline=OL)
    d.line([(x + 10, yb - 10), (x + 13, yb - 6), (x + 13, yb - 2)], fill=OL)


def tires(d, x, yb):
    for i in range(3):
        d.ellipse([x, yb - 5 - i * 4, x + 12, yb - i * 4], fill=(48, 48, 56), outline=OL)


def crates(d, x, yb):
    for bx, by, s in ((x, yb - 10, 10), (x + 10, yb - 10, 10), (x + 5, yb - 20, 10)):
        d.rectangle([bx, by, bx + s, by + s], fill=(176, 130, 80), outline=OL)
        d.line([(bx, by), (bx + s, by + s)], fill=(140, 100, 60))


def clock(d, x, yb):
    d.rectangle([x, yb - 30, x + 10, yb], fill=(122, 78, 52), outline=OL)
    d.ellipse([x + 1, yb - 28, x + 9, yb - 20], fill=(236, 226, 196), outline=OL)
    d.line([(x + 5, yb - 24), (x + 5, yb - 27)], fill=OL)
    d.line([(x + 5, yb - 24), (x + 7, yb - 24)], fill=OL)
    d.rectangle([x + 3, yb - 17, x + 7, yb - 5], fill=(92, 58, 40))
    d.line([(x + 5, yb - 16), (x + 5, yb - 8)], fill=(220, 190, 90))


def hydrant(d, x, yb):
    d.rectangle([x - 3, yb - 10, x + 3, yb], fill=(214, 60, 52), outline=OL)
    d.ellipse([x - 3, yb - 13, x + 3, yb - 8], fill=(214, 60, 52), outline=OL)
    d.rectangle([x - 5, yb - 7, x + 5, yb - 5], fill=(190, 50, 44), outline=OL)


def hose(d, x, yb):
    d.ellipse([x, yb - 12, x + 12, yb], fill=(214, 200, 170), outline=OL)
    d.ellipse([x + 3, yb - 9, x + 9, yb - 3], fill=(160, 60, 52))


def grave(d, x, yb, cross=False):
    if cross:
        d.rectangle([x + 3, yb - 16, x + 5, yb], fill=(150, 150, 156), outline=OL)
        d.rectangle([x, yb - 13, x + 8, yb - 11], fill=(150, 150, 156), outline=OL)
    else:
        d.rounded_rectangle([x, yb - 14, x + 10, yb], 4, fill=(140, 142, 150), outline=OL)
        d.line([(x + 3, yb - 9), (x + 7, yb - 9)], fill=(110, 112, 120))


def lost_box(d, x, yb):
    d.rectangle([x, yb - 16, x + 14, yb], fill=(70, 96, 170), outline=OL)
    d.rectangle([x + 2, yb - 13, x + 12, yb - 9], fill=(230, 230, 236))
    d.rectangle([x + 5, yb - 6, x + 9, yb - 4], fill=(240, 200, 70))


def barrier(d, x, yb):
    for k in (0, 18):
        d.rectangle([x + k, yb - 10, x + k + 2, yb], fill=(60, 62, 74))
    d.rectangle([x - 2, yb - 12, x + 22, yb - 8], fill=(240, 240, 240), outline=OL)
    for k in range(0, 24, 6):
        d.rectangle([x - 2 + k, yb - 12, x + 1 + k, yb - 8], fill=(214, 60, 52))


def med_box(d, x, yb):
    d.rectangle([x, yb - 14, x + 16, yb], fill=(240, 242, 246), outline=OL)
    d.rectangle([x + 6, yb - 12, x + 10, yb - 2], fill=(70, 170, 110))
    d.rectangle([x + 3, yb - 9, x + 13, yb - 5], fill=(70, 170, 110))


def wheelchair(d, x, yb):
    d.ellipse([x, yb - 10, x + 10, yb], outline=(70, 74, 90), width=2)
    d.rectangle([x + 3, yb - 18, x + 5, yb - 8], fill=(70, 74, 90))
    d.rectangle([x + 3, yb - 10, x + 11, yb - 8], fill=(80, 120, 190))


def console(d, x, yb):
    d.rectangle([x, yb - 22, x + 18, yb], fill=(56, 66, 84), outline=OL)
    d.rectangle([x + 2, yb - 20, x + 16, yb - 10], fill=(80, 220, 230))
    for k in range(3):
        d.line([(x + 4, yb - 18 + k * 3), (x + 4 + 4 + k * 3, yb - 18 + k * 3)], fill=(220, 250, 255))
    d.rectangle([x + 4, yb - 7, x + 14, yb - 4], fill=(40, 46, 60))


def antenna(d, x, yb):
    d.line([(x, yb), (x, yb - 26)], fill=(110, 120, 140), width=2)
    d.ellipse([x - 3, yb - 30, x + 3, yb - 24], fill=(90, 230, 230), outline=OL)


def lounger(d, x, yb):
    d.polygon([(x, yb - 4), (x + 18, yb - 4), (x + 22, yb - 10), (x + 18, yb - 6), (x, yb - 6)], fill=(246, 246, 240), outline=OL)
    d.line([(x + 2, yb - 4), (x + 2, yb)], fill=OL)
    d.line([(x + 16, yb - 4), (x + 16, yb)], fill=OL)


def barrel(d, x, yb, c=(190, 80, 50)):
    d.rectangle([x, yb - 12, x + 9, yb], fill=c, outline=OL)
    d.line([(x, yb - 8), (x + 9, yb - 8)], fill=shade(c, 0.7))
    d.line([(x, yb - 4), (x + 9, yb - 4)], fill=shade(c, 0.7))


def pallet(d, x, yb):
    d.rectangle([x, yb - 4, x + 18, yb], fill=(170, 132, 84), outline=OL)
    for k in (2, 8, 14):
        d.rectangle([x + k, yb - 2, x + k + 2, yb], fill=(110, 84, 54))


def mushrooms(d, x, yb):
    for mx, s in ((x, 4), (x + 6, 3)):
        d.rectangle([mx, yb - s, mx + 1, yb], fill=(236, 226, 206))
        d.pieslice([mx - s, yb - s * 2 - 1, mx + s + 1, yb - s + 2], 180, 360, fill=(214, 70, 60), outline=OL)


def candle(d, x, yb):
    d.rectangle([x, yb - 12, x + 2, yb], fill=(150, 120, 60))
    d.rectangle([x - 4, yb - 14, x + 6, yb - 12], fill=(150, 120, 60))
    for k in (-4, 0, 4):
        d.rectangle([x + k + 1, yb - 18, x + k + 2, yb - 14], fill=(246, 240, 220))
        d.point((x + k + 1, yb - 19), fill=(250, 200, 80))


# ── 지역 ────────────────────────────────────────────
# 각 지역: bg(d, rng) 로 하늘 · 먼 풍경 · 땅, plat = (윗면, 테, 꾸밈), props(d) 로 소품 (발판 뒤)
# 소품 자리: 왼쪽 뒤 x≈160~176 · 오른쪽 뒤 x≈246~262, 바닥 y≈64
L, R_ = 162, 250
YB = 64


def alley_bg(d, rng):
    sky(d, SKY["day"])
    skyline(d, rng, (170, 182, 204), (192, 202, 222), 16, 40)
    for x0, x1, h in ((0, 34, 44), (30, 70, 30), (66, 98, 22), (238, 270, 26), (266, 296, 38), (292, 320, 48)):
        building(d, x0, x1, h, (132, 140, 164), (156, 164, 186))
    d.rectangle([34, HOR - 20, 66, HOR - 16], fill=(70, 150, 112))
    d.line([(34, HOR - 16), (66, HOR - 16)], fill=(226, 140, 70))
    poles(d, [22, 300])
    ground(d, [(2, (196, 196, 204)), (10, (204, 162, 160)), (6, (188, 146, 146)), (22, (122, 124, 136)), (30, (112, 114, 126)), (0, (102, 104, 116))])


def alley_props(d):
    bags(d, L + 4, YB - 6)
    vending(d, R_ + 2, YB)


def archery_bg(d, rng):
    sky(d, SKY["day"])
    hills(d, rng, HOR - 6, 6, (150, 186, 150))
    treeline(d, rng, (236, 196, 214), 10, r=(7, 12), dark=(212, 170, 192))  # 벚나무
    for x in range(0, W, 16):  # 초록 철망
        d.line([(x, HOR - 12), (x, HOR)], fill=(84, 130, 96))
    d.line([(0, HOR - 12), (W, HOR - 12)], fill=(84, 130, 96))
    for x in (60, 120, 200, 270):
        d.ellipse([x - 4, HOR - 10, x + 4, HOR - 2], fill=(240, 240, 236))
        d.ellipse([x - 2, HOR - 8, x + 2, HOR - 4], fill=(220, 70, 60))
    ground(d, [(8, (128, 176, 104)), (16, (116, 164, 94)), (24, (106, 152, 86)), (0, (96, 140, 80))])


def archery_props(d):
    apple_tree(d, L + 2, YB)
    target(d, R_ + 6, YB)
    vending(d, R_ + 16, YB + 2, body=(70, 140, 200))


def stream_bg(d, rng):
    sky(d, SKY["day"])
    treeline(d, rng, (92, 150, 104), 10, r=(7, 13), dark=(74, 128, 88))
    ground(d, [(8, (126, 174, 106)), (10, (96, 160, 206)), (6, (120, 176, 214)), (18, (118, 166, 100)), (0, (106, 154, 90))])
    for _ in range(14):
        x = rng.randint(0, W)
        d.line([(x, HOR + 11), (x + 8, HOR + 11)], fill=(200, 226, 240))


def stream_props(d):
    rocks(d, L, YB - 2)
    reeds(d, L + 14, YB - 2)
    vending(d, R_ + 2, YB, body=(70, 140, 200))


def forest_bg(d, rng):
    sky(d, SKY["green"])
    treeline(d, rng, (84, 128, 100), 26, r=(10, 18), dark=(70, 112, 86))
    treeline(d, rng, (60, 104, 76), 12, r=(8, 14), dark=(50, 90, 66))
    ground(d, [(10, (74, 120, 76)), (18, (66, 110, 68)), (0, (58, 100, 62))])


def forest_props(d):
    apple_tree(d, L + 2, YB, gold=True)
    mushrooms(d, L + 16, YB - 2)
    vending(d, R_ + 2, YB, body=(80, 150, 90))


def uptown_bg(d, rng):
    sky(d, SKY["day"])
    treeline(d, rng, (120, 160, 120), 6, r=(6, 10), dark=(104, 146, 106))
    for x0, x1, h, wall, roof in ((0, 40, 28, (226, 214, 196), (176, 84, 66)), (44, 84, 22, (214, 204, 190), (150, 76, 60)),
                                  (230, 268, 24, (230, 220, 204), (170, 90, 70)), (272, 320, 30, (216, 206, 192), (156, 80, 64))):
        building(d, x0, x1, h, wall, (150, 170, 196), roof=(10, roof), step=8)
    for x in (100, 150, 200):
        lamp(d, x, HOR + 2)
    ground(d, [(4, (180, 186, 160)), (8, (190, 120, 104)), (8, (176, 110, 96)), (22, (150, 150, 158)), (0, (138, 138, 146))])


def uptown_props(d):
    lamp(d, L + 2, YB)
    vending(d, R_ + 2, YB, body=(90, 110, 170))


def harbor_bg(d, rng):
    sky(d, SKY["sea"])
    sea(d, HOR - 10, HOR, (84, 132, 180), (150, 190, 220), rng)
    d.rectangle([24, HOR - 46, 34, HOR], fill=(240, 236, 230))  # 등대
    for y in range(HOR - 42, HOR, 10):
        d.rectangle([24, y, 34, y + 4], fill=(200, 70, 60))
    d.rectangle([22, HOR - 52, 36, HOR - 46], fill=(70, 74, 90))
    d.rectangle([26, HOR - 50, 32, HOR - 48], fill=(250, 226, 140))
    for x0, x1, h in ((210, 250, 18), (252, 290, 24)):
        building(d, x0, x1, h, (150, 120, 110), None, roof=(6, (170, 80, 70)))
    d.rectangle([296, HOR - 40, 300, HOR], fill=(214, 160, 50))
    d.rectangle([270, HOR - 40, 316, HOR - 37], fill=(214, 160, 50))
    ground(d, [(4, (150, 150, 156)), (6, (226, 186, 70)), (24, (140, 140, 148)), (0, (126, 126, 134))])


def harbor_props(d):
    bollard(d, L + 4, YB)
    buoy(d, L + 16, YB)
    vending(d, R_ + 2, YB, body=(70, 120, 180))


def pond_bg(d, rng):
    sky(d, SKY["day"])
    treeline(d, rng, (104, 156, 110), 10, r=(7, 12), dark=(88, 140, 96))
    for x in (40, 260):  # 버드나무
        d.ellipse([x - 12, HOR - 30, x + 12, HOR - 4], fill=(140, 180, 100))
        for k in range(-10, 11, 3):
            d.line([(x + k, HOR - 18), (x + k, HOR - 2)], fill=(120, 164, 86))
    ground(d, [(6, (126, 172, 104)), (14, (92, 150, 180)), (6, (108, 164, 192)), (16, (116, 164, 98)), (0, (104, 152, 88))])


def pond_props(d):
    apple_tree(d, L + 2, YB)
    reeds(d, R_ - 4, YB - 2)
    vending(d, R_ + 8, YB, body=(70, 140, 200))


def beach_bg(d, rng):
    sky(d, SKY["sea"])
    sea(d, HOR - 12, HOR, (70, 140, 190), (170, 210, 236), rng)
    for x, k in ((16, 1), (300, -1)):  # 야자수
        d.line([(x, HOR + 4), (x + 4 * k, HOR - 34)], fill=(110, 84, 60), width=3)
        for a in (-0.9, -0.3, 0.3, 0.9, 1.6, -1.6):
            ex, ey = x + 4 * k + int(16 * math.cos(a - math.pi / 2)), HOR - 34 + int(10 * math.sin(a - math.pi / 2) + 6)
            d.line([(x + 4 * k, HOR - 34), (ex, ey)], fill=(70, 130, 80), width=3)
    ground(d, [(6, (232, 216, 176)), (18, (226, 206, 162)), (0, (214, 194, 150))])


def beach_props(d):
    umbrella(d, L + 8, YB)
    vending(d, R_ + 2, YB, body=(236, 150, 60))


def temple_bg(d, rng):
    sky(d, SKY["warm"])
    mountains(d, [(40, 30, 50), (120, 22, 40), (220, 34, 60), (300, 24, 40)], (140, 160, 168))
    treeline(d, rng, (96, 140, 98), 6, r=(6, 10), dark=(82, 124, 86))
    d.rectangle([130, HOR - 20, 190, HOR], fill=(150, 90, 70))  # 절 (기와지붕)
    d.polygon([(120, HOR - 20), (160, HOR - 32), (200, HOR - 20)], fill=(70, 74, 84))
    d.line([(118, HOR - 20), (202, HOR - 20)], fill=(52, 56, 64), width=2)
    for x in range(136, 186, 8):
        d.rectangle([x, HOR - 16, x + 4, HOR - 4], fill=(200, 150, 90))
    ground(d, [(6, (196, 176, 140)), (20, (184, 164, 128)), (0, (172, 152, 118))])


def temple_props(d):
    lantern(d, L + 6, YB)
    apple_tree(d, R_ + 6, YB)


def gas_bg(d, rng):
    sky(d, SKY["day"])
    treeline(d, rng, (120, 160, 120), 6, r=(6, 10), dark=(104, 146, 106))
    d.rectangle([80, HOR - 30, 240, HOR - 24], fill=(70, 110, 180))  # 주유소 지붕
    d.rectangle([80, HOR - 24, 240, HOR - 22], fill=(240, 240, 244))
    for x in (100, 156, 212):
        d.rectangle([x, HOR - 22, x + 4, HOR], fill=(220, 222, 228))
    for x in (120, 176):
        d.rectangle([x, HOR - 12, x + 8, HOR], fill=(230, 232, 236))
        d.rectangle([x + 2, HOR - 10, x + 6, HOR - 7], fill=(70, 110, 180))
    building(d, 250, 300, 22, (226, 226, 230), (150, 186, 210))
    ground(d, [(4, (190, 190, 198)), (26, (120, 122, 134)), (0, (108, 110, 122))])
    for x in range(0, W, 24):
        d.rectangle([x, HOR + 16, x + 12, HOR + 17], fill=(226, 196, 70))


def gas_props(d):
    pump(d, L, YB)
    tires(d, L + 14, YB)
    vending(d, R_ + 2, YB, body=(70, 110, 180))


def warehouse_bg(d, rng):
    sky(d, SKY["grey"])
    for x0, x1, h, c in ((0, 70, 34, (120, 130, 150)), (74, 140, 28, (106, 118, 140)), (190, 260, 32, (118, 128, 148)), (262, 320, 26, (104, 116, 136))):
        d.rectangle([x0, HOR - h, x1, HOR], fill=c)
        for x in range(x0 + 3, x1, 4):  # 골함석
            d.line([(x, HOR - h + 2), (x, HOR)], fill=shade(c, 0.9))
        d.polygon([(x0 - 2, HOR - h), ((x0 + x1) // 2, HOR - h - 8), (x1 + 2, HOR - h)], fill=shade(c, 0.8))
    for x, c in ((146, (180, 90, 60)), (164, (70, 120, 170)), (155, (190, 150, 60))):
        d.rectangle([x, HOR - (16 if x == 155 else 8), x + 16, HOR - (8 if x == 155 else 0)], fill=c)
    ground(d, [(4, (168, 168, 174)), (26, (150, 150, 158)), (0, (138, 138, 146))])


def warehouse_props(d):
    crates(d, L, YB)
    pallet(d, R_ - 8, YB)
    vending(d, R_ + 12, YB, body=(110, 120, 140))


def school_bg(d, rng):
    sky(d, SKY["day"])
    treeline(d, rng, (236, 200, 216), 8, r=(6, 10), dark=(214, 176, 196))  # 벚나무
    building(d, 70, 250, 30, (226, 214, 190), (150, 180, 210), step=8)
    d.rectangle([150, HOR - 40, 170, HOR - 30], fill=(226, 214, 190))
    d.ellipse([154, HOR - 39, 166, HOR - 31], fill=(250, 250, 246), outline=(90, 80, 70))
    d.line([(160, HOR - 35), (160, HOR - 38)], fill=(60, 50, 50))
    ground(d, [(4, (180, 200, 160)), (24, (206, 170, 120)), (0, (196, 160, 112))])


def school_props(d):
    clock(d, L + 2, YB)
    vending(d, R_ + 2, YB, body=(200, 90, 70))


def factory_bg(d, rng):
    sky(d, SKY["grey"])
    for x, h in ((40, 50), (60, 40), (250, 46)):  # 굴뚝 + 연기
        d.rectangle([x, HOR - h, x + 8, HOR], fill=(120, 110, 104))
        d.rectangle([x, HOR - h, x + 8, HOR - h + 3], fill=(170, 80, 60))
        for k in range(3):
            d.ellipse([x - 2 + k * 6, HOR - h - 10 - k * 6, x + 10 + k * 6, HOR - h - k * 6], fill=(160, 164, 172))
    building(d, 0, 110, 26, (128, 122, 120), (150, 146, 140))
    building(d, 200, 320, 30, (124, 118, 116), (150, 146, 140))
    d.ellipse([140, HOR - 22, 178, HOR + 2], fill=(150, 156, 164))  # 탱크
    d.line([(110, HOR - 14), (200, HOR - 14)], fill=(100, 96, 96), width=2)  # 배관
    ground(d, [(4, (170, 164, 156)), (26, (148, 144, 140)), (0, (136, 132, 128))])


def factory_props(d):
    vending(d, L, YB, body=(200, 80, 60))
    vending(d, L + 15, YB, body=(70, 120, 180))
    barrel(d, R_ + 4, YB)


def fire_bg(d, rng):
    sky(d, SKY["day"])
    skyline(d, rng, (172, 184, 204), (194, 204, 222), 12, 30)
    d.rectangle([90, HOR - 30, 230, HOR], fill=(176, 92, 74))  # 벽돌 소방서
    for x in (100, 142, 184):
        d.rectangle([x, HOR - 20, x + 34, HOR], fill=(220, 70, 60))
        for y in range(HOR - 18, HOR, 4):
            d.line([(x + 1, y), (x + 33, y)], fill=(190, 56, 50))
    d.rectangle([232, HOR - 50, 248, HOR], fill=(176, 92, 74))
    ground(d, [(4, (190, 190, 198)), (26, (122, 124, 136)), (0, (110, 112, 124))])
    d.rectangle([0, HOR + 18, W, HOR + 19], fill=(226, 196, 70))


def fire_props(d):
    hydrant(d, L + 6, YB)
    hose(d, L + 14, YB)
    vending(d, R_ + 2, YB, body=(200, 70, 60))


def cemetery_bg(d, rng):
    sky(d, SKY["grey"])
    treeline(d, rng, (112, 126, 120), 10, r=(8, 14), dark=(98, 112, 106))
    for x in (60, 250):  # 납골당
        d.rectangle([x, HOR - 22, x + 26, HOR], fill=(150, 150, 154))
        d.polygon([(x - 3, HOR - 22), (x + 13, HOR - 32), (x + 29, HOR - 22)], fill=(124, 124, 130))
        d.rectangle([x + 9, HOR - 14, x + 17, HOR], fill=(96, 96, 104))
    for x in range(0, W, 6):  # 철 울타리
        d.line([(x, HOR - 8), (x, HOR)], fill=(70, 72, 80))
    d.line([(0, HOR - 6), (W, HOR - 6)], fill=(70, 72, 80))
    ground(d, [(6, (100, 120, 96)), (20, (92, 110, 88)), (0, (84, 100, 80))])


def cemetery_props(d):
    grave(d, L, YB)
    grave(d, L + 12, YB, cross=True)
    apple_tree(d, R_ - 2, YB)
    vending(d, R_ + 12, YB, body=(110, 110, 130))


def police_bg(d, rng):
    sky(d, SKY["day"])
    skyline(d, rng, (172, 184, 204), (194, 204, 222), 12, 28)
    building(d, 80, 240, 32, (226, 230, 238), (110, 140, 190), step=8)
    d.rectangle([140, HOR - 40, 180, HOR - 33], fill=(50, 70, 140))
    d.rectangle([150, HOR - 38, 170, HOR - 35], fill=(240, 240, 246))
    d.rectangle([250, HOR - 44, 251, HOR], fill=(150, 150, 160))
    d.rectangle([252, HOR - 44, 264, HOR - 37], fill=(60, 90, 170))
    ground(d, [(4, (196, 196, 204)), (26, (124, 126, 138)), (0, (112, 114, 126))])


def police_props(d):
    barrier(d, L - 2, YB)
    lost_box(d, R_ - 4, YB)
    vending(d, R_ + 12, YB, body=(60, 90, 170))


def chapel_bg(d, rng):
    sky(d, SKY["day"])
    mountains(d, [(30, 26, 44), (290, 30, 50)], (150, 170, 190))
    d.rectangle([110, HOR - 28, 210, HOR], fill=(236, 226, 206))  # 성당 (크림 벽 · 파란 지붕)
    for x, h in ((112, 46), (150, 58), (196, 44)):
        d.rectangle([x, HOR - h + 12, x + 12, HOR], fill=(236, 226, 206))
        d.polygon([(x - 2, HOR - h + 12), (x + 6, HOR - h), (x + 14, HOR - h + 12)], fill=(80, 110, 180))
    d.ellipse([154, HOR - 24, 166, HOR - 12], fill=(120, 150, 210), outline=(180, 160, 120))
    for x in range(120, 205, 10):
        d.rectangle([x, HOR - 18, x + 3, HOR - 8], fill=(120, 150, 210))
    ground(d, [(6, (196, 190, 176)), (20, (186, 178, 164)), (0, (174, 166, 152))])


def chapel_props(d):
    apple_tree(d, L + 2, YB)
    candle(d, R_ - 2, YB)
    vending(d, R_ + 10, YB, body=(80, 110, 180))


def hospital_bg(d, rng):
    sky(d, SKY["day"])
    treeline(d, rng, (236, 204, 218), 6, r=(6, 9), dark=(216, 182, 200))
    building(d, 90, 230, 34, (240, 242, 246), (150, 186, 214), step=8)
    d.rectangle([150, HOR - 46, 170, HOR - 34], fill=(240, 242, 246))
    d.rectangle([157, HOR - 44, 163, HOR - 36], fill=(70, 170, 110))  # 초록 십자 (이터널 리턴 병원)
    d.rectangle([153, HOR - 42, 167, HOR - 38], fill=(70, 170, 110))
    building(d, 236, 300, 24, (226, 228, 234), (150, 186, 214))
    ground(d, [(4, (200, 200, 208)), (26, (128, 130, 142)), (0, (116, 118, 130))])


def hospital_props(d):
    wheelchair(d, L + 4, YB)
    med_box(d, R_ - 6, YB)
    vending(d, R_ + 12, YB, body=(70, 160, 110))


def lab_bg(d, rng):
    sky(d, SKY["lab"])
    d.polygon([(80, HOR), (160, HOR - 44), (240, HOR)], fill=(84, 96, 118))  # 연구소 (마름모 요새)
    d.polygon([(110, HOR), (160, HOR - 28), (210, HOR)], fill=(100, 114, 138))
    d.line([(160, HOR - 44), (160, HOR - 58)], fill=(110, 124, 150), width=2)
    d.ellipse([157, HOR - 62, 163, HOR - 56], fill=(90, 230, 230))
    for x0, x1, h in ((0, 60, 20), (260, 320, 24)):
        d.rectangle([x0, HOR - h, x1, HOR], fill=(70, 82, 102))
        d.line([(x0, HOR - h + 4), (x1, HOR - h + 4)], fill=(90, 220, 230))
    ground(d, [(4, (90, 104, 124)), (26, (78, 90, 108)), (0, (68, 80, 96))])
    for x in range(0, W, 30):
        d.line([(x, HOR + 6), (x + 12, HOR + 6)], fill=(90, 210, 220))


def lab_props(d):
    console(d, L - 2, YB)
    antenna(d, R_ + 8, YB)


def hotel_bg(d, rng):
    sky(d, SKY["sea"])
    for i, (x0, x1, h) in enumerate(((60, 260, 22), (80, 240, 34), (100, 220, 46))):  # 계단식 하얀 호텔
        building(d, x0, x1, h, (240, 240, 236), (150, 190, 214), step=7)
    for x, k in ((20, 1), (296, -1)):
        d.line([(x, HOR + 2), (x + 3 * k, HOR - 26)], fill=(110, 84, 60), width=3)
        for a in (-0.9, -0.3, 0.3, 0.9, 1.6, -1.6):
            ex, ey = x + 3 * k + int(14 * math.cos(a - math.pi / 2)), HOR - 26 + int(9 * math.sin(a - math.pi / 2) + 5)
            d.line([(x + 3 * k, HOR - 26), (ex, ey)], fill=(70, 140, 84), width=3)
    ground(d, [(4, (226, 222, 210)), (10, (110, 190, 220)), (16, (214, 210, 198)), (0, (202, 198, 186))])


def hotel_props(d):
    lounger(d, L - 4, YB)
    umbrella(d, R_ - 2, YB, c=(60, 130, 200))
    vending(d, R_ + 12, YB, body=(60, 130, 200))


def barge_bg(d, rng):
    sky(d, SKY["dusk"])
    sea(d, HOR - 8, HOR, (70, 92, 124), (120, 140, 170), rng)
    for x0, x1 in ((0, 90), (110, 210), (230, 320)):  # 이어진 배
        d.polygon([(x0, HOR - 12), (x1, HOR - 12), (x1 - 6, HOR), (x0 + 6, HOR)], fill=(66, 70, 84))
        d.rectangle([x0 + 10, HOR - 22, x0 + 34, HOR - 12], fill=(84, 90, 106))
    d.rectangle([150, HOR - 56, 156, HOR - 12], fill=(214, 160, 50))  # 크레인
    d.rectangle([120, HOR - 60, 210, HOR - 56], fill=(214, 160, 50))
    d.line([(200, HOR - 56), (200, HOR - 36)], fill=OL)
    barrel(d, 196, HOR - 24)
    ground(d, [(4, (94, 100, 114)), (6, (226, 186, 60)), (20, (86, 92, 106)), (0, (76, 82, 96))])


def barge_props(d):
    barrel(d, L, YB, (190, 80, 50))
    barrel(d, L + 10, YB, (60, 110, 150))
    vending(d, R_ + 2, YB, body=(196, 130, 50))


# 지역 → (배경, 소품, 윗면, 꾸밈)
REGIONS = {
    "alley": (alley_bg, alley_props, split(s_crosswalk(), s_bricks((204, 162, 160), (188, 146, 146))), "manhole"),
    "archery": (archery_bg, archery_props, s_grass((122, 172, 98), (106, 156, 86), (150, 196, 120)), "lane"),
    "stream": (stream_bg, stream_props, wavy_split(s_grass((122, 172, 98), (106, 156, 86), (150, 196, 120)),
                                                   s_water((96, 160, 206), (120, 178, 216), (210, 232, 244)), 0.58, edge=(150, 146, 136)), "stones"),
    "forest": (forest_bg, forest_props, wavy_split(s_grass((84, 136, 82), (70, 120, 70), (110, 160, 96)),
                                                   s_dirt((150, 120, 86), (130, 102, 72)), 0.7, 0.05), "tufts"),
    "uptown": (uptown_bg, uptown_props, split(s_herring((196, 128, 110), (170, 104, 90)), s_grass((110, 156, 96), (96, 140, 84), (130, 176, 110)), 0.72, (186, 186, 190)), None),
    "harbor": (harbor_bg, harbor_props, split(s_planks((168, 128, 86), (120, 88, 60)), s_water((76, 132, 184), (100, 152, 200), (196, 222, 240)), 0.7, (140, 140, 146)), "rope"),
    "pond": (pond_bg, pond_props, wavy_split(s_grass((122, 172, 98), (106, 156, 86), (150, 196, 120)),
                                             s_water((88, 150, 176), (110, 168, 192), (196, 226, 236)), 0.5, 0.08, edge=(150, 146, 120)), "lily"),
    "beach": (beach_bg, beach_props, wavy_split(s_sand((232, 214, 172), (214, 194, 150)),
                                               s_water((70, 150, 210), (96, 170, 224), (220, 240, 250)), 0.6, 0.07, edge=(246, 246, 240)), "shells"),
    "temple": (temple_bg, temple_props, s_stone((176, 170, 158), (132, 126, 118), (190, 184, 170)), None),
    "gas": (gas_bg, gas_props, s_asphalt(), "parking"),
    "warehouse": (warehouse_bg, warehouse_props, s_hazard((150, 150, 158)), None),
    "school": (school_bg, school_props, s_track((196, 90, 70)), None),
    "factory": (factory_bg, factory_props, s_metal((134, 138, 146), (104, 108, 118)), "hazard"),
    "fire": (fire_bg, fire_props, s_asphalt((100, 102, 114)), "firelane"),
    "cemetery": (cemetery_bg, cemetery_props, wavy_split(s_dirt((112, 100, 84), (96, 86, 72)), s_grass((92, 116, 86), (80, 102, 76), (110, 132, 100)), 0.55, 0.06), "slab"),
    "police": (police_bg, police_props, s_tiles((150, 154, 166), (126, 130, 142)), "parking"),
    "chapel": (chapel_bg, chapel_props, s_stone((200, 192, 176), (156, 148, 136), (214, 206, 190)), "rose"),
    "hospital": (hospital_bg, hospital_props, s_tiles((226, 230, 236), (196, 202, 212), 10, 5), "cross"),
    "lab": (lab_bg, lab_props, s_glow((78, 90, 110), (64, 74, 92), (90, 220, 230)), None),
    "hotel": (hotel_bg, hotel_props, split(s_tiles((230, 228, 220), (206, 202, 192)), s_water((96, 190, 222), (130, 206, 232), (230, 246, 250)), 0.62, (246, 246, 246)), None),
    "barge": (barge_bg, barge_props, s_metal((96, 102, 116), (76, 82, 96), 20), "hazard"),
}


def decor_fn(kind):
    """발판 위 꾸밈 (상대 발판에만, 실험체가 서는 가운데는 비워요)"""
    def f(d, w, h, rng):
        if kind == "manhole":
            d.ellipse([10, 16, 20, 20], fill=(70, 72, 82), outline=(54, 56, 66))
        elif kind == "lane":
            for x in (30, 64, 98):
                d.line([(x, 6), (x + 2, h - 6)], fill=(236, 240, 226))
        elif kind == "stones":
            for x, y in ((78, 10), (88, 20), (96, 13)):
                d.ellipse([x, y, x + 6, y + 3], fill=(150, 148, 140), outline=(110, 108, 100))
        elif kind == "tufts":
            for x, y in ((14, 14), (30, 22), (52, 9)):
                for k in range(3):
                    d.line([(x + k * 2, y), (x + k * 2 - 1 + k, y - 3)], fill=(60, 110, 60))
        elif kind == "rope":
            d.ellipse([12, 14, 24, 20], outline=(200, 170, 110), width=2)
        elif kind == "lily":
            for x, y in ((80, 12), (96, 20), (104, 10)):
                d.ellipse([x, y, x + 6, y + 3], fill=(84, 150, 84))
        elif kind == "shells":
            for x, y in ((20, 12), (40, 22)):
                d.ellipse([x, y, x + 3, y + 2], fill=(246, 210, 200))
        elif kind == "parking":
            for x in (20, 44, 84, 108):
                d.line([(x, 8), (x - 2, h - 8)], fill=(236, 236, 240))
        elif kind == "hazard":
            for x in range(10, w - 10, 6):
                if 6 < x < 30 or w - 30 < x < w - 6:
                    d.line([(x, h - 9), (x + 3, h - 6)], fill=(226, 186, 60), width=2)
        elif kind == "firelane":  # 앞쪽 가장자리 빨강 · 하양 빗금 (소방차 자리)
            for x in range(16, w - 16, 6):
                d.line([(x, h - 8), (x + 3, h - 5)], fill=(210, 64, 56) if (x // 6) % 2 else (236, 236, 240), width=2)
        elif kind == "slab":
            d.rectangle([18, 12, 32, 18], fill=(150, 150, 154), outline=(110, 110, 116))
        elif kind == "rose":
            cx, cy = w // 2, h // 2
            d.ellipse([cx - 14, cy - 5, cx + 14, cy + 5], outline=(150, 140, 120))
            d.ellipse([cx - 6, cy - 2, cx + 6, cy + 2], outline=(150, 140, 120))
        elif kind == "cross":
            cx, cy = w // 2 + 30, h // 2
            d.rectangle([cx - 2, cy - 5, cx + 2, cy + 5], fill=(70, 170, 110))
            d.rectangle([cx - 7, cy - 2, cx + 7, cy + 2], fill=(70, 170, 110))
    return f if kind else None


def draw_region(name):
    bg_fn, props_fn, surface, deco = REGIONS[name]
    rng = random.Random(name)
    bg = Image.new("RGB", (W, H))
    bg_fn(ImageDraw.Draw(bg), rng)
    bg = speed_blur(bg)
    b = Image.new("RGBA", (W, 132), (0, 0, 0, 0))
    props = Image.new("RGBA", (W, 132), (0, 0, 0, 0))
    props_fn(ImageDraw.Draw(props))
    b.alpha_composite(props)
    b.alpha_composite(platform(128, 33, surface, 2, decor=decor_fn(deco)), (152, 57))
    a = Image.new("RGBA", (W, 132), (0, 0, 0, 0))
    a.alpha_composite(platform(120, 30, surface, 1), (44, 117))
    return bg.convert("RGBA"), a, b


def save(img, path):
    img.save(path, optimize=True)
    done.append(str(path.relative_to(ROOT / "assets")).replace("\\", "/"))


def main():
    only = next((a.split(",") for a in sys.argv[sys.argv.index("--only") + 1:][:1]), None) if "--only" in sys.argv else None
    drawn = {name: draw_region(name) for name in REGIONS if not only or name in only}
    empty = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    for biome, region in BIOME_REGION.items():
        if region not in drawn or not (ARENA / f"{biome}_bg.png").exists():
            continue
        bg, a, b = drawn[region]
        save(bg, ARENA / f"{biome}_bg.png")
        save(a, ARENA / f"{biome}_a.png")
        save(b, ARENA / f"{biome}_b.png")
        for k in (1, 2, 3):
            if (ARENA / f"{biome}_b_{k}.png").exists():
                save(empty, ARENA / f"{biome}_b_{k}.png")
    if MARK.exists():
        marks = set(json.load(open(MARK, encoding="utf-8")))
        before = len(marks)
        marks -= set(done)
        json.dump(sorted(marks), open(MARK, "w", encoding="utf-8"), ensure_ascii=False, indent=0)
        print(f"임시 그림 목록에서 뺀 것: {before - len(marks)}개")
    print(f"지역 {len(drawn)}곳 · 그림 {len(done)}개")
    if "--preview" in sys.argv:
        out = Path(sys.argv[sys.argv.index("--preview") + 1])
        cols = 4
        sheet = Image.new("RGB", (W * cols, (H - 48) * math.ceil(len(drawn) / cols)), (0, 0, 0))
        for i, (name, (bg, a, b)) in enumerate(drawn.items()):
            tile = bg.copy()
            tile.alpha_composite(b, (0, 0))
            tile.alpha_composite(a, (0, 0))
            ImageDraw.Draw(tile).text((4, 4), name, fill=(255, 255, 255))
            sheet.paste(tile.crop((0, 0, W, H - 48)).convert("RGB"), ((i % cols) * W, (i // cols) * (H - 48)))
        sheet.save(out, optimize=True)
        print("미리보기", out)


if __name__ == "__main__":
    main()
