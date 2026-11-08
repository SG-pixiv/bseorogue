# SPDX-FileCopyrightText: 2026 SG
# SPDX-License-Identifier: AGPL-3.0-only
"""
블서로그 UI 그림 (ER 인게임 느낌) 만들기

포켓로그 UI 그림은 쓸 수 없어서 단색 임시 그림이었어요. 이 스크립트가 같은 이름 · 같은 크기 ·
같은 아틀라스 칸으로 UI 를 새로 그려요 (모두 코드로 그려서 스타일이 같아요).

스타일: 어두운 남색 판 + 얇은 테두리 + 모서리 깎기(왼쪽 위 · 오른쪽 아래) + 금색 강조.
창 스타일 1~5 (설정의 "창 스타일"): 1 남색+금색(기본) · 2 남색+청록 · 3 먹색+은색 · 4 먹색+주황 · 5 보라.

글꼴: 갈무리7 · 갈무리9 (OFL). 저장소에 넣지 않고 npm 에서 받아요:
  mkdir -p /tmp/galmuri && cd /tmp/galmuri && npm pack galmuri && tar xzf galmuri-*.tgz
쓰는 법 (저장소 맨 위에서):
  python3 scripts/er-ui/make_ui.py [--fonts /tmp/galmuri/package/dist]
그린 파일은 assets/.placeholders.json 에서 빠져요 (임시 그림 만들기가 덮어쓰지 않게).
"""
import json
import os
import sys
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parents[2]
IMG = ROOT / "assets" / "images"
UI = IMG / "ui"
KO = UI / "text_images" / "ko"
MARK = ROOT / "assets" / ".placeholders.json"
FONTS = Path(sys.argv[sys.argv.index("--fonts") + 1]) if "--fonts" in sys.argv else Path("/tmp/galmuri/package/dist")

# ── 색 ─────────────────────────────────────────────
INK = (6, 8, 13, 255)
WHITE = (236, 240, 247, 255)
DIM = (150, 162, 186, 255)
GOLD = (240, 180, 41, 255)
GOLD_D = (168, 118, 18, 255)
TEAL = (46, 196, 182, 255)
RED = (226, 76, 76, 255)
TRACK = (9, 12, 19, 255)
CLEAR = (0, 0, 0, 0)

# 창 스타일 1~5: 바탕 · 위쪽 바탕 · 테두리 · 강조
THEMES = {
    1: ((20, 25, 38), (27, 33, 50), (74, 88, 118), GOLD),
    2: ((18, 26, 36), (24, 35, 48), (62, 104, 120), TEAL),
    3: ((22, 23, 26), (31, 32, 37), (96, 98, 108), (200, 206, 218, 255)),
    4: ((26, 21, 20), (36, 28, 26), (120, 84, 60), (244, 132, 52, 255)),
    5: ((27, 21, 42), (36, 28, 56), (106, 84, 152), (198, 160, 255, 255)),
}

# 역할군(타입) 색 · 이름 (locales/ko/pokemon-info.json 과 같게)
TYPE_STYLE = {
    "unknown": ((90, 96, 110), "???"),
    "normal": ((112, 120, 104), "야생"),
    "fighting": ((198, 92, 52), "브루저"),
    "flying": ((110, 140, 200), "비행"),
    "poison": ((140, 80, 160), "독"),
    "ground": ((170, 136, 80), "땅"),
    "rock": ((92, 118, 168), "탱커"),
    "bug": ((176, 46, 60), "보스"),
    "ghost": ((96, 84, 150), "고스트"),
    "steel": ((130, 140, 156), "강철"),
    "fire": ((222, 96, 52), "불꽃"),
    "water": ((60, 128, 214), "물"),
    "grass": ((82, 160, 80), "풀"),
    "electric": ((222, 180, 40), "전기"),
    "psychic": ((150, 82, 212), "스증딜러"),
    "ice": ((96, 186, 206), "얼음"),
    "dragon": ((218, 150, 36), "평원딜"),
    "dark": ((70, 60, 84), "암살자"),
    "fairy": ((60, 176, 140), "서포터"),
    "stellar": ((70, 150, 200), "스텔라"),
}
SHORT = {"psychic": "스증", "dragon": "원딜", "dark": "암살", "fighting": "브루", "fairy": "서폿", "rock": "탱커", "normal": "야생", "bug": "보스"}

STATUS_STYLE = {
    "pokerus": ((150, 82, 212), "감염"),
    "burn": ((222, 96, 52), "화상"),
    "faint": ((96, 100, 112), "기절"),
    "freeze": ((96, 186, 206), "빙결"),
    "paralysis": ((222, 180, 40), "마비"),
    "poison": ((140, 80, 160), "독"),
    "sleep": ((110, 120, 140), "수면"),
    "toxic": ((110, 50, 140), "맹독"),
}
CATEGORY_STYLE = {"physical": ((198, 92, 52), "물리"), "special": ((90, 110, 210), "스증"), "status": ((120, 128, 140), "변화")}
HP_COLORS = {"high": ((120, 224, 128), (70, 186, 92), (40, 130, 60)), "medium": ((252, 216, 96), (226, 178, 40), (160, 120, 20)), "low": ((246, 118, 106), (214, 64, 64), (150, 36, 40))}
EXP_COLORS = ((130, 196, 255), (70, 150, 240), (40, 96, 180))

