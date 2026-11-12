# SPDX-FileCopyrightText: 2026 SG
# SPDX-License-Identifier: AGPL-3.0-only
"""
블서로그 기술 연출 7종 (공용) — 그림 + 연출 순서(JSON)를 코드로 만들어요

포켓몬 기술 연출 그림은 저작권 때문에 저장소에 없어서, 모든 스킬이 반투명 네모 임시 연출이었어요.
실험체 스킬은 이 7개 중 하나를 써요 (어느 것을 쓸지는 src/data/bseorogue/skill-anim.ts):

  이름    연출 파일 (battle-anims/)   그림 (images/battle_anims/)   언제
  베기    slash.json                  bseo-slash.png                칼 · 도끼 · 창 같은 무기
  타격    tackle.json                 bseo-strike.png               망치 · 글러브 · 방망이 같은 무기
  투사체  shadow-ball.json            bseo-shot.png                 총 · 활 · 던지기 · 아르카나 · 기타 · 카메라
  폭발    explosion.json              bseo-blast.png                궁극기(R) 중 위력 100 이상
  회복    recover.json                bseo-heal.png                 체력 회복 변화 스킬
  강화    focus-energy.json           bseo-buff.png                 자기 강화 변화 스킬
  약화    tail-whip.json              bseo-debuff.png               상대에게 거는 변화 스킬

그림 칸은 96×96 (한 줄 5칸, 포켓로그 연출 그림 규격). 연출은 한 칸이 3프레임(50ms).
쓰는 법 (저장소 맨 위에서): python3 -B scripts/er-fx/make_fx.py
그린 파일은 assets/.placeholders.json 에서 빠져요 (임시 그림 만들기가 덮어쓰지 않게).
"""
import json
import math
from pathlib import Path

from PIL import Image, ImageDraw, ImageFilter

ROOT = Path(__file__).resolve().parents[2]
ANIM_DIR = ROOT / "assets" / "battle-anims"
IMG_DIR = ROOT / "assets" / "images" / "battle_anims"
MARK = ROOT / "assets" / ".placeholders.json"

CELL = 96
SS = 4  # 4배로 그리고 줄여서 가장자리를 부드럽게
COLS = 5

WHITE = (250, 252, 255)
CYAN = (99, 214, 255)
GOLD = (242, 192, 76)
ORANGE = (255, 128, 48)
RED = (214, 60, 40)
GREEN = (110, 226, 130)
PURPLE = (170, 110, 255)
SMOKE = (120, 120, 132)

# 연출 속 자리: 내 실험체 가운데 (0, 0), 상대 가운데 (128, -64)
U = (0, 0)
T = (128, -64)

done: list[str] = []


def canvas():
    img = Image.new("RGBA", (CELL * SS, CELL * SS), (0, 0, 0, 0))
    return img, ImageDraw.Draw(img)


def shrink(img, glow=0):
    if glow:
        blur = img.filter(ImageFilter.GaussianBlur(glow * SS))
        img = Image.alpha_composite(blur, img)
    return img.resize((CELL, CELL), Image.LANCZOS)


def rgba(c, a):
    return (c[0], c[1], c[2], max(0, min(255, int(a))))


def P(x, y):
    """96칸 좌표 → 그리는 좌표"""
    return (x * SS, y * SS)


def crescent(d, cx, cy, r, a0, a1, width, color, alpha):
    """끝이 가는 초승달 (a0 → a1 도, 가운데가 제일 두꺼움)"""
    n = 40
    outer, inner = [], []
    for i in range(n + 1):
        s = i / n
        a = math.radians(a0 + (a1 - a0) * s)
        w = width * math.sin(math.pi * s)
        outer.append(P(cx + r * math.cos(a), cy + r * math.sin(a)))
        inner.append(P(cx + (r - w) * math.cos(a), cy + (r - w) * math.sin(a)))
    d.polygon(outer + inner[::-1], fill=rgba(color, alpha))


def star(d, cx, cy, r_out, r_in, n, rot, color, alpha):
    pts = []
    for i in range(n * 2):
        r = r_out if i % 2 == 0 else r_in
        a = math.radians(rot + i * 180 / n)
        pts.append(P(cx + r * math.cos(a), cy + r * math.sin(a)))
    d.polygon(pts, fill=rgba(color, alpha))


