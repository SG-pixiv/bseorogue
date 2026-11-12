# SPDX-FileCopyrightText: 2026 SG
# SPDX-License-Identifier: AGPL-3.0-only
"""
블서로그 지역 배경 21곳 (루미아 섬) — 전투 배경 · 발판을 코드로 그려요

2026년 이터널 리턴 기준이에요 (공식 패치노트, 팬키트에는 지역 그림이 없고 섬 지도만 있어요):
  - 시즌 11 (2026-04): 21번째 지역 바지선 (항구와 공장 사이, 배 4척이 이어진 어두운 해상 작업장, 크레인 · 배럴),
    자연 지역(숲 · 연못 · 절 · 양궁장 · 성당 · 묘지) 사과나무, 학교 괘종시계, 경찰서 분실물 상자, 병원 의료 지원
  - 시즌 13 (2026-11): 연구소를 뺀 모든 지역에 음식 자판기 (공장은 2대)

포켓로그 지역(바이옴) 35곳을 루미아 섬 21곳에 나눠 붙였어요 (이름은 locales/ko/biomes.json, 역할군은
src/data/bseorogue/regions.ts). 같은 지역에 붙은 바이옴은 같은 그림을 써요.
  - <바이옴>_bg.png   320×180 배경 (지평선 y≈66, 아래 48칸은 전투 창에 가려요)
  - <바이옴>_a.png    320×132 내 발판 (가운데 104, 132 · 반만 보여요)
  - <바이옴>_b.png    320×132 상대 발판 (가운데 216, 72)
  - <바이옴>_b_1~3    상대 발판 위 소품 (투명, 지금은 안 써요)
도트 느낌으로 1배에 바로 그려요 (부드럽게 하지 않아요). 지역마다 함수 하나 (REGIONS).

쓰는 법 (저장소 맨 위에서): python3 -B scripts/er-ui/make_arenas.py [--preview docs/arenas-preview.png]
그린 파일은 assets/.placeholders.json 에서 빠져요 (임시 그림 만들기가 덮어쓰지 않게).
"""
import json
import math
import random
import sys
from pathlib import Path

from PIL import Image, ImageDraw

ROOT = Path(__file__).resolve().parents[2]
ARENA = ROOT / "assets" / "images" / "arenas"
MARK = ROOT / "assets" / ".placeholders.json"
W, H = 320, 180
HORIZON = 66
OUTLINE = (26, 28, 44)

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


# ── 그리기 도우미 ─────────────────────────────────
def shade(c, k):
    return tuple(max(0, min(255, int(v * k))) for v in c[:3])


def sky(d, top, bottom, y0=0, y1=HORIZON, bands=8):
    for y in range(y0, y1):
        t = (y - y0) / max(1, y1 - y0 - 1)
        t = round(t * (bands - 1)) / (bands - 1)  # 띠 모양 (도트 느낌)
        d.line([(0, y), (W, y)], fill=tuple(int(top[i] + (bottom[i] - top[i]) * t) for i in range(3)))


def ground(d, color, y0=HORIZON, stripes=None):
    d.rectangle([0, y0, W, H], fill=color)
    if stripes:
        for i, y in enumerate(range(y0, H, 6)):
            d.line([(0, y), (W, y)], fill=stripes if i % 2 else shade(color, 0.96))