done: list[str] = []


def rgba(c, a=255):
    return tuple(c[:3]) + (a,)


def font(size=8, big=False):
    name = "Galmuri9.ttf" if big else "Galmuri7.ttf"
    path = FONTS / name
    if not path.exists():
        sys.exit(f"글꼴이 없어요: {path} (위 docstring 대로 npm 에서 받아요)")
    return ImageFont.truetype(str(path), size)


F7 = None
F9 = None

# 아주 작은 글자 (3×5) — 숫자 · 영문 몇 개
MINI = {
    "0": ["111", "101", "101", "101", "111"], "1": ["010", "110", "010", "010", "111"], "2": ["111", "001", "111", "100", "111"],
    "3": ["111", "001", "111", "001", "111"], "4": ["101", "101", "111", "001", "001"], "5": ["111", "100", "111", "001", "111"],
    "6": ["111", "100", "111", "101", "111"], "7": ["111", "001", "010", "010", "010"], "8": ["111", "101", "111", "101", "111"],
    "9": ["111", "101", "111", "001", "111"], "/": ["001", "001", "010", "100", "100"], "+": ["000", "010", "111", "010", "000"],
    "-": ["000", "000", "111", "000", "000"], "H": ["101", "101", "111", "101", "101"], "P": ["110", "101", "110", "100", "100"],
    "L": ["100", "100", "100", "100", "111"], "v": ["000", "101", "101", "101", "010"], "E": ["111", "100", "110", "100", "111"],
    "X": ["101", "101", "010", "101", "101"], "N": ["101", "111", "111", "111", "101"], "o": ["000", "010", "101", "101", "010"],
    ".": ["0", "0", "0", "0", "1"],
}

# 5×7 숫자 (HP 숫자처럼 8px 칸을 꽉 채우는 숫자)
DIG57 = {
    "0": ["01110", "10001", "10011", "10101", "11001", "10001", "01110"],
    "1": ["00100", "01100", "00100", "00100", "00100", "00100", "01110"],
    "2": ["01110", "10001", "00001", "00110", "01000", "10000", "11111"],
    "3": ["11110", "00001", "00001", "01110", "00001", "00001", "11110"],
    "4": ["00010", "00110", "01010", "10010", "11111", "00010", "00010"],
    "5": ["11111", "10000", "11110", "00001", "00001", "10001", "01110"],
    "6": ["00110", "01000", "10000", "11110", "10001", "10001", "01110"],
    "7": ["11111", "00001", "00010", "00100", "01000", "01000", "01000"],
    "8": ["01110", "10001", "10001", "01110", "10001", "10001", "01110"],
    "9": ["01110", "10001", "10001", "01111", "00001", "00010", "01100"],
    "/": ["00001", "00010", "00010", "00100", "01000", "01000", "10000"],
}


def digit57(d, x, y, ch, fill, outline=INK):
    g = DIG57.get(ch)
    if not g:
        return
    for gy, row in enumerate(g):
        for gx, b in enumerate(row):
            if b == "1":
                for ox, oy in ((1, 0), (0, 1), (1, 1)):  # 오른쪽 아래 그림자
                    d.point((x + gx + ox, y + gy + oy), fill=outline)
    for gy, row in enumerate(g):
        for gx, b in enumerate(row):
            if b == "1":
                d.point((x + gx, y + gy), fill=fill)



def mini_text(d, x, y, text, fill, outline=None, scale=1):
    """3×5 글자 (outline 이 있으면 1px 테두리)"""
    def put(px, py, c):
        d.rectangle([px, py, px + scale - 1, py + scale - 1], fill=c)
    cx = x
    for ch in text:
        g = MINI.get(ch)
        if not g:
            cx += 2 * scale
            continue
        if outline:
            for gy, row in enumerate(g):
                for gx, b in enumerate(row):
                    if b == "1":
                        for ox, oy in ((-1, 0), (1, 0), (0, -1), (0, 1)):
                            put(cx + (gx + ox) * scale, y + (gy + oy) * scale, outline)
        for gy, row in enumerate(g):
            for gx, b in enumerate(row):
                if b == "1":
                    put(cx + gx * scale, y + gy * scale, fill)
        cx += (len(g[0]) + 1) * scale
    return cx - x


def mini_width(text):
    return sum(len(MINI[c][0]) + 1 if c in MINI else 2 for c in text) - 1


def text(d, xy, s, fill=WHITE, f=None, shadow=True):
    f = f or F7
    d.fontmode = "1"
    x, y = xy
    if shadow:
        d.text((x + 1, y + 1), s, font=f, fill=INK)
    d.text((x, y), s, font=f, fill=fill)


def text_center(d, box, s, fill=WHITE, f=None, shadow=True, dy=0):
    f = f or F7
    x0, y0, x1, y1 = box
    l, t, r, b = d.textbbox((0, 0), s, font=f)
    x = x0 + (x1 - x0 - (r - l)) // 2 - l
    y = y0 + (y1 - y0 - (b - t)) // 2 - t + dy
    text(d, (x, y), s, fill, f, shadow)


