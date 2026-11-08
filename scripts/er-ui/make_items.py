# SPDX-FileCopyrightText: 2026 SG
# SPDX-License-Identifier: AGPL-3.0-only
"""
블서로그 아이템 아이콘 · 보급 상자(볼) 그림 만들기 (UI 2단계, 11-08)

포켓로그 아이템 그림은 저장소에 없어서(임시 네모) 여기서 새로 그려요.
아이템 이름(영어 키)을 보고 종류별 모양 + 색으로 그려요. 이름은 locales/ko/modifier-type.json 의
블서로그 이름(고기 · 눈물젖은 빵 · VF 혈액 샘플 · 강화 모듈 …)에 맞췄어요.

만드는 것:
  assets/images/items/<이름>.png   32×32 (낱장, 아틀라스의 원본)
  assets/images/items.png / .json  533칸 아틀라스 (원래 칸 이름 · 순서 그대로, 투명 둘레는 잘라서)
  assets/images/pokeball/*.png     보급 상자 18장 (닫힘 · 열리는 중 · 열림 × 6종)
  assets/images/pb.png / .json     위 18장 아틀라스
  assets/images/inputs/*.png       키보드 · 패드 키 아이콘 (원래 칸 자리 그대로)
  알 · 빈 칸(?) · 반짝이 별 · 시간 아이콘 · 요약 화면 A/Z 키 · 알 기술 아이콘
  assets/starter-colors.json       실험체 색 두 개 (사탕 아이콘 · 도감에 씀, 실험체 그림에서 뽑아요)
  docs/item-icons-preview.png      한눈에 보기 (4배, 이름 없이)

쓰는 법: python3 -I -B scripts/er-ui/make_items.py
"""
import json
import re
import sys
import zlib
from pathlib import Path

from PIL import Image, ImageDraw

ROOT = Path(__file__).resolve().parents[2]
IMG = ROOT / "assets" / "images"
MARK = ROOT / "assets" / ".placeholders.json"
S = 32
OUT = (26, 28, 44, 255)

# ── 색 ─────────────────────────────────────────────
RED = (214, 64, 64)
ORANGE = (232, 132, 48)
YELLOW = (240, 200, 70)
GOLD = (232, 176, 48)
GREEN = (84, 170, 84)
MINT = (120, 218, 176)
TEAL = (46, 180, 170)
BLUE = (70, 130, 220)
SKY = (130, 196, 240)
PURPLE = (150, 90, 210)
PINK = (236, 130, 170)
BROWN = (150, 96, 56)
TAN = (214, 170, 110)
WHITE = (232, 236, 244)
GRAY = (140, 148, 164)
SLATE = (70, 76, 96)
BLACK = (44, 44, 56)
SILVER = (192, 200, 214)
CREAM = (244, 228, 190)
GLASS = (200, 226, 240)

# 역할군(타입) 색: make_ui.py 의 TYPE_STYLE 을 조금 밝게
TYPE = {
    "normal": (150, 156, 140), "fighting": (214, 108, 64), "flying": (130, 160, 220), "poison": (160, 96, 186),
    "ground": (196, 158, 96), "rock": (110, 138, 196), "bug": (204, 62, 78), "ghost": (116, 100, 180),
    "steel": (160, 170, 188), "fire": (236, 112, 60), "water": (72, 146, 232), "grass": (96, 184, 92),
    "electric": (240, 200, 56), "psychic": (170, 98, 232), "ice": (116, 206, 226), "dragon": (236, 168, 48),
    "dark": (88, 76, 104), "fairy": (72, 196, 158), "stellar": (110, 180, 230), "typeless": (150, 156, 170),
}
TYPES = "|".join(TYPE)
PLATE = {"draco": "dragon", "dread": "dark", "earth": "ground", "fist": "fighting", "flame": "fire", "icicle": "ice",
         "insect": "bug", "iron": "steel", "meadow": "grass", "mind": "psychic", "pixie": "fairy", "sky": "flying",
         "splash": "water", "spooky": "ghost", "stone": "rock", "toxic": "poison", "zap": "electric", "blank": "normal",
         "legend": "stellar"}
HUES = [RED, ORANGE, YELLOW, GREEN, TEAL, BLUE, SKY, PURPLE, PINK, (120, 200, 80), (90, 110, 210), (200, 120, 90)]


def hue(name):
    return HUES[zlib.crc32(name.encode()) % len(HUES)]


def mix(c, t, k):
    return tuple(round(a + (b - a) * k) for a, b in zip(c[:3], t[:3]))


def light(c, k=0.35):
    return mix(c, (255, 255, 255), k)


def dark(c, k=0.35):
    return mix(c, (0, 0, 0), k)


# ── 그리기 바탕: 모양(마스크) 하나 = 한 겹, 테두리 빛(왼쪽 위 밝게 · 오른쪽 아래 어둡게) 자동 ──
class Icon:
    def __init__(self, w=S, h=S):
        self.w, self.h = w, h
        self.img = Image.new("RGBA", (w, h), (0, 0, 0, 0))

    def mask(self, fn):
        m = Image.new("L", (self.w, self.h), 0)
        fn(ImageDraw.Draw(m))
        return m

    def add(self, fn, c, shade=True, flat=False):
        m = self.mask(fn)
        mp, px = m.load(), self.img.load()
        box = m.getbbox()
        if not box:
            return self
        x0, y0, x1, y1 = box
        bw, bh = max(1, x1 - x0), max(1, y1 - y0)

        def inside(x, y):
            return 0 <= x < self.w and 0 <= y < self.h and mp[x, y]

        for y in range(y0, y1):
            for x in range(x0, x1):
                if not mp[x, y]:
                    continue
                col = c
                if not flat:
                    if (x - x0) / bw + (y - y0) / bh > 1.3:
                        col = dark(c, 0.14)
                    if shade:
                        if not inside(x, y - 1) or not inside(x - 1, y):
                            col = light(c, 0.32)
                        elif not inside(x, y + 1) or not inside(x + 1, y):
                            col = dark(c, 0.32)
                px[x, y] = (*col[:3], 255)
        return self

    def cut(self, fn):
        """구멍 내기 (투명으로)"""
        m = self.mask(fn)
        self.img.paste((0, 0, 0, 0), mask=m)
        return self

    def dot(self, pts, c):
        px = self.img.load()
        for x, y in pts:
            if 0 <= x < self.w and 0 <= y < self.h:
                px[x, y] = (*c[:3], 255)
        return self

    def done(self, outline=True):
        if outline:
            src = self.img.copy().load()
            px = self.img.load()
            for y in range(self.h):
                for x in range(self.w):
                    if src[x, y][3]:
                        continue
                    if any(0 <= x + dx < self.w and 0 <= y + dy < self.h and src[x + dx, y + dy][3]
                           for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1))):
                        px[x, y] = OUT
        return self.img


def E(b):
    return lambda d: d.ellipse(b, fill=255)


def P(p):
    return lambda d: d.polygon(p, fill=255)


def R(b, r=0):
    return (lambda d: d.rounded_rectangle(b, r, fill=255)) if r else (lambda d: d.rectangle(b, fill=255))


def L(p, w=1):
    return lambda d: d.line(p, fill=255, width=w)


def shine(ic, x, y):
    return ic.dot([(x, y), (x + 1, y), (x, y + 1)], (255, 255, 255))


# ── 모양들 ───────────────────────────────────────────
def gem(c, c2=None):
    ic = Icon().add(P([(16, 6), (24, 12), (24, 20), (16, 26), (8, 20), (8, 12)]), c)
    ic.add(P([(16, 9), (21, 13), (16, 16), (11, 13)]), light(c, 0.45), shade=False, flat=True)
    if c2:
        ic.add(E((14, 18, 18, 22)), c2, flat=True)
    return shine(ic, 11, 12).done()


def type_gem(c):
    ic = Icon().add(P([(16, 6), (25, 16), (16, 26), (7, 16)]), c)
    ic.add(P([(16, 9), (21, 15), (11, 15)]), light(c, 0.45), shade=False, flat=True)
    return shine(ic, 12, 14).done()


def shard(c):
    ic = Icon()
    ic.add(P([(7, 15), (11, 17), (11, 27), (6, 27)]), dark(c, 0.1))
    ic.add(P([(21, 12), (26, 18), (24, 27), (19, 27)]), dark(c, 0.1))
    ic.add(P([(15, 4), (20, 10), (19, 27), (12, 27), (11, 10)]), c)
    ic.add(L([(14, 9), (14, 24)]), light(c, 0.5), shade=False, flat=True)
    return ic.done()


