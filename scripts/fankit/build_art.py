# SPDX-FileCopyrightText: 2026 SG
# SPDX-License-Identifier: AGPL-3.0-only
"""
이터널 리턴 팬키트 그림 → 블서로그 전투 그림 · 아이콘

팬키트 폴더(실험체마다 "번호. 영어이름" 폴더)를 읽어서
  - 전투 그림:  assets/er/char/<ER번호>_<스킨번호>.png  (전신, 없으면 반신. 높이 96 안쪽)
  - 아이콘:     assets/er/char-icons.png  (40×30 칸 한 장에 모아서. 얼굴 Mini, 없으면 반신에서 얼굴 쪽)
  - 목록:       src/data/bseorogue/art-manifest.ts
  - 출처 기록:  assets/er/art-sources.json  (그림마다 어느 팬키트 파일 · 종류로 만들었는지)
를 만들어요. 팬키트 번호는 ER 번호와 다를 때가 있어서(예: 팬키트 017 = 쇼이치 = ER 18) 영어 이름으로 맞춰요.
파일 이름의 숫자(_00, _02, Skin_03_Full, S01 …)가 ER 스킨 번호예요 (0 = 기본 모습).

팬키트가 zip 17개로 나뉘어 있고 컴퓨터마다 일부만 있어서, 기본은 **더하기**예요:
이미 만든 그림은 그대로 두고, 새 폴더에서 찾은 그림만 더해요.
같은 스킨이 이미 있으면 더 좋은 종류(전투: 전신 > 반신 > SD, 아이콘: 얼굴 > 반신 > 전신)일 때만 바꿔요.

쓰는 법:  python3 scripts/fankit/build_art.py <팬키트 폴더> [<팬키트 폴더> ...]
          python3 scripts/fankit/build_art.py --fresh <팬키트 폴더> ...   (전부 지우고 새로)
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
SOURCES = ROOT / "assets/er/art-sources.json"
MANIFEST = ROOT / "src/data/bseorogue/art-manifest.ts"

# 전투 그림 크기 (게임 화면 단위. 포켓로그 큰 포켓몬 정도)
BATTLE_W, BATTLE_H = 92, 96
ICON_W, ICON_H = 40, 30
ICON_COLS = 32

# 야생동물 (팬키트 Wild Animal 폴더 파일 이름 → 블서로그 종 이름)
WILD = {"bat": "BAT", "hound": "WILD_DOG", "wilddog": "WILD_DOG", "boar": "BOAR", "wolf": "WOLF", "bear": "BEAR", "chicken": "CHICKEN"}

# 낮을수록 좋아요. 기록이 없는 예전 그림은 "?" (바꾸지 않아요)
PREFER_BATTLE = {"full": 0, "half": 1, "sd": 2, "mini": 9}
PREFER_ICON = {"mini": 0, "half": 1, "full": 2, "sd": 3}


def norm(name: str) -> str:
    name = unicodedata.normalize("NFKD", name)
    name = "".join(c for c in name if not unicodedata.combining(c))
    return re.sub(r"[^a-z]", "", name.lower())


def er_characters() -> dict[str, int]:
    text = ER_DATA.read_text(encoding="utf-8")
    found = re.findall(r'"(\d+)": \{\s*name: "[^"]+",\s*en: "([^"]+)"', text)
    return {norm(en): int(code) for code, en in found}


KIND = re.compile(r"(full|half|mini|sd)", re.I)


def skin_number(stem: str, parent: str) -> int:
    """파일 이름에서 스킨 번호. 숫자가 없으면 폴더로 짐작 (기본 폴더 = 0, "06. 스킨" = 1, "07." = 2 …)"""
    nums = re.findall(r"(?<![a-z])s?(\d{1,3})(?!\d)", stem.lower())
    if nums:
        return int(nums[-1])
    m = re.match(r"(\d+)\.", parent)
    if m and "default" not in parent.lower() and int(m.group(1)) >= 6:
        return int(m.group(1)) - 5
    return 0


def classify(rel: Path) -> tuple[str, int] | None:
    """(종류, 스킨 번호). 설정화 · 배경화면 · 스킬 · 로비는 빼요"""
    parts = [p.lower() for p in rel.parts]
    if any(w in p for p in parts for w in ("concept", "wallpaper", "skill", "lobby", "bonus")):
        return None
    stem = rel.stem
    kind = KIND.search(stem)
    if not kind:
        return None
    k = kind.group(1).lower()
    skin = skin_number(stem, rel.parent.name)
    if "cadet" in str(rel).lower():
        skin = 900 + (skin if re.search(r"\d", stem) else 0)  # 랭크 보상 스킨: 다른 그림이 없을 때만
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
    if kind == "mini" and im.width * im.height > 600 * 600:
        # 이름은 Mini 인데 큰 그림(반신)인 것들이 있어요 → 반신처럼 얼굴 쪽을 잘라요
        kind = "half"
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


def read_manifest() -> tuple[dict[str, list[int]], dict[str, dict[int, tuple[int, int]]]]:
    """지금 art-manifest.ts 의 (전투 그림 스킨, 아이콘 자리)"""
    if not MANIFEST.exists():
        return {}, {}
    text = MANIFEST.read_text(encoding="utf-8")
    battle_part, icon_part = text.split("BSEO_ICON_FRAMES", 1)
    art = {k.strip('"'): json.loads(v) for k, v in re.findall(r'^\s+("[^"]+"|\d+): (\[[^\]]*\]),$', battle_part, re.M)}
    frames: dict[str, dict[int, tuple[int, int]]] = {}
    for k, v in re.findall(r'^\s+("[^"]+"|\d+): (\{.*\}),$', icon_part, re.M):
        frames[k.strip('"')] = {int(s): tuple(xy) for s, xy in json.loads(v).items()}
    return art, frames


def sort_key(key: str) -> tuple:
    return (not key.isdigit(), int(key) if key.isdigit() else 0, key)


def main(argv: list[str]) -> None:
    fresh = "--fresh" in argv
    kits = [a for a in argv if a != "--fresh"]
    names = er_characters()

    # 1) 팬키트에서 찾은 그림: key("18" / "wild:BAT") → skin → [(kind, path, rel)]
    found: dict[str, dict[int, list[tuple[str, Path, str]]]] = {}
    unknown: set[str] = set()
    for kit in kits:
        for path in sorted(Path(kit).rglob("*.png")):
            rel = path.relative_to(kit)
            top = rel.parts[0]
            m = re.match(r"\d+\.\s*(.+)", top)
            label = m.group(1) if m else top
            if "wild animal" in label.lower():
                key = next((v for k, v in WILD.items() if k in norm(path.stem)), None)
                if key:
                    found.setdefault(f"wild:{key}", {}).setdefault(0, []).append(("full", path, str(rel)))
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
                found.setdefault(str(code), {}).setdefault(c[1], []).append((c[0], path, str(rel)))

    # 야생동물은 보통 그림을 먼저 (Mutant_ 는 보통 그림이 없을 때만)
    for key, skins in found.items():
        if key.startswith("wild:"):
            for files in skins.values():
                files.sort(key=lambda f: "mutant" in f[2].lower())

    # 2) 지금 있는 것 (더하기 모드)
    old_art, old_frames = ({}, {}) if fresh else read_manifest()
    sources: dict[str, dict[str, dict[str, str]]] = {"battle": {}, "icon": {}}
    if not fresh and SOURCES.exists():
        sources = json.loads(SOURCES.read_text(encoding="utf-8"))
    old_sheet = Image.open(ICONS).convert("RGBA") if (not fresh and ICONS.exists()) else None

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    if fresh:
        for old in OUT_DIR.glob("*.png"):
            old.unlink()
        sources = {"battle": {}, "icon": {}}

    art: dict[str, set[int]] = {k: set(v) for k, v in old_art.items()}
    icons: dict[tuple[str, int], Image.Image] = {}
    if old_sheet is not None:
        for key, skins in old_frames.items():
            for skin, (x, y) in skins.items():
                icons[(key, skin)] = old_sheet.crop((x, y, x + ICON_W, y + ICON_H))

    def better(table: dict[str, int], kind: str, old_kind: str | None) -> bool:
        if old_kind is None:
            return True  # 처음 생기는 그림
        if old_kind == "?":
            return False  # 기록 없는 예전 그림은 그대로
        return table[kind] < table.get(old_kind, 99)

    added_battle = added_icon = 0
    for key, skins in sorted(found.items(), key=lambda kv: sort_key(kv[0])):
        for skin, files in sorted(skins.items()):
            name = f"{key}_{skin}".replace("wild:", "wild_")
            id_ = f"{key}_{skin}"
            battle = sorted((f for f in files if f[0] != "mini"), key=lambda f: PREFER_BATTLE[f[0]])
            face = sorted(files, key=lambda f: PREFER_ICON[f[0]])
            if battle:
                had = skin in art.get(key, set())
                old_kind = sources["battle"].get(id_, {}).get("kind") if had else None
                if had and old_kind is None:
                    old_kind = "?"
                if better(PREFER_BATTLE, battle[0][0], old_kind):
                    battle_image(battle[0][1]).save(OUT_DIR / f"{name}.png", optimize=True)
                    art.setdefault(key, set()).add(skin)
                    sources["battle"][id_] = {"kind": battle[0][0], "file": battle[0][2].replace("\\", "/")}
                    added_battle += 1
            if face:
                had = (key, skin) in icons
                old_kind = sources["icon"].get(id_, {}).get("kind") if had else None
                if had and old_kind is None:
                    old_kind = "?"
                if better(PREFER_ICON, face[0][0], old_kind):
                    icons[(key, skin)] = icon_image(face[0][1], face[0][0])
                    sources["icon"][id_] = {"kind": face[0][0], "file": face[0][2].replace("\\", "/")}
                    added_icon += 1

    # 3) 아이콘 한 장 (ER 번호 · 스킨 순서)
    ordered = sorted(icons.items(), key=lambda kv: (sort_key(kv[0][0]), kv[0][1]))
    rows = max(1, -(-len(ordered) // ICON_COLS))
    sheet = Image.new("RGBA", (ICON_COLS * ICON_W, rows * ICON_H), (0, 0, 0, 0))
    frames: dict[str, dict[int, list[int]]] = {}
    for i, ((key, skin), cell) in enumerate(ordered):
        x, y = (i % ICON_COLS) * ICON_W, (i // ICON_COLS) * ICON_H
        sheet.alpha_composite(cell, (x, y))
        frames.setdefault(key, {})[skin] = [x, y]
    sheet.save(ICONS, optimize=True)

    def ts_record(d: dict) -> str:
        lines = []
        for key in sorted(d, key=sort_key):
            k = key if key.isdigit() else json.dumps(key)
            v = d[key]
            v = sorted(v) if isinstance(v, set) else {str(s): v[s] for s in sorted(v)}
            lines.append(f"  {k}: {json.dumps(v, ensure_ascii=False)},")
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
    sources = {k: dict(sorted(v.items(), key=lambda kv: (sort_key(kv[0].rsplit("_", 1)[0]), int(kv[0].rsplit("_", 1)[1])))) for k, v in sources.items()}
    SOURCES.write_text(json.dumps(sources, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")

    chars_battle = {k for k in art if k.isdigit()}
    chars_icon = {k for k in frames if k.isdigit()}
    print(f"이번에 더한 것: 전투 그림 {added_battle}장 · 아이콘 {added_icon}칸")
    print(f"전체: 전투 그림 실험체 {len(chars_battle)}명 ({sum(len(v) for v in art.values())}장) · 아이콘 실험체 {len(chars_icon)}명 ({len(ordered)}칸)")
    missing = sorted(set(names.values()) - {int(k) for k in chars_icon})
    if missing:
        print("그림이 하나도 없는 ER 번호:", ", ".join(map(str, missing)))
    if unknown:
        print("이름을 못 맞춘 폴더:", ", ".join(sorted(unknown)))


if __name__ == "__main__":
    if len([a for a in sys.argv[1:] if a != "--fresh"]) < 1:
        print(__doc__)
        sys.exit(1)
    main(sys.argv[1:])
