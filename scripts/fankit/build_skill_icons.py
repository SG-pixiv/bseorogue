# SPDX-FileCopyrightText: 2026 SG
# SPDX-License-Identifier: AGPL-3.0-only
"""
이터널 리턴 팬키트 스킬 아이콘 → 블서로그 스킬 아이콘

팬키트 폴더(실험체마다 "번호. 영어이름/03. Skill Icon/*.png")를 읽어서
  - 아이콘:   assets/er/skill/<ER번호>_<p|q|w|e|r>.png  (72×72, 모서리 살짝 둥글게)
  - 목록:     src/data/bseorogue/skill-icon-manifest.ts  (아이콘이 있는 ER번호 → 키)
  - 출처 기록: assets/er/skill-icon-sources.json  (아이콘마다 어느 팬키트 파일로 만들었는지)
를 만들어요. 팬키트 번호와 ER 번호가 다를 수 있어서 영어 이름으로 맞춰요 (build_art.py 와 같은 방식).

파일 이름이 제각각이에요:
  Jackie_W_Adrenaline Burst · Hart_Q_1 · 05. Alex_Melee Q · Silvia_Human_E · 01. P · Echion_R0-1 · Tia_Q4 · Hyejin_Passive
→ 이름을 _ · 띄어쓰기 · - 로 나눠서 처음 나오는 P/Passive/Q/W/E/R(+숫자) 조각을 키로 써요.
  같은 키가 여러 개면: 숫자 없는 것 > 작은 숫자 > 짧은 이름. 두 모습이 있는 실험체는 한쪽만
  (실비아 Human, 알렉스 Melee, 데비&마를렌 Debi, 리 안 LyAnh). D(블레어) · Sua_RQ 같은 것은 안 써요.
  패시브는 _P / _Passive, 없으면 _T (아드리아나 · 캐시 · 아델라 · 버니스 · 리오 · 윌리엄 · 헨리).

더하기 방식: 이미 있는 아이콘은 그대로 두고 새로 찾은 키만 더해요 (출처 기록이 있는 것은 더 좋은 후보면 바꿔요).
처음부터: --fresh

쓰는 법:  python3 -B scripts/fankit/build_skill_icons.py <팬키트 폴더> [<폴더> ...]
"""
import json
import re
import sys
import unicodedata
from pathlib import Path

from PIL import Image, ImageDraw

ROOT = Path(__file__).resolve().parents[2]
ER_DATA = ROOT / "src/data/bseorogue/er-data.ts"
OUT_DIR = ROOT / "assets/er/skill"
SOURCES = ROOT / "assets/er/skill-icon-sources.json"
MANIFEST = ROOT / "src/data/bseorogue/skill-icon-manifest.ts"

SIZE = 72  # 화면에서 12칸(× 6배 = 72px)으로 그려서 1:1. 다른 크기로 그릴 땐 부드럽게 줄여요 (LINEAR)
KEYS = ("p", "q", "w", "e", "r")

# 두 모습 · 두 캐릭터가 있는 실험체: 이 말이 들어간 파일을 먼저 써요
PREFER_WORD = {"silvia": "human", "alex": "melee", "debimarlene": "debi", "lyanh": "lyanh"}
# 이 말이 들어간 파일은 아예 안 써요
SKIP_WORD = {"lyanh": ("ghost",), "fiora": ("old",)}

TOKEN = re.compile(r"^(passive|p|t|q|w|e|r)(\d*)$", re.I)


def norm(name: str) -> str:
    name = unicodedata.normalize("NFKD", name)
    name = "".join(c for c in name if not unicodedata.combining(c))
    return re.sub(r"[^a-z]", "", name.lower())


def er_characters() -> dict[str, int]:
    text = ER_DATA.read_text(encoding="utf-8")
    found = re.findall(r'"(\d+)": \{\s*name: "[^"]+",\s*en: "([^"]+)"', text)
    return {norm(en): int(code) for code, en in found}


def skill_key(stem: str) -> tuple[str, int] | None:
    """파일 이름 → (키, 숫자). 숫자 없으면 0. 못 찾으면 None"""
    stem = re.sub(r"^\d+\.\s*", "", stem)  # "05. Alex_Melee Q" 앞 번호
    stem = re.sub(r"\(.*?\)", "", stem)
    for tok in re.split(r"[_\s]+", stem):
        head = tok.split("-")[0]  # Echion_P3-1 · Arda_R-W
        m = TOKEN.match(head)
        if m:
            k = m.group(1).lower()
            if k == "t":  # 아드리아나 · 캐시 · 아델라 · 버니스 · 리오 · 윌리엄 · 헨리는 패시브가 _T
                return "p", 100 + int(m.group(2) or 0)
            k = "p" if k == "passive" else k
            if "-" in tok and not tok.split("-")[1].isdigit():
                return None  # Arda_R-W (궁극기 중 바뀌는 W) 같은 것
            return k, int(m.group(2) or 0)
    return None