def zcrystal(c):
    ic = Icon().add(P([(16, 3), (23, 16), (16, 29), (9, 16)]), c)
    ic.add(P([(16, 6), (20, 16), (16, 16)]), light(c, 0.45), shade=False, flat=True)
    return ic.done()


def plate(c):
    ic = Icon().add(R((6, 7, 26, 25), 2), light(c, 0.15))
    ic.add(P([(16, 11), (21, 16), (16, 21), (11, 16)]), dark(c, 0.15))
    return shine(ic, 8, 9).done()


def disc(c):
    ic = Icon().add(E((5, 5, 27, 27)), c)
    ic.add(E((11, 11, 21, 21)), SILVER)
    ic.cut(E((14, 14, 18, 18)))
    return shine(ic, 9, 9).done()


def book(c):
    ic = Icon().add(R((8, 5, 24, 27), 1), c)
    ic.add(R((21, 6, 24, 26)), WHITE, flat=True)
    ic.add(R((8, 9, 21, 12)), GOLD, flat=True)
    ic.add(R((11, 15, 18, 22), 1), light(c, 0.4), flat=True)
    return ic.done()


def berry(c):
    ic = Icon().add(E((7, 10, 25, 27)), c)
    ic.add(L([(16, 11), (16, 6)], 1), BROWN, shade=False)
    ic.add(P([(16, 8), (21, 4), (24, 6), (20, 10)]), GREEN)
    return shine(ic, 10, 14).done()


def stone(c):
    ic = Icon().add(P([(9, 13), (13, 8), (21, 8), (25, 14), (24, 23), (17, 26), (10, 24), (7, 18)]), mix(GRAY, c, 0.25))
    ic.add(P([(16, 12), (20, 16), (16, 21), (12, 16)]), c)
    return shine(ic, 12, 11).done()


def ribbon(c, c2=GOLD):
    ic = Icon()
    ic.add(P([(11, 16), (15, 17), (13, 28), (9, 26)]), dark(c, 0.15))
    ic.add(P([(17, 17), (21, 16), (23, 26), (19, 28)]), dark(c, 0.15))
    ic.add(E((7, 3, 25, 21)), c)
    ic.add(E((11, 7, 21, 17)), c2)
    return shine(ic, 13, 9).done()


def leaf(c):
    ic = Icon().add(P([(6, 25), (9, 15), (17, 8), (26, 6), (24, 15), (17, 22), (9, 26)]), c)
    ic.add(L([(8, 24), (22, 9)]), dark(c, 0.3), shade=False, flat=True)
    return ic.done()


def charm(c, c2=None):
    ic = Icon().add(L([(16, 3), (16, 9)], 2), SILVER, shade=False)
    ic.add(E((7, 8, 25, 26)), c)
    ic.add(E((11, 12, 21, 22)), c2 or light(c, 0.3))
    return shine(ic, 10, 12).done()


def bottle(c, glass=GLASS, cap=BROWN):
    ic = Icon().add(R((13, 5, 19, 12)), glass)
    ic.add(R((9, 10, 23, 27), 3), glass)
    ic.add(R((10, 16, 22, 26), 2), c)
    ic.add(R((12, 2, 20, 6), 1), cap)
    return shine(ic, 11, 12).done()


def can(c, band=WHITE):
    ic = Icon().add(R((9, 5, 23, 27), 2), c)
    ic.add(R((9, 12, 23, 18)), band, flat=True)
    ic.add(R((10, 5, 22, 7)), SILVER, flat=True)
    return ic.done()


def perfume(c, cap=GOLD):
    ic = Icon().add(R((14, 6, 18, 11)), GLASS)
    ic.add(P([(16, 10), (25, 18), (16, 27), (7, 18)]), c)
    ic.add(E((12, 1, 20, 7)), cap)
    return shine(ic, 12, 16).done()


def spray(c):
    ic = Icon().add(R((13, 4, 19, 9)), GRAY)
    ic.add(R((10, 8, 22, 27), 2), c)
    ic.add(R((10, 14, 22, 19)), WHITE, flat=True)
    return ic.done()


def vial(c, n=1):
    ic = Icon()
    spots = [(12, 0)] if n == 1 else [(5, 3), (12, 0), (19, 3)]
    for x, dy in spots:
        w = 8 if n == 1 else 7
        ic.add(R((x, 6 + dy, x + w, 27), 3), GLASS)
        ic.add(R((x + 1, 13 + dy, x + w - 1, 26), 2), c)
        ic.add(R((x - 1, 3 + dy, x + w + 1, 7 + dy), 1), SLATE)
    return ic.done()


def pen(c, c2=WHITE):
    ic = Icon().add(R((13, 2, 19, 6), 1), c2)
    ic.add(R((11, 5, 21, 24), 3), c)
    ic.add(R((13, 9, 19, 17), 1), GLASS, flat=True)
    ic.add(R((14, 24, 18, 29)), GRAY)
    return ic.done()


def pill(c):
    ic = Icon().add(E((7, 7, 25, 25)), c)
    ic.add(E((11, 11, 21, 21)), light(c, 0.25), flat=True)
    return shine(ic, 10, 10).done()


def capsule(c):
    ic = Icon().add(R((5, 11, 27, 21), 5), WHITE)
    ic.add(R((5, 11, 16, 21), 5), c)
    ic.add(R((12, 11, 16, 21)), c)
    return shine(ic, 8, 13).done()


def flask(c):
    ic = Icon().add(R((13, 4, 19, 13)), GLASS)
    ic.add(E((7, 11, 25, 29)), GLASS)
    ic.add(E((8, 17, 24, 28)), c)
    ic.add(R((12, 2, 20, 5), 1), BROWN)
    return shine(ic, 10, 14).done()


def drop(c):
    ic = Icon().add(P([(16, 3), (23, 16), (9, 16)]), c)
    ic.add(E((8, 11, 24, 27)), c)
    return shine(ic, 11, 15).done()


def module(c):
    ic = Icon()
    for x in (9, 13, 17, 21):
        ic.add(R((x, 5, x + 1, 9)), SILVER, shade=False)
        ic.add(R((x, 23, x + 1, 27)), SILVER, shade=False)
    ic.add(R((5, 8, 26, 24), 2), SLATE)
    ic.add(R((9, 12, 22, 20), 1), c)
    return shine(ic, 10, 13).done()


def coin(c=GOLD, n=1):
    ic = Icon()
    if n == 1:
        ic.add(E((7, 7, 25, 25)), c).add(E((11, 11, 21, 21)), dark(c, 0.12), flat=True)
        return shine(ic, 10, 10).done()
    for i, (x, y) in enumerate(((9, 15), (5, 9), (12, 6))):
        ic.add(E((x, y, x + 14, y + 14)), c if i != 1 else light(c, 0.1))
    return ic.done()


def bar(c=GOLD):
    ic = Icon().add(P([(5, 24), (9, 12), (23, 12), (27, 24)]), c)
    ic.add(P([(10, 14), (22, 14), (24, 22), (8, 22)]), light(c, 0.2), flat=True)
    return ic.done()


def egg(c, c2=WHITE):
    ic = Icon().add(E((8, 4, 24, 28)), c)
    ic.add(E((11, 14, 15, 18)), c2, flat=True).add(E((17, 19, 21, 23)), c2, flat=True)
    return shine(ic, 12, 8).done()


def ticket(c):
    ic = Icon().add(R((3, 10, 28, 22), 1), c)
    ic.cut(E((1, 14, 5, 18))).cut(E((26, 14, 30, 18)))
    ic.dot([(20, y) for y in range(12, 21, 2)], dark(c, 0.35))
    ic.add(R((7, 14, 16, 15)), WHITE, flat=True).add(R((7, 17, 13, 18)), WHITE, flat=True)
    return ic.done()


def lens(c):
    ic = Icon().add(L([(20, 20), (27, 27)], 3), SLATE, shade=False)
    ic.add(E((5, 5, 23, 23)), GRAY)
    ic.add(E((8, 8, 20, 20)), c)
    return shine(ic, 10, 10).done()


def glasses(c):
    ic = Icon().add(L([(13, 15), (19, 15)], 1), SLATE, shade=False)
    ic.add(R((3, 11, 14, 20), 3), c).add(R((18, 11, 29, 20), 3), c)
    ic.add(R((5, 13, 12, 18), 2), GLASS, flat=True).add(R((20, 13, 27, 18), 2), GLASS, flat=True)
    return ic.done()


def orb(c):
    ic = Icon().add(E((6, 6, 26, 26)), c)
    ic.add(E((12, 12, 22, 22)), dark(c, 0.2), flat=True)
    return shine(ic, 10, 10).done()


