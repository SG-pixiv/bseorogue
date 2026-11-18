# SPDX-FileCopyrightText: 2026 SG
# SPDX-License-Identifier: AGPL-3.0-only
"""
블서로그 사운드 목록 페이지 만들기 (SG에게 보내는 "어디에 어떤 소리" 페이지)

게임에 들어간 소리를 모아서 한 장짜리 HTML 페이지(재생 버튼 · 파형 · 어디서 나는지 · 출처)로 만들어요.
  - 이터널 리턴 게임: 효과음 · BGM · 실험체 스킬 소리 (scripts/sound/build_er_sound.py → assets/er/sound-sources.json)
  - 팬키트:    안내 방송 assets/er/announce/ (assets/er/announce-sources.json) · 실험체 음성 몇 개 예시
  - 직접 합성: scripts/sound/make_sfx.py --list 의 효과음 중 게임 소리가 없는 자리 (assets/audio/...)

  python3 -I -B scripts/sound/sound_page.py <출력 폴더>
    → <출력 폴더>/index.html + <출력 폴더>/sounds/... (재생용 소리 복사본)
  그다음 그 폴더를 artifact 로 올려요 (사운드 목록 페이지 주소는 docs/이어서-할-일.md 4-23 · 4-24).
필요한 것: ffmpeg (m4a · mp3 파형 읽기)
"""

import json
import re
import shutil
import subprocess
import sys
import wave
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[2]
ASSETS = ROOT / "assets"
TEMPLATE = Path(__file__).resolve().parent / "sound_page.tmpl"  # HTML 틀 (biome 검사를 피하려고 .tmpl)
PEAKS = 56

GROUPS = [
    ("ui", "버튼 · 메뉴"),
    ("battle", "전투"),
    ("grow", "성장 · 보상 · 상점"),
    ("light", "빛 · 진화"),
    ("ball", "영입 볼"),
    ("box", "보급 상자"),
    ("skill", "스킬 연출"),
    ("skillsfx", "실험체 스킬 소리 (예시)"),
    ("announce", "안내 방송"),
    ("voice", "실험체 음성 (예시)"),
]
SOURCES = {"ost": "이터널 리턴 게임", "fankit": "팬키트", "synth": "직접 합성"}

BATTLE = {"hit", "hit_strong", "hit_weak", "faint", "flee", "low_hp"}
LIGHT = {"sparkle", "shine", "shing", "charge", "beam"}

# 실험체 음성 예시: (ER 번호, 이름, 키, 설명)
VOICE_SAMPLES = [
    (30, "일레븐", "select", "실험체가 나올 때 · 고를 때 (등장 대사)"),
    (30, "일레븐", "q", "스킬 Q 를 쓸 때"),
    (30, "일레븐", "die", "쓰러질 때"),
    (11, "유키", "r", "스킬 R 를 쓸 때"),
]

# 실험체 스킬 소리 예시 (ER 번호). 전부는 87명 343개라 몇 명만
SKILL_SAMPLES = [1, 2, 7, 11, 21, 30, 33, 64]
ER_SOURCES = ASSETS / "er" / "sound-sources.json"


def group_of(path: str) -> str:
    folder, name = path.split("/", 1)
    name = name.removesuffix(".wav")
    if folder == "ui":
        return "ui"
    if folder == "battle_anims":
        return "skill"
    if name in BATTLE:
        return "battle"
    if name in LIGHT:
        return "light"
    if name.startswith(("pb_", "crit_")):
        return "ball"
    if name.startswith(("egg_", "gacha_")):
        return "box"
    return "grow"


def samples(path: Path) -> tuple[np.ndarray, float]:
    """소리 → (−1~1 배열, 길이 초)"""
    if path.suffix == ".wav":
        with wave.open(str(path)) as w:
            sr = w.getframerate()
            raw = w.readframes(w.getnframes())
            a = np.frombuffer(raw, np.int16).astype(np.float32) / 32768
            if w.getnchannels() > 1:
                a = a.reshape(-1, w.getnchannels()).mean(axis=1)
            return a, len(a) / sr
    raw = subprocess.run(
        ["ffmpeg", "-v", "error", "-i", str(path), "-ac", "1", "-ar", "22050", "-f", "f32le", "-"],
        capture_output=True,
        check=True,
    ).stdout
    a = np.frombuffer(raw, np.float32)
    return a, len(a) / 22050


def peaks(a: np.ndarray) -> list[float]:
    if len(a) == 0:
        return [0.0] * PEAKS
    chunks = np.array_split(np.abs(a), PEAKS)
    p = np.array([c.max() if len(c) else 0.0 for c in chunks])
    top = p.max() or 1.0
    return [round(float(x / top), 3) for x in p]


