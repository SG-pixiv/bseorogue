# SPDX-FileCopyrightText: 2026 SG
# SPDX-License-Identifier: AGPL-3.0-only
"""
완성된 실험체 도트 → 게임에 넣기 (도트 가이드 docs/dot-guide, 가이드 문서의 검사 목록)

받는 파일 이름 (둘 중 아무거나):
  <ER번호>_<스킨>.png        예: 1_0.png  (전투 80×80)       1_0_icon.png  (아이콘 40×30)
  <실험체 이름>_<스킨>.png   예: 재키_0.png · Jackie_1_icon.png
검사 (하나라도 틀리면 넣지 않아요):
  크기 (전투 80×80 · 아이콘 40×30) · 반투명 픽셀 없음 · 투명 빼고 15색 이하 · 빈 그림 아님 · 있는 ER 번호
알려만 주는 것: 발끝이 맨 아래 1px 위인지 · 외곽선 색(#1a1c2c)을 썼는지 · 키(S 60 · M 68 · L 74)

넣는 곳:
  assets/er/dot/<ER번호>_<스킨>.png · _icon.png    1배 그대로 (게임에서 확대 · 축소 없어요)
  assets/er/dot-icons.png                          아이콘을 한 장에 모은 것
  src/data/bseorogue/dot-manifest.ts               목록 (자동 생성)
게임은 도트가 있는 실험체는 팬키트 그림보다 도트를 먼저 써요 (placeholder-art.ts).

쓰는 법:
  python3 -B scripts/er-dot/import_dot.py <도트.png 또는 폴더> [...]   검사하고 넣기 → 목록 다시 만들기
  python3 -B scripts/er-dot/import_dot.py --check <도트.png 또는 폴더>  검사만
  python3 -B scripts/er-dot/import_dot.py                              (파일을 지운 뒤) 목록 · 아이콘 한 장만 다시
"""
import re
import shutil
import sys
from pathlib import Path

from PIL import Image

ROOT = Path(__file__).resolve().parents[2]
ER_DATA = ROOT / "src/data/bseorogue/er-data.ts"
DOT_DIR = ROOT / "assets/er/dot"
ICON_SHEET = ROOT / "assets/er/dot-icons.png"
MANIFEST = ROOT / "src/data/bseorogue/dot-manifest.ts"

BATTLE = (80, 80)
ICON = (40, 30)
ICON_COLS = 32
MAX_COLORS = 15
OUTLINE = (0x1A, 0x1C, 0x2C)
HEIGHTS = {"S": 60, "M": 68, "L": 74}
NAME = re.compile(r"^(.+?)_(\d{1,3})(_icon)?$", re.I)


def er_names() -> dict[str, int]:
    """실험체 이름(한국어 · 영어, 띄어쓰기 · 대소문자 무시) → ER 번호"""
    text = ER_DATA.read_text(encoding="utf-8")
    out = {}
    for code, ko, en in re.findall(r'"(\d+)": \{\s*name: "([^"]+)",\s*en: "([^"]+)"', text):
        for n in (code, ko, en):
            out[re.sub(r"[\s.\-']", "", n).lower()] = int(code)
    return out


def check(path: Path, names: dict[str, int]) -> tuple[tuple[int, int, bool] | None, list[str], list[str]]:
    """→ ((ER번호, 스킨, 아이콘인지) 또는 None, 틀린 것, 알림)"""
    errors, notes = [], []
    m = NAME.match(path.stem)
    if not m:
        return None, ["파일 이름은 <ER번호 또는 이름>_<스킨>.png (아이콘은 _icon) 이어야 해요"], notes
    code = names.get(re.sub(r"[\s.\-']", "", m[1]).lower())
    if code is None:
        return None, [f"'{m[1]}' 라는 실험체가 없어요"], notes
    skin, is_icon = int(m[2]), bool(m[3])
    key = (code, skin, is_icon)
    try:
        with Image.open(path) as src:
            im = src.convert("RGBA") if src.mode != "RGBA" else src.copy()
    except Exception as e:  # noqa: BLE001 — 그림이 아닌 파일
        return key, [f"그림을 못 열어요 ({e})"], notes
    want = ICON if is_icon else BATTLE
    if im.size != want:
        errors.append(f"크기가 {im.size[0]}×{im.size[1]} 예요 ({'아이콘' if is_icon else '전투'}는 {want[0]}×{want[1]})")
    px = list(im.getdata()) if not hasattr(im, "get_flattened_data") else list(im.get_flattened_data())
    semi = sum(1 for p in px if 0 < p[3] < 255)
    if semi:
        errors.append(f"반투명 픽셀이 {semi}개 있어요 (완전 투명 아니면 완전 불투명만)")
    colors = {p[:3] for p in px if p[3] == 255}
    if not colors:
        errors.append("빈 그림이에요")
    elif len(colors) > MAX_COLORS:
        errors.append(f"색이 {len(colors)}개예요 (투명 빼고 {MAX_COLORS}개 이하, clean_dot.py 로 줄일 수 있어요)")
    if colors and OUTLINE not in colors:
        notes.append("외곽선 색 #1a1c2c 를 안 썼어요 (가이드 팔레트)")
    if colors and not is_icon and im.size == want:
        w, h = im.size
        rows = [y for y in range(h) if any(px[y * w + x][3] for x in range(w))]
        bottom, top = rows[-1], rows[0]
        if bottom != h - 2:
            notes.append(f"발끝이 맨 아래에서 {h - 1 - bottom}px 위예요 (가이드: 1px 위)")
        tall = bottom - top + 1
        size = min(HEIGHTS, key=lambda k: abs(HEIGHTS[k] - tall))
        notes.append(f"키 {tall}px (가까운 등급 {size} {HEIGHTS[size]}px)")
    return key, errors, notes