def blackhole(c=PURPLE):
    ic = Icon().add(E((4, 4, 28, 28)), dark(c, 0.3))
    ic.add(E((8, 8, 24, 24)), c, flat=True)
    ic.add(E((11, 11, 21, 21)), BLACK, flat=True)
    return ic.done()


def claw(c):
    ic = Icon()
    for dx in (0, 6, 12):
        ic.add(P([(7 + dx, 26), (10 + dx, 26), (12 + dx, 14), (10 + dx, 5), (8 + dx, 12)]), c)
    return ic.done()


def band(c):
    ic = Icon().add(E((4, 9, 28, 23)), c)
    ic.cut(E((8, 12, 24, 20)))
    ic.add(P([(20, 18), (26, 28), (22, 28), (18, 21)]), dark(c, 0.1))
    return ic.done()


def drive(c):
    ic = Icon().add(R((7, 7, 25, 25), 1), SLATE)
    ic.add(R((9, 9, 23, 17)), c)
    ic.add(R((10, 20, 22, 23)), SILVER, flat=True)
    return ic.done()


def mask(c):
    ic = Icon().add(E((6, 6, 26, 26)), c)
    ic.cut(E((9, 12, 14, 16))).cut(E((18, 12, 23, 16)))
    ic.add(R((13, 20, 19, 22)), dark(c, 0.3), flat=True)
    return ic.done()


def sweet(c):
    ic = Icon().add(E((6, 14, 26, 27)), TAN)
    ic.add(E((7, 10, 25, 20)), c)
    ic.add(E((14, 5, 19, 10)), RED)
    return ic.done()


def apple(c):
    ic = Icon().add(E((7, 9, 25, 27)), c)
    ic.add(L([(16, 10), (17, 5)], 1), BROWN, shade=False)
    ic.add(P([(17, 7), (22, 4), (24, 7), (19, 9)]), GREEN)
    return shine(ic, 10, 13).done()


def cup(c):
    ic = Icon().add(E((4, 22, 28, 28)), WHITE)
    ic.add(E((20, 13, 28, 21)), c).cut(E((22, 15, 26, 19)))
    ic.add(P([(6, 11), (24, 11), (21, 24), (9, 24)]), c)
    ic.add(R((7, 11, 23, 13)), dark(c, 0.3), flat=True)
    return ic.done()


def mushroom(c):
    ic = Icon().add(R((12, 15, 20, 27), 2), CREAM)
    ic.add(E((5, 5, 27, 19)), c)
    ic.add(E((9, 8, 13, 11)), WHITE, flat=True).add(E((18, 9, 22, 12)), WHITE, flat=True)
    return ic.done()


def scale(c):
    ic = Icon().add(P([(16, 5), (24, 10), (23, 21), (16, 27), (9, 21), (8, 10)]), c)
    ic.add(L([(16, 9), (16, 23)]), light(c, 0.4), shade=False, flat=True)
    return ic.done()


def gadget(c):
    ic = Icon().add(R((6, 5, 26, 27), 3), SLATE)
    ic.add(R((9, 8, 23, 18), 1), c)
    ic.add(E((10, 21, 14, 25)), RED, flat=True).add(R((17, 22, 23, 24)), SILVER, flat=True)
    return shine(ic, 11, 10).done()


def herb(c):
    ic = Icon().add(L([(16, 28), (16, 10)], 2), dark(GREEN, 0.2), shade=False)
    ic.add(P([(16, 12), (8, 7), (7, 14)]), c).add(P([(16, 14), (25, 9), (25, 17)]), c)
    ic.add(P([(16, 6), (13, 2), (19, 2)]), c).add(P([(16, 20), (9, 17), (10, 23)]), c)
    return ic.done()


def seed(c):
    ic = Icon().add(E((9, 11, 23, 27)), c)
    ic.add(P([(16, 12), (11, 5), (15, 4)]), GREEN).add(P([(16, 12), (21, 4), (23, 8)]), GREEN)
    return shine(ic, 12, 15).done()


def crate(c, band=None):
    ic = Icon().add(R((5, 10, 27, 27), 1), c)
    ic.add(R((4, 7, 28, 12), 1), light(c, 0.15))
    ic.add(R((14, 7, 18, 27)), band or GOLD, flat=True)
    ic.add(R((8, 16, 11, 19)), dark(c, 0.3), flat=True)
    return ic.done()


def meat():
    ic = Icon().add(L([(19, 19), (26, 26)], 3), WHITE, shade=False)
    ic.add(E((23, 23, 28, 28)), WHITE).add(E((24, 20, 29, 25)), WHITE)
    ic.add(E((4, 5, 22, 23)), (176, 74, 56))
    ic.add(E((8, 9, 17, 17)), (214, 110, 90), flat=True)
    return ic.done()


def bread():
    ic = Icon().add(R((4, 10, 28, 25), 7), TAN)
    for x in (10, 16, 22):
        ic.add(L([(x - 2, 14), (x + 1, 18)]), dark(TAN, 0.25), shade=False, flat=True)
    return shine(ic, 8, 12).done()


def mintchoco():
    ic = Icon().add(P([(10, 16), (22, 16), (16, 29)]), TAN)
    ic.add(E((8, 4, 24, 19)), MINT)
    ic.dot([(12, 9), (17, 8), (14, 13), (20, 12), (11, 15), (18, 15)], (70, 40, 30))
    return ic.done()


def burger():
    ic = Icon().add(R((6, 19, 26, 25), 2), TAN)
    ic.add(R((5, 16, 27, 19)), (110, 64, 40))
    ic.add(R((5, 15, 27, 16)), GREEN, flat=True)
    ic.add(E((6, 6, 26, 18)), (226, 160, 80))
    ic.dot([(11, 10), (15, 9), (19, 11), (13, 12)], CREAM)
    return ic.done()


def soup():
    ic = Icon().add(L([(12, 3), (11, 8)]), SILVER, shade=False).add(L([(19, 2), (20, 7)]), SILVER, shade=False)
    ic.add(P([(4, 15), (28, 15), (23, 26), (9, 26)]), WHITE)
    ic.add(E((5, 12, 27, 18)), ORANGE, flat=True)
    return ic.done()


def battery():
    ic = Icon().add(R((13, 3, 19, 7)), SILVER)
    ic.add(R((9, 6, 23, 28), 2), SLATE)
    ic.add(P([(18, 9), (12, 18), (16, 18), (14, 25), (20, 15), (16, 15)]), YELLOW, flat=True)
    return ic.done()


def medkit(c, cross=WHITE):
    ic = Icon().add(R((12, 5, 20, 10), 1), SLATE).cut(R((14, 7, 18, 10)))
    ic.add(R((4, 9, 28, 27), 2), c)
    ic.add(R((14, 12, 18, 24)), cross, flat=True).add(R((10, 16, 22, 20)), cross, flat=True)
    return ic.done()


def gift(c=PINK):
    ic = Icon().add(E((9, 4, 16, 10)), GOLD).add(E((16, 4, 23, 10)), GOLD)
    ic.add(R((7, 12, 25, 27)), c).add(R((6, 9, 26, 13)), light(c, 0.15))
    ic.add(R((15, 9, 17, 27)), GOLD, flat=True)
    return ic.done()


def lunchbox(c=RED):
    ic = Icon().add(R((4, 11, 28, 26), 2), c)
    ic.add(R((4, 11, 28, 15)), light(c, 0.2), flat=True)
    ic.add(L([(6, 8), (26, 4)], 1), BROWN, shade=False).add(L([(6, 10), (26, 6)], 1), BROWN, shade=False)
    return ic.done()


def bell(c=GOLD):
    ic = Icon().add(E((14, 23, 19, 28)), dark(c, 0.3))
    ic.add(P([(16, 4), (22, 9), (23, 20), (26, 24), (6, 24), (9, 20), (10, 9)]), c)
    return shine(ic, 12, 10).done()


def crown(c=GOLD):
    ic = Icon().add(P([(5, 24), (5, 10), (11, 16), (16, 7), (21, 16), (27, 10), (27, 24)]), c)
    ic.add(E((14, 17, 18, 21)), RED, flat=True)
    return ic.done()


def ring(c=GOLD, stone=TEAL):
    ic = Icon().add(E((6, 9, 26, 28)), c).cut(E((10, 13, 22, 24)))
    ic.add(P([(16, 3), (21, 8), (16, 13), (11, 8)]), stone)
    return ic.done()


def paper(c=CREAM, top=RED):
    ic = Icon().add(R((6, 5, 26, 27), 1), c)
    ic.add(R((6, 5, 26, 10)), top, flat=True)
    for y in (14, 18, 22):
        ic.add(R((9, y, 23, y)), dark(c, 0.3), flat=True)
    return ic.done()