def building(d, x, y, w, h, color, win=(255, 226, 140), cols=None, rows=None, roof=None, rng=None):
    d.rectangle([x, y, x + w, HORIZON + 2], fill=color, outline=shade(color, 0.7))
    if roof:
        d.polygon([(x - 3, y), (x + w // 2, y - roof), (x + w + 3, y)], fill=shade(color, 0.75))
    cols = cols or max(1, w // 9)
    rows = rows or max(1, (HORIZON - y) // 10)
    for r in range(rows):
        for c in range(cols):
            wx = x + 3 + c * (w - 4) // cols
            wy = y + 4 + r * 9
            if wy + 4 > HORIZON:
                continue
            lit = rng.random() < 0.55 if rng else True
            d.rectangle([wx, wy, wx + 3, wy + 4], fill=win if lit else shade(color, 0.6))


def tree(d, x, y, r, leaf=(58, 120, 66), trunk=(92, 64, 44)):
    d.rectangle([x - 1, y, x + 1, y + r + 4], fill=trunk)
    d.ellipse([x - r, y - r, x + r, y + r // 2], fill=leaf, outline=shade(leaf, 0.7))
    d.ellipse([x - r + 2, y - r + 1, x, y - r // 3], fill=shade(leaf, 1.2))


def pine(d, x, y, h, leaf=(40, 96, 70)):
    d.rectangle([x - 1, y + h - 3, x + 1, y + h + 2], fill=(80, 56, 40))
    for k in range(3):
        top = y + k * h // 4
        w = (k + 2) * h // 7
        d.polygon([(x, top), (x - w, top + h // 2), (x + w, top + h // 2)], fill=shade(leaf, 1 + k * 0.08), outline=shade(leaf, 0.7))


def vending(d, x, y=HORIZON + 3, c=(52, 104, 196)):
    """음식 자판기 (시즌 13). (x, y) = 왼쪽 아래"""
    d.rectangle([x, y - 16, x + 9, y], fill=c, outline=OUTLINE)
    d.rectangle([x + 1, y - 15, x + 8, y - 14], fill=shade(c, 1.3))
    d.rectangle([x + 1, y - 13, x + 6, y - 6], fill=(214, 236, 250))  # 진열창
    for i, cc in enumerate(((230, 80, 70), (250, 200, 80), (110, 190, 110))):
        d.point((x + 2 + i * 2, y - 11), fill=cc)
        d.point((x + 2 + i * 2, y - 8), fill=cc)
    d.rectangle([x + 7, y - 12, x + 8, y - 9], fill=(250, 220, 120))  # 버튼
    d.rectangle([x + 2, y - 4, x + 6, y - 2], fill=(30, 34, 50))  # 꺼내는 곳


def apple_tree(d, x, y, r, leaf=(70, 136, 70), gold=False):
    """사과나무 (시즌 11, 자연 지역). 열 개에 하나쯤 황금사과"""
    tree(d, x, y, r, leaf=leaf)
    spots = [(-r // 2, -r // 3), (r // 3, -r // 2), (0, 0), (r // 2, -1), (-r // 3, 2 - r // 6)]
    for i, (dx, dy) in enumerate(spots):
        c = (250, 206, 70) if gold and i == 2 else (224, 60, 54)
        d.rectangle([x + dx, y + dy - r // 4, x + dx + 1, y + dy - r // 4 + 1], fill=c)


def grandfather_clock(d, x, y=HORIZON + 3):
    """괘종시계 (시즌 11, 학교)"""
    wood = (120, 78, 48)
    d.rectangle([x, y - 24, x + 8, y], fill=wood, outline=OUTLINE)
    d.polygon([(x - 1, y - 24), (x + 4, y - 28), (x + 9, y - 24)], fill=shade(wood, 0.8), outline=OUTLINE)
    d.ellipse([x + 1, y - 22, x + 7, y - 16], fill=(250, 244, 220), outline=OUTLINE)
    d.line([(x + 4, y - 19), (x + 4, y - 21)], fill=OUTLINE)
    d.line([(x + 4, y - 19), (x + 5, y - 19)], fill=OUTLINE)
    d.rectangle([x + 2, y - 13, x + 6, y - 3], fill=shade(wood, 0.6))
    d.line([(x + 4, y - 13), (x + 5, y - 6)], fill=(240, 200, 80))  # 추
    d.rectangle([x + 4, y - 6, x + 6, y - 4], fill=(240, 200, 80))


def lost_box(d, x, y=HORIZON + 3):
    """분실물 상자 (시즌 11, 경찰서)"""
    c = (60, 84, 150)
    d.rectangle([x, y - 10, x + 14, y], fill=c, outline=OUTLINE)
    d.rectangle([x, y - 10, x + 14, y - 7], fill=shade(c, 1.3), outline=OUTLINE)
    d.rectangle([x + 6, y - 7, x + 8, y - 3], fill=(250, 210, 70), outline=OUTLINE)  # 자물쇠
    d.line([(x + 2, y - 2), (x + 12, y - 2)], fill=shade(c, 0.7))


def barrel(d, x, y, c=(190, 80, 50)):
    """배럴 (시즌 11, 바지선). (x, y) = 왼쪽 아래"""
    d.rectangle([x, y - 10, x + 7, y], fill=c, outline=OUTLINE)
    d.line([(x + 1, y - 7), (x + 6, y - 7)], fill=shade(c, 0.65))
    d.line([(x + 1, y - 3), (x + 6, y - 3)], fill=shade(c, 0.65))
    d.point((x + 2, y - 9), fill=shade(c, 1.4))


def hills(d, y, amp, color, seed, step=16):
    rng = random.Random(seed)
    pts = [(0, H), (0, y)]
    for x in range(0, W + step, step):
        pts.append((x, y - rng.randint(0, amp)))
    pts.append((W, H))
    d.polygon(pts, fill=color)


def platform(img, cx, cy, rx, ry, top, rim, pattern=None, seed=0):
    """발판: 윗면 + 옆면 + 테두리. pattern(d, box, rng) 으로 무늬"""
    d = ImageDraw.Draw(img)
    d.ellipse([cx - rx, cy - ry + 4, cx + rx, cy + ry + 4], fill=rim, outline=OUTLINE)
    d.ellipse([cx - rx, cy - ry, cx + rx, cy + ry], fill=top, outline=OUTLINE)
    if pattern:
        layer = Image.new("RGBA", img.size, (0, 0, 0, 0))
        pattern(ImageDraw.Draw(layer), (cx - rx, cy - ry, cx + rx, cy + ry), random.Random(seed))
        mask = Image.new("L", img.size, 0)
        ImageDraw.Draw(mask).ellipse([cx - rx + 2, cy - ry + 2, cx + rx - 2, cy + ry - 2], fill=255)
        img.paste(layer, (0, 0), Image.composite(layer.getchannel("A"), Image.new("L", img.size, 0), mask))
    d.arc([cx - rx + 6, cy - ry + 2, cx + rx - 6, cy + ry - 2], 200, 300, fill=shade(top, 1.18))


def pat_tiles(color, step=10):
    def f(d, box, rng):
        x0, y0, x1, y1 = box
        for x in range(int(x0), int(x1), step):
            d.line([(x, y0), (x + (x - (x0 + x1) / 2) * 0.15, y1)], fill=color)
        for y in range(int(y0), int(y1), max(3, step // 3)):
            d.line([(x0, y), (x1, y)], fill=color)
    return f


def pat_dots(colors, n=60):
    def f(d, box, rng):
        x0, y0, x1, y1 = box
        for _ in range(n):
            x, y = rng.uniform(x0, x1), rng.uniform(y0, y1)
            d.point((x, y), fill=rng.choice(colors))
    return f


def pat_grass(color):
    def f(d, box, rng):
        x0, y0, x1, y1 = box
        for _ in range(40):
            x, y = rng.uniform(x0, x1), rng.uniform(y0 + 2, y1)
            d.line([(x, y), (x + rng.choice((-1, 0, 1)), y - 2)], fill=color)
    return f


def pat_planks(color, step=5):
    def f(d, box, rng):
        x0, y0, x1, y1 = box
        for y in range(int(y0), int(y1), step):
            d.line([(x0, y), (x1, y)], fill=color)
            for _ in range(3):
                x = rng.uniform(x0, x1)
                d.line([(x, y), (x, y + step)], fill=color)
    return f


def pat_rings(color):
    def f(d, box, rng):
        x0, y0, x1, y1 = box
        cx, cy = (x0 + x1) / 2, (y0 + y1) / 2
        for k in (0.35, 0.65):
            rx, ry = (x1 - x0) / 2 * k, (y1 - y0) / 2 * k
            d.ellipse([cx - rx, cy - ry, cx + rx, cy + ry], outline=color)
    return f


# ── 지역 ─────────────────────────────────────────
def alley(d, rng):
    sky(d, (60, 72, 120), (232, 150, 112))
    for x in range(-6, W, 34):
        h = rng.randint(14, 34)
        building(d, x, HORIZON - h, 30, h, (88, 70, 86), rng=rng)
    ground(d, (78, 80, 92))
    d.rectangle([0, 6, 54, HORIZON + 2], fill=(132, 70, 58), outline=OUTLINE)  # 왼쪽 벽돌 벽
    for y in range(8, HORIZON, 5):
        for x in range((y // 5) % 2 * 5, 54, 10):
            d.rectangle([x, y, x + 8, y + 3], outline=(110, 56, 48))
    d.line([(54, 18), (W, 8)], fill=OUTLINE)  # 전깃줄
    d.line([(54, 22), (W, 14)], fill=OUTLINE)
    d.rectangle([270, 30, 290, HORIZON], fill=(60, 60, 70))  # 쓰레기통
    vending(d, 40, c=(196, 70, 60))
    return dict(top=(92, 94, 106), rim=(60, 62, 74), pattern=pat_dots([(70, 72, 84), (110, 112, 124)]))


def archery(d, rng):
    sky(d, (110, 170, 230), (196, 230, 250))
    hills(d, HORIZON - 4, 8, (110, 170, 96), 1)
    ground(d, (124, 186, 98), stripes=(116, 176, 92))
    for x in (60, 140, 230, 290):  # 과녁
        d.line([(x, HORIZON - 2), (x - 6, HORIZON + 10)], fill=(110, 76, 48))
        d.line([(x, HORIZON - 2), (x + 6, HORIZON + 10)], fill=(110, 76, 48))
        for r, c in ((9, (240, 240, 240)), (7, (60, 120, 210)), (5, (220, 60, 50)), (2, (250, 210, 60))):
            d.ellipse([x - r, HORIZON - 12 - r, x + r, HORIZON - 12 + r], fill=c, outline=OUTLINE if r == 9 else None)
    for x in range(0, W, 12):  # 울타리
        d.line([(x, HORIZON + 14), (x, HORIZON + 8)], fill=(236, 236, 240))
    d.line([(0, HORIZON + 9), (W, HORIZON + 9)], fill=(236, 236, 240))
    apple_tree(d, 100, HORIZON - 12, 11, gold=True)
    apple_tree(d, 28, HORIZON - 10, 10)
    vending(d, 304)
    return dict(top=(130, 190, 100), rim=(86, 134, 70), pattern=pat_grass((104, 160, 84)))


def stream(d, rng):
    sky(d, (120, 180, 230), (210, 236, 250))
    for x in range(0, W, 22):
        tree(d, x + rng.randint(-4, 4), HORIZON - 14 - rng.randint(0, 6), 10)
    ground(d, (110, 170, 96))
    d.polygon([(0, HORIZON + 26), (W, HORIZON + 8), (W, HORIZON + 22), (0, HORIZON + 44)], fill=(90, 160, 220))
    for k in range(18):
        x = rng.randint(0, W)
        y = int(HORIZON + 26 - x * 18 / W) + rng.randint(2, 12)
        d.line([(x, y), (x + 5, y)], fill=(200, 236, 255))
    for k in range(10):
        x, y = rng.randint(0, W), rng.randint(HORIZON + 4, H - 4)
        d.ellipse([x, y, x + 6, y + 3], fill=(150, 150, 150), outline=(100, 100, 110))
    vending(d, 14)
    return dict(top=(126, 180, 104), rim=(90, 130, 80), pattern=pat_dots([(150, 150, 150), (110, 160, 90)], 40))


def forest(d, rng):
    sky(d, (90, 150, 140), (180, 220, 190))
    for layer, (c, y) in enumerate((((60, 110, 90), HORIZON - 26), ((44, 92, 64), HORIZON - 14))):
        for x in range(-8, W + 8, 14 - layer * 2):
            pine(d, x + rng.randint(-3, 3), y + rng.randint(-6, 4), 26 + rng.randint(0, 10), c)
    ground(d, (76, 116, 66))
    for k in range(5):  # 햇살
        x = rng.randint(20, W - 20)
        d.polygon([(x, 0), (x + 8, 0), (x + 30, HORIZON), (x + 18, HORIZON)], fill=(150, 196, 150))
    apple_tree(d, 44, HORIZON - 8, 12, leaf=(64, 128, 70))
    apple_tree(d, 128, HORIZON - 6, 11, leaf=(64, 128, 70), gold=True)
    vending(d, 300, c=(60, 130, 90))
    return dict(top=(104, 84, 60), rim=(70, 56, 42), pattern=pat_dots([(170, 120, 50), (90, 140, 70), (130, 96, 64)], 50))


def uptown(d, rng):
    sky(d, (130, 180, 236), (220, 236, 250))
    for x in range(0, W, 46):
        h = rng.randint(18, 26)
        c = rng.choice([(236, 226, 210), (220, 210, 196), (200, 214, 226)])
        building(d, x + 4, HORIZON - h, 36, h, c, win=(150, 196, 230), roof=10, rows=2, rng=rng)
    ground(d, (170, 170, 176))
    for x in range(0, W, 46):  # 울타리 나무 · 가로등
        d.ellipse([x + 30, HORIZON - 6, x + 46, HORIZON + 4], fill=(70, 140, 80), outline=(50, 100, 60))
        d.line([(x + 20, HORIZON + 4), (x + 20, HORIZON - 22)], fill=OUTLINE)
        d.rectangle([x + 18, HORIZON - 25, x + 22, HORIZON - 22], fill=(255, 236, 160))
    vending(d, 6, c=(230, 230, 236))
    return dict(top=(200, 196, 188), rim=(140, 136, 130), pattern=pat_tiles((176, 170, 160), 12))


def harbor(d, rng):
    sky(d, (110, 160, 214), (220, 230, 240))
    d.rectangle([0, HORIZON - 16, W, HORIZON + 6], fill=(60, 120, 180))
    for k in range(20):
        x, y = rng.randint(0, W), rng.randint(HORIZON - 14, HORIZON + 4)
        d.line([(x, y), (x + 4, y)], fill=(170, 210, 240))
    for x in (40, 230):  # 크레인
        d.rectangle([x, HORIZON - 50, x + 4, HORIZON], fill=(220, 120, 50), outline=OUTLINE)
        d.rectangle([x - 20, HORIZON - 52, x + 40, HORIZON - 48], fill=(220, 120, 50), outline=OUTLINE)
        d.line([(x + 34, HORIZON - 48), (x + 34, HORIZON - 30)], fill=OUTLINE)
    for i, x in enumerate(range(100, 200, 24)):  # 컨테이너
        c = [(200, 70, 60), (60, 120, 190), (220, 180, 60), (70, 150, 100)][i % 4]
        d.rectangle([x, HORIZON - 10, x + 22, HORIZON + 4], fill=c, outline=OUTLINE)
        for xx in range(x + 3, x + 22, 4):
            d.line([(xx, HORIZON - 8), (xx, HORIZON + 2)], fill=shade(c, 0.8))
    ground(d, (150, 120, 90), y0=HORIZON + 6)
    for y in range(HORIZON + 8, H, 6):
        d.line([(0, y), (W, y)], fill=(120, 92, 66))
    vending(d, 80, HORIZON + 8)
    return dict(top=(160, 124, 88), rim=(110, 84, 60), pattern=pat_planks((126, 96, 68)))


def pond(d, rng):
    sky(d, (130, 186, 220), (220, 240, 236))
    for i, x in enumerate(range(0, W, 26)):
        if i in (2, 9):
            apple_tree(d, x + rng.randint(-5, 5), HORIZON - 12, 11, leaf=(80, 140, 80), gold=i == 9)
        else:
            tree(d, x + rng.randint(-5, 5), HORIZON - 12, 11, leaf=(80, 140, 80))
    ground(d, (110, 166, 100))
    d.ellipse([20, HORIZON + 6, 300, H + 40], fill=(80, 150, 180), outline=(60, 110, 130))
    for k in range(9):  # 연잎
        x, y = rng.randint(40, 280), rng.randint(HORIZON + 14, H - 10)
        d.ellipse([x, y, x + 10, y + 4], fill=(90, 170, 90), outline=(60, 120, 60))
        if k % 3 == 0:
            d.point((x + 5, y + 1), fill=(250, 170, 200))
    for x in range(10, W, 18):
        d.line([(x, HORIZON + 6), (x + 1, HORIZON - 4)], fill=(80, 120, 60))
    vending(d, 302, c=(60, 130, 90))
    return dict(top=(120, 176, 104), rim=(80, 120, 72), pattern=pat_grass((100, 156, 86)))


def beach(d, rng):
    sky(d, (90, 170, 230), (210, 240, 250))
    d.rectangle([0, HORIZON - 14, W, HORIZON + 4], fill=(70, 150, 210))
    for k in range(16):
        x, y = rng.randint(0, W), rng.randint(HORIZON - 12, HORIZON + 2)
        d.line([(x, y), (x + 5, y)], fill=(220, 240, 255))
    ground(d, (236, 214, 160), y0=HORIZON + 4)
    d.line([(0, HORIZON + 4), (W, HORIZON + 4)], fill=(250, 250, 250))
    for x in (30, 290):  # 야자수
        d.line([(x, HORIZON + 8), (x + 6, HORIZON - 30)], fill=(130, 90, 50), width=3)
        for a in range(0, 360, 60):
            r = math.radians(a)
            d.line([(x + 6, HORIZON - 30), (x + 6 + 14 * math.cos(r), HORIZON - 30 + 6 * math.sin(r) + 4)], fill=(60, 150, 70), width=2)
    d.polygon([(250, HORIZON - 8), (236, HORIZON - 2), (264, HORIZON - 2)], fill=(230, 80, 70))  # 파라솔
    d.line([(250, HORIZON - 2), (250, HORIZON + 10)], fill=OUTLINE)
    vending(d, 62, HORIZON + 8, c=(240, 150, 60))
    return dict(top=(240, 220, 168), rim=(200, 176, 120), pattern=pat_dots([(220, 196, 140), (250, 236, 200)], 70))


def temple(d, rng):
    sky(d, (150, 180, 220), (236, 228, 214))
    hills(d, HORIZON - 18, 20, (120, 140, 150), 7, step=30)
    hills(d, HORIZON - 6, 10, (90, 120, 100), 8, step=22)
    x, y = 110, HORIZON - 30  # 기와지붕 법당
    d.rectangle([x + 10, y + 10, x + 90, HORIZON], fill=(170, 60, 50), outline=OUTLINE)
    for k in range(4):
        d.rectangle([x + 18 + k * 18, y + 16, x + 28 + k * 18, HORIZON - 2], fill=(60, 120, 100))
    d.polygon([(x - 6, y + 12), (x + 4, y + 2), (x + 96, y + 2), (x + 106, y + 12), (x + 50, y + 6)], fill=(60, 64, 76), outline=OUTLINE)
    d.polygon([(x + 14, y + 2), (x + 50, y - 10), (x + 86, y + 2)], fill=(70, 74, 88), outline=OUTLINE)
    for xx in (40, 70, 250, 285):
        pine(d, xx, HORIZON - 30, 30, (50, 100, 70))
    ground(d, (196, 186, 160))
    apple_tree(d, 16, HORIZON - 10, 11)
    apple_tree(d, 304, HORIZON - 8, 10)
    vending(d, 96)
    return dict(top=(190, 186, 176), rim=(130, 124, 116), pattern=pat_tiles((160, 154, 142), 14))


def gas(d, rng):
    sky(d, (230, 150, 90), (250, 214, 150))
    hills(d, HORIZON - 4, 6, (170, 130, 90), 3, step=40)
    d.rectangle([70, HORIZON - 40, 250, HORIZON - 32], fill=(230, 230, 236), outline=OUTLINE)  # 지붕
    d.rectangle([70, HORIZON - 36, 250, HORIZON - 34], fill=(220, 60, 50))
    for x in (90, 226):
        d.rectangle([x, HORIZON - 32, x + 4, HORIZON], fill=(200, 200, 206))
    for x in (120, 180):  # 주유기
        d.rectangle([x, HORIZON - 16, x + 12, HORIZON], fill=(220, 60, 50), outline=OUTLINE)
        d.rectangle([x + 2, HORIZON - 14, x + 10, HORIZON - 9], fill=(200, 236, 250))
    d.rectangle([280, HORIZON - 44, 284, HORIZON], fill=(120, 120, 126))  # 간판
    d.rectangle([268, HORIZON - 56, 296, HORIZON - 44], fill=(250, 210, 60), outline=OUTLINE)
    ground(d, (96, 96, 104))
    for x in range(10, W, 40):
        d.rectangle([x, HORIZON + 30, x + 18, HORIZON + 32], fill=(240, 220, 90))
    vending(d, 44, c=(196, 70, 60))
    return dict(top=(150, 150, 156), rim=(100, 100, 108), pattern=pat_tiles((130, 130, 136), 20))


def warehouse(d, rng):
    d.rectangle([0, 0, W, HORIZON], fill=(84, 90, 104))
    for x in range(0, W, 16):  # 철판 벽
        d.line([(x, 0), (x, HORIZON)], fill=(70, 76, 88))
    for y in (10, 36):  # 선반 + 상자
        d.rectangle([0, y + 18, W, y + 20], fill=(150, 110, 70))
        x = 4
        while x < W - 10:
            w = rng.randint(10, 20)
            h = rng.randint(8, 16)
            c = rng.choice([(190, 150, 100), (170, 130, 86), (120, 140, 170)])
            d.rectangle([x, y + 18 - h, x + w, y + 18], fill=c, outline=OUTLINE)
            d.line([(x, y + 18 - h // 2), (x + w, y + 18 - h // 2)], fill=shade(c, 0.8))
            x += w + rng.randint(2, 8)
    d.rectangle([0, 0, W, 4], fill=(200, 200, 160))
    ground(d, (130, 130, 134))
    vending(d, 300)
    return dict(top=(150, 150, 154), rim=(100, 100, 106), pattern=pat_dots([(130, 130, 134), (170, 170, 174)], 50))


def school(d, rng):
    sky(d, (120, 180, 236), (214, 236, 252))
    building(d, 80, HORIZON - 40, 160, 40, (236, 222, 196), win=(150, 196, 230), cols=12, rows=3, rng=None)
    d.rectangle([150, HORIZON - 52, 170, HORIZON - 40], fill=(236, 222, 196), outline=shade((236, 222, 196), 0.7))
    d.ellipse([153, HORIZON - 50, 167, HORIZON - 42], fill=(250, 250, 250), outline=OUTLINE)  # 시계
    d.line([(160, HORIZON - 46), (160, HORIZON - 49)], fill=OUTLINE)
    d.line([(160, HORIZON - 46), (163, HORIZON - 46)], fill=OUTLINE)
    for x in (20, 50, 270, 300):
        tree(d, x, HORIZON - 12, 10, leaf=(90, 160, 90))
    ground(d, (200, 160, 110))
    d.ellipse([-40, HORIZON + 14, W + 40, H + 60], outline=(250, 250, 250))
    grandfather_clock(d, 66)
    vending(d, 284)
    return dict(top=(196, 92, 70), rim=(140, 64, 50), pattern=pat_rings((236, 236, 236)))


def factory(d, rng):
    sky(d, (130, 130, 140), (200, 190, 180))
    for x, h in ((30, 50), (60, 40), (250, 56)):
        d.rectangle([x, HORIZON - h, x + 10, HORIZON], fill=(110, 100, 100), outline=OUTLINE)
        d.rectangle([x, HORIZON - h + 6, x + 10, HORIZON - h + 9], fill=(220, 60, 50))
        for k in range(4):
            r = 5 + k * 2
            d.ellipse([x + 5 - r + k * 6, HORIZON - h - 6 - k * 7 - r, x + 5 + r + k * 6, HORIZON - h - 6 - k * 7 + r], fill=(176, 176, 180))
    building(d, 90, HORIZON - 24, 140, 24, (130, 120, 112), win=(250, 200, 100), cols=10, rows=2, rng=rng)
    d.polygon([(90, HORIZON - 24), (110, HORIZON - 34), (130, HORIZON - 24), (150, HORIZON - 34), (170, HORIZON - 24), (190, HORIZON - 34), (210, HORIZON - 24), (230, HORIZON - 34), (230, HORIZON - 24)], fill=(100, 92, 88))
    d.line([(0, HORIZON - 4), (W, HORIZON - 4)], fill=(90, 90, 96), width=3)  # 관
    ground(d, (110, 108, 108))
    vending(d, 76, c=(196, 130, 50))  # 공장은 자판기 2대
    vending(d, 290)
    return dict(top=(140, 144, 152), rim=(96, 98, 106), pattern=pat_tiles((120, 124, 132), 16))


def fire(d, rng):
    sky(d, (120, 170, 230), (226, 230, 240))
    d.rectangle([60, HORIZON - 40, 260, HORIZON], fill=(200, 60, 50), outline=OUTLINE)
    for k in range(3):  # 차고 문
        x = 76 + k * 60
        d.rectangle([x, HORIZON - 26, x + 44, HORIZON], fill=(230, 230, 236), outline=OUTLINE)
        for y in range(HORIZON - 24, HORIZON, 4):
            d.line([(x, y), (x + 44, y)], fill=(190, 190, 200))
    d.rectangle([60, HORIZON - 40, 260, HORIZON - 34], fill=(240, 240, 240))
    d.rectangle([272, HORIZON - 50, 290, HORIZON], fill=(200, 60, 50), outline=OUTLINE)  # 망루
    ground(d, (150, 150, 156))
    d.rectangle([0, HORIZON + 20, W, HORIZON + 22], fill=(240, 220, 90))
    vending(d, 40, c=(196, 70, 60))
    return dict(top=(170, 170, 176), rim=(116, 116, 124), pattern=pat_tiles((150, 150, 156), 18))


def cemetery(d, rng):
    sky(d, (40, 36, 70), (110, 90, 130))
    d.ellipse([250, 10, 270, 30], fill=(240, 236, 210))
    hills(d, HORIZON - 6, 8, (50, 56, 70), 5, step=30)
    for x in (30, 280):  # 마른 나무
        d.line([(x, HORIZON), (x, HORIZON - 30)], fill=(40, 34, 44), width=3)
        d.line([(x, HORIZON - 20), (x - 10, HORIZON - 32)], fill=(40, 34, 44), width=2)
        d.line([(x, HORIZON - 24), (x + 12, HORIZON - 34)], fill=(40, 34, 44), width=2)
    ground(d, (60, 76, 70))
    for k in range(12):  # 비석
        x, y = rng.randint(10, W - 20), rng.randint(HORIZON - 4, HORIZON + 30)
        if k % 3 == 0:
            d.rectangle([x + 3, y - 10, x + 5, y], fill=(150, 150, 160))
            d.rectangle([x, y - 7, x + 8, y - 5], fill=(150, 150, 160))
        else:
            d.rectangle([x, y - 8, x + 8, y], fill=(130, 130, 140), outline=OUTLINE)
            d.ellipse([x, y - 11, x + 8, y - 5], fill=(130, 130, 140), outline=OUTLINE)
            d.rectangle([x + 1, y - 7, x + 7, y - 1], fill=(130, 130, 140))
    apple_tree(d, 112, HORIZON - 12, 11, leaf=(52, 84, 70))
    vending(d, 300, c=(70, 80, 130))
    return dict(top=(70, 86, 76), rim=(46, 58, 52), pattern=pat_grass((56, 72, 64)))


def police(d, rng):
    sky(d, (110, 150, 210), (210, 226, 246))
    building(d, 70, HORIZON - 40, 180, 40, (196, 204, 220), win=(120, 170, 220), cols=14, rows=3, rng=None)
    d.rectangle([130, HORIZON - 50, 190, HORIZON - 40], fill=(40, 70, 140), outline=OUTLINE)
    d.text((140, HORIZON - 50), "POLICE", fill=(250, 250, 250))
    for x, c in ((40, (60, 110, 230)), (280, (230, 60, 60))):  # 경광등
        d.ellipse([x - 6, HORIZON - 26, x + 6, HORIZON - 14], fill=c, outline=OUTLINE)
        d.line([(x, HORIZON - 14), (x, HORIZON)], fill=OUTLINE)
    ground(d, (130, 130, 140))
    lost_box(d, 10)
    vending(d, 54)
    return dict(top=(150, 156, 170), rim=(100, 106, 120), pattern=pat_tiles((130, 136, 150), 14))


def chapel(d, rng):
    sky(d, (150, 170, 220), (240, 220, 210))
    x = 120
    d.rectangle([x, HORIZON - 34, x + 80, HORIZON], fill=(220, 210, 196), outline=OUTLINE)
    d.polygon([(x - 4, HORIZON - 34), (x + 40, HORIZON - 52), (x + 84, HORIZON - 34)], fill=(110, 80, 70), outline=OUTLINE)
    d.rectangle([x + 34, HORIZON - 70, x + 46, HORIZON - 44], fill=(220, 210, 196), outline=OUTLINE)
    d.rectangle([x + 39, HORIZON - 80, x + 41, HORIZON - 70], fill=(240, 200, 80))  # 십자가
    d.rectangle([x + 35, HORIZON - 77, x + 45, HORIZON - 75], fill=(240, 200, 80))
    d.ellipse([x + 30, HORIZON - 30, x + 50, HORIZON - 12], fill=(200, 80, 140), outline=OUTLINE)  # 장미창
    d.line([(x + 40, HORIZON - 30), (x + 40, HORIZON - 12)], fill=(250, 220, 120))
    d.line([(x + 30, HORIZON - 21), (x + 50, HORIZON - 21)], fill=(250, 220, 120))
    for xx in (40, 70, 250, 280):
        pine(d, xx, HORIZON - 26, 26, (60, 110, 80))
    ground(d, (170, 160, 150))
    apple_tree(d, 100, HORIZON - 10, 10)
    apple_tree(d, 302, HORIZON - 10, 10, gold=True)
    vending(d, 14, c=(120, 90, 80))
    return dict(top=(196, 188, 178), rim=(140, 132, 124), pattern=pat_tiles((176, 168, 158), 12))


def hospital(d, rng):
    sky(d, (140, 196, 236), (226, 242, 250))
    building(d, 70, HORIZON - 46, 180, 46, (240, 244, 248), win=(130, 190, 230), cols=14, rows=4, rng=None)
    d.rectangle([146, HORIZON - 60, 174, HORIZON - 46], fill=(240, 244, 248), outline=OUTLINE)
    d.rectangle([157, HORIZON - 58, 163, HORIZON - 48], fill=(220, 60, 60))
    d.rectangle([152, HORIZON - 56, 168, HORIZON - 50], fill=(220, 60, 60))
    ground(d, (200, 206, 212))
    # 의료 지원 (시즌 11): 구급상자 보관함
    d.rectangle([290, HORIZON - 9, 304, HORIZON + 3], fill=(244, 246, 250), outline=OUTLINE)
    d.rectangle([296, HORIZON - 6, 298, HORIZON], fill=(220, 60, 60))
    d.rectangle([294, HORIZON - 4, 300, HORIZON - 2], fill=(220, 60, 60))
    vending(d, 54, c=(90, 170, 200))
    return dict(top=(226, 232, 238), rim=(160, 168, 178), pattern=pat_tiles((200, 208, 216), 12))


def lab(d, rng):
    d.rectangle([0, 0, W, HORIZON], fill=(24, 30, 48))
    for x in range(0, W, 32):  # 벽 판
        d.rectangle([x + 2, 6, x + 30, HORIZON - 6], fill=(34, 42, 66), outline=(50, 62, 96))
        d.line([(x + 6, 14), (x + 26, 14)], fill=(99, 214, 255))
    for x in (60, 160, 260):  # 배양 관
        d.rectangle([x - 8, 10, x + 8, HORIZON - 2], fill=(40, 120, 140), outline=(99, 214, 255))
        for k in range(5):
            yy = rng.randint(14, HORIZON - 8)
            bx = x + rng.randint(-4, 2)
            d.ellipse([bx, yy, bx + 3, yy + 3], fill=(170, 240, 255))
    ground(d, (40, 46, 64))
    for x in range(0, W, 24):
        d.line([(x, HORIZON), (x - 40, H)], fill=(52, 60, 84))
    return dict(top=(56, 66, 92), rim=(34, 40, 60), pattern=pat_rings((99, 214, 255)))


def hotel(d, rng):
    sky(d, (40, 50, 100), (200, 120, 140))
    building(d, 100, 4, 120, HORIZON - 4, (150, 120, 100), win=(255, 220, 140), cols=10, rows=6, rng=rng)
    d.rectangle([140, HORIZON - 14, 180, HORIZON], fill=(200, 170, 90), outline=OUTLINE)  # 입구
    for x in range(10, 100, 24):
        building(d, x, HORIZON - 20, 20, 20, (70, 70, 100), rng=rng)
    for x in range(224, W, 24):
        building(d, x, HORIZON - 18, 20, 18, (70, 70, 100), rng=rng)
    ground(d, (120, 40, 50))
    vending(d, 124, c=(200, 170, 90))
    return dict(top=(150, 48, 60), rim=(100, 30, 40), pattern=pat_tiles((176, 140, 70), 16))


def barge(d, rng):
    """바지선 (시즌 11, 21번째 지역): 배 4척이 이어진 어두운 해상 작업장, 크레인이 배럴을 내려요"""
    sky(d, (36, 42, 62), (104, 108, 124))
    d.rectangle([0, HORIZON - 16, W, HORIZON + 8], fill=(38, 60, 82))  # 바다
    for k in range(22):
        x, y = rng.randint(0, W), rng.randint(HORIZON - 14, HORIZON + 6)
        d.line([(x, y), (x + 4, y)], fill=(86, 118, 142))
    steel = (58, 62, 76)
    for x, w, cab in ((6, 96, 12), (212, 104, 78)):  # 뒤쪽 배 두 척
        d.polygon([(x, HORIZON - 10), (x + w, HORIZON - 10), (x + w - 8, HORIZON + 2), (x + 8, HORIZON + 2)], fill=steel, outline=OUTLINE)
        d.line([(x + 2, HORIZON - 7), (x + w - 2, HORIZON - 7)], fill=(170, 60, 50))
        d.rectangle([x + cab, HORIZON - 26, x + cab + 22, HORIZON - 10], fill=(84, 90, 106), outline=OUTLINE)  # 선실
        for wx in (x + cab + 3, x + cab + 10, x + cab + 17):
            d.rectangle([wx, HORIZON - 22, wx + 3, HORIZON - 18], fill=(250, 214, 120))
        for i in range(3):  # 갑판 화물
            cx = x + (40 if cab < 40 else 8) + i * 14
            c = [(150, 70, 56), (64, 100, 140), (170, 140, 60)][i]
            d.rectangle([cx, HORIZON - 18, cx + 12, HORIZON - 10], fill=c, outline=OUTLINE)
    d.line([(102, HORIZON - 9), (212, HORIZON - 9)], fill=(120, 124, 136), width=2)  # 배를 잇는 다리
    for x in range(106, 212, 8):
        d.line([(x, HORIZON - 9), (x, HORIZON - 13)], fill=(120, 124, 136))
    d.line([(102, HORIZON - 13), (212, HORIZON - 13)], fill=(120, 124, 136))
    crane = (214, 160, 50)  # 크레인
    d.rectangle([146, HORIZON - 60, 152, HORIZON - 9], fill=crane, outline=OUTLINE)
    for y in range(HORIZON - 56, HORIZON - 10, 8):
        d.line([(147, y), (151, y + 6)], fill=shade(crane, 0.6))
    d.rectangle([118, HORIZON - 64, 204, HORIZON - 60], fill=crane, outline=OUTLINE)
    d.rectangle([136, HORIZON - 70, 150, HORIZON - 64], fill=(84, 90, 106), outline=OUTLINE)  # 조종실
    d.line([(196, HORIZON - 60), (196, HORIZON - 38)], fill=OUTLINE)
    barrel(d, 192, HORIZON - 28)  # 매달린 배럴
    d.rectangle([0, HORIZON + 8, W, H], fill=(70, 76, 90))  # 앞 갑판
    for y in range(HORIZON + 14, H, 8):
        d.line([(0, y), (W, y)], fill=(58, 62, 76))
    for x in range(-20, W, 44):
        d.line([(x + 30, HORIZON + 8), (x, H)], fill=(58, 62, 76))
    for x in range(0, W, 12):  # 노란 · 검정 경고선
        d.rectangle([x, HORIZON + 8, x + 5, HORIZON + 10], fill=(232, 190, 60))
    for x, c in ((8, (190, 80, 50)), (18, (60, 110, 150)), (286, (190, 80, 50)), (296, (200, 170, 60)), (306, (190, 80, 50))):
        barrel(d, x, HORIZON + 22, c)
    vending(d, 44, HORIZON + 12, c=(196, 130, 50))
    return dict(top=(92, 98, 112), rim=(54, 58, 70), pattern=pat_tiles((72, 78, 92), 14))


REGIONS = {"alley": alley, "archery": archery, "stream": stream, "forest": forest, "uptown": uptown, "harbor": harbor,
           "pond": pond, "beach": beach, "temple": temple, "gas": gas, "warehouse": warehouse, "school": school,
           "factory": factory, "fire": fire, "cemetery": cemetery, "police": police, "chapel": chapel,
           "hospital": hospital, "lab": lab, "hotel": hotel, "barge": barge}


def draw_region(name):
    rng = random.Random(name)
    bg = Image.new("RGBA", (W, H), (0, 0, 0, 255))
    d = ImageDraw.Draw(bg)
    plat = REGIONS[name](d, rng)
    a = Image.new("RGBA", (W, 132), (0, 0, 0, 0))
    platform(a, 104, 132, 62, 18, plat["top"], plat["rim"], plat.get("pattern"), seed=1)
    b = Image.new("RGBA", (W, 132), (0, 0, 0, 0))
    platform(b, 216, 72, 64, 17, plat["top"], plat["rim"], plat.get("pattern"), seed=2)
    return bg, a, b


def save(img, path):
    img.save(path, optimize=True)
    done.append(str(path.relative_to(ROOT / "assets")).replace("\\", "/"))


def main():
    drawn = {name: draw_region(name) for name in REGIONS}
    empty = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    for biome, region in BIOME_REGION.items():
        bg, a, b = drawn[region]
        if not (ARENA / f"{biome}_bg.png").exists():
            continue
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