def entry(group: str, where: str, file: Path, out: Path, source: str, **extra) -> dict:
    rel = file.relative_to(ASSETS).as_posix()
    # 페이지에 올릴 때 m4a 는 받아 주지 않아서 mp3 로 바꿔 넣어요 (게임 파일은 그대로 m4a)
    page_rel = rel.removesuffix(".m4a") + ".mp3" if rel.endswith(".m4a") else rel
    dst = out / "sounds" / page_rel
    dst.parent.mkdir(parents=True, exist_ok=True)
    if page_rel == rel:
        shutil.copyfile(file, dst)
    else:
        subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", str(file), "-c:a", "libmp3lame", "-b:a", "64k", str(dst)], check=True)
    a, dur = samples(file)
    return {
        "group": group,
        "where": where,
        "file": f"assets/{rel}",
        "src": f"sounds/{page_rel}",
        "dur": round(dur, 2),
        "source": source,
        "peaks": peaks(a),
        **extra,
    }


def main(argv: list[str]) -> None:
    if not argv:
        sys.exit(__doc__)
    out = Path(argv[0])
    if (out / "sounds").exists():
        shutil.rmtree(out / "sounds")
    out.mkdir(parents=True, exist_ok=True)
    rows: list[dict] = []

    listing = subprocess.run(
        [sys.executable, "-I", "-B", str(ROOT / "scripts" / "sound" / "make_sfx.py"), "--list"],
        capture_output=True,
        text=True,
        check=True,
    ).stdout
    er = json.loads(ER_SOURCES.read_text(encoding="utf-8")) if ER_SOURCES.exists() else {"sfx": {}, "bgm": {}, "skill": {}}
    for line in listing.splitlines():
        path, where = line.split("\t", 1)
        key = path if path.endswith(".wav") else f"{path}.wav"
        game = er["sfx"].get(key)
        if game:  # 이터널 리턴 게임 소리가 있으면 그것 (합성 소리는 예비)
            note = f"게임 소리 {game['from'].rsplit('/', 1)[1]}"
            rows.append(entry(group_of(path), where, ASSETS / "er" / "audio" / key, out, "ost", note=note))
        else:
            rows.append(entry(group_of(path), where, ASSETS / "audio" / key, out, "synth"))

    names = dict(re.findall(r'\n  "(\d+)": \{\n    name: "([^"]+)"', (ROOT / "src/data/bseorogue/er-data.ts").read_text(encoding="utf-8")))
    total = len(er["skill"])
    for code in SKILL_SAMPLES:
        for key in "qwer":
            if f"{code}_{key}" in er["skill"]:
                file = ASSETS / "er" / "sfx" / f"{code}_{key}.m4a"
                note = f"{total}개 중 예시 · 게임 소리 {er['skill'][f'{code}_{key}'].rsplit('/', 1)[1]}"
                rows.append(entry("skillsfx", f"{names[str(code)]}: 스킬 {key.upper()} 를 쓸 때", file, out, "ost", note=note))

    announce = json.loads((ASSETS / "er" / "announce-sources.json").read_text(encoding="utf-8"))
    # 게임에서 쓰는 방송 먼저, 안 쓰는 방송은 뒤에 (방송 내용을 제목으로)
    for key, info in sorted(announce.items(), key=lambda kv: not kv[1]["scene"]):
        scene = info["scene"]
        same = f"같은 방송 {len(info['files'])}개 중 1"
        rows.append(
            entry(
                "announce",
                scene or f"방송: {info['what']}",
                ASSETS / "er" / "announce" / f"{key}_0.m4a",
                out,
                "fankit",
                note=f"방송: {info['what']} · {same}" if scene else same,
                unused=not scene,
            )
        )

    for code, name, key, where in VOICE_SAMPLES:
        file = ASSETS / "er" / "voice" / f"{code}_{key}_0.m4a"
        if file.exists():
            rows.append(entry("voice", f"{name}: {where}", file, out, "fankit", note="실험체 음성 (90명 1,595개 중 예시)"))

    bgm = []
    for name, info in er["bgm"].items():
        note = f"게임 곡 {' + '.join(c.rsplit('/', 1)[1] for c in info['from'])}"
        if info["loop"]:
            note += f" · {info['loop']:.1f}초부터 반복"
        bgm.append(entry("bgm", info["where"], ASSETS / "er" / "audio" / "bgm" / f"{name}.mp3", out, "ost", key=name, note=note))

    data = {"groups": GROUPS, "sources": SOURCES, "sfx": rows, "bgm": bgm}
    html = TEMPLATE.read_text(encoding="utf-8").replace("__DATA__", json.dumps(data, ensure_ascii=False))
    (out / "index.html").write_text(html, encoding="utf-8")
    counts = {s: sum(1 for r in rows if r["source"] == s) for s in SOURCES}
    print(f"소리 {len(rows)}줄 ({counts}) · BGM {sum(1 for b in bgm if not b.get('missing'))}/{len(bgm)} → {out}/index.html")


if __name__ == "__main__":
    main(sys.argv[1:])