def map_icon():
    ic = Icon().add(P([(4, 8), (12, 5), (20, 8), (28, 5), (28, 24), (20, 27), (12, 24), (4, 27)]), (120, 186, 120))
    ic.add(E((14, 11, 22, 19)), SKY, flat=True)
    ic.add(L([(12, 6), (12, 24)]), dark(GREEN, 0.2), flat=True).add(L([(20, 9), (20, 26)]), dark(GREEN, 0.2), flat=True)
    ic.dot([(17, 15), (18, 15), (17, 14)], RED)
    return ic.done()


def doll(c=PINK):
    ic = Icon().add(E((6, 4, 13, 12)), c).add(E((19, 4, 26, 12)), c)
    ic.add(E((7, 7, 25, 27)), c)
    ic.dot([(12, 15), (19, 15)], OUT[:3]).dot([(15, 19), (16, 19)], dark(c, 0.4))
    return ic.done()


def stick(c=BROWN):
    return Icon().add(L([(7, 26), (25, 6)], 3), c).add(E((22, 3, 28, 9)), RED).done()


def glove(c=RED):
    ic = Icon().add(R((7, 8, 25, 22), 5), c)
    ic.add(R((10, 20, 22, 27), 1), WHITE)
    ic.add(L([(12, 10), (12, 16)]), dark(c, 0.3), flat=True).add(L([(17, 10), (17, 16)]), dark(c, 0.3), flat=True)
    return ic.done()


def net(c=GOLD):
    ic = Icon().add(L([(16, 18), (26, 28)], 2), BROWN, shade=False)
    ic.add(E((4, 4, 20, 20)), c).cut(E((6, 6, 18, 18)))
    ic.add(E((6, 6, 18, 18)), WHITE, shade=False, flat=True)
    for k in (9, 12, 15):
        ic.add(L([(k, 7), (k, 17)]), SILVER, flat=True).add(L([(7, k), (17, k)]), SILVER, flat=True)
    return ic.done()


def scroll(c=CREAM, roll=BROWN):
    ic = Icon().add(R((7, 6, 25, 26)), c)
    ic.add(R((5, 4, 27, 8), 2), roll).add(R((5, 24, 27, 28), 2), roll)
    for y in (12, 16, 20):
        ic.add(R((10, y, 22, y)), dark(c, 0.35), flat=True)
    return ic.done()


def sword(c=SILVER):
    ic = Icon().add(P([(24, 4), (27, 5), (13, 20), (11, 18)]), c)
    ic.add(L([(8, 15), (16, 23)], 2), GOLD, shade=False)
    ic.add(L([(5, 27), (11, 21)], 2), BROWN, shade=False)
    return ic.done()


def shield(c=SILVER):
    ic = Icon().add(P([(6, 6), (26, 6), (25, 18), (16, 28), (7, 18)]), c)
    ic.add(P([(16, 9), (22, 9), (21, 18), (16, 23)]), dark(c, 0.2), flat=True)
    return ic.done()


def bag(c=TAN):
    ic = Icon().add(P([(9, 12), (23, 12), (27, 26), (5, 26)]), c)
    ic.add(R((12, 7, 20, 12), 1), c).add(R((11, 11, 21, 13)), RED, flat=True)
    return ic.done()


def bone():
    ic = Icon().add(L([(9, 23), (23, 9)], 4), CREAM)
    for b in ((4, 20, 10, 26), (7, 23, 13, 29), (19, 3, 25, 9), (22, 6, 28, 12)):
        ic.add(E(b), CREAM)
    return ic.done()


def leek():
    ic = Icon().add(L([(8, 26), (20, 14)], 4), WHITE)
    ic.add(P([(18, 12), (26, 3), (28, 5), (23, 13), (21, 16)]), GREEN)
    return ic.done()


def feather(c):
    ic = Icon().add(P([(8, 27), (12, 17), (20, 7), (26, 4), (24, 12), (17, 21)]), c)
    ic.add(L([(8, 27), (24, 6)]), WHITE, shade=False, flat=True)
    return ic.done()


def lock_capsule():
    ic = Icon().add(E((10, 3, 22, 15)), SILVER).cut(E((13, 6, 19, 12)))
    ic.add(R((7, 11, 25, 27), 2), GOLD)
    ic.add(R((15, 16, 17, 22)), dark(GOLD, 0.4), flat=True)
    return ic.done()


def watermelon():
    ic = Icon().add(E((5, 6, 27, 27)), (70, 160, 70))
    for x in (10, 16, 22):
        ic.add(L([(x, 8), (x - 1, 25)]), (40, 100, 44), shade=False, flat=True)
    return shine(ic, 9, 10).done()


def chocolate():
    ic = Icon().add(R((7, 5, 25, 27), 1), (110, 64, 40))
    for x in (13, 19):
        ic.add(L([(x, 6), (x, 26)]), (80, 44, 28), flat=True)
    for y in (12, 19):
        ic.add(L([(8, y), (24, y)]), (80, 44, 28), flat=True)
    ic.add(R((7, 21, 25, 27)), (200, 60, 60), flat=True)
    return ic.done()


def potato(c=(196, 150, 96), skin=None):
    ic = Icon().add(P([(5, 16), (9, 9), (17, 7), (25, 10), (27, 18), (22, 25), (12, 26), (6, 22)]), c)
    ic.dot([(11, 13), (18, 11), (21, 18), (13, 20)], dark(c, 0.3))
    return ic.done()


def sweet_potato(c=(170, 60, 96), inside=GOLD):
    ic = Icon().add(P([(4, 20), (8, 11), (18, 6), (27, 7), (26, 15), (17, 23), (8, 25)]), c)
    ic.add(E((20, 6, 28, 13)), inside, flat=True)
    return ic.done()


def drumstick():
    ic = Icon().add(L([(19, 19), (26, 26)], 3), WHITE, shade=False)
    ic.add(E((23, 23, 28, 28)), WHITE).add(E((24, 20, 29, 25)), WHITE)
    ic.add(E((4, 5, 22, 23)), (214, 150, 60))
    ic.dot([(9, 10), (13, 9), (8, 15), (15, 14), (11, 18)], (176, 110, 40))
    return ic.done()


def truffle():
    ic = Icon().add(P([(6, 16), (9, 8), (16, 5), (24, 8), (27, 16), (23, 25), (14, 27), (7, 23)]), (90, 66, 56))
    ic.dot([(10, 12), (15, 9), (21, 13), (12, 19), (19, 20), (24, 17)], (60, 44, 38))
    return ic.done()


def jar(c=(110, 64, 40), lid=WHITE):
    ic = Icon().add(R((7, 9, 25, 27), 3), c)
    ic.add(R((8, 4, 24, 9), 1), lid)
    ic.add(R((9, 14, 23, 20)), WHITE, flat=True)
    ic.add(R((12, 16, 20, 17)), RED, flat=True)
    return ic.done()


BERRY = {"sitrus_berry": lambda: apple(RED), "lum_berry": lambda: apple(GOLD), "enigma_berry": watermelon,
         "liechi_berry": chocolate, "ganlon_berry": potato, "petaya_berry": lambda: mushroom(CREAM),
         "apicot_berry": sweet_potato, "salac_berry": drumstick, "lansat_berry": truffle,
         "starf_berry": lambda: sweet_potato((200, 110, 60), (250, 200, 80)), "leppa_berry": jar}


# ── 이름 → 그림 규칙 (위에서부터 먼저 맞는 것) ─────────────
FOODS = {"potion": meat, "super_potion": bread, "hyper_potion": mintchoco, "max_potion": burger, "full_restore": soup}
DRINKS = {"ether": (SKY, GLASS, SILVER), "max_ether": ((236, 176, 60), GLASS, BROWN), "elixir": ((236, 120, 90), GLASS, RED),
          "max_elixir": ((120, 196, 120), (186, 220, 190), GOLD)}
STATUS_HEAL = {"antidote": (160, 96, 186), "awakening": SKY, "burn_heal": ORANGE, "ice_heal": (116, 206, 226), "paralyze_heal": YELLOW}
X_ITEMS = {"attack": RED, "defense": BLUE, "sp_atk": PURPLE, "sp_def": TEAL, "speed": YELLOW, "accuracy": GREEN}
MODULE = {"silk_scarf": "normal", "black_belt": "fighting", "sharp_beak": "flying", "poison_barb": "poison", "soft_sand": "ground",
          "hard_stone": "rock", "silver_powder": "bug", "spell_tag": "ghost", "metal_coat": "steel", "charcoal": "fire",
          "mystic_water": "water", "miracle_seed": "grass", "magnet": "electric", "twisted_spoon": "psychic",
          "never_melt_ice": "ice", "dragon_fang": "dragon", "black_glasses": "dark", "fairy_feather": "fairy"}
