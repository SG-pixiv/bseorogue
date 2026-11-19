# SPDX-FileCopyrightText: 2026 SG
# SPDX-License-Identifier: AGPL-3.0-only
"""(11-19 견본, SG 확인 전) 포켓로그 방식 견본: 골목길 (배경 띠 + 먼 도시 실루엣 · 전깃줄 / 횡단보도 + 보도블록 발판 / 자판기 · 쓰레기봉투)"""
import random, sys
from pathlib import Path
from PIL import Image, ImageDraw

OUT = Path(sys.argv[1]); OUT.mkdir(parents=True, exist_ok=True)
W, H = 320, 180
OL = (38, 34, 44)  # 외곽선

def stripes(d, y0, y1, c_top, c_bot):
    """포켓로그 띠 경계: 위 색과 아래 색을 한 줄씩 번갈아 (2줄)"""
    d.rectangle([0, y0, W, y1], fill=c_bot)
    for k in (0, 2):
        d.line([(0, y0 + k), (W, y0 + k)], fill=c_top)

# ── 배경 ──
SKY = [(112, 146, 196), (138, 168, 212), (164, 190, 226), (190, 210, 236), (214, 226, 242)]
FAR_B, FAR_W = (170, 182, 204), (192, 202, 222)     # 먼 건물 (옅게)
NEAR_B, NEAR_W = (132, 140, 164), (156, 164, 186)    # 가까운 건물
POLE = (84, 88, 106)
CURB, WALK, WALK2 = (196, 196, 204), (204, 162, 160), (188, 146, 146)
ROAD = [(122, 124, 136), (112, 114, 126), (102, 104, 116)]
HOR = 62

bg = Image.new("RGB", (W, H)); d = ImageDraw.Draw(bg)
band = [0, 10, 20, 30, 40, HOR]
for i, c in enumerate(SKY):
    if i == 0:
        d.rectangle([0, 0, W, band[1]], fill=c)
    else:
        stripes(d, band[i], band[i + 1] if i + 1 < len(band) else HOR, SKY[i - 1], c)
rng = random.Random(7)
# 먼 건물 (옅고 높낮이)
x = -4
while x < W:
    w = rng.randint(14, 30); h = rng.randint(16, 40)
    d.rectangle([x, HOR - h, x + w, HOR], fill=FAR_B)
    for wy in range(HOR - h + 4, HOR - 4, 5):
        for wx in range(x + 3, x + w - 2, 5):
            if rng.random() < 0.55: d.point((wx, wy), fill=FAR_W)
    x += w + rng.randint(0, 3)
# 가까운 건물 (양쪽에 몰려서 가운데 골목이 보이게)
for x0, x1, h in ((0, 34, 44), (30, 70, 30), (66, 98, 22), (238, 270, 26), (266, 296, 38), (292, 320, 48)):
    d.rectangle([x0, HOR - h, x1, HOR], fill=NEAR_B)
    d.line([(x0, HOR - h), (x1, HOR - h)], fill=(118, 126, 150))
    for wy in range(HOR - h + 5, HOR - 6, 6):
        for wx in range(x0 + 3, x1 - 3, 6):
            d.rectangle([wx, wy, wx + 2, wy + 2], fill=NEAR_W)
# 편의점 간판 (초록 · 주황 줄, 일러스트의 24시 가게)
d.rectangle([34, HOR - 20, 66, HOR - 16], fill=(70, 150, 112)); d.line([(34, HOR - 16), (66, HOR - 16)], fill=(226, 140, 70))
# 전봇대 · 전깃줄
for px in (22, 300):
    d.rectangle([px, 6, px + 2, HOR + 2], fill=POLE); d.rectangle([px - 6, 12, px + 8, 13], fill=POLE)
def wire(y0, sag):
    pts = [(22 + 1 + t * (300 - 22), y0 + sag * 4 * t * (1 - t)) for t in [i / 40 for i in range(41)]]
    d.line(pts, fill=(70, 74, 92))
wire(13, 10); wire(16, 13)
# 땅: 연석 · 보도 · 아스팔트 띠
d.rectangle([0, HOR, W, HOR + 2], fill=CURB)
stripes(d, HOR + 3, HOR + 12, CURB, WALK)
stripes(d, HOR + 12, HOR + 18, WALK, WALK2)
stripes(d, HOR + 18, HOR + 40, WALK2, ROAD[0])
stripes(d, HOR + 40, HOR + 70, ROAD[0], ROAD[1])
stripes(d, HOR + 70, H, ROAD[1], ROAD[2])
bg.save(OUT / "alley_bg.png")

