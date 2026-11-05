# SPDX-FileCopyrightText: 2026 SG
# SPDX-License-Identifier: AGPL-3.0-only
"""
이터널 리턴 팬키트 그림 → 블서로그 전투 그림 · 아이콘

팬키트 폴더(실험체마다 "번호. 영어이름" 폴더)를 읽어서
  - 전투 그림:  assets/er/char/<ER번호>_<스킨번호>.png  (전신, 없으면 반신. 높이 96 안쪽)
  - 아이콘:     assets/er/char-icons.png  (40×30 칸 한 장에 모아서. 얼굴 Mini, 없으면 반신에서 얼굴 쪽)
  - 목록:       src/data/bseorogue/art-manifest.ts
를 만들어요. 팬키트 번호는 ER 번호와 다를 때가 있어서(예: 팬키트 017 = 쇼이치 = ER 18) 영어 이름으로 맞춰요.
파일 이름 끝 숫자(_00, _02 …)가 ER 스킨 번호예요 (0 = 기본 모습).

쓰는 법:  python3 scripts/fankit/build_art.py <팬키트 폴더> [<팬키트 폴더> ...]
"""
import json
import re
import sys
import unicodedata
from pathlib import Path

from PIL import Image, ImageDraw, ImageFilter

ROOT = Path(__file__).resolve().parents[2]
ER_DATA = ROOT / "src/data/bseorogue/er-data.ts"
OUT_DIR = ROOT / "assets/er/char"
ICONS = ROOT / "assets/er/char-icons.png"
MANIFEST = ROOT / "src/data/bseorogue/art-manifest.ts"

# 전투 그림 크기 (게임 화면 단위. 포켓로그 큰 포켓몬 정도)
BATTLE_W, BATTLE_H = 92, 96
ICON_W, ICON_H = 40, 30
ICON_COLS = 32

# 야생동물 (팬키트 Wild Animal 폴더 파일 이름 → 블서로그 종 이름)
WILD = {"bat": "BAT", "hound": "WILD_DOG", "wilddog": "WILD_DOG", "boar": "BOAR", "wolf": "WOLF", "bear": "BEAR", "chicken": "CHICKEN"}


def norm(name: str) -> str:
    name = unicodedata.normalize("NFKD", name)
    name = "".join(c for c in name if not unicodedata.combining(c))
    return re.sub(r"[^a-z]", "", name.lower())


def er_characters() -> dict[str, int]:
    text = ER_DATA.read_text(encoding="utf-8")
    found = re.findall(r'"(\d+)": \{\s*name: "[^"]+",\s*en: "([^"]+)"', text)
    return {norm(en): int(code) for code, en in found}


KIND = re.compile(r"(full|half|mini|sd)", re.I)
SKIN = re.compile(r"_0*(\d{1,3})$")


def classify(path: Path) -> tuple[str, int] | None:
    """(종류, 스킨 번호). 설정화 · 배경화면 · 스킬은 빼요"""
    parts = [p.lower() for p in path.parts]
    if any("concept" in p or "wallpaper" in p or "skill" in p or "lobby" in p for p in parts):
        return None
    stem = path.stem
    kind = KIND.search(stem)
    if not kind:
        return None
    k = kind.group(1).lower()
    m = SKIN.search(stem)
    skin = int(m.group(1)) if m else 0
    if "cadet" in str(path).lower():
        skin = 900 + skin  # 랭크 보상 스킨: 다른 그림이 없을 때만
    return k, skin


def trim(im: Image.Image) -> Image.Image:
    box = im.getchannel("A").point(lambda a: 255 if a > 16 else 0).getbbox()
    return im.crop(box) if box else im


def fit(im: Image.Image, w: int, h: int) -> Image.Image:
    s = min(w / im.width, h / im.height)
    size = (max(1, round(im.width * s)), max(1, round(im.height * s)))
    out = im.resize(size, Image.LANCZOS)
    # 작게 줄이면 흐려져서 살짝 또렷하게
    return out.filter(ImageFilter.UnsharpMask(radius=0.6, percent=60, threshold=2))


def battle_image(src: Path) -> Image.Image:
    im = trim(Image.open(src).convert("RGBA"))
    return fit(im, BATTLE_W, BATTLE_H)