CRATES = {"pb": (SILVER, RED), "gb": (BLUE, RED), "ub": (BLACK, YELLOW), "rb": (TEAL, PINK), "mb": (PURPLE, PINK),
          "lb": (BLACK, GOLD), "pb_gold": (GOLD, RED), "pb_silver": (SILVER, BLUE), "strange_ball": (PINK, TEAL)}
CHARMS = {"exp_charm": (BLUE, None), "super_exp_charm": (SILVER, BLUE), "golden_exp_charm": (GOLD, YELLOW), "shiny_charm": (YELLOW, WHITE),
          "oval_charm": (WHITE, PINK), "healing_charm": (GREEN, WHITE), "catching_charm": (RED, WHITE), "ability_charm": (PURPLE, WHITE)}
EGGS = {"common_egg": (WHITE, GRAY), "rare_egg": (BLUE, WHITE), "epic_egg": (PURPLE, WHITE), "legendary_egg": (GOLD, RED),
        "manaphy_egg": (SKY, RED), "mystery_egg": (GRAY, PURPLE), "rogue_egg": (TEAL, WHITE), "golden_egg": (GOLD, YELLOW),
        "lucky_egg": (CREAM, RED)}


def draw(name: str) -> Image.Image:
    n = name
    base = n[3:] if n.startswith("wl_") else n
    if base in FOODS:
        return FOODS[base]()
    if base in DRINKS:
        return bottle(*DRINKS[base])
    if base in STATUS_HEAL:
        return spray(STATUS_HEAL[base])
    if base == "full_heal":
        return medkit(WHITE, RED)
    if base == "revive":
        return battery()
    if base == "max_revive":
        return medkit(TEAL)
    if base in ("sacred_ash",):
        return gift()
    if base in ("guard_spec",):
        return pen(SILVER, BLUE)
    if n.startswith("wl_"):
        return {"ability_urge": lambda: pill(PURPLE), "item_drop": lambda: bag(), "item_urge": lambda: pill(GOLD),
                "reset_urge": lambda: pill(SKY), "custom_spliced": lambda: gadget(PURPLE), "custom_thief": lambda: glove(SLATE)
                }.get(base, lambda: crate(hue(n)))()
    if n in CRATES:
        return crate(*CRATES[n])
    if n in ("rare_candy", "candy"):
        return vial(RED)
    if n == "rarer_candy":
        return vial(RED, 3)
    if n == "candy_overlay":
        return vial(WHITE)
    if n in ("pp_up", "pp_max"):
        return can(BLUE if n == "pp_up" else GOLD)
    if n in ("lure", "super_lure", "max_lure"):
        return perfume({"lure": PINK, "super_lure": SILVER, "max_lure": GOLD}[n])
    if n in ("repel", "super_repel", "max_repel"):
        return spray({"repel": GREEN, "super_repel": BLUE, "max_repel": GOLD}[n])
    m = re.fullmatch(r"x_(\w+)", n)
    if m:
        return pen(X_ITEMS.get(m[1], GRAY))
    if n == "dire_hit":
        return pen(ORANGE, RED)
    vit = {"hp_up": lambda: pill(GOLD), "protein": lambda: pen(RED, WHITE), "iron": lambda: flask(BLUE),
           "calcium": lambda: drop(SKY), "zinc": lambda: capsule(GREEN), "carbos": lambda: capsule(PURPLE)}
    if n in vit:
        return vit[n]()
    if n in MODULE:
        return module(TYPE[MODULE[n]])
    if n == "nugget":
        return coin(GOLD)
    if n == "big_nugget":
        return coin(GOLD, 3)
    if n == "relic_gold":
        return bar(GOLD)
    if n == "amulet_coin":
        return charm(GOLD, YELLOW)
    if n == "coin_case":
        return bag(BROWN)
    if n in CHARMS:
        return charm(*CHARMS[n])
    if n in EGGS:
        return egg(*EGGS[n])
    if n in ("coupon", "mystic_ticket", "golden_mystic_ticket", "pair_of_tickets"):
        return ticket({"coupon": TEAL, "mystic_ticket": PURPLE, "golden_mystic_ticket": GOLD, "pair_of_tickets": PINK}[n])
    if n in ("mini_black_hole", "boss_mini_black_hole"):
        return blackhole(PURPLE if n.startswith("mini") else RED)
    if n == "map":
        return map_icon()
    if n == "leftovers":
        return lunchbox()
    if n == "mega_bracelet":
        return ring(SILVER, (110, 210, 160))
    if n in ("dynamax_band",):
        return band(RED)
    if n in ("tera_orb",):
        return orb(SKY)
    if n == "calendar":
        return paper()
    if n in ("exp_share", "exp_balance", "scanner", "dna_splicers", "upgrade", "dubious_disc", "electirizer", "magmarizer",
             "protector", "n_lunarizer", "n_solarizer", "reveal_glass", "metronome", "booster_energy", "loaded_dice"):
        return gadget({"exp_share": SKY, "exp_balance": TEAL, "scanner": GREEN, "dna_splicers": PURPLE, "upgrade": BLUE,
                       "dubious_disc": PINK, "electirizer": YELLOW, "magmarizer": ORANGE, "protector": GRAY,
                       "n_lunarizer": PURPLE, "n_solarizer": GOLD, "reveal_glass": SKY, "metronome": SILVER,
                       "booster_energy": YELLOW, "loaded_dice": RED}.get(n, hue(n)))
    if n == "lock_capsule":
        return lock_capsule()
    if n in ("ability_capsule",):
        return capsule(PURPLE)
    if n in ("berry_pouch", "berry_pot"):
        return bag(PINK if n == "berry_pouch" else BROWN)
    if n == "candy_jar":
        return bottle(RED, GLASS, GOLD)
    if n in ("berry_juice_good", "berry_juice_bad", "black_sludge"):
        return bottle({"berry_juice_good": ORANGE, "berry_juice_bad": (120, 110, 70), "black_sludge": BLACK}[n])
    if n == "old_gateau":
        return sweet(BROWN)
    if n == "shell_bell" or n == "soothe_bell":
        return bell(PINK if n == "shell_bell" else GOLD)
    if n in ("kings_rock", "relic_crown", "leaders_crest"):
        return crown(GOLD if n != "leaders_crest" else SILVER)
    if n in ("focus_band", "focus_sash", "choice_scarf", "muscle_band", "expert_belt", "binding_band", "macho_brace",
             "relic_band", "reaper_cloth", "galarica_cuff", "galarica_wreath", "linking_cord"):
        return band({"focus_band": RED, "focus_sash": ORANGE, "choice_scarf": BLUE, "muscle_band": YELLOW, "expert_belt": BLACK,
                     "binding_band": TEAL, "macho_brace": GRAY, "relic_band": GOLD, "reaper_cloth": PURPLE,
                     "galarica_cuff": TEAL, "galarica_wreath": TEAL, "linking_cord": PINK}[n])
    if n in ("scope_lens", "wide_lens", "multi_lens", "zoom_lens", "diffusion_lens"):
        return lens({"scope_lens": RED, "wide_lens": SKY, "multi_lens": PURPLE, "zoom_lens": GREEN, "diffusion_lens": PINK}[n])
    if n in ("wise_glasses", "choice_specs"):
        return glasses(BLUE if n == "choice_specs" else SLATE)
    if n in ("toxic_orb", "flame_orb", "light_ball", "red_orb", "blue_orb", "lustrous_globe", "soul_dew", "griseous_core",
             "adamant_crystal", "unknown", "inverse"):
        return orb({"toxic_orb": PURPLE, "flame_orb": ORANGE, "light_ball": YELLOW, "red_orb": RED, "blue_orb": BLUE,
                    "lustrous_globe": PINK, "soul_dew": SKY, "griseous_core": SLATE, "adamant_crystal": TEAL,
                    "unknown": GRAY, "inverse": BLACK}[n])
    if n in ("quick_claw", "grip_claw", "razor_claw", "razor_fang", "deep_sea_tooth"):
        return claw({"quick_claw": YELLOW, "grip_claw": GRAY, "razor_claw": SILVER, "razor_fang": WHITE, "deep_sea_tooth": CREAM}[n])
    m = re.fullmatch(r"(burn|chill|douse|shock)_drive", n)
    if m:
        return drive({"burn": RED, "chill": SKY, "douse": BLUE, "shock": YELLOW}[m[1]])
    if n.endswith("_mask"):
        return mask({"cornerstone_mask": GRAY, "hearthflame_mask": RED, "wellspring_mask": BLUE}.get(n, TEAL))
    if n.endswith("_sweet"):
        return sweet({"berry_sweet": RED, "clover_sweet": GREEN, "flower_sweet": PINK, "love_sweet": PINK, "ribbon_sweet": PURPLE,
                      "star_sweet": YELLOW, "strawberry_sweet": RED}.get(n, PINK))
    if n in ("whipped_dream",):
        return sweet(WHITE)
    if n.endswith("_apple"):
        return apple({"sweet_apple": RED, "tart_apple": GREEN, "syrupy_apple": GOLD}.get(n, RED))
    if n.endswith("_teacup") or n.endswith("_pot"):
        return cup({"masterpiece_teacup": GOLD}.get(n, TEAL))
    if "mushroom" in n:
        return mushroom(RED if n == "max_mushrooms" else ORANGE)
    if n in ("white_herb", "power_herb", "mirror_herb", "big_root", "gracidea", "mystic_mint"):
        return herb({"white_herb": WHITE, "power_herb": RED, "mirror_herb": SKY, "big_root": BROWN, "gracidea": PINK,
                     "mystic_mint": MINT}[n])
    if n == "reviver_seed":
        return seed(TAN)
    m = re.fullmatch(r"mint_(\w+)", n)
    if m:
        return leaf({"atk": RED, "def": BLUE, "spatk": PURPLE, "spdef": TEAL, "spd": YELLOW, "neutral": MINT}.get(m[1], MINT))
    if n in ("dragon_scale", "prism_scale", "deep_sea_scale"):
        return scale({"dragon_scale": TEAL, "prism_scale": PINK, "deep_sea_scale": BLUE}[n])
    if n in ("eviolite", "everstone"):
        return gem((176, 140, 220)) if n == "eviolite" else stone(GRAY)
    if n.endswith("_meteorite") or n in ("mystical_rock", "peat_block", "black_augurite", "hard_stone", "oval_stone"):
        return stone({"hard_meteorite": PURPLE, "sharp_meteorite": RED, "smooth_meteorite": BLUE, "mystical_rock": TEAL,
                      "peat_block": BROWN, "black_augurite": BLACK, "oval_stone": WHITE}.get(n, GRAY))
    if n.endswith("_stone"):
        return stone({"fire_stone": ORANGE, "water_stone": BLUE, "leaf_stone": GREEN, "thunder_stone": YELLOW, "ice_stone": SKY,
                      "moon_stone": SLATE, "sun_stone": ORANGE, "dusk_stone": PURPLE, "dawn_stone": TEAL, "shiny_stone": WHITE,
                      "light_stone": WHITE, "dark_stone": BLACK}.get(n, hue(n)))
    if n in ("sun_flute", "moon_flute"):
        return stick(GOLD if n == "sun_flute" else SILVER)
    if n in ("baton",):
        return stick(GRAY)
    if n.startswith("lucky_punch") or n == "golden_punch":
        return glove({"lucky_punch": RED, "lucky_punch_great": BLUE, "lucky_punch_ultra": YELLOW, "lucky_punch_master": PURPLE,
                      "golden_punch": GOLD}[n])
    if n == "golden_net":
        return net()
    if n == "clefairy_doll":
        return doll()
    if n.startswith("scroll_of"):
        return scroll(CREAM, BLACK if "darkness" in n else BLUE)
    if n == "rusted_sword":
        return sword((176, 150, 120))
    if n == "rusted_shield":
        return shield((176, 150, 120))
    if n in ("auspicious_armor", "malicious_armor", "metal_alloy", "metal_powder", "quick_powder", "sachet"):
        if n.endswith("powder") or n == "sachet":
            return bag({"metal_powder": SILVER, "quick_powder": YELLOW, "sachet": PINK}[n])
        return shield({"auspicious_armor": GOLD, "malicious_armor": PURPLE, "metal_alloy": SILVER}[n])
    if n == "thick_club":
        return bone()
    if n == "leek":
        return leek()
    if n.endswith("_reins_of_unity"):
        return band(SKY if n.startswith("icy") else BLACK)
    if n == "prison_bottle":
        return bottle(PURPLE, GLASS, GOLD)
    if n == "chipped_pot" or n == "cracked_pot":
        return cup(PURPLE)
    if n in ("eviolite",):
        return gem(PURPLE)
    if n in ("weakness_policy", "blunder_policy"):
        return paper(CREAM, RED if n == "weakness_policy" else BLUE)
    if n in ("shed_shell",):
        return scale(YELLOW)
    if n in BERRY:  # 블서로그 이름 (locales/ko/berry.json): 사과 · 황금사과 · 수박 · 초콜릿 …
        return BERRY[n]()
    if n.endswith("_berry"):
        return berry(hue(n))
    if n == "fairy_feather":
        return feather(TYPE["fairy"])
    # 역할군(타입) 이름이 붙은 것
    m = re.fullmatch(rf"({TYPES})_(gem|memory|tera_shard)", n)
    if m:
        return {"gem": type_gem, "memory": disc, "tera_shard": shard}[m[2]](TYPE[m[1]])
    if n == "stellar_tera_shard":
        return shard(TYPE["stellar"])
    m = re.fullmatch(r"(\w+)_plate", n)
    if m and m[1] in PLATE:
        return plate(TYPE[PLATE[m[1]]])
    m = re.fullmatch(rf"tm_({TYPES})", n)
    if m:
        return book(TYPE[m[1]])
    m = re.fullmatch(rf"ribbon_({TYPES})", n)
    if m:
        return ribbon(TYPE[m[1]])
    if "ribbon" in n:
        gen = re.fullmatch(r"ribbon_gen(\d)", n)
        if gen:
            return ribbon(HUES[int(gen[1]) % len(HUES)], SILVER)
        return ribbon({"classic_ribbon_default": BLUE, "classic_ribbon_5": TEAL, "classic_ribbon_10": PURPLE, "classic_ribbon_15": RED,
                       "master_ribbon": PURPLE, "ultra_ribbon": YELLOW, "great_ribbon": BLUE, "common_ribbon": GRAY,
                       "rogue_ribbon": TEAL, "hardcore_ribbon": BLACK, "inverse_ribbon": BLACK, "ribbon_friendship": PINK,
                       "fresh_start_ribbon": GREEN, "flip_stats_ribbon": ORANGE}.get(n, hue(n)))
    if n.endswith("_z") or n == "ultranecrozium_z":
        return zcrystal(hue(n))
    if re.search(r"ite(_[xy])?$", n):
        return gem(hue(n), WHITE)
    return crate(hue(n))