def char_dir(path: Path) -> Path | None:
    for parent in path.parents:
        if re.match(r"^\d{3}\. ", parent.name):
            return parent
    return None


def collect(roots: list[Path], codes: dict[str, int]) -> dict[int, dict[str, tuple[tuple, Path]]]:
    best: dict[int, dict[str, tuple[tuple, Path]]] = {}
    for root in roots:
        for f in sorted(root.rglob("*.png")):
            if "skill icon" not in str(f.parent.name).lower():
                continue
            cd = char_dir(f)
            if cd is None:
                continue
            who = norm(re.sub(r"^\d+\.\s*", "", cd.name))
            code = codes.get(who)
            if code is None:
                print(f"  ? ER 번호를 못 찾음: {cd.name}")
                continue
            low = f.stem.lower().replace(" ", "")
            if any(w in low for w in SKIP_WORD.get(who, ())):
                continue
            key = skill_key(f.stem)
            if key is None:
                continue
            k, num = key
            prefer = PREFER_WORD.get(who)
            rank = (0 if (prefer is None or prefer in low) else 1, num, len(f.stem), f.name)
            cur = best.setdefault(code, {}).get(k)
            if cur is None or rank < cur[0]:
                best[code][k] = (rank, f)
    return best


def icon(src: Path) -> Image.Image:
    im = Image.open(src).convert("RGBA")
    side = min(im.size)
    im = im.crop(((im.width - side) // 2, (im.height - side) // 2, (im.width + side) // 2, (im.height + side) // 2))
    im = im.resize((SIZE, SIZE), Image.LANCZOS)
    mask = Image.new("L", (SIZE, SIZE), 0)
    ImageDraw.Draw(mask).rounded_rectangle((0, 0, SIZE - 1, SIZE - 1), radius=9, fill=255)
    out = Image.new("RGBA", (SIZE, SIZE), (0, 0, 0, 0))
    out.paste(im, (0, 0), mask)
    return out


def write_manifest(have: dict[int, set[str]]) -> None:
    lines = [
        "/*",
        " * SPDX-FileCopyrightText: 2026 SG",
        " * SPDX-License-Identifier: AGPL-3.0-only",
        " */",
        "",
        "// 이 파일은 scripts/fankit/build_skill_icons.py 가 만들어요. 직접 고치지 마세요.",
        "// 그림(assets/er/skill/)은 님블뉴런 팬키트에서 왔어요 (assets/er/README.md).",
        "",
        "/** ER 번호 → 스킬 아이콘이 있는 키 (p = 패시브) */",
        "export const BSEO_SKILL_ICONS: Readonly<Record<number, string>> = {",
    ]
    for code in sorted(have):
        keys = "".join(k for k in KEYS if k in have[code])
        lines.append(f'  {code}: "{keys}",')
    lines += ["};", ""]
    MANIFEST.write_text("\n".join(lines), encoding="utf-8")


def main(argv: list[str]) -> int:
    fresh = "--fresh" in argv
    roots = [Path(a) for a in argv if not a.startswith("--")]
    if not roots:
        print(__doc__)
        return 1
    codes = er_characters()
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    sources: dict[str, str] = {} if fresh or not SOURCES.exists() else json.loads(SOURCES.read_text(encoding="utf-8"))
    if fresh:
        for old in OUT_DIR.glob("*.png"):
            old.unlink()
    best = collect(roots, codes)
    added = replaced = 0
    for code, keys in sorted(best.items()):
        for k, (rank, src) in keys.items():
            name = f"{code}_{k}"
            out = OUT_DIR / f"{name}.png"
            rel = str(src.relative_to(src.parents[2]))  # "NNN. 이름/03. Skill Icon/파일"
            if out.exists() and sources.get(name) == rel:
                continue
            if out.exists():
                replaced += 1
            else:
                added += 1
            # 128색으로 줄여서 저장 (12KB → 3KB, 화면 크기에선 차이가 거의 안 보여요)
            icon(src).quantize(128, Image.Quantize.FASTOCTREE, dither=Image.Dither.FLOYDSTEINBERG).save(out, optimize=True)
            sources[name] = rel
    have: dict[int, set[str]] = {}
    for f in OUT_DIR.glob("*.png"):
        code, k = f.stem.split("_")
        have.setdefault(int(code), set()).add(k)
    write_manifest(have)
    SOURCES.write_text(json.dumps(dict(sorted(sources.items(), key=lambda x: (int(x[0].split("_")[0]), x[0]))), ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    full = [c for c in have if all(k in have[c] for k in "qwer")]
    print(f"더함 {added} · 바꿈 {replaced} · 실험체 {len(have)}명 (Q W E R 다 있는 실험체 {len(full)}명)")
    all_codes = set(codes.values())
    for c in sorted(all_codes):
        miss = [k for k in "pqwer" if k not in have.get(c, set())]
        if miss:
            print(f"  {c:>3} 빠짐: {' '.join(miss).upper()}")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