def circle(d, cx, cy, r, color, alpha, width=0):
    box = [P(cx - r, cy - r), P(cx + r, cy + r)]
    if width:
        d.ellipse(box, outline=rgba(color, alpha), width=max(1, int(width * SS)))
    else:
        d.ellipse(box, fill=rgba(color, alpha))


def chevron(d, cx, cy, size, up, color, alpha, thick=3.0):
    s = size
    if up:
        pts = [(cx - s, cy + s * 0.5), (cx, cy - s * 0.5), (cx + s, cy + s * 0.5)]
    else:
        pts = [(cx - s, cy - s * 0.5), (cx, cy + s * 0.5), (cx + s, cy - s * 0.5)]
    d.line([P(*p) for p in pts], fill=rgba(color, alpha), width=int(thick * SS), joint="curve")


def plus(d, cx, cy, s, color, alpha):
    w = s * 0.36
    d.rectangle([P(cx - w, cy - s), P(cx + w, cy + s)], fill=rgba(color, alpha))
    d.rectangle([P(cx - s, cy - w), P(cx + s, cy + w)], fill=rgba(color, alpha))


# ── 그림 ─────────────────────────────────────────
def draw_slash():
    frames = []
    for t, fade in ((0.3, 1), (0.6, 1), (0.9, 1), (1.0, 1), (1.0, 0.65), (1.0, 0.3)):
        img, d = canvas()
        a0, a1 = 200, 200 + 150 * t
        crescent(d, 52, 56, 38, a0, a1, 11, CYAN, 150 * fade)
        crescent(d, 52, 56, 36, a0, a1, 6, WHITE, 255 * fade)
        if t >= 0.9:  # 두 번째 얇은 줄
            crescent(d, 46, 50, 30, a0 + 10, a1 - 10, 3, WHITE, 200 * fade)
        frames.append(shrink(img, glow=1.5))
    return frames


def draw_strike():
    frames = []
    for i, (r, fade) in enumerate(((14, 1), (26, 1), (34, 0.9), (38, 0.6), (40, 0.3))):
        img, d = canvas()
        star(d, 48, 48, r, r * 0.42, 8, i * 8, GOLD, 220 * fade)
        star(d, 48, 48, r * 0.7, r * 0.3, 8, i * 8 + 22, WHITE, 255 * fade)
        circle(d, 48, 48, r * 0.25, WHITE, 255 * fade)
        for k in range(6):  # 튀는 조각
            a = math.radians(k * 60 + 15 + i * 6)
            rr = r * 1.15
            circle(d, 48 + rr * math.cos(a), 48 + rr * math.sin(a), 2.2, WHITE, 230 * fade)
        frames.append(shrink(img, glow=1.2))
    return frames


def draw_shot():
    frames = []
    # 0: 날아가는 구슬 (오른쪽이 앞)
    img, d = canvas()
    for k in range(6):
        circle(d, 48 - 6 - k * 5, 48, 7 - k, CYAN, 140 - k * 20)
    circle(d, 48, 48, 11, CYAN, 210)
    circle(d, 48, 48, 6, WHITE, 255)
    frames.append(shrink(img, glow=2))
    # 1~5: 맞은 자리
    for r, fade in ((10, 1), (18, 1), (26, 0.8), (32, 0.5), (36, 0.25)):
        img, d = canvas()
        circle(d, 48, 48, r, CYAN, 230 * fade, width=4)
        circle(d, 48, 48, r * 0.45, WHITE, 255 * fade)
        for k in range(8):
            a = math.radians(k * 45)
            p0 = (48 + r * 0.7 * math.cos(a), 48 + r * 0.7 * math.sin(a))
            p1 = (48 + r * 1.2 * math.cos(a), 48 + r * 1.2 * math.sin(a))
            d.line([P(*p0), P(*p1)], fill=rgba(WHITE, 230 * fade), width=2 * SS)
        frames.append(shrink(img, glow=1.5))
    return frames


