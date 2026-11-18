# SPDX-FileCopyrightText: 2026 SG
# SPDX-License-Identifier: AGPL-3.0-only
"""
이터널 리턴 팬키트 안내 방송 → 블서로그 안내 방송 (판 시작 · 금지구역 · 남은 생존자 · 승리 …)

팬키트 `drive-download-…/01. Announce/KOR/ER 어나운스_<이름>_<01|02>.wav` (한국어 57개) 를 읽어서
  - 소리:      assets/er/announce/<키>_<0|1>.m4a  (AAC · 모노 · 64kbps, 앞뒤 무음 자르기, 소리 크기 −18 LUFS,
               실험체 음성과 같은 설정)
  - 목록:      src/data/bseorogue/announce-manifest.ts  (키마다 몇 개 · 무슨 방송인지)
  - 출처 기록: assets/er/announce-sources.json
를 만들어요. 같은 방송이 2개(_01 · _02)씩 있어서 게임에서 둘 중 하나를 골라요.

어느 장면에서 트는지는 게임 쪽 `src/data/bseorogue/announce.ts` 가 정해요 (이 표의 `scene` 은 목록 설명용).

쓰는 법:  python3 -I -B scripts/fankit/build_announce.py <팬키트 폴더>
          (폴더 안 어디든 "01. Announce/KOR" 가 있으면 돼요)
필요한 것: ffmpeg
"""
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from build_voice import convert  # noqa: E402

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "assets" / "er" / "announce"
SOURCES = ROOT / "assets" / "er" / "announce-sources.json"
MANIFEST = ROOT / "src" / "data" / "bseorogue" / "announce-manifest.ts"
PREFIX = "ER 어나운스_"

# 팬키트 파일 이름(가운데) → (키, 방송 내용 요약, 블서로그에서 트는 곳). 트는 곳이 "" 면 아직 안 써요
TABLE: list[tuple[str, str, str, str]] = [
    ("게임 시작", "start", "실험 시작 안내", "판 시작 (1웨이브)"),
    ("게임 종료", "win", "승리 안내", "50웨이브 클리어"),
    ("누군가 사망", "dead", "생존자 사망 안내", "판 실패 (파티 전멸)"),
    ("금지구역1", "zone1", "첫 번째 금지구역 지정", "10웨이브 보스를 이겼을 때"),
    ("금지구역2", "zone2", "두 번째 금지구역 지정", "20웨이브 보스를 이겼을 때"),
    ("금지구역3", "zone3", "세 번째 금지구역 지정", "30웨이브 보스를 이겼을 때"),
    ("금지구역4", "zone4", "네 번째 금지구역 지정", ""),
    ("금지구역5", "zone5", "다섯 번째 금지구역 지정", ""),
    ("금지구역6", "zone6", "여섯 번째 금지구역 지정", ""),
    ("금지구역7", "zone7", "일곱 번째 금지구역 지정", ""),
    ("금지구역8", "zone8", "여덟 번째 금지구역 지정", ""),
    ("금지구역9", "zone9", "아홉 번째 금지구역 지정", ""),
    ("금지구역", "zone", "새 금지구역 지정", ""),
    ("금지구역 가속", "hurry", "생존자가 적어 금지구역 가속", ""),
    ("생존자 10명 남음", "left10", "생존자 10명 남음", "40웨이브를 이겼을 때 (10웨이브 남음)"),
    ("생존자 5명 남음", "left5", "생존자 5명 남음", "45웨이브를 이겼을 때"),
    ("생존자 3명 남음", "left3", "최종 생존자 3명", "47웨이브를 이겼을 때"),
    ("생존자 2명 남음", "left2", "최종 생존자 2명", "48웨이브를 이겼을 때"),
    ("안전지대 해제 안내", "safe_off", "임시 안전지대 해제 (더 이상 안전한 곳이 없음)", "49웨이브를 이겼을 때 (다음은 최종 보스)"),
    ("누군가 해킹1", "hack", "시스템 비정상 접근 감지", "50웨이브 최종 보스(루미)가 나올 때"),
    ("누군가 3, 4킬을 기록", "kill3", "누군가 연쇄 처치 중", "쓰러지지 않고 5연승"),
    ("누군가 5, 6킬을 기록", "kill5", "누군가 루미아 섬을 지배 중", "쓰러지지 않고 15연승"),
    ("누군가 7킬을 기록", "kill7", "누군가 생존자의 절반을 처치", "25웨이브를 이겼을 때 (판의 절반)"),
    ("누군가 8킬 이상을 기록", "kill8", "전설이 탄생 중", "쓰러지지 않고 35연승"),
    ("항공보급 실시", "supply", "항공 보급 도착", "보급 요청(뽑기)에서 보급 상자가 나올 때"),
    ("항공보급 예고", "supply_soon", "1분 뒤 항공 보급 도착", ""),
    ("안전지대 예고 안내", "safe_soon", "1분 뒤 마지막 금지구역 · 임시 안전지대 예고", ""),
    ("안전지대 지정 안내", "safe_set", "마지막 금지구역 지정 · 임시 안전지대", ""),
    ("안전지대 해제 예고 안내", "safe_off_soon", "1분 뒤 임시 안전지대 해제", ""),
]


