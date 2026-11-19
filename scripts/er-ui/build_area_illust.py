# SPDX-FileCopyrightText: 2026 SG
# SPDX-License-Identifier: AGPL-3.0-only
"""
이터널 리턴 게임 안의 지역 일러스트 → assets/er/area-illust/ (11-19 SG "게임 파일 안의 지역 그림, 일러스트 찾아서 넣어줘")

어디 있나: 스토리 모드(아카이브) 대화 배경 그림 'Img_BG_Lumia_<지역>_<낮/밤>' (2044×1020, 옆에서 본 그림).
  게임 폴더 EternalReturn_Data/StreamingAssets/aa/Addressables/ 의 묶음 하나에 있어요
  (13.0.0 기준 1d98d1c106cca0238ac3b6d9078cc485.bundle, 303MB. 업데이트로 이름이 바뀌면 'ArchiveDialogue' 아틀라스가 든 묶음).
  지역 21곳 중 9곳만 있어요 (골목길 · 묘지 · 성당 · 공장 · 숲 · 항구 · 호텔 · 연구소 · 모래사장) + 카지노 · 요트 · 뗏목 · 균열.
  나머지 지역은 위에서 본 지도 조각(Img_Map_00_<지역>)뿐이라 전투 배경으로는 안 써요.

쓰는 법: python3 -I -B scripts/er-ui/build_area_illust.py <묶음 파일 또는 PNG 폴더>
  - 묶음(.bundle): UnityPy 로 스프라이트를 꺼내요
  - 폴더: AnimeStudio 등으로 꺼낸 Img_BG_Lumia_*.png 를 읽어요
  → assets/er/area-illust/<이름>.jpg (절반 크기 1022×510, 원본 비율) · area-illust-sources.json
  (11-19 SG가 전투 배경을 포켓로그 방식으로 정해서 지금은 전투에 안 써요. 지역 색 참고 · 나중에 지역 카드용)
"""
import json
import sys
from pathlib import Path

from PIL import Image

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "assets" / "er" / "area-illust"
SOURCES = ROOT / "assets" / "er" / "area-illust-sources.json"

# 게임 스프라이트 이름 → (저장 이름, 설명)
NAMES = {
    "Img_BG_Lumia_Alley_Day": ("alley_day", "골목길 낮"),
    "Img_BG_Lumia_Alley_Night": ("alley_night", "골목길 밤"),
    "Img_BG_Lumia_Cemetery_Day": ("cemetery_day", "묘지 낮"),
    "Img_BG_Lumia_Cemetery_S13": ("cemetery_s13", "묘지 (시즌 13)"),
    "Img_BG_Lumia_Denomination_Day": ("chapel_day", "성당 낮"),
    "Img_BG_Lumia_Denomination_Night": ("chapel_night", "성당 밤"),
    "Img_BG_Lumia_Factory_Day": ("factory_day", "공장 낮"),
    "Img_BG_Lumia_Forestl_Day": ("forest_day", "숲 낮"),
    "Img_BG_Lumia_Forestl_Night": ("forest_night", "숲 밤"),
    "Img_BG_Lumia_Harbor_Day": ("harbor_day", "항구 낮"),
    "Img_BG_Lumia_Hotel_Day": ("hotel_day", "호텔 낮"),
    "Img_BG_Lumia_Hotel_Night": ("hotel_night", "호텔 밤"),
    "Img_BG_Lumia_InsideLab_01": ("lab_inside", "연구소 안"),
    "Img_BG_Lumia_MonitorLab": ("lab_monitor", "연구소 관제실"),
    "Img_BG_Lumia_SandBeach_Day": ("beach_day", "모래사장 낮"),
    "Img_BG_Lumia_SandBeach_Night": ("beach_night", "모래사장 밤"),
    "Img_BG_Lumia_Casino": ("casino", "카지노"),
    "Img_BG_Lumia_Yacht": ("yacht", "요트"),
    "Img_BG_Lumia_Raft": ("raft", "뗏목"),
    "Img_BG_Lumia_Rift": ("rift", "균열"),
}


def from_bundle(path: Path) -> dict[str, Image.Image]:
    import UnityPy

    env = UnityPy.load(str(path))
    out = {}
    for obj in env.objects:
        if obj.type.name != "Sprite":
            continue
        sp = obj.read()
        if sp.m_Name in NAMES:
            out[sp.m_Name] = sp.image.convert("RGB")
    return out


def from_folder(path: Path) -> dict[str, Image.Image]:
    out = {}
    for f in path.rglob("Img_BG_Lumia_*.png"):
        if f.stem in NAMES:
            out[f.stem] = Image.open(f).convert("RGB")
    return out


def main() -> None:
    if len(sys.argv) < 2:
        sys.exit(__doc__)
    src = Path(sys.argv[1])
    found = from_folder(src) if src.is_dir() else from_bundle(src)
    OUT.mkdir(parents=True, exist_ok=True)
    sources = json.load(open(SOURCES, encoding="utf-8")) if SOURCES.exists() else {}
    for game, im in sorted(found.items()):
        name, label = NAMES[game]
        small = im.resize((im.width // 2, im.height // 2), Image.LANCZOS)
        small.save(OUT / f"{name}.jpg", quality=88, optimize=True)
        sources[name] = {"game": game, "name": label, "size": list(im.size), "from": "ER 13.0.0 Addressables (ArchiveDialogue)"}
    json.dump(dict(sorted(sources.items())), open(SOURCES, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    missing = sorted(set(NAMES) - set(found))
    print(f"지역 일러스트 {len(found)}개 → {OUT.relative_to(ROOT)}")
    if missing:
        print("  (못 찾음)", missing)


if __name__ == "__main__":
    main()