# ── 보급 상자 (볼) 18장: 12×16 칸, 닫힘은 아래 12줄 · 열리는 중 13줄 · 열림 16줄 ──
BALLS = {"pb": (SILVER, RED), "gb": (BLUE, RED), "ub": (BLACK, YELLOW), "rb": (TEAL, PINK), "mb": (PURPLE, PINK), "lb": (BLACK, GOLD)}


def ball(kind, state):
    body, band = BALLS[kind]
    ic = Icon(12, 16)
    ic.add(R((2, 9, 9, 14)), body)
    if state == "closed":
        ic.add(R((1, 6, 10, 9)), light(body, 0.15))
    elif state == "opening":
        ic.add(P([(1, 5), (10, 3), (10, 6), (1, 8)]), light(body, 0.15))
    else:
        ic.add(R((1, 1, 10, 3)), light(body, 0.15))
        ic.add(R((3, 7, 8, 8)), (255, 244, 196), shade=False, flat=True)
    ic.add(R((5, 9, 6, 14)), band, shade=False, flat=True)
    img = ic.done()
    return img


# ── 입력 키 아이콘 (키보드 · 패드): 원래 칸 자리 그대로 다시 그려요 ──
F35 = {
    "A": "010101111101101", "B": "110101110101110", "C": "011100100100011", "D": "110101101101110", "E": "111100110100111",
    "F": "111100110100100", "G": "011100101101011", "H": "101101111101101", "I": "111010010010111", "J": "001001001101010",
    "K": "101101110101101", "L": "100100100100111", "M": "101111111101101", "N": "110101101101101", "O": "010101101101010",
    "P": "110101110100100", "Q": "010101101110011", "R": "110101110101101", "S": "011100010001110", "T": "111010010010010",
    "U": "101101101101111", "V": "101101101101010", "W": "101101111111101", "X": "101101010101101", "Y": "101101010010010",
    "Z": "111001010100111", "0": "010101101101010", "1": "010110010010111", "2": "110001010100111", "3": "110001010001110",
    "4": "101101111001001", "5": "111100110001110", "6": "011100110101010", "7": "111001010010010", "8": "010101010101010",
    "9": "010101011001110", "+": "000010111010000", "-": "000000111000000", "[": "110100100100110", "]": "011001001001011",
    ";": "000010000010100", "'": "010010000000000", "/": "001001010100100", "\\": "100100010001001", ",": "000000000010100",
    ".": "000000000000010", "~": "000011110000000", "^": "010111000000000", "v": "000000000111010", "<": "001011111011001",
    ">": "100110111110100", "=": "000111000111000", "o": "000010101010000",
}
UP, DOWN, LEFT, RIGHT = "010111111000000", "000000111111010", "001011111011001", "100110111110100"
KEY_LABEL = {"KEY_ARROW_UP": "^", "KEY_ARROW_DOWN": "v", "KEY_ARROW_LEFT": "<", "KEY_ARROW_RIGHT": ">",
             "LEFT_BRACKET": "[", "RIGHT_BRACKET": "]", "MINUS": "-", "PLUS": "+", "QUOTE": "'", "SEMICOLON": ";",
             "TILDE": "~", "BACK_SLASH": "\\", "FORWARD_SLASH": "/", "COMMA": ",", "PERIOD": ".", "PAGE_UP": "PGUP",
             "PAGE_DOWN": "PGDN"}