def find_kor(folders: list[str]) -> Path:
    for f in folders:
        p = Path(f)
        if p.name == "KOR" and p.parent.name == "01. Announce":
            return p
        for hit in sorted(p.rglob("01. Announce/KOR")):
            return hit
    sys.exit("'01. Announce/KOR' 폴더를 찾지 못했어요")


def main(argv: list[str]) -> None:
    if not argv:
        sys.exit(__doc__)
    kor = find_kor(argv)
    OUT.mkdir(parents=True, exist_ok=True)
    counts: dict[str, int] = {}
    sources: dict[str, dict] = {}
    names = {name: (key, what, scene) for name, key, what, scene in TABLE}
    missing = []
    for name, key, what, scene in TABLE:
        files = sorted(kor.glob(f"{PREFIX}{name}_[0-9][0-9].wav"))
        if not files:
            missing.append(name)
            continue
        for i, src in enumerate(files):
            convert(src, OUT / f"{key}_{i}.m4a")
        counts[key] = len(files)
        sources[key] = {"what": what, "scene": scene, "files": [f"01. Announce/KOR/{f.name}" for f in files]}
    extra = sorted(
        f.name for f in kor.glob("*.wav") if f.stem.removeprefix(PREFIX).rsplit("_", 1)[0] not in names
    )
    SOURCES.write_text(json.dumps(sources, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    lines = [
        "/*",
        " * SPDX-FileCopyrightText: 2026 SG",
        " * SPDX-License-Identifier: AGPL-3.0-only",
        " */",
        "",
        "// 이 파일은 scripts/fankit/build_announce.py 가 만들어요. 직접 고치지 마세요.",
        "// 소리 파일(assets/er/announce/)은 님블뉴런 팬키트 안내 방송(한국어)에서 가져와 줄인 것이에요.",
        "",
        "/** 안내 방송 키 → 같은 방송 몇 개 (파일: er/announce/<키>_<0부터>.m4a) */",
        "export const BSEO_ANNOUNCES = {",
    ]
    for _name, key, what, _scene in TABLE:
        if key in counts:
            lines.append(f"  /** {what} */")
            lines.append(f"  {key}: {counts[key]},")
    lines += ["} as const;", "", "export type BseoAnnounceKey = keyof typeof BSEO_ANNOUNCES;", ""]
    MANIFEST.write_text("\n".join(lines), encoding="utf-8")
    print(f"안내 방송 {len(counts)}종 {sum(counts.values())}개 → {OUT.relative_to(ROOT)}")
    if missing:
        print("팬키트에 없는 것:", ", ".join(missing))
    if extra:
        print("표에 없는 파일 (안 씀):", ", ".join(extra))


if __name__ == "__main__":
    main(sys.argv[1:])
