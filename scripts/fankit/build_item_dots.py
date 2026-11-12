# SPDX-FileCopyrightText: 2026 SG
# SPDX-License-Identifier: AGPL-3.0-only
"""
이터널 리턴 팬키트 아이템 그림 → 블서로그 아이템 도트 (32×32)

팬키트 `02. Ingame_Image` 의 아이템 그림(256×142 쯤)을 도트로 바꿔요:
  그림만 잘라내기 → 28칸 안으로 줄이기 → 반투명 없애기 · 떨어진 티끌 지우기 → 어두운 그림은 밝게 →
  색 수 줄이기(14색) → 외곽선 1px (#1a1c2c)
나오는 것:
  assets/er/item/<아이템 파일 이름>.png   32×32 도트 (make_items.py 가 코드 그림보다 먼저 써요)
  assets/er/item-sources.json            아이템마다 어느 팬키트 파일로 만들었는지
  docs/item-dots-preview.png             한눈에 보기 (원본 → 도트, 4배)
어느 아이템에 어느 그림을 쓰는지는 아래 ITEMS 표 (게임 아이템 이름은 locales/ko/modifier-type.json).
색만 바꿔 여러 개로 쓰는 것: 강화 모듈(역할군 18색) · 테라피스(19색) · 부적(8색).

쓰는 법: python3 -I -B scripts/fankit/build_item_dots.py <팬키트 폴더> [<폴더> …]
         (폴더 안 어디든 "02. Ingame_Image" 가 있으면 돼요)
         그다음 python3 -I -B scripts/er-ui/make_items.py 로 아틀라스를 다시 만들어요
"""
import importlib.util
import json
import sys
from pathlib import Path

from PIL import Image, ImageEnhance

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "assets" / "er" / "item"
SOURCES = ROOT / "assets" / "er" / "item-sources.json"
PREVIEW = ROOT / "docs" / "item-dots-preview.png"
S = 32
INNER = 28
COLORS = 14
OUTLINE = (0x1A, 0x1C, 0x2C, 255)