KEY_FACE, KEY_TOP, KEY_SIDE, KEY_INK = (44, 52, 72), (66, 76, 104), (28, 32, 46), (236, 240, 247)


def text35(img, x, y, label, c):
    px = img.load()
    for ch in label:
        g = F35.get(ch.upper() if ch not in "v^<>o" else ch)
        if g:
            for i, b in enumerate(g):
                if b == "1" and 0 <= x + i % 3 < img.width and 0 <= y + i // 3 < img.height:
                    px[x + i % 3, y + i // 3] = (*c, 255)
        x += 4


def keycap(w, h, label):
    img = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    d.rounded_rectangle((0, 0, w - 1, h - 1), 2, fill=(*KEY_SIDE, 255), outline=OUT)
    d.rounded_rectangle((1, 1, w - 2, h - 3), 1, fill=(*KEY_FACE, 255))
    d.line([(2, 1), (w - 3, 1)], fill=(*KEY_TOP, 255))
    tw = len(label) * 4 - 1
    text35(img, (w - tw) // 2, (h - 2 - 5) // 2 + 1, label, KEY_INK)
    return img


PAD_COLORS = {"A": (84, 170, 84), "B": (214, 64, 64), "X": (70, 130, 220), "Y": (232, 176, 48)}


def pad_button(name, w, h):
    img = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    key = name.replace("XB_Letter_", "").replace("_OL", "")
    if key in ("UP", "DOWN", "LEFT", "RIGHT"):
        d.rounded_rectangle((0, 0, w - 1, h - 1), 2, fill=(*KEY_FACE, 255), outline=OUT)
        text35(img, (w - 3) // 2, (h - 5) // 2, {"UP": "^", "DOWN": "v", "LEFT": "<", "RIGHT": ">"}[key], KEY_INK)
        return img
    if key in PAD_COLORS or key in ("CROSS", "CIRCLE", "SQUARE", "TRIANGLE"):
        col = PAD_COLORS.get(key, {"CROSS": (70, 130, 220), "CIRCLE": (214, 64, 64), "SQUARE": (200, 110, 190),
                                   "TRIANGLE": (46, 180, 170)}.get(key))
        d.ellipse((0, 0, w - 1, h - 1), fill=(*KEY_FACE, 255), outline=OUT)
        if key in PAD_COLORS:
            text35(img, (w - 3) // 2, (h - 5) // 2, key, col)
        elif key == "CROSS":
            d.line([(4, 4), (7, 7)], fill=(*col, 255)); d.line([(7, 4), (4, 7)], fill=(*col, 255))
        elif key == "CIRCLE":
            d.ellipse((3, 3, 8, 8), outline=(*col, 255))
        elif key == "SQUARE":
            d.rectangle((4, 4, 7, 7), outline=(*col, 255))
        else:
            d.polygon([(6, 3), (9, 8), (3, 8)], outline=(*col, 255))
        return img
    if key in ("LS", "RS", "L3", "R3"):
        d.ellipse((0, 0, w - 1, h - 1), fill=(*KEY_SIDE, 255), outline=OUT)
        d.ellipse((2, 2, w - 3, h - 3), fill=(*KEY_FACE, 255))
        text35(img, (w - 3) // 2, (h - 5) // 2, key[0], KEY_INK)
        return img
    label = {"Bumper_L": "LB", "Bumper_R": "RB", "Trigger_L": "LT", "Trigger_R": "RT", "SELECT": "=", "START": "=",
             "MINUS": "-", "PLUS": "+", "TOUCH": "o"}.get(key, key)
    d.rounded_rectangle((0, 1, w - 1, h - 2), 3, fill=(*KEY_FACE, 255), outline=OUT)
    tw = len(label) * 4 - 1
    text35(img, (w - tw) // 2, (h - 5) // 2, label, KEY_INK)
    return img


def inputs(done):
    for kind in ("keyboard", "xbox", "dualshock", "procon"):
        jp = IMG / "inputs" / f"{kind}.json"
        data = json.load(open(jp, encoding="utf-8"))
        fr = data["frames"]
        items = fr.items() if isinstance(fr, dict) else [(f["filename"], f) for f in fr]
        sheet = Image.open(IMG / "inputs" / f"{kind}.png").convert("RGBA")
        sheet = Image.new("RGBA", sheet.size, (0, 0, 0, 0))
        for fname, f in items:
            name = fname.rsplit(".", 1)[0]
            r = f["frame"]
            if kind == "keyboard":
                img = keycap(r["w"], r["h"], KEY_LABEL.get(name, name))
            else:
                img = pad_button(name, r["w"], r["h"])
            sheet.paste(img, (r["x"], r["y"]))
        sheet.save(IMG / "inputs" / f"{kind}.png", optimize=True)
        done.append(f"images/inputs/{kind}.png")


# ── 실험체 색 (사탕 아이콘 · 도감 색): 실험체 그림에서 많이 쓴 색 두 개 ──
def starter_colors(done):
    path = ROOT / "assets" / "starter-colors.json"
    colors = json.load(open(path, encoding="utf-8"))
    for f in sorted((ROOT / "assets" / "er" / "char").glob("*_0.png")):
        if not f.stem.split("_")[0].isdigit():  # 야생동물 그림은 건너뛰어요
            continue
        er = int(f.stem.split("_")[0])
        im = Image.open(f).convert("RGBA")
        px = [p[:3] for p in (im.get_flattened_data() if hasattr(im, "get_flattened_data") else im.getdata()) if p[3] > 200]
        if not px:
            continue
        q = Image.new("RGB", (len(px), 1))
        q.putdata(px)
        pal = q.quantize(6, method=Image.Quantize.MEDIANCUT)
        counts = sorted(pal.getcolors(), reverse=True)
        raw = pal.getpalette()
        cols = [tuple(raw[i * 3:i * 3 + 3]) for _, i in counts]

        def ok(c):
            return 40 < sum(c) / 3 < 225

        main = next((c for c in cols if ok(c)), cols[0])
        second = max((c for c in cols if c != main), key=lambda c: sum(abs(a - b) for a, b in zip(c, main)), default=main)
        hexes = ["%02x%02x%02x" % dark(main, 0.15), "%02x%02x%02x" % second]
        for stage in range(3):
            colors[str(1030 + er * 3 + stage)] = hexes
    with open(path, "w", encoding="utf-8") as fp:
        json.dump(colors, fp, separators=(",", ":"))
    done.append("starter-colors.json")


# ── 알 · 빈 칸 · 반짝이 별 · 시간 아이콘 · 작은 키 ──────────────
EGG_TIER = {"0": (SILVER, WHITE), "1": (BLUE, SKY), "2": (GOLD, YELLOW), "3": (PURPLE, PINK), "manaphy": (SKY, RED)}


def egg_small(w, h, c, c2):
    ew = min(w - 2, round(h * 0.78))  # 알 모양: 세로로 길고 위가 좁게
    x0 = (w - ew) // 2

    def shape(d):
        d.ellipse((x0, round(h * 0.3), x0 + ew - 1, h - 2), fill=255)
        d.ellipse((x0 + round(ew * 0.12), 1, x0 + ew - 1 - round(ew * 0.12), round(h * 0.75)), fill=255)

    ic = Icon(w, h).add(shape, c)
    cx, cy = w // 2, h // 2 + 1
    ic.add(R((cx - 3, cy, cx - 2, cy + 1)), c2, flat=True).add(R((cx + 1, cy + 2, cx + 2, cy + 3)), c2, flat=True)
    return shine(ic, max(2, w // 3), max(2, h // 4)).done()


def unknown_slot(w, h):
    img = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    d.rounded_rectangle((1, 1, w - 2, h - 2), 3, fill=(40, 46, 64, 180), outline=(96, 108, 140, 255))
    q = "111001011000010"  # ? (3×5) 를 2배로
    px = img.load()
    x0, y0 = (w - 6) // 2, (h - 10) // 2
    for i, b in enumerate(q):
        if b == "1":
            for dx in (0, 1):
                for dy in (0, 1):
                    px[x0 + (i % 3) * 2 + dx, y0 + (i // 3) * 2 + dy] = (150, 162, 186, 255)
    return img


def star(w, h, c):
    cx, cy, r1, r2 = w / 2 - 0.5, h / 2, min(w, h) / 2 - 1, min(w, h) / 4 - 0.5
    import math
    pts = []
    for i in range(10):
        a = -math.pi / 2 + i * math.pi / 5
        r = r1 if i % 2 == 0 else r2
        pts.append((round(cx + r * math.cos(a)), round(cy + r * math.sin(a))))
    return shine(Icon(w, h).add(P(pts), c), int(cx) - 1, int(cy) - 2).done()


TIME_SKY = {"dawn": ((236, 150, 120), (250, 200, 150)), "day": ((110, 180, 240), (250, 220, 90)),
            "dusk": ((200, 100, 120), (250, 160, 80)), "night": ((40, 52, 100), (230, 232, 250))}


def time_icon(t, layer):
    sky, body = TIME_SKY[t]
    ic = Icon(16, 16)
    if layer == "bg":
        ic.add(E((1, 1, 14, 14)), sky, shade=False)
        return ic.img
    if layer == "mg":
        if t == "night":
            ic.add(E((4, 2, 11, 9)), body).cut(E((7, 1, 13, 7)))
        else:
            ic.add(E((5, 2, 10, 7)), body)
        return ic.img
    img = Image.new("RGBA", (16, 16), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    d.ellipse((0, 0, 15, 15), outline=OUT)
    d.ellipse((1, 1, 14, 14), outline=(*GOLD, 255))
    d.chord((1, 1, 14, 14), 20, 160, fill=(*dark(sky, 0.45), 255))
    return img


def prompt_key(letter):
    img = keycap(8, 8, "")
    text35(img, 2, 1, letter, KEY_INK)
    return img


def redraw_atlas(json_path: Path, fn, done):
    data = json.load(open(json_path, encoding="utf-8"))
    tex = data["textures"][0] if "textures" in data else data
    fr = tex["frames"]
    items = [(k, v) for k, v in fr.items()] if isinstance(fr, dict) else [(f["filename"], f) for f in fr]
    png = json_path.with_suffix(".png")
    sheet = Image.new("RGBA", Image.open(png).size, (0, 0, 0, 0))
    for name, f in items:
        r = f["frame"]
        sheet.paste(fn(name, r["w"], r["h"]), (r["x"], r["y"]))
    sheet.save(png, optimize=True)
    done.append(str(png.relative_to(ROOT / "assets")).replace("\\", "/"))


def extras(done):
    def save(img, rel):
        img.save(IMG / rel, optimize=True)
        done.append(f"images/{rel}")

    redraw_atlas(IMG / "egg" / "egg_icons.json", lambda n, w, h: egg_small(w, h, *EGG_TIER[n]), done)
    redraw_atlas(IMG / "egg" / "egg.json", lambda n, w, h: egg_small(w, h, *EGG_TIER[n.replace("egg_", "")]), done)
    redraw_atlas(IMG / "pokemon_icons_0.json",
                 lambda n, w, h: unknown_slot(w, h) if n == "unknown" else egg_small(w, h, *EGG_TIER["0"]), done)
    redraw_atlas(IMG / "ui" / "shiny_icons.json", lambda n, w, h: star(w, h, {"0": YELLOW, "1": SKY, "2": RED}[n]), done)
    save(egg_small(32, 32, *EGG_TIER["0"]).crop((0, 0, 32, 32)), "ui/common_egg.png")
    save(disc(TYPE["normal"]), "ui/normal_memory.png")
    for t in TIME_SKY:
        for layer in ("bg", "mg", "fg"):
            save(time_icon(t, layer), f"ui/{t}_icon_{layer}.png")
    save(prompt_key("A"), "ui/summary_profile_prompt_a.png")
    save(prompt_key("Z"), "ui/summary_profile_prompt_z.png")


def pack(images: dict[str, Image.Image], order: list[str], width: int):
    """선반 쌓기. 투명 둘레를 잘라서 칸 정보(trimmed)와 같이 돌려줘요"""
    rects, x, y, shelf = {}, 0, 0, 0
    for name in order:
        im = images[name]
        box = im.getbbox() or (0, 0, 1, 1)
        w, h = box[2] - box[0], box[3] - box[1]
        if x + w > width:
            x, y, shelf = 0, y + shelf, 0
        rects[name] = (x, y, w, h, box)
        x += w
        shelf = max(shelf, h)
    sheet = Image.new("RGBA", (width, y + shelf), (0, 0, 0, 0))
    for name, (x, y, w, h, box) in rects.items():
        sheet.paste(images[name].crop(box), (x, y))
    return sheet, rects


def write_atlas(json_path: Path, png_name: str, images, order, width):
    data = json.load(open(json_path, encoding="utf-8"))
    sheet, rects = pack(images, order, width)
    tex = data["textures"][0]
    tex["image"] = png_name
    tex["size"] = {"w": sheet.width, "h": sheet.height}
    by = {f["filename"]: f for f in tex["frames"]}
    for name, (x, y, w, h, box) in rects.items():
        f = by[name]
        sw, sh = images[name].size
        f["rotated"] = False
        f["trimmed"] = (w, h) != (sw, sh)
        f["sourceSize"] = {"w": sw, "h": sh}
        f["spriteSourceSize"] = {"x": box[0], "y": box[1], "w": w, "h": h}
        f["frame"] = {"x": x, "y": y, "w": w, "h": h}
    sheet.save(json_path.with_name(png_name), optimize=True)
    with open(json_path, "w", encoding="utf-8") as fp:
        json.dump(data, fp, indent=2, ensure_ascii=False)
        fp.write("\n")
    return sheet


def main():
    done = []
    data = json.load(open(IMG / "items.json", encoding="utf-8"))
    order = [f["filename"] for f in data["textures"][0]["frames"]]
    images = {n: draw(n) for n in order}
    for n, im in images.items():
        im.save(IMG / "items" / f"{n}.png", optimize=True)
        done.append(f"images/items/{n}.png")
    write_atlas(IMG / "items.json", "items.png", images, order, 512)
    done += ["images/items.json", "images/items.png"]

    pbd = json.load(open(IMG / "pb.json", encoding="utf-8"))
    pb_order = [f["filename"] for f in pbd["textures"][0]["frames"]]
    pb_images = {}
    for n in pb_order:
        kind, _, state = n.partition("_")
        pb_images[n] = ball(kind, {"": "closed", "opening": "opening", "open": "open"}[state])
        pb_images[n].save(IMG / "pokeball" / f"{n}.png", optimize=True)
        done.append(f"images/pokeball/{n}.png")
    write_atlas(IMG / "pb.json", "pb.png", pb_images, pb_order, 12)
    done += ["images/pb.json", "images/pb.png"]

    inputs(done)
    starter_colors(done)
    extras(done)

    # 한눈에 보기 (4배)
    cols = 24
    rows = (len(order) + cols - 1) // cols
    sheet = Image.new("RGBA", (cols * 34 + 2, rows * 34 + 2), (36, 40, 54, 255))
    for i, n in enumerate(order):
        sheet.alpha_composite(images[n], (2 + (i % cols) * 34, 2 + (i // cols) * 34))
    sheet.resize((sheet.width * 2, sheet.height * 2), Image.NEAREST).save(ROOT / "docs" / "item-icons-preview.png", optimize=True)

    if MARK.exists():
        marks = set(json.load(open(MARK, encoding="utf-8")))
        before = len(marks)
        marks -= set(done)
        json.dump(sorted(marks), open(MARK, "w", encoding="utf-8"), ensure_ascii=False, indent=0)
        print(f"임시 그림 목록에서 뺀 것: {before - len(marks)}개")
    print(f"아이템 {len(order)}개 · 보급 상자 {len(pb_order)}개")


if __name__ == "__main__":
    sys.exit(main())