def draw_blast():
    frames = []
    seq = [(8, 0, 1), (16, 0, 1), (26, 0, 1), (34, 6, 1), (40, 14, 0.95), (44, 22, 0.85), (46, 30, 0.65), (47, 36, 0.45), (47, 40, 0.28), (47, 43, 0.12)]
    for r, hole, fade in seq:
        img, d = canvas()
        circle(d, 48, 48, r, RED, 200 * fade)
        circle(d, 48, 48, r * 0.8, ORANGE, 230 * fade)
        circle(d, 48, 48, r * 0.55, GOLD, 245 * fade)
        circle(d, 48, 48, r * 0.3, WHITE, 255 * fade)
        if hole:  # 가운데부터 사라지며 연기
            mask = Image.new("L", img.size, 255)
            ImageDraw.Draw(mask).ellipse([P(48 - hole, 48 - hole), P(48 + hole, 48 + hole)], fill=0)
            img.putalpha(Image.composite(img.getchannel("A"), Image.new("L", img.size, 0), mask))
            d = ImageDraw.Draw(img)
            for k in range(7):
                a = math.radians(k * 51 + hole * 3)
                circle(d, 48 + (hole + 4) * math.cos(a), 48 + (hole + 4) * math.sin(a), 6, SMOKE, 150 * fade)
        frames.append(shrink(img, glow=2))
    return frames


def draw_heal():
    frames = []
    spots = [(30, 70, 0), (60, 76, 2), (44, 60, 1), (70, 58, 3), (24, 50, 2), (54, 46, 0)]
    for i in range(8):
        img, d = canvas()
        fade = 1 if i < 5 else (8 - i) / 3.5
        circle(d, 48, 56, 30 + i, GREEN, 32 * fade)
        for x, y, delay in spots:
            k = i - delay
            if k < 0:
                continue
            plus(d, x, y - k * 5, 4.5, GREEN, 240 * fade)
            plus(d, x, y - k * 5, 2.2, WHITE, 255 * fade)
        frames.append(shrink(img, glow=1.5))
    return frames


def draw_buff():
    frames = []
    for i in range(8):
        img, d = canvas()
        fade = 1 if i < 5 else (8 - i) / 3.5
        ry = 8 + i * 1.5
        d.ellipse([P(48 - 30, 84 - ry), P(48 + 30, 84 + ry * 0.4)], outline=rgba(GOLD, 200 * fade), width=3 * SS)
        for k, x in enumerate((30, 48, 66)):
            y = 72 - ((i * 7 + k * 9) % 40)
            chevron(d, x, y, 7, True, GOLD, 240 * fade, 3.4)
            chevron(d, x, y, 7, True, WHITE, 200 * fade, 1.4)
        frames.append(shrink(img, glow=1.5))
    return frames


def draw_debuff():
    frames = []
    for i in range(8):
        img, d = canvas()
        fade = 1 if i < 5 else (8 - i) / 3.5
        circle(d, 48, 50, 34 - i, PURPLE, 70 * fade, width=3)
        for k, x in enumerate((30, 48, 66)):
            y = 26 + ((i * 7 + k * 9) % 40)
            chevron(d, x, y, 7, False, PURPLE, 240 * fade, 3.4)
            chevron(d, x, y, 7, False, WHITE, 170 * fade, 1.2)
        frames.append(shrink(img, glow=1.5))
    return frames