def icon_image(src: Path, kind: str) -> Image.Image:
    im = Image.open(src).convert("RGBA")
    if kind != "mini":
        # 반신 · 전신: 위쪽 가운데(얼굴 쪽)를 네모로
        im = trim(im)
        side = round(im.width * (0.5 if kind == "half" else 0.42))
        left = (im.width - side) // 2
        top = round(im.height * (0.02 if kind == "half" else 0.03))
        im = im.crop((left, top, left + side, top + side))
    else:
        side = min(im.width, im.height)
        im = im.crop(((im.width - side) // 2, 0, (im.width - side) // 2 + side, side))
    face = im.resize((ICON_H - 2, ICON_H - 2), Image.LANCZOS)
    cell = Image.new("RGBA", (ICON_W, ICON_H), (0, 0, 0, 0))
    mask = Image.new("L", face.size, 0)
    ImageDraw.Draw(mask).rounded_rectangle((0, 0, face.width - 1, face.height - 1), radius=4, fill=255)
    frame = Image.new("RGBA", (ICON_H, ICON_H), (0, 0, 0, 0))
    ImageDraw.Draw(frame).rounded_rectangle((0, 0, ICON_H - 1, ICON_H - 1), radius=5, fill=(29, 36, 51, 255))
    frame.paste(face, (1, 1), mask)
    cell.alpha_composite(frame, ((ICON_W - ICON_H) // 2, 0))
    return cell


PREFER_BATTLE = {"full": 0, "half": 1, "sd": 2, "mini": 9}
PREFER_ICON = {"mini": 0, "half": 1, "full": 2, "sd": 3}


def main(kits: list[str]) -> None:
    names = er_characters()
    # code(또는 "wild:이름") → skin → [(kind, path)]
    found: dict[object, dict[int, list[tuple[str, Path]]]] = {}
    unknown: set[str] = set()
    for kit in kits:
        for path in Path(kit).rglob("*.png"):
            rel = path.relative_to(kit)
            top = rel.parts[0]
            m = re.match(r"\d+\.\s*(.+)", top)
            label = m.group(1) if m else top
            if "wild animal" in label.lower():
                key = next((v for k, v in WILD.items() if k in norm(path.stem)), None)
                if key:
                    found.setdefault(f"wild:{key}", {}).setdefault(0, []).append(("full", path))
                continue
            if "cadet" in label.lower() and len(rel.parts) > 1:
                # "Season 11 - Eleven" → Eleven
                label = rel.parts[1].split("-")[-1]
            code = names.get(norm(label))
            if code is None:
                unknown.add(label)
                continue
            c = classify(rel)
            if c:
                found.setdefault(code, {}).setdefault(c[1], []).append((c[0], path))

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    for old in OUT_DIR.glob("*.png"):
        old.unlink()
    art: dict[str, list[int]] = {}
    icons: list[tuple[str, int, Image.Image]] = []
    for key, skins in sorted(found.items(), key=lambda kv: str(kv[0])):
        for skin, files in sorted(skins.items()):
            battle = sorted((f for f in files if f[0] != "mini"), key=lambda f: PREFER_BATTLE[f[0]])
            face = sorted(files, key=lambda f: PREFER_ICON[f[0]])
            name = f"{key}_{skin}".replace("wild:", "wild_")
            if battle:
                battle_image(battle[0][1]).save(OUT_DIR / f"{name}.png", optimize=True)
                art.setdefault(str(key), []).append(skin)
            if face:
                icons.append((str(key), skin, icon_image(face[0][1], face[0][0])))

    rows = max(1, -(-len(icons) // ICON_COLS))
    sheet = Image.new("RGBA", (ICON_COLS * ICON_W, rows * ICON_H), (0, 0, 0, 0))
    frames: dict[str, dict[int, list[int]]] = {}
    for i, (key, skin, cell) in enumerate(icons):
        x, y = (i % ICON_COLS) * ICON_W, (i // ICON_COLS) * ICON_H
        sheet.alpha_composite(cell, (x, y))
        frames.setdefault(key, {})[skin] = [x, y]
    sheet.save(ICONS, optimize=True)

    def ts_record(d: dict) -> str:
        lines = []
        for key in sorted(d, key=lambda k: (not k.isdigit(), int(k) if k.isdigit() else 0, k)):
            k = key if key.isdigit() else json.dumps(key)
            lines.append(f"  {k}: {json.dumps(d[key], ensure_ascii=False)},")
        return "\n".join(lines)

    MANIFEST.write_text(
        "/*\n * SPDX-FileCopyrightText: 2026 SG\n * SPDX-License-Identifier: AGPL-3.0-only\n */\n\n"
        "// 이 파일은 scripts/fankit/build_art.py 가 만들어요. 직접 고치지 마세요.\n"
        "// 그림 파일(assets/er/)은 님블뉴런 팬키트에서 가져와 크기만 줄인 것이에요.\n\n"
        "/** 전투 그림이 있는 스킨 번호 (ER 번호 → 스킨 번호들). 그림: er/char/<ER번호>_<스킨>.png, 야생동물은 \"wild:이름\" */\n"
        f"export const BSEO_ART_SKINS: Readonly<Record<string | number, readonly number[]>> = {{\n{ts_record(art)}\n}};\n\n"
        "/** 아이콘 자리 (er/char-icons.png 안의 왼쪽 위 x, y · 칸 40×30) */\n"
        f"export const BSEO_ICON_FRAMES: Readonly<Record<string | number, Readonly<Record<number, readonly [number, number]>>>> = {{\n{ts_record(frames)}\n}};\n",
        encoding="utf-8",
    )
    chars = [k for k in found if isinstance(k, int)]
    print(f"실험체 {len(chars)}명 · 전투 그림 {sum(len(v) for v in art.values())}장 · 아이콘 {len(icons)}칸")
    if unknown:
        print("이름을 못 맞춘 폴더:", ", ".join(sorted(unknown)))


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(1)
    main(sys.argv[1:])