F = "03. Consumables/Food/"
B = "03. Consumables/Boost/"
M = "05. Material/"
W = "01. Weapons/"
A = "02. Armor/"
# 아이템 그림 파일 이름 → (팬키트 경로, 블서로그 이름)
ITEMS = {
    "potion": (F + "004. Meat.png", "고기"),
    "super_potion": (F + "010. Bread In Tears.png", "눈물젖은 빵"),
    "hyper_potion": (F + "026. Mint Choco Ice Cream.png", "민트 초코"),
    "max_potion": (F + "999. #11 Combo Meal.png", "일레븐 세트"),
    "full_restore": (F + "035. Perpetual Stew.png", "만년수프"),
    "ether": (F + "008. Water.png", "물"),
    "elixir": (F + "019. Boiling Water.png", "뜨거운 물"),
    "max_elixir": (F + "020. Flower Liquor.png", "백일취"),
    "full_heal": (F + "029. First Aid Kit.png", "구급상자"),
    "sitrus_berry": (F + "018. Apple.png", "사과"),
    "lum_berry": (F + "034. Golden Apple.png", "황금사과"),
    "enigma_berry": (F + "11. Watermelon.png", "수박"),
    "liechi_berry": (F + "005. Chocolate.png", "초콜릿"),
    "ganlon_berry": (F + "001. Potato.png", "감자"),
    "petaya_berry": (F + "006. Edible Mushroom.png", "양송이 버섯"),
    "apicot_berry": (F + "024. Yellow Sweet Potato.png", "호박 고구마"),
    "salac_berry": (F + "007. Fried Chicken.png", "후라이드 치킨"),
    "lansat_berry": (F + "027. Truffle.png", "트러플"),
    "starf_berry": (F + "032. Sweet Potato.png", "꿀고구마"),
    "leppa_berry": (F + "015. Choco Spread.png", "루텔라"),
    "big_mushroom": (F + "017. Grilled Mushroom Skewers.png", "기억버섯"),
    "leftovers": ("03. Consumables/Omurice.png", "먹다 남은 도시락 (2026 시즌 11 오므라이스)"),
    "white_herb": ("03. Consumables/Oriental Herb.png", "하양허브"),
    "revive": (B + "08. Gadget Energy Pack.png", "가젯 에너지 팩"),
    "max_revive": ("00. Gadget/Kiosk Remote.png", "부활 키트"),
    "hp_up": (B + "05. Zen Vitality.png", "대환단"),
    "protein": (B + "07. Combat Epinephrine.png", "컴뱃 에피네프린"),
    "iron": (B + "04. Holy Water.png", "성수"),
    "calcium": (B + "06. Tear of Selene.png", "셀레네의 눈물"),
    "zinc": (B + "01. Capsule_Essence.png", "캡슐 - 생명 (2026 시즌 11)"),
    "carbos": (B + "03. Capsule_Galaxy.png", "캡슐 - 우주 (2026 시즌 11)"),
    "toxic_orb": (B + "02. Capsule_Sanguine.png", "출혈구슬 (2026 시즌 11 캡슐 - 선혈)"),
    "flame_orb": (W + "12. Throw/013. Fireball.png", "화염구슬"),
    "sacred_ash": ("06. Exchangeable/04. Aglaia_s Gift - Legendary.png", "아글라이아의 선물"),
    "rare_candy": (M + "060. VF Blood Sample.png", "VF 혈액 샘플"),
    "rarer_candy": (M + "060. VF Blood Sample.png", "VF 혈액 샘플 세트"),
    "relic_gold": (M + "047. Gold.png", "현상금"),
    "mystical_rock": (M + "058. Meteorite.png", "신비한바위"),
    "eviolite": (M + "999. Gem of Evolution.png", "진화의휘석"),
    "reviver_seed": (M + "057. Tree of Life.png", "부활의씨앗"),
    "shell_bell": (M + "019. Turtle Shell.png", "조개껍질방울"),
    "amulet_coin": (A + "03. Arm, Accessory/047. Buccaneer Doubloon.png", "크레딧 부적"),
    "soothe_bell": (A + "03. Arm, Accessory/029. Music Box.png", "평온의방울"),
    "quick_claw": (A + "03. Arm, Accessory/043. Nightmare Nails.png", "선제공격손톱"),
    "grip_claw": (W + "16. Glove/014. White Claw Punch.png", "끈기갈고리손톱"),
    "golden_punch": (W + "16. Glove/012. Buddha_s Palm.png", "골든펀치"),
    "scanner": (A + "03. Arm, Accessory/036. Radar.png", "실험체 분석기"),
    "dynamax_band": (A + "03. Arm, Accessory/003. Bracelet.png", "다이맥스 밴드"),
    "mega_bracelet": (A + "03. Arm, Accessory/010. Golden Bracelet.png", "메가링"),
    "tera_orb": (W + "22. Arcana/001. Glass Bead.png", "테라스탈오브"),
    "wide_lens": (W + "21. Camera/001. Lens.png", "광각렌즈"),
    "scope_lens": (W + "21. Camera/002. Rangefinder.png", "초점렌즈"),
    "zoom_lens": (W + "21. Camera/012. Triple Focus.png", "멀티렌즈"),
    "exp_share": (A + "02. Head/047. Commander Headset.png", "관전 학습 장치"),
    "kings_rock": (A + "02. Head/011. Crown.png", "왕의징표석"),
    "focus_band": (A + "02. Head/001. Hairband.png", "기합의머리띠"),
    "baton": (W + "11. Bat/001. Short Rod.png", "배턴"),
}
# 색만 바꿔 쓰는 바탕 그림
MODULE_SRC = M + "062. Tac. Skill Module.png"
SHARD_SRC = M + "034. Crimson Shard.png"
CHARM_SRC = W + "13. Shuriken/010. Mystic Jade Charm.png"