# ── 발판 ──
ASPH, ASPH2, ASPH3 = (92, 94, 106), (82, 84, 96), (104, 106, 118)
WHITE, WHITE2 = (226, 228, 232), (196, 198, 206)
RIM, RIM2 = (60, 54, 62), (78, 72, 80)

def platform(w, h, seed, items=False):
    """포켓로그 발판: 두꺼운 테 + 윗면 (왼쪽 횡단보도 아스팔트 · 오른쪽 보도블록)"""
    rng = random.Random(seed)
    im = Image.new("RGBA", (w, h), (0, 0, 0, 0)); px = im.load()
    cx, cy, rx, ry = (w - 1) / 2, (h - 1) / 2, w / 2, h / 2
    for y in range(h):
        for x in range(w):
            e = ((x - cx) / rx) ** 2 + ((y - cy) / ry) ** 2
            if e > 1: continue
            ei = ((x - cx) / (rx - 4)) ** 2 + ((y - cy) / (ry - 2.5)) ** 2
            if ei > 1:
                px[x, y] = RIM if e > 0.9 or y > cy else RIM2; continue
            u, v = x / w, y / h
            split = 0.66 + 0.05 * (v - 0.5)
            if abs(u - split) < 0.012:
                c = (208, 208, 214)                        # 연석
            elif u > split:                                # 보도블록 (어긋난 벽돌)
                row = y // 3; off = 3 if row % 2 else 0
                c = WALK2 if (y % 3 == 0 or (x + off) % 7 == 0) else WALK
            else:
                c = ASPH
                if rng.random() < 0.06: c = ASPH2 if rng.random() < 0.6 else ASPH3
                xs = x + (v - 0.5) * 6                     # 횡단보도 줄 (조금 기울게)
                if 0.12 * w < xs < 0.56 * w and 0.18 < v < 0.84 and int(xs) % 8 < 4:
                    c = WHITE if v < 0.7 else WHITE2
            if ei > 0.82: c = tuple(int(k * 0.86) for k in c)   # 가장자리 어둡게
            px[x, y] = c + (255,)
    # 맨홀
    if w > 100:
        dd = ImageDraw.Draw(im); mx, my = int(0.07 * w) + 6, int(0.55 * h)
        dd.ellipse([mx - 5, my - 2, mx + 5, my + 2], fill=(70, 72, 82), outline=(54, 56, 66))
    return im

b = Image.new("RGBA", (W, 132), (0, 0, 0, 0))
plat_b = platform(128, 33, 2)
# 소품 (발판 뒤쪽에 서 있게: 발판보다 먼저 그려서 아래가 가려지게)
props = Image.new("RGBA", (W, 132), (0, 0, 0, 0)); pd = ImageDraw.Draw(props)
vx, vy = 252, 40   # 음식 자판기 (시즌 13, 연구소 빼고 전부)
pd.rectangle([vx, vy, vx + 13, vy + 24], fill=(204, 70, 60), outline=OL)
pd.rectangle([vx + 2, vy + 2, vx + 11, vy + 11], fill=(246, 234, 176))
for i, c in enumerate([(84, 160, 220), (236, 120, 60), (110, 180, 90), (230, 70, 90)]):
    pd.rectangle([vx + 3 + (i % 2) * 4, vy + 3 + (i // 2) * 4, vx + 5 + (i % 2) * 4, vy + 5 + (i // 2) * 4], fill=c)
pd.rectangle([vx + 3, vy + 15, vx + 10, vy + 18], fill=(48, 40, 50))
pd.line([(vx + 1, vy + 1), (vx + 1, vy + 23)], fill=(232, 110, 96))
# 쓰레기봉투 (왼쪽 뒤)
for bx, by, c in ((166, 58, (54, 56, 70)), (174, 56, (66, 68, 84))):
    pd.ellipse([bx, by, bx + 10, by + 9], fill=c, outline=OL); pd.point((bx + 5, by), fill=(150, 150, 166))
b.alpha_composite(props)
b.alpha_composite(plat_b, (152, 57))
# 꼬깔 (발판 앞 왼쪽 위에)
pd2 = ImageDraw.Draw(b); cx0, cy0 = 160, 72
pd2.polygon([(cx0, cy0 - 9), (cx0 - 4, cy0), (cx0 + 4, cy0)], fill=(236, 120, 52), outline=OL)
pd2.line([(cx0 - 2, cy0 - 4), (cx0 + 2, cy0 - 4)], fill=(240, 240, 240))
b.save(OUT / "alley_b.png")

a = Image.new("RGBA", (W, 132), (0, 0, 0, 0))
a.alpha_composite(platform(120, 30, 1), (44, 117))
a.save(OUT / "alley_a.png")
print("ok")