def chamfer(x0, y0, x1, y1, c, corners="tl,br"):
    """모서리 깎은 다각형 점 (x1, y1 포함)"""
    tl = "tl" in corners
    tr = "tr" in corners
    br = "br" in corners
    bl = "bl" in corners
    pts = []
    pts += [(x0, y0 + c), (x0 + c, y0)] if tl else [(x0, y0)]
    pts += [(x1 - c, y0), (x1, y0 + c)] if tr else [(x1, y0)]
    pts += [(x1, y1 - c), (x1 - c, y1)] if br else [(x1, y1)]
    pts += [(x0 + c, y1), (x0, y1 - c)] if bl else [(x0, y1)]
    return pts


def panel(d, box, theme=1, c=3, alpha=255, accent=True, band=True, border=None, fill=None, corners="tl,br"):
    """ER 느낌 판: 모서리 깎기 + 테두리 + 위쪽 조금 밝게 + 왼쪽 위 금색 강조"""
    x0, y0, x1, y1 = box
    if x1 - x0 < 2 or y1 - y0 < 2:
        return
    base, top, line, acc = THEMES[theme]
    fill = fill or base
    pts = chamfer(x0, y0, x1, y1, c, corners)
    d.polygon(pts, fill=rgba(fill, alpha))
    if band and y1 - y0 >= 8:
        bh = max(2, min(6, (y1 - y0) // 5))
        for i in range(bh):
            yy = y0 + 1 + i
            xs = x0 + 1 + max(0, c - 1 - i) if "tl" in corners else x0 + 1
            d.line([(xs, yy), (x1 - 1, yy)], fill=rgba(top, alpha))
    d.polygon(pts, outline=rgba(border or line))
    if accent and c >= 2 and "tl" in corners:
        d.line([(x0, y0 + c), (x0 + c, y0)], fill=acc)
        d.line([(x0 + c, y0), (x0 + c + min(6, (x1 - x0) // 4), y0)], fill=acc)


def new(w, h):
    img = Image.new("RGBA", (w, h), CLEAR)
    return img, ImageDraw.Draw(img)


def frames(json_path):
    data = json.load(open(json_path, encoding="utf-8"))
    fr = data["textures"][0]["frames"] if "textures" in data else data["frames"]
    if isinstance(fr, dict):
        fr = [dict(filename=k, **v) for k, v in fr.items()]
    return [(f["filename"], f["frame"]["x"], f["frame"]["y"], f["frame"]["w"], f["frame"]["h"]) for f in fr]


def save(img, path: Path):
    img.save(path, optimize=True)
    done.append(str(path.relative_to(ROOT / "assets")).replace("\\", "/"))


def size_of(path: Path):
    with Image.open(path) as im:
        return im.size


# ── 창 · 대화창 ─────────────────────────────────────
def windows():
    for t in THEMES:
        for suf, c, band, accent in (("", 3, True, True), ("_thin", 3, False, True), ("_xthin", 2, False, False)):
            img, d = new(24, 24)
            panel(d, (0, 0, 23, 23), t, c=c, band=band, accent=accent)
            save(img, UI / "windows" / f"window_{t}{suf}.png")
    # 아래쪽 대화창 바탕 (스타일마다 한 칸)
    w, h = size_of(UI / "bg.png")
    img, d = new(w, h)
    for name, x, y, fw, fh in frames(UI / "bg.json"):
        t = int(name) if name.isdigit() and int(name) in THEMES else 1
        panel(d, (x, y, x + fw - 1, y + fh - 1), t, c=4)
        d.line([(x + 4, y + 2), (x + 44, y + 2)], fill=rgba(THEMES[t][3], 140))
    save(img, UI / "bg.png")
    w, h = size_of(UI / "namebox.png")
    img, d = new(w, h)
    for name, x, y, fw, fh in frames(UI / "namebox.json"):
        t = int(name) if name.isdigit() and int(name) in THEMES else 1
        panel(d, (x, y, x + fw - 1, y + fh - 1), t, c=2, band=False)
    save(img, UI / "namebox.png")
    w, h = size_of(UI / "overlay_message.png")
    img, d = new(w, h)
    panel(d, (0, 0, w - 1, h - 1), 1, c=6)
    save(img, UI / "overlay_message.png")


# ── 커서 · 선택 ─────────────────────────────────────
def cursors():
    for name, flip in (("cursor", False), ("cursor_reverse", True)):
        w, h = size_of(UI / f"{name}.png")
        img, d = new(w, h)
        mid = h // 2
        for i in range(w - 1):  # 오른쪽을 가리키는 삼각형
            half = max(0, (w - 2 - i))
            half = min(half, mid - 1)
            x = i
            d.line([(x, mid - half), (x, mid + half)], fill=GOLD)
        d.line([(0, mid - (mid - 1)), (0, mid + (mid - 1))], fill=GOLD_D)
        if flip:
            img = img.transpose(Image.FLIP_LEFT_RIGHT)
        save(img, UI / f"{name}.png")
    # 대화 넘기기 ▼ (칸마다 높이가 조금 달라서 통통 튀어요)
    w, h = size_of(UI / "prompt.png")
    img, d = new(w, h)
    for name, x, y, fw, fh in frames(UI / "prompt.json"):
        top = y + fh - 5
        for i, half in enumerate((3, 2, 1, 0)):
            d.line([(x + 3 - half, top + i), (x + 3 + half, top + i)], fill=GOLD)
    save(img, UI / "prompt.png")
    for name in ("bmenu_sel", "mmenu_sel", "boolean_sel", "select_gen_cursor", "select_gen_cursor_highlight"):
        w, h = size_of(UI / f"{name}.png")
        img, d = new(w, h)
        col = TEAL if "highlight" in name else GOLD
        d.polygon(chamfer(0, 0, w - 1, h - 1, 2), fill=rgba(col, 46), outline=col)
        save(img, UI / f"{name}.png")
    for name, col, thick in (("select_cursor", GOLD, 1), ("select_cursor_highlight", TEAL, 1), ("select_cursor_highlight_thick", TEAL, 2), ("select_cursor_pokerus", (198, 160, 255, 255), 1)):
        w, h = size_of(UI / f"{name}.png")
        img, d = new(w, h)
        arm = 5
        for t in range(thick):
            for (cx, cy, sx, sy) in ((t, t, 1, 1), (w - 1 - t, t, -1, 1), (t, h - 1 - t, 1, -1), (w - 1 - t, h - 1 - t, -1, -1)):
                d.line([(cx, cy), (cx + sx * arm, cy)], fill=col)
                d.line([(cx, cy), (cx, cy + sy * arm)], fill=col)
        save(img, UI / f"{name}.png")
    w, h = size_of(UI / "scroll_bar.png")
    img, d = new(w, h)
    d.rectangle([1, 0, w - 2, h - 1], fill=TRACK, outline=rgba(THEMES[1][2]))
    save(img, UI / "scroll_bar.png")
    w, h = size_of(UI / "scroll_bar_handle.png")
    img, d = new(w, h)
    d.rectangle([0, 0, w - 1, h - 1], fill=GOLD)
    save(img, UI / "scroll_bar_handle.png")


# ── 바 (HP · 경험치) ────────────────────────────────
def bar_rows(d, x, y, w, h, cols):
    light, base, dark = cols
    for i in range(h):
        c = light if i == 0 and h > 1 else (dark if i == h - 1 and h > 2 else base)
        d.line([(x, y + i), (x + w - 1, y + i)], fill=rgba(c))


def bars():
    for name in ("overlay_hp", "overlay_hp_boss", "party_slot_hp_overlay"):
        w, h = size_of(UI / f"{name}.png")
        img, d = new(w, h)
        for fname, x, y, fw, fh in frames(UI / f"{name}.json"):
            bar_rows(d, x, y, fw, fh, HP_COLORS.get(fname, HP_COLORS["high"]))
        save(img, UI / f"{name}.png")
    for name in ("overlay_exp", "summary_stats_overlay_exp"):
        w, h = size_of(UI / f"{name}.png")
        img, d = new(w, h)
        bar_rows(d, 0, 0, w, h, EXP_COLORS)
        save(img, UI / f"{name}.png")
    # 파티 칸 HP 바 바탕 (글자 "HP" 는 따로 그림)
    w, h = size_of(UI / "party_slot_hp_bar.png")
    img, d = new(w, h)
    d.polygon(chamfer(0, 0, w - 1, h - 1, 2), fill=TRACK, outline=rgba(THEMES[1][2]))
    save(img, UI / "party_slot_hp_bar.png")
    w, h = size_of(UI / "party_slot_overlay_hp.png")
    img, d = new(w, h)
    save(img, UI / "party_slot_overlay_hp.png")  # 안 쓰는 그림: 비워요
    w, h = size_of(UI / "party_exp_bar.png")
    img, d = new(w, h)
    panel(d, (0, 0, w - 1, h - 1), 1, c=2, band=False, accent=False)
    save(img, UI / "party_exp_bar.png")


# ── 전투 정보 창 ─────────────────────────────────────
def track(d, x, y, w, h):
    d.rectangle([x - 1, y - 1, x + w, y + h], fill=TRACK, outline=rgba(THEMES[1][2]))


def battle_info():
    specs = {
        # 이름: (강조색, HP 바 (x, y, w, h) 이미지 좌표, 경험치 바)
        "pbinfo_player": (TEAL, (69, 20, 48, 2), (32, 39, 85, 2)),
        "pbinfo_player_mini": (TEAL, (69, 20, 48, 2), None),
        "pbinfo_enemy_mini": (RED, (59, 20, 48, 2), None),
        "pbinfo_enemy_boss": (RED, (69, 18, 86, 4), None),
    }
    for name, (acc, hp, exp) in specs.items():
        for suffix in ("", "_stats"):
            p = UI / f"{name}{suffix}.png"
            if not p.exists():
                continue
            w, h = size_of(p)
            img, d = new(w, h)
            enemy = "enemy" in name
            panel(d, (0, 0, w - 1, h - 1), 1, c=6, corners="tr,bl" if enemy else "tl,br", accent=False)
            # 강조 줄: 플레이어는 왼쪽 위, 상대는 오른쪽 위
            if enemy:
                d.line([(w - 7, 0), (w - 1, 6)], fill=acc)
                d.line([(w - 20, 0), (w - 7, 0)], fill=acc)
            else:
                d.line([(0, 6), (6, 0)], fill=acc)
                d.line([(6, 0), (19, 0)], fill=acc)
            if suffix == "":
                track(d, *hp)
                if exp:
                    track(d, *exp)
            save(img, p)
    w, h = size_of(UI / "pb_tray_ball.png")
    img, d = new(w, h)
    for fname, x, y, fw, fh in frames(UI / "pb_tray_ball.json"):
        cx, cy = x + fw // 2, y + fh // 2
        dia = [(cx, cy - 3), (cx + 3, cy), (cx, cy + 3), (cx - 3, cy)]
        if fname == "ball":
            d.polygon(dia, fill=TEAL, outline=INK)
        elif fname == "empty":
            d.polygon(dia, outline=DIM)
        elif fname == "faint":
            d.polygon(dia, fill=(90, 40, 46, 255), outline=INK)
        else:
            d.polygon(dia, fill=GOLD, outline=INK)
    save(img, UI / "pb_tray_ball.png")
    for name, col in (("pb_tray_overlay_player", TEAL), ("pb_tray_overlay_enemy", RED)):
        w, h = size_of(UI / f"{name}.png")
        img, d = new(w, h)
        d.line([(0, h - 1), (w - 1, h - 1)], fill=rgba(THEMES[1][2]))
        d.line([(0, h - 2), (w // 3, h - 2)], fill=col)
        save(img, UI / f"{name}.png")


# ── 파티 화면 ─────────────────────────────────────
SLOT_STATE = {
    "": ((24, 30, 44), (74, 88, 118), False),
    "_sel": ((36, 44, 66), GOLD, True),
    "_fnt": ((40, 24, 28), (110, 60, 66), False),
    "_fnt_sel": ((56, 30, 36), GOLD, True),
    "_swap": ((18, 40, 46), TEAL, False),
    "_swap_sel": ((24, 54, 60), GOLD, True),
}


def slot_state(fname, base):
    rest = fname[len(base):]
    return SLOT_STATE.get(rest, SLOT_STATE[""])


def party():
    for base in ("party_slot", "party_slot_main"):
        w, h = size_of(UI / f"{base}.png")
        img, d = new(w, h)
        for fname, x, y, fw, fh in frames(UI / f"{base}.json"):
            fill, line, sel = slot_state(fname, base)
            panel(d, (x, y, x + fw - 1, y + fh - 1), 1, c=4, fill=fill, border=line, accent=sel)
        save(img, UI / f"{base}.png")
    p = UI / "party_slot_main_short.png"
    if p.exists() and (UI / "party_slot_main_short.json").exists():
        w, h = size_of(p)
        img, d = new(w, h)
        for fname, x, y, fw, fh in frames(UI / "party_slot_main_short.json"):
            fill, line, sel = slot_state(fname, "party_slot_main_short")
            panel(d, (x, y, x + fw - 1, y + fh - 1), 1, c=4, fill=fill, border=line, accent=sel)
        save(img, p)
    for base in ("party_cancel", "party_discard", "party_transfer"):
        w, h = size_of(UI / f"{base}.png")
        img, d = new(w, h)
        for fname, x, y, fw, fh in frames(UI / f"{base}.json"):
            sel = fname.endswith("_sel") or fname == "selected"
            panel(d, (x, y, x + fw - 1, y + fh - 1), 1, c=3, fill=(36, 44, 66) if sel else None, border=GOLD if sel else None, accent=sel, band=False)
        save(img, UI / f"{base}.png")
    w, h = size_of(UI / "party_pb.png")
    img, d = new(w, h)
    for fname, x, y, fw, fh in frames(UI / "party_pb.json"):
        sel = fname.endswith("_sel")
        cx, cy, r = x + fw // 2, y + fh // 2, min(fw, fh) // 2 - 2
        dia = [(cx, cy - r), (cx + r, cy), (cx, cy + r), (cx - r, cy)]
        d.polygon(dia, fill=GOLD if sel else (36, 44, 66, 255), outline=INK)
        d.polygon([(cx, cy - r + 3), (cx + r - 3, cy), (cx, cy + r - 3), (cx - r + 3, cy)], outline=WHITE if sel else TEAL)
    save(img, UI / "party_pb.png")


# ── 정보(요약) 화면 · 시작 고르기 ───────────────────
def screens():
    for name in ("summary_profile", "summary_stats", "summary_moves", "starter_container_bg", "summary_moves_effect", "summary_status",
                 "ability_bar_left", "ability_bar_right", "bgm_bar", "achv_bar", "achv_bar_2", "achv_bar_3", "achv_bar_4", "achv_bar_5"):
        p = UI / f"{name}.png"
        if not p.exists():
            continue
        w, h = size_of(p)
        img, d = new(w, h)
        panel(d, (0, 0, w - 1, h - 1), 1, c=5 if min(w, h) > 40 else 3, alpha=255)
        if name.startswith("summary_") and h > 100:  # 제목 띠
            d.rectangle([6, 2, w - 2, 13], fill=rgba(THEMES[1][1]))
            d.line([(6, 14), (w - 2, 14)], fill=rgba(THEMES[1][2]))
        save(img, p)
    w, h = size_of(UI / "summary_moves_cursor.png")
    img, d = new(w, h)
    for fname, x, y, fw, fh in frames(UI / "summary_moves_cursor.json"):
        col = GOLD if fname == "highlight" else TEAL
        d.polygon(chamfer(x, y, x + fw - 1, y + fh - 1, 2), fill=rgba(col, 50), outline=col)
    save(img, UI / "summary_moves_cursor.png")
    w, h = size_of(UI / "summary_moves_overlay_row.png")
    img, d = new(w, h)
    d.rectangle([0, 0, w - 1, h - 1], fill=rgba(THEMES[1][1], 120))
    d.line([(0, h - 1), (w - 1, h - 1)], fill=rgba(THEMES[1][2]))
    save(img, UI / "summary_moves_overlay_row.png")


def backgrounds():
    """화면 전체 배경 (불투명) — 어두운 바탕 + 아주 옅은 사선 무늬"""
    for p in sorted(UI.glob("*.png")):
        if size_of(p) != (320, 180):
            continue
        img, d = new(320, 180)
        d.rectangle([0, 0, 319, 179], fill=(13, 16, 24, 255))
        for k in range(-180, 320, 10):
            d.line([(k, 179), (k + 179, 0)], fill=(17, 21, 31, 255))
        d.line([(0, 0), (319, 0)], fill=rgba(THEMES[1][2]))
        d.line([(0, 0), (40, 0)], fill=GOLD)
        save(img, p)


# ── 글자 그림 · 아이콘 ──────────────────────────────
def badge(d, box, color, label, f=None, outline=True):
    x0, y0, x1, y1 = box
    d.polygon(chamfer(x0, y0, x1, y1, 2), fill=rgba(color), outline=INK if outline else None)
    d.line([(x0 + 2, y0 + 1), (x1 - 1, y0 + 1)], fill=rgba(tuple(min(255, v + 40) for v in color)))
    if label:
        text_center(d, (x0, y0, x1 + 1, y1 + 1), label, WHITE, f or F7, shadow=True)


def fit_label(d, label, width, f):
    """글자가 칸보다 넓으면 줄인 이름"""
    l, _, r, _ = d.textbbox((0, 0), label, font=f)
    return label if r - l <= width else None


def icons():
    # 역할군 배지 (types_ko · types)
    for atlas in ("types_ko", "types"):
        p = IMG / f"{atlas}.png"
        if not p.exists():
            continue
        w, h = size_of(p)
        img, d = new(w, h)
        for fname, x, y, fw, fh in frames(IMG / f"{atlas}.json"):
            color, label = TYPE_STYLE.get(fname, TYPE_STYLE["unknown"])
            label = fit_label(d, label, fw - 3, F7) or SHORT.get(fname) or label[:2]
            badge(d, (x, y, x + fw - 1, y + fh - 1), color, label)
        save(img, p)
    # 전투 정보 창 옆 역할군 아이콘 (세로 줄 아틀라스) · 시작 고르기 배경 칸
    for atlas in ("pbinfo_player_type", "pbinfo_player_type1", "pbinfo_player_type2", "pbinfo_enemy_type", "pbinfo_enemy_type1", "pbinfo_enemy_type2", "type_bgs"):
        p = UI / f"{atlas}.png"
        if not p.exists():
            continue
        w, h = size_of(p)
        img, d = new(w, h)
        for fname, x, y, fw, fh in frames(UI / f"{atlas}.json"):
            color, label = TYPE_STYLE.get(fname, TYPE_STYLE["unknown"])
            short = (SHORT.get(fname) or label)[:1]
            badge(d, (x + 1, y + 1, x + fw - 2, y + fh - 2), color, short if fh >= 10 else None)
        save(img, p)
    # 상태이상
    for atlas in ("statuses_ko", "statuses"):
        p = IMG / f"{atlas}.png"
        if not p.exists():
            continue
        w, h = size_of(p)
        img, d = new(w, h)
        for fname, x, y, fw, fh in frames(IMG / f"{atlas}.json"):
            color, label = STATUS_STYLE.get(fname, ((96, 100, 112), "?"))
            d.rectangle([x, y, x + fw - 1, y + fh - 1], fill=rgba(color))
            text_center(d, (x, y, x + fw, y + fh), label, WHITE, F7, shadow=False, dy=0)
        save(img, p)
    # 기술 분류 (물리 · 스증 · 변화)
    for atlas in ("categories",):
        p = IMG / f"{atlas}.png"
        w, h = size_of(p)
        img, d = new(w, h)
        for fname, x, y, fw, fh in frames(IMG / f"{atlas}.json"):
            color, label = CATEGORY_STYLE.get(fname, ((96, 100, 112), "?"))
            badge(d, (x, y, x + fw - 1, y + fh - 1), color, label)
        save(img, p)


def numbers():
    for name, col in (("numbers", WHITE), ("numbers_red", (246, 118, 106, 255))):
        w, h = size_of(UI / f"{name}.png")
        img, d = new(w, h)
        for fname, x, y, fw, fh in frames(UI / f"{name}.json"):
            digit57(d, x + 1, y, fname, col)
        save(img, UI / f"{name}.png")
    w, h = size_of(UI / "pbinfo_stat_numbers.png")
    img, d = new(w, h)
    for fname, x, y, fw, fh in frames(UI / "pbinfo_stat_numbers.json"):
        if fname == "empty":
            continue
        s = fname if fname.startswith("-") or fname == "0" else "+" + fname
        col = (120, 224, 128, 255) if not s.startswith("-") and s != "0" else ((246, 118, 106, 255) if s.startswith("-") else DIM)
        mini_text(d, x + (fw - mini_width(s)) // 2, y + 1, s, col, INK)
    save(img, UI / "pbinfo_stat_numbers.png")


def text_images():
    def label(rel, s, mini=False, col=WHITE):
        p = KO / rel
        w, h = size_of(p)
        img, d = new(w, h)
        if mini:
            mini_text(d, (w - mini_width(s)) // 2, (h - 5) // 2, s, col, INK)
        else:
            text_center(d, (0, 0, w, h), s, col, F7)
        save(img, p)

    label("battle_ui/overlay_hp_label_ko.png", "HP", mini=True, col=GOLD)
    label("battle_ui/overlay_hp_label_boss_ko.png", "HP", mini=True, col=GOLD)
    label("battle_ui/overlay_lv_ko.png", "Lv", mini=True, col=GOLD)
    label("battle_ui/overlay_exp_label_ko.png", "EXP", mini=True, col=(130, 196, 255, 255))
    label("party_ui/party_slot_overlay_hp_ko.png", "HP", mini=True, col=GOLD)
    label("party_ui/party_slot_overlay_lv_ko.png", "Lv", mini=True, col=GOLD)
    label("summary/summary_dexnb_label_ko.png", "No", mini=True, col=GOLD)
    label("summary/summary_moves_overlay_pp_ko.png", "PP", mini=True, col=GOLD)
    label("summary/summary_stats_expbar_title_ko.png", "EXP", mini=True, col=(130, 196, 255, 255))
    for rel, s in (("summary/summary_moves_descriptions_title_ko.png", "설명"), ("summary/summary_moves_effect_title_ko.png", "효과"),
                   ("summary/summary_moves_moves_title_ko.png", "스킬"), ("summary/summary_profile_ability_ko.png", "특성"),
                   ("summary/summary_profile_passive_ko.png", "패시브"), ("summary/summary_profile_memo_title_ko.png", "메모"),
                   ("summary/summary_profile_profile_title_ko.png", "프로필"), ("summary/summary_stats_exp_title_ko.png", "경험치"),
                   ("summary/summary_stats_item_title_ko.png", "아이템"), ("summary/summary_stats_stats_title_ko.png", "스탯")):
        label(rel, s, col=GOLD)
    # 정보 화면 쪽 탭: 지금 쪽만 금색
    for i, rel in enumerate(("summary/summary_tabs_1_ko.png", "summary/summary_tabs_2_ko.png", "summary/summary_tabs_3_ko.png")):
        p = KO / rel
        w, h = size_of(p)
        img, d = new(w, h)
        panel(d, (0, 0, w - 1, h - 1), 1, c=3, band=False, accent=False, border=GOLD)
        text_center(d, (0, 0, w, h), ("프로필", "스탯", "스킬")[i], GOLD, F7)
        save(img, p)
    # 전투 능력치 이름 (한 글자, 칸 크기는 그대로)
    p = KO / "battle_ui/pbinfo_stat_ko.png"
    w, h = size_of(p)
    img, d = new(w, h)
    one = {"SPATK": "증", "SPDEF": "저", "CRIT": "치", "ACC": "명", "ATK": "공", "DEF": "방", "EVA": "회", "SPD": "속", "HP": "체"}
    for fname, x, y, fw, fh in frames(KO / "battle_ui/pbinfo_stat_ko.json"):
        text_center(d, (x, y, x + fw, y + fh), one.get(fname, "?"), DIM, F7, shadow=False)
    save(img, p)
    p = KO / "summary/summary_dexnb_label_overlay_shiny_ko.png"
    w, h = size_of(p)
    img, d = new(w, h)
    save(img, p)


def small_icons():
    """작은 UI 아이콘 (별 · 자물쇠 · 결정 · 하트 · 캡슐 …). 색이 덧입혀지는 것(candy, friendship)은 흰색 바탕"""
    def icon(name, draw):
        p = UI / f"{name}.png"
        if not p.exists():
            return
        w, h = size_of(p)
        img, d = new(w, h)
        draw(d, w, h)
        save(img, p)

    def diamond(d, cx, cy, r, fill, outline=INK):
        d.polygon([(cx, cy - r), (cx + r, cy), (cx, cy + r), (cx - r, cy)], fill=fill, outline=outline)

    def star(d, w, h, col):
        cx, cy = w // 2, h // 2
        r = min(w, h) // 2 - 1
        d.line([(cx, cy - r), (cx, cy + r)], fill=col)
        d.line([(cx - r, cy), (cx + r, cy)], fill=col)
        k = max(1, r // 2)
        d.line([(cx - k, cy - k), (cx + k, cy + k)], fill=col)
        d.line([(cx - k, cy + k), (cx + k, cy - k)], fill=col)
        d.point((cx, cy), fill=WHITE)

    icon("icon_owned", lambda d, w, h: diamond(d, w // 2, h // 2, 3, GOLD))
    icon("favorite", lambda d, w, h: star(d, w, h, GOLD))
    for n in ("shiny", "shiny_small"):
        icon(n, lambda d, w, h: star(d, w, h, GOLD))
    for n, col in (("shiny_1", TEAL), ("shiny_small_1", TEAL), ("shiny_2", (226, 76, 120, 255)), ("shiny_small_2", (226, 76, 120, 255))):
        icon(n, lambda d, w, h, col=col: star(d, w, h, col))

    def lock(d, w, h):
        d.rectangle([2, h // 2 - 1, w - 3, h - 2], fill=GOLD, outline=INK)
        d.arc([3, 1, w - 4, h // 2 + 3], 180, 360, fill=GOLD, width=2)
        d.point((w // 2, h // 2 + 2), fill=INK)

    icon("icon_lock", lock)

    def crystal(d, w, h, inner=False):
        cx, cy = w // 2, h // 2
        if inner:
            diamond(d, cx, cy, 3, (255, 255, 255, 255), None)
        else:
            d.polygon([(cx, 1), (w - 3, cy - 2), (w - 3, cy + 2), (cx, h - 2), (2, cy + 2), (2, cy - 2)], fill=(232, 236, 244, 255), outline=INK)

    icon("candy", lambda d, w, h: crystal(d, w, h))
    icon("candy_overlay", lambda d, w, h: crystal(d, w, h, inner=True))

    def heart(d, w, h, inner=False):
        pts = [(w // 2, h - 2), (1, h // 2 - 1), (1, 3), (3, 1), (w // 2 - 1, 1), (w // 2, 3), (w // 2 + 1, 1), (w - 4, 1), (w - 2, 3), (w - 2, h // 2 - 1)]
        if inner:
            d.polygon([(w // 2, h - 4), (4, h // 2 - 1), (4, 4), (w - 5, 4), (w - 5, h // 2 - 1)], fill=(255, 255, 255, 255))
        else:
            d.polygon(pts, fill=(232, 236, 244, 255), outline=INK)

    icon("friendship", lambda d, w, h: heart(d, w, h))
    icon("friendship_overlay", lambda d, w, h: heart(d, w, h, inner=True))

    def capsule(d, w, h, col):
        d.rounded_rectangle([1, 0, w - 2, h - 1], radius=2, fill=col, outline=INK)
        d.line([(1, h // 2), (w - 2, h // 2)], fill=INK)

    icon("ha_capsule", lambda d, w, h: capsule(d, w, h, GOLD))
    for n, col in (("champion_ribbon", GOLD), ("champion_ribbon_bronze", (196, 120, 70, 255)), ("champion_ribbon_silver", (200, 206, 218, 255)),
                   ("champion_ribbon_emerald", (70, 200, 120, 255)), ("champion_ribbon_diamond", (140, 210, 255, 255))):
        icon(n, lambda d, w, h, col=col: (d.polygon([(1, 0), (w - 2, 0), (w - 2, h - 1), (w // 2, h - 3), (1, h - 1)], fill=col, outline=INK)))
    icon("passive_bg", lambda d, w, h: panel(d, (0, 0, w - 1, h - 1), 1, c=2, band=False, accent=False, border=GOLD))
    icon("icon_egg_move", lambda d, w, h: diamond(d, w // 2, h // 2, 3, TEAL))
    icon("icon_stop", lambda d, w, h: (d.rectangle([2, 2, w - 3, h - 3], fill=RED, outline=INK)))

    def saving(d, w, h):
        d.rectangle([2, 2, w - 3, h - 3], fill=(36, 44, 66, 255), outline=GOLD)
        d.rectangle([5, 2, w - 6, 6], fill=GOLD)
        d.rectangle([4, h - 7, w - 5, h - 3], fill=WHITE)

    icon("saving_icon", saving)
    for n in ("icon_spliced", "icon_tera", "cursor_tera", "type_tera"):  # 블서로그에서 안 쓰는 그림: 비워요
        icon(n, lambda d, w, h: None)


def unmark():
    if not MARK.exists():
        return
    marks = set(json.load(open(MARK, encoding="utf-8")))
    before = len(marks)
    marks -= set(done)
    json.dump(sorted(marks), open(MARK, "w", encoding="utf-8"), ensure_ascii=False, indent=0)
    print(f"임시 그림 목록에서 뺀 것: {before - len(marks)}개")


def main():
    global F7, F9
    F7 = font(8)
    F9 = font(10, big=True)
    windows()
    cursors()
    bars()
    battle_info()
    party()
    screens()
    backgrounds()
    icons()
    numbers()
    text_images()
    small_icons()
    unmark()
    print(f"그린 그림 {len(done)}개")


if __name__ == "__main__":
    main()