def load_make_items():
    """make_items.py 의 색 표(TYPE · MODULE · CHARMS)를 같이 써요"""
    spec = importlib.util.spec_from_file_location("make_items", ROOT / "scripts" / "er-ui" / "make_items.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def find_root(folders: list[str]) -> Path:
    for f in folders:
        p = Path(f)
        if p.name == "02. Ingame_Image":
            return p
        for q in p.rglob("02. Ingame_Image"):
            if q.is_dir() and (q / "05. Material").exists():
                return q
    raise SystemExit('"02. Ingame_Image" 폴더를 못 찾았어요')


def to_dot(src: Image.Image, tint=None, inner=INNER) -> Image.Image:
    """큰 그림 → 32×32 도트"""
    im = src.convert("RGBA")
    # 희미한 빛 · 그림자는 빼고 그림만 잘라요
    solid = im.getchannel("A").point(lambda a: 255 if a >= 96 else 0)
    box = solid.getbbox()
    if not box:
        return Image.new("RGBA", (S, S), (0, 0, 0, 0))
    im = im.crop(box)
    k = inner / max(im.size)
    w, h = max(1, round(im.width * k)), max(1, round(im.height * k))
    small = im.convert("RGBa").resize((w, h), Image.BOX).convert("RGBA")
    alpha = despeckle(small.getchannel("A").point(lambda a: 255 if a >= 120 else 0))
    rgb = small.convert("RGB")
    gray = rgb.convert("L")
    lum = [g for g, a in zip(gray.tobytes(), alpha.tobytes()) if a]
    if tint:
        px = [tuple(min(255, int(tint[i] * (0.35 + g / 150))) for i in range(3)) for g in gray.tobytes()]
        col = Image.new("RGB", rgb.size)
        col.putdata(px)
        rgb = Image.blend(rgb, col, 0.78)
    elif lum and sum(lum) / len(lum) < 80:
        # 어두운 그림(카메라 · 헤드셋 …)은 어두운 창 위에서 안 보여서 밝게
        g = 0.62 if sum(lum) / len(lum) < 55 else 0.75
        rgb = rgb.point(lambda v: int(255 * (v / 255) ** g))
    rgb = ImageEnhance.Color(rgb).enhance(1.25)
    rgb = ImageEnhance.Contrast(rgb).enhance(1.12)
    # 색 수 줄이기 (투명한 곳은 빼고 세요)
    flat = Image.new("RGB", rgb.size, (0, 0, 0))
    flat.paste(rgb, (0, 0), alpha)
    pal = flat.quantize(colors=COLORS + 1, method=Image.MEDIANCUT, dither=Image.NONE).convert("RGB")
    out = Image.new("RGBA", (S, S), (0, 0, 0, 0))
    ox, oy = (S - w) // 2, (S - h) // 2
    body = pal.convert("RGBA")
    body.putalpha(alpha)
    out.paste(body, (ox, oy), alpha)
    # 외곽선: 그림 바로 바깥 한 칸
    a = out.getchannel("A").load()
    px = out.load()
    edge = []
    for y in range(S):
        for x in range(S):
            if a[x, y]:
                continue
            if any(0 <= x + dx < S and 0 <= y + dy < S and a[x + dx, y + dy] for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1))):
                edge.append((x, y))
    for x, y in edge:
        px[x, y] = OUTLINE
    return out


def despeckle(alpha: Image.Image, keep: int = 5) -> Image.Image:
    """큰 덩어리에서 떨어진 작은 티끌(반짝이 · 연기)은 지워요"""
    w, h = alpha.size
    a = alpha.load()
    seen = [[False] * w for _ in range(h)]
    out = Image.new("L", (w, h), 0)
    o = out.load()
    for y in range(h):
        for x in range(w):
            if not a[x, y] or seen[y][x]:
                continue
            stack, blob = [(x, y)], []
            seen[y][x] = True
            while stack:
                cx, cy = stack.pop()
                blob.append((cx, cy))
                for dx in (-1, 0, 1):
                    for dy in (-1, 0, 1):
                        nx, ny = cx + dx, cy + dy
                        if 0 <= nx < w and 0 <= ny < h and a[nx, ny] and not seen[ny][nx]:
                            seen[ny][nx] = True
                            stack.append((nx, ny))
            if len(blob) >= keep:
                for bx, by in blob:
                    o[bx, by] = 255
    return out