def gather(args: list[str]) -> list[Path]:
    out = []
    for a in args:
        p = Path(a)
        out.extend(sorted(p.glob("*.png")) if p.is_dir() else [p])
    return out


def rebuild() -> tuple[int, int]:
    """assets/er/dot 를 다시 읽어 목록 · 아이콘 한 장 만들기"""
    battle, icons = {}, {}
    for f in sorted(DOT_DIR.glob("*.png")) if DOT_DIR.exists() else []:
        m = re.fullmatch(r"(\d+)_(\d+)(_icon)?", f.stem)
        if m:
            (icons if m[3] else battle).setdefault(int(m[1]), []).append(int(m[2]))
    frames = {}
    cells = [(c, s) for c in sorted(icons) for s in sorted(icons[c])]
    if cells:
        rows = (len(cells) + ICON_COLS - 1) // ICON_COLS
        sheet = Image.new("RGBA", (min(len(cells), ICON_COLS) * ICON[0], rows * ICON[1]), (0, 0, 0, 0))
        for i, (c, s) in enumerate(cells):
            x, y = (i % ICON_COLS) * ICON[0], (i // ICON_COLS) * ICON[1]
            with Image.open(DOT_DIR / f"{c}_{s}_icon.png") as icon:
                sheet.paste(icon.convert("RGBA"), (x, y))
            frames.setdefault(c, {})[s] = (x, y)
        sheet.save(ICON_SHEET, optimize=True)
    elif ICON_SHEET.exists():
        ICON_SHEET.unlink()

    def rec(d: dict) -> str:
        return "\n".join(f"  {k}: {v}," for k, v in d.items())

    lines = [
        "/*",
        " * SPDX-FileCopyrightText: 2026 SG",
        " * SPDX-License-Identifier: AGPL-3.0-only",
        " */",
        "",
        "// 이 파일은 scripts/er-dot/import_dot.py 가 만들어요. 직접 고치지 마세요.",
        "",
        "/** 전투 도트가 있는 스킨 (ER 번호 → 스킨 번호들). 그림: er/dot/<ER번호>_<스킨>.png (80×80, 1배) */",
        "export const BSEO_DOT_SKINS: Readonly<Record<number, readonly number[]>> = {",
        rec({c: f"[{', '.join(map(str, sorted(v)))}]" for c, v in sorted(battle.items())}),
        "};",
        "",
        "/** 아이콘 도트 자리 (er/dot-icons.png 안, ER 번호 → 스킨 → [x, y], 40×30) */",
        "export const BSEO_DOT_ICON_FRAMES: Readonly<Record<number, Readonly<Record<number, readonly [number, number]>>>> = {",
        rec({c: "{ " + ", ".join(f"{s}: [{x}, {y}]" for s, (x, y) in sorted(v.items())) + " }" for c, v in sorted(frames.items())}),
        "};",
        "",
    ]
    MANIFEST.write_text("\n".join(lines).replace("{\n\n};", "{};"), encoding="utf-8")
    return sum(len(v) for v in battle.values()), len(cells)


def main() -> None:
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    only_check = "--check" in sys.argv
    names = er_names()
    files = gather(args)
    ok, bad = [], 0
    for f in files:
        key, errors, notes = check(f, names)
        tag = f"{key[0]}_{key[1]}{'_icon' if key[2] else ''}" if key else "?"
        print(f"{'✔' if not errors else '✘'} {f.name} → {tag}")
        for e in errors:
            print(f"    ✘ {e}")
        for n in notes:
            print(f"    · {n}")
        if errors:
            bad += 1
        else:
            ok.append((f, tag))
    if only_check:
        sys.exit(1 if bad else 0)
    DOT_DIR.mkdir(parents=True, exist_ok=True)
    for f, tag in ok:
        shutil.copyfile(f, DOT_DIR / f"{tag}.png")
    n_battle, n_icon = rebuild()
    print(f"넣음 {len(ok)}개 · 못 넣음 {bad}개 → 지금 도트: 전투 {n_battle}장 · 아이콘 {n_icon}장 ({MANIFEST.relative_to(ROOT)})")
    if bad:
        sys.exit(1)


if __name__ == "__main__":
    main()