def sheet(name, frames):
    rows = math.ceil(len(frames) / COLS)
    out = Image.new("RGBA", (CELL * COLS, CELL * rows), (0, 0, 0, 0))
    for i, f in enumerate(frames):
        out.paste(f, ((i % COLS) * CELL, (i // COLS) * CELL))
    path = IMG_DIR / f"{name}.png"
    out.save(path, optimize=True)
    done.append(str(path.relative_to(ROOT / "assets")).replace("\\", "/"))
    return len(frames)


# ── 연출 순서 ─────────────────────────────────────
def who(target, x, y, opacity=255):
    """내 실험체(0) · 상대(1) 그림 칸. 매 프레임 넣어야 안 사라져요"""
    return {"x": x, "y": y, "zoomX": 100, "zoomY": 100, "visible": True, "target": target, "graphicFrame": 0,
            "opacity": opacity, "locked": True, "priority": 1, "focus": 3}


def fx(x, y, frame, zoom=100, opacity=255, focus=1, angle=0, mirror=False, blend=0):
    return {"x": x, "y": y, "zoomX": zoom, "zoomY": zoom, "angle": angle, "mirror": mirror, "visible": True,
            "target": 2, "graphicFrame": frame, "opacity": opacity, "blendType": blend, "priority": 1, "focus": focus}


def frame(user=(0, 0), target=(128, -64), *gfx):
    return [who(0, *user), who(1, *target), *gfx]


def anim(file, graphic, frames, position):
    data = {"id": -1, "graphic": graphic, "frames": frames, "frameTimedEvents": {}, "position": position, "hue": 0}
    path = ANIM_DIR / file
    path.write_text(json.dumps(data, ensure_ascii=False, separators=(",", ":")), encoding="utf-8")
    done.append(str(path.relative_to(ROOT / "assets")).replace("\\", "/"))


def shake(i, amp=4):
    return (T[0] + (amp if i % 2 == 0 else -amp), T[1])


def main():
    IMG_DIR.mkdir(parents=True, exist_ok=True)
    n_slash = sheet("bseo-slash", draw_slash())
    n_strike = sheet("bseo-strike", draw_strike())
    sheet("bseo-shot", draw_shot())
    n_blast = sheet("bseo-blast", draw_blast())
    n_heal = sheet("bseo-heal", draw_heal())
    n_buff = sheet("bseo-buff", draw_buff())
    n_debuff = sheet("bseo-debuff", draw_debuff())

    # 타격: 앞으로 달려들어 쾅
    fr = [frame(), frame((10, -5)), frame((22, -11))]
    for i in range(n_strike):
        fr.append(frame((22 - i * 5, -11 + i * 2.5), shake(i, 5 - i), fx(*T, i, zoom=80)))
    fr.append(frame())
    anim("tackle.json", "bseo-strike", fr, 3)

    # 베기: 살짝 다가가서 사선으로 벰
    fr = [frame(), frame((8, -4))]
    for i in range(n_slash):
        fr.append(frame((14 if i < 3 else 8, -7 if i < 3 else -4), shake(i, 3) if 1 <= i <= 4 else T, fx(T[0] - 4, T[1] + 14, i, zoom=90)))
    fr.append(frame())
    anim("slash.json", "bseo-slash", fr, 1)

    # 투사체: 내 쪽에서 상대 쪽으로 날아가서 터짐
    fr = [frame()]
    steps = 6
    for k in range(1, steps + 1):
        s = k / steps
        fr.append(frame(U, T, fx(U[0] + (T[0] - U[0]) * s, U[1] + (T[1] - U[1]) * s, 0, zoom=70, focus=3)))
    for i in range(1, 6):
        fr.append(frame(U, shake(i, 3) if i < 4 else T, fx(*T, i, zoom=85)))
    fr.append(frame())
    anim("shadow-ball.json", "bseo-shot", fr, 3)

    # 폭발: 기를 모았다가 상대 자리에서 크게 터짐
    fr = [frame(), frame((0, 0)), frame((-3, 0)), frame((3, 0)), frame((0, 0))]
    for i in range(n_blast):
        fr.append(frame(U, shake(i, 6 - i // 2) if i < 8 else T, fx(*T, i, zoom=120)))
    fr.append(frame())
    anim("explosion.json", "bseo-blast", fr, 2)

    # 회복 · 강화: 내 실험체 자리
    for file, graphic, n in (("recover.json", "bseo-heal", n_heal), ("focus-energy.json", "bseo-buff", n_buff)):
        fr = [frame()] + [frame(U, T, fx(*U, i, zoom=90, focus=2)) for i in range(n)] + [frame()]
        anim(file, graphic, fr, 2)

    # 약화: 상대 자리
    fr = [frame()] + [frame(U, T, fx(*T, i, zoom=90)) for i in range(n_debuff)] + [frame()]
    anim("tail-whip.json", "bseo-debuff", fr, 1)

    if MARK.exists():
        marks = set(json.load(open(MARK, encoding="utf-8")))
        before = len(marks)
        marks -= set(done)
        json.dump(sorted(marks), open(MARK, "w", encoding="utf-8"), ensure_ascii=False, indent=0)
        print(f"임시 그림 목록에서 뺀 것: {before - len(marks)}개")
    print(f"그림 · 연출 {len(done)}개: " + " ".join(Path(p).name for p in done))


if __name__ == "__main__":
    main()