def pair(dot: Image.Image) -> Image.Image:
    """같은 그림 두 개를 겹쳐서 (세트)"""
    small = dot.resize((24, 24), Image.NEAREST)
    out = Image.new("RGBA", (S, S), (0, 0, 0, 0))
    out.alpha_composite(small, (1, 2))
    out.alpha_composite(small, (8, 7))
    return out


def main() -> None:
    folders = [a for a in sys.argv[1:] if not a.startswith("--")]
    if not folders:
        raise SystemExit(__doc__)
    root = find_root(folders)
    mi = load_make_items()
    order = [f["filename"] for f in json.load(open(ROOT / "assets/images/items.json", encoding="utf-8"))["textures"][0]["frames"]]
    OUT.mkdir(parents=True, exist_ok=True)
    sources, shown, missing = {}, [], []

    def put(name: str, rel: str, label: str, tint=None, post=None) -> None:
        f = root / rel
        if not f.exists():
            missing.append(f"{name}: {rel}")
            return
        with Image.open(f) as src:
            dot = to_dot(src, tint)
            if post:
                dot = post(dot)
            if len(shown) < 200 and not tint:
                shown.append((src.convert("RGBA").copy(), dot))
        dot.save(OUT / f"{name}.png", optimize=True)
        sources[name] = {"file": rel, "name": label, **({"tint": list(tint)} if tint else {})}

    for name, (rel, label) in ITEMS.items():
        put(name, rel, label, post=pair if name == "rarer_candy" else None)
    for name, typ in mi.MODULE.items():
        put(name, MODULE_SRC, f"강화 모듈 ({typ})", tint=mi.TYPE[typ])
    for name in order:
        if name.endswith("_tera_shard"):
            typ = name[: -len("_tera_shard")]
            put(name, SHARD_SRC, f"테라피스 ({typ})", tint=mi.TYPE.get(typ, (200, 200, 210)))
    for name, (c, _c2) in mi.CHARMS.items():
        put(name, CHARM_SRC, f"부적 ({name})", tint=c)
    unknown = sorted(n for n in sources if n not in order)
    json.dump(dict(sorted(sources.items())), open(SOURCES, "w", encoding="utf-8"), ensure_ascii=False, indent=1)

    # 한눈에 보기: 원본(64) → 도트(4배 128)
    cols = 6
    cw, ch = 64 + 8 + 128 + 12, 136
    sheet = Image.new("RGBA", (cols * cw + 8, ((len(shown) + cols - 1) // cols) * ch + 8), (36, 40, 54, 255))
    for i, (src, dot) in enumerate(shown):
        x, y = 8 + (i % cols) * cw, 8 + (i // cols) * ch
        box = src.getchannel("A").point(lambda a: 255 if a >= 96 else 0).getbbox()
        thumb = src.crop(box) if box else src
        thumb.thumbnail((64, 64))
        sheet.alpha_composite(thumb, (x + (64 - thumb.width) // 2, y + (128 - thumb.height) // 2))
        sheet.alpha_composite(dot.resize((128, 128), Image.NEAREST), (x + 72, y))
    sheet.convert("RGB").save(PREVIEW, optimize=True)
    print(f"도트 {len(sources)}개 → {OUT.relative_to(ROOT)} · 미리보기 {PREVIEW.relative_to(ROOT)}")
    for m in missing:
        print("  (없음)", m)
    if unknown:
        print("  (아틀라스에 없는 이름)", unknown)


if __name__ == "__main__":
    main()
