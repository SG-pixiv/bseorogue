# SPDX-FileCopyrightText: 2026 SG
# SPDX-License-Identifier: AGPL-3.0-only
"""
이터널 리턴 게임 소리를 블서로그 자리에 넣기 (11-18 SG: "사운드는 사용해도돼")

소리는 SG PC 의 이터널 리턴 설치 폴더에서 AnimeStudio 로 꺼낸 것이에요 (docs/이어서-할-일.md 4-24).
  1. AnimeStudio(Escartem) → Options › Export options 에서 "Convert AudioClip to WAV" 끄기
  2. File › Load file → `EternalReturn_Data/data.unity3d` (8GB, 몇 분 걸려요. 임시 파일은 게임 폴더 옆에 생겨요)
  3. Filter Type › AudioClip → Export › Filtered assets → 빈 폴더 (예: E:\\다운로드\\er-sound)
     → `sound/{bgm,ui,fx,voice}/…/<이름>.fsb` 로 1만 8천 개쯤 나와요 (container path 로 묶음)

  python3 -I -B scripts/sound/build_er_sound.py <꺼낸 폴더>        → 아래 표대로 만들기 (UnityPy 필요: pip install UnityPy)
  python3 -I -B scripts/sound/build_er_sound.py --list             → 표만 보기 (자리 · 원본 · 어디서)

만드는 것 (전부 assets/er/ 아래 = 님블뉴런 저작물, AGPL 아님):
  - assets/er/audio/{ui,se,battle_anims}/<이름>.wav   효과음 (32kHz 모노 16비트, 앞 무음 자르기 · 길이 자르기 · 크기 맞추기)
  - assets/er/audio/bgm/<이름>.mp3                    BGM (스테레오 96kbps, 크기 −15 LUFS)
  - assets/er/sfx/<ER번호>_<q|w|e|r>.m4a              실험체 스킬 효과음 (AAC 모노 64kbps, 2.2초까지)
  - src/data/bseorogue/er-sound-manifest.ts           게임이 읽는 목록 (자동 생성)
  - assets/er/sound-sources.json                      자리마다 어느 게임 소리로 만들었는지

직접 합성한 효과음(scripts/sound/make_sfx.py → assets/audio/)은 지우지 않고 예비로 둬요.
여기 표에서 한 줄을 빼면 그 자리는 다시 합성 소리가 나와요.
"""

from __future__ import annotations

import io
import json
import re
import subprocess
import sys
import tempfile
import wave
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[2]
ER = ROOT / "assets" / "er"
MANIFEST = ROOT / "src" / "data" / "bseorogue" / "er-sound-manifest.ts"
SOURCES = ER / "sound-sources.json"

# ── 효과음 표: 게임 소리 파일(assets/audio 기준) → (게임 소리, 최대 길이 초, 어디서) ──────────
SFX: dict[str, tuple[str, float, str]] = {
    "ui/select.wav": ("sound/ui/oui_tabclick", 0.4, "버튼 · 칸 고르기"),
    "ui/menu_open.wav": ("sound/ui/oui_windowopen", 0.6, "메뉴 · 창 열기"),
    "ui/error.wav": ("sound/ui/cannotdeploy", 0.8, "안 되는 칸을 눌렀을 때"),
    "se/hit.wav": ("sound/fx/common/hit_punch", 0.6, "스킬에 맞을 때 (보통)"),
    "se/hit_strong.wav": ("sound/fx/common/hitskilltwohandsword_r1", 1.3, "스킬에 크게 맞을 때"),
    "se/hit_weak.wav": ("sound/fx/common/hitskillhammer_r1", 0.5, "스킬에 약하게 맞을 때"),
    "se/faint.wav": ("sound/fx/common/death", 1.8, "실험체가 쓰러질 때"),
    "se/flee.wav": ("sound/fx/common/tacticalskill_blink", 1.2, "도망칠 때"),
    "se/exp.wav": ("sound/ui/autodisintegratecountup", 1.0, "경험치 막대가 찰 때"),
    "se/level_up.wav": ("sound/ui/skillup", 1.5, "레벨이 오를 때"),
    "se/level_up_fanfare.wav": ("sound/ui/oui_levelup_v1", 1.7, "레벨업 · 해금 팡파르"),
    "se/item_fanfare.wav": ("sound/ui/oui_reward_v1", 1.3, "아이템 · 보상을 받을 때"),
    "se/stat_up.wav": ("sound/ui/researchupgrade", 1.2, "능력이 오를 때"),
    "se/stat_down.wav": ("sound/ui/tierchange_demotion", 2.0, "능력이 내려갈 때"),
    "se/restore.wav": ("sound/ui/consume_drink_1", 0.9, "회복 아이템 · 체력 회복"),
    "se/low_hp.wav": ("sound/ui/minimap_under_attack", 1.2, "체력이 적을 때 경고음"),
    "se/sparkle.wav": ("sound/ui/infusion_highlight", 0.4, "반짝일 때"),
    "se/shine.wav": ("sound/ui/equipmentinstall_legend", 2.0, "진화 · 모습이 바뀔 때 빛"),
    "se/shing.wav": ("sound/ui/skilllvupopen", 0.9, "짧은 반짝 쇳소리 (잠재력 · 사탕 막대)"),
    "se/charge.wav": ("sound/ui/disintegratestart", 3.0, "진화 전에 힘 모으기"),
    "se/beam.wav": ("sound/ui/skillevoupopen", 1.2, "진화 · 모습 바뀌는 순간"),
    "se/upgrade.wav": ("sound/ui/equipmentinstall_epic", 1.4, "보상 등급이 오를 때 · 잠금 풀기"),
    "se/buy.wav": ("sound/ui/infusion_buy", 1.0, "상점에서 살 때"),
    "se/achv.wav": ("sound/ui/oui_seasoncollection_completed", 2.5, "업적 달성"),
    "se/pb_throw.wav": ("sound/fx/common/attackthrow", 0.4, "영입 볼을 던질 때"),
    "se/pb_rel.wav": ("sound/ui/boxopen", 0.7, "볼이 열릴 때 · 실험체가 나올 때"),
    "se/pb_bounce_1.wav": ("sound/ui/card_flip_start", 0.5, "볼이 튈 때 · 보상 칸 뒤집기"),
    "se/pb_bounce_2.wav": ("sound/ui/dropitem", 0.3, "볼이 튈 때 (낮은 톡)"),
    "se/pb_move.wav": ("sound/fx/common/kiosk_panelrattle", 0.6, "볼 · 보급 상자가 흔들릴 때"),
    "se/pb_catch.wav": ("sound/ui/mission_completed_minor", 1.0, "영입 성공"),
    "se/pb_lock.wav": ("sound/ui/mark_select", 0.8, "볼이 잠길 때"),
    "se/crit_throw.wav": ("sound/fx/common/throw_weapon_fire", 1.5, "영입 볼이 크게 날아갈 때"),
    "se/pb_tray_enter.wav": ("sound/ui/oui_modeslideopen_v1", 0.3, "남은 볼 줄이 들어올 때"),
    "se/pb_tray_ball.wav": ("sound/ui/pickupitem", 0.3, "볼 줄에 볼 하나"),
    "se/pb_tray_empty.wav": ("sound/ui/oui_btnclick_v1", 0.2, "볼 줄에 빈칸 하나"),
    "se/egg_crack.wav": ("sound/fx/common/opensound_box_01", 0.8, "보급 상자에 금이 갈 때"),
    "se/egg_hatch.wav": ("sound/ui/lootbox_basic_start", 3.0, "보급 상자가 열릴 때"),
    "se/gacha_dial.wav": ("sound/ui/autodisintegratecounter", 0.7, "보급 요청 손잡이 돌리기"),
    "se/gacha_running.wav": ("sound/fx/common/kiosk_ing", 1.3, "보급 요청 기계가 돌아갈 때"),
    "se/gacha_dispense.wav": ("sound/fx/common/mobilekiosk_createbox_sfx", 2.4, "보급 상자가 나올 때"),
    "battle_anims/bseo-slash.wav": ("sound/fx/common/skillonehandsword", 1.0, "스킬 연출: 베기 (실험체 스킬 소리가 없을 때)"),
    "battle_anims/bseo-strike.wav": ("sound/fx/common/skillhammer", 0.9, "스킬 연출: 타격"),
    "battle_anims/bseo-shot.wav": ("sound/fx/common/skillpistol_v1", 0.9, "스킬 연출: 투사체"),
    "battle_anims/bseo-blast.wav": ("sound/fx/common/battlezoneobject_explode", 1.7, "스킬 연출: 폭발"),
    "battle_anims/bseo-heal.wav": ("sound/fx/common/selfcure_start", 1.2, "스킬 연출: 회복"),
    "battle_anims/bseo-buff.wav": ("sound/fx/common/itemskill_alacrity_buff", 1.1, "스킬 연출: 강화"),
    "battle_anims/bseo-debuff.wav": ("sound/fx/common/infusion_ephemeralnightmare_debuff", 1.8, "스킬 연출: 약화"),
}

# ── BGM 표: 게임 BGM 열쇠 → (파일 이름, [게임 곡, …], 어디서). 곡이 둘이면 첫 곡 뒤에 둘째 곡이 반복돼요 ──
LOOP_A, LOOP_B, LOOP_C = "sound/bgm/p2-1", "sound/bgm/p2-2", "sound/bgm/p1"
BGM: dict[str, tuple[str, list[str], str]] = {
    "title": ("title", ["sound/bgm/bgm_lobby"], "타이틀 화면"),
    "menu": ("menu", ["sound/bgm/bser_bgm_strategymap_lumia"], "시작 실험체 고르기 · 메뉴"),
    "battle_wild": ("battle_wild", ["sound/bgm/p0"], "1~4웨이브 전투"),
    "battle_trainer": ("battle_trainer", ["sound/bgm/p3"], "팀 전투 (마스터즈 · KEL 팀)"),
    "bseo_leader": ("bseo_leader", ["sound/bgm/endgame_bgm_a"], "관장 전투"),
    "bseo_final": ("bseo_final", ["sound/bgm/endgame_bgm_b"], "50웨이브 최종 보스"),
    "bw/victory_trainer": ("victory", ["sound/bgm/victorycutscene_bgm"], "팀 · 관장 전투 이겼을 때"),
    "bw/heal": ("heal", ["sound/fx/common/revival"], "전원 회복할 때"),
    "bw/evolution": ("evolution", ["sound/bgm/bgm_lobby_seasonreward_v1"], "스킨 진화하는 동안"),
    "bw/evolution_fanfare": ("evolution_fanfare", ["sound/ui/resultvictory"], "스킨 진화 끝"),
    "bw/minor_fanfare": ("minor_fanfare", ["sound/ui/oui_reward_v1"], "작은 팡파르"),
}
# 지역: 블서로그 지역 → (ER 지역 곡, 뒤에 반복할 곡). 지역 곡은 20초쯤이라 그 뒤로 전투 곡이 반복돼요
AREA: dict[str, tuple[str, str, str]] = {
    "alley": ("alley", LOOP_A, "골목길"),
    "archery": ("archery", LOOP_B, "양궁장"),
    "stream": ("forest", LOOP_C, "개울"),
    "forest": ("forest", LOOP_C, "숲"),
    "uptown": ("uptown", LOOP_A, "고급 주택가"),
    "harbor": ("harbor", LOOP_B, "항구"),
    "pond": ("pond", LOOP_C, "연못"),
    "beach": ("sandybeach", LOOP_A, "모래사장"),
    "temple": ("temple", LOOP_B, "절"),
    "gasStation": ("downtown", LOOP_C, "주유소"),
    "warehouse": ("factory", LOOP_A, "창고"),
    "school": ("school", LOOP_B, "학교"),
    "factory": ("factory", LOOP_A, "공장"),
    "fireStation": ("downtown", LOOP_C, "소방서"),
    "cemetery": ("cemetery", LOOP_A, "묘지"),
    "police": ("downtown", LOOP_C, "경찰서"),
    "chapel": ("church", LOOP_B, "성당"),
    "hospital": ("hospital", LOOP_C, "병원"),
    "lab": ("laboratory", LOOP_A, "연구소"),
    "barge": ("harbor", LOOP_B, "바지선"),
    "hotel": ("hotel", LOOP_C, "호텔"),
}
# 포켓로그 바이옴 열쇠 → 블서로그 지역 (src/data/bseorogue/regions.ts 와 같게)
BIOME_AREA: dict[str, str] = {
    "town": "alley", "slum": "alley", "plains": "archery", "grass": "stream", "tall_grass": "forest", "forest": "forest",
    "jungle": "forest", "snowy_forest": "hotel", "metropolis": "uptown", "sea": "harbor", "seabed": "barge",
    "swamp": "pond", "lake": "pond", "beach": "beach", "desert": "beach", "island": "beach", "mountain": "temple",
    "temple": "temple", "badlands": "gasStation", "cave": "warehouse", "ice_cave": "warehouse", "meadow": "school",
    "power_plant": "factory", "factory": "factory", "construction_site": "factory", "volcano": "fireStation",
    "graveyard": "cemetery", "wasteland": "cemetery", "dojo": "police", "ruins": "chapel", "fairy_cave": "hospital",
    "abyss": "lab", "space": "lab", "laboratory": "lab", "end": "lab",
}

# ── 실험체 스킬 효과음: 파일 이름에 skill01~04 가 들어간 것 중 시전 소리 > 맞는 소리 순 ──
SKIP = re.compile(r"charg|loop|ready|aim|maintain|_end|move|jump(ing)?$|idle|cancel|_s$|_s_|wait|target_scan|drone_scan"
                  r"|detected|count|projectilesound|_in(_|$)|evo")
CAST = [("attack", 6), ("fire", 6), ("shot", 6), ("swing", 6), ("throw", 5), ("activation", 5), ("active", 5),
        ("cast", 5), ("start", 4), ("effect", 3), ("on", 2)]
HIT = [("hit", 6), ("explode", 6), ("impact", 6), ("bump", 4), ("collision", 4), ("boom", 5)]
SKILL_MAX = 2.2
# 이름 규칙으로는 못 고르는 자리 (게임에 시전 소리가 따로 없거나 빈 파일이에요): (ER 번호, 키) → sound/fx/ 아래 폴더
SKILL_OVERRIDE = {
    (1, "q"): "jackie/s003/skilldualsword_1",  # 재키 Q: 무기 공용 소리를 써서 재키 폴더의 쌍검 스킬 소리
    (3, "e"): "fiora/s000/fiora_skill03_move",  # 피오라 E: 돌진 소리뿐
    (32, "e"): "william/s000/william_skill03_move",  # 윌리엄 E: 달리기 소리뿐
    (34, "w"): "nathapon/s000/nathapon_skill02_active",  # 나타폰 W: attack 은 빈 파일
    (65, "e"): "debimarlene/s000/debi_skill03_dash",  # 데비&마를렌 E: attack 은 빈 파일
}


# ── 소리 다루기 ─────────────────────────────────────


def find_src(root: Path, container: str) -> Path | None:
    """container 경로(소문자) → 꺼낸 폴더의 .fsb 또는 .wav 파일"""
    d = root / container
    for ext in ("*.fsb", "*.wav"):
        hit = sorted(d.glob(ext)) if d.is_dir() else []
        if hit:
            return hit[0]
    return None


def decode(path: Path) -> tuple[np.ndarray, int]:
    """(float32 [n, 채널], 샘플레이트)"""
    data = path.read_bytes()
    if path.suffix.lower() == ".fsb":
        import fmod_toolkit  # UnityPy 와 같이 깔려요

        data = next(iter(fmod_toolkit.raw_to_wav(data, path.stem, 2, 44100).values()))
    with wave.open(io.BytesIO(data)) as w:
        sr, ch, sw, n = w.getframerate(), w.getnchannels(), w.getsampwidth(), w.getnframes()
        raw = w.readframes(n)
    if sw == 2:
        x = np.frombuffer(raw, "<i2").astype(np.float32) / 32768
    elif sw == 4:
        x = np.frombuffer(raw, "<f4").astype(np.float32)
    else:
        raise ValueError(f"{path}: {sw * 8}비트 wav")
    return x.reshape(-1, ch), sr


def tidy(x: np.ndarray, sr: int, max_len: float, lead_db: float = -45.0) -> np.ndarray:
    """앞 무음 자르기 · 끝 무음 자르기 · 최대 길이(넘으면 끝을 짧게 줄여 끄기)"""
    a = np.abs(x).max(axis=1)
    on = np.where(a > 10 ** (lead_db / 20))[0]
    if len(on) == 0:
        return x[:1]
    x = x[max(0, on[0] - int(0.005 * sr)) : on[-1] + int(0.02 * sr)]
    if len(x) > max_len * sr:
        x = x[: int(max_len * sr)].copy()
        fade = int(min(0.15, max_len / 4) * sr)
        x[-fade:] *= np.linspace(1, 0, fade)[:, None]
    tail = min(len(x), int(0.01 * sr))
    x[-tail:] *= np.linspace(1, 0, tail)[:, None]
    return x


def level(x: np.ndarray, sr: int, target_db: float = -16.0, peak_db: float = -1.0, max_gain_db: float = 18.0) -> np.ndarray:
    """가장 큰 0.1초 RMS 를 목표에 맞추고, 끝값이 넘치지 않게"""
    m = x.mean(axis=1)
    win = max(1, int(0.1 * sr))
    if len(m) <= win:
        rms = float(np.sqrt(np.mean(m**2)) + 1e-9)
    else:
        c = np.cumsum(np.concatenate([[0.0], m.astype(np.float64) ** 2]))
        rms = float(np.sqrt((c[win:] - c[:-win]).max() / win) + 1e-9)
    g = min(10 ** (max_gain_db / 20), 10 ** (target_db / 20) / rms)
    peak = np.abs(x).max() * g
    if peak > 10 ** (peak_db / 20):
        g *= 10 ** (peak_db / 20) / peak
    return x * g


def write_wav(path: Path, x: np.ndarray, sr: int) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    y = (np.clip(x, -1, 1) * 32767).astype("<i2")
    with wave.open(str(path), "wb") as w:
        w.setnchannels(x.shape[1])
        w.setsampwidth(2)
        w.setframerate(sr)
        w.writeframes(y.tobytes())


def ffmpeg(src: Path, dst: Path, *args: str) -> None:
    dst.parent.mkdir(parents=True, exist_ok=True)
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", str(src), *args, str(dst)], check=True)


def duration(path: Path) -> float:
    out = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", str(path)],
                         capture_output=True, text=True, check=True).stdout
    return round(float(out), 3)


# ── 스킬 소리 고르기 ───────────────────────────────


def score(name: str, table: list[tuple[str, int]]) -> int:
    return max((w for tok, w in table if re.search(rf"(^|_){tok}(_|\d|$)", name)), default=0)


def pick_skill(root: Path, fx: str) -> dict[str, Path]:
    """실험체 폴더(sound/fx/<이름>) → {q|w|e|r: 파일}. 기본 모습(s000)부터 봐요"""
    base = root / "sound" / "fx" / fx
    if not base.is_dir():
        return {}
    out: dict[str, Path] = {}
    for n, key in enumerate("qwer", start=1):
        tag = re.compile(rf"skill0?{n}(?!\d)")
        for skin in sorted(p for p in base.iterdir() if p.is_dir()):
            names = [p.name for p in skin.iterdir() if p.is_dir() and tag.search(p.name) and not SKIP.search(p.name)]
            cast = [(score(nm, CAST), -len(nm), nm) for nm in names if score(nm, CAST) and not score(nm, HIT)]
            hit = [(score(nm, HIT), -len(nm), nm) for nm in names if score(nm, HIT)]
            best = max(cast)[2] if cast else max(hit)[2] if hit else min(names, key=len) if names else None
            src = find_src(root, f"sound/fx/{fx}/{skin.name}/{best}") if best else None
            if src and src.stat().st_size > 1024:
                out[key] = src
                break
    return out


def er_characters() -> dict[int, str]:
    """ER 번호 → 소리 폴더 이름 (er-data.ts 의 영어 이름을 소문자로)"""
    src = (ROOT / "src" / "data" / "bseorogue" / "er-data.ts").read_text(encoding="utf-8")
    return {int(code): en.lower() for code, en in re.findall(r'\n  "(\d+)": \{\n    name: "[^"]+",\n    en: "([^"]+)"', src)}


# ── 만들기 ─────────────────────────────────────────


def build(root: Path) -> None:
    sources: dict[str, dict] = {"sfx": {}, "bgm": {}, "skill": {}}
    sfx_files: dict[str, str] = {}
    for key, (cont, max_len, where) in SFX.items():
        src = find_src(root, cont)
        if not src:
            print("없음", key, cont)
            continue
        x, sr = decode(src)
        x = level(tidy(x.mean(axis=1, keepdims=True), sr, max_len), sr)
        with tempfile.TemporaryDirectory() as tmp:
            raw = Path(tmp) / "a.wav"
            write_wav(raw, x, sr)
            dst = ER / "audio" / key
            ffmpeg(raw, dst, "-ar", "32000", "-ac", "1", "-c:a", "pcm_s16le")
        sfx_files[key] = f"er/audio/{key}"
        sources["sfx"][key] = {"from": cont, "where": where, "sec": duration(dst)}

    bgm_files: dict[str, str] = {}
    loops: dict[str, float] = {}
    jobs: list[tuple[str, str, list[str], str]] = [(k, f, srcs, w) for k, (f, srcs, w) in BGM.items()]
    area_file: dict[str, str] = {}
    for area, (stinger, loop, name) in AREA.items():
        file = f"area_{stinger}_{loop.rsplit('/', 1)[1].replace('-', '')}"
        area_file[area] = file
        if all(j[1] != file for j in jobs):
            jobs.append((f"area:{area}", file, [f"sound/bgm/bser_areabgm_{stinger}", loop], name))
    made: dict[str, float] = {}
    for key, file, conts, where in jobs:
        parts = []
        sr0 = None
        for cont in conts:
            src = find_src(root, cont)
            if not src:
                raise SystemExit(f"BGM 원본 없음: {cont}")
            x, sr = decode(src)
            if x.shape[1] == 1:
                x = np.repeat(x, 2, axis=1)
            if sr0 and sr != sr0:  # 샘플레이트가 다르면 첫 곡에 맞춰요
                idx = np.linspace(0, len(x) - 1, int(len(x) * sr0 / sr))
                x = np.stack([np.interp(idx, np.arange(len(x)), x[:, c]) for c in range(2)], axis=1).astype(np.float32)
                sr = sr0
            sr0 = sr
            parts.append(x)
        loop_at = 0.0
        if len(parts) == 2:  # 지역 곡: 끝 무음은 자르고 0.25초 쉬었다가 반복 곡
            first = tidy(parts[0], sr0, 999, lead_db=-60)
            gap = np.zeros((int(0.25 * sr0), 2), np.float32)
            loop_at = round((len(first) + len(gap)) / sr0, 3)
            x = np.concatenate([first, gap, parts[1]])
        else:
            x = parts[0]
        with tempfile.TemporaryDirectory() as tmp:
            raw = Path(tmp) / "a.wav"
            write_wav(raw, x, sr0)
            dst = ER / "audio" / "bgm" / f"{file}.mp3"
            ffmpeg(raw, dst, "-af", "loudnorm=I=-15:TP=-1.5:LRA=11", "-ar", "44100", "-c:a", "libmp3lame", "-b:a", "96k")
        made[file] = loop_at
        sources["bgm"][file] = {"from": conts, "where": where, "sec": duration(dst), "loop": loop_at}
        if not key.startswith("area:"):
            bgm_files[key] = f"er/audio/bgm/{file}.mp3"
            if loop_at:
                loops[key] = loop_at
    for biome, area in BIOME_AREA.items():
        bgm_files[biome] = f"er/audio/bgm/{area_file[area]}.mp3"
        loops[biome] = made[area_file[area]]

    skill: dict[int, str] = {}
    for code, fx in sorted(er_characters().items()):
        picked = pick_skill(root, fx)
        for (c, key), path in SKILL_OVERRIDE.items():
            src = find_src(root, f"sound/fx/{path}") if c == code and key not in picked else None
            if src:
                picked[key] = src
        for key, src in sorted(picked.items(), key=lambda kv: "qwer".index(kv[0])):
            x, sr = decode(src)
            x = level(tidy(x.mean(axis=1, keepdims=True), sr, SKILL_MAX), sr)
            with tempfile.TemporaryDirectory() as tmp:
                raw = Path(tmp) / "a.wav"
                write_wav(raw, x, sr)
                dst = ER / "sfx" / f"{code}_{key}.m4a"
                ffmpeg(raw, dst, "-ac", "1", "-c:a", "aac", "-b:a", "64k")
            skill[code] = skill.get(code, "") + key
            sources["skill"][f"{code}_{key}"] = str(src.parent.relative_to(root)).replace("\\", "/")

    write_manifest(sfx_files, bgm_files, loops, skill)
    SOURCES.write_text(json.dumps(sources, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    print(f"효과음 {len(sfx_files)} · BGM 파일 {len(made)} (열쇠 {len(bgm_files)}) · 스킬 소리 {sum(map(len, skill.values()))}개 ({len(skill)}명)")


def write_manifest(sfx: dict[str, str], bgm: dict[str, str], loops: dict[str, float], skill: dict[int, str]) -> None:
    def obj(d: dict) -> str:
        return "{\n" + "".join(f"  {json.dumps(str(k)) if not isinstance(k, int) else k}: {json.dumps(v)},\n" for k, v in d.items()) + "}"

    MANIFEST.write_text(
        f"""/*
 * SPDX-FileCopyrightText: 2026 SG
 * SPDX-License-Identifier: AGPL-3.0-only
 */

// 이 파일은 scripts/sound/build_er_sound.py 가 만들어요. 직접 고치지 마세요.
// 소리 파일(assets/er/audio · assets/er/sfx)은 이터널 리턴 게임 소리예요 (님블뉴런 저작물).

/** 효과음: assets/audio 기준 파일 → 대신 받을 파일 (assets 기준). 여기 없는 소리는 원래 파일(합성 소리 등) */
export const ER_SOUND_FILES: Readonly<Record<string, string>> = {obj(sfx)};

/** BGM 열쇠 → 파일 (assets 기준). 지역(바이옴 열쇠)은 지역 곡 + 반복 곡 */
export const ER_BGM_FILES: Readonly<Record<string, string>> = {obj(bgm)};

/** BGM 반복 시작점 (초). 곡이 끝나면 여기로 돌아가요. 없으면 처음부터 */
export const ER_BGM_LOOP: Readonly<Record<string, number>> = {obj(loops)};

/** 실험체 스킬 효과음이 있는 키 (ER 번호 → "qwer" 중 있는 것). 파일: er/sfx/<ER번호>_<키>.m4a */
export const ER_SKILL_SFX: Readonly<Record<number, string>> = {obj(skill)};
""",
        encoding="utf-8",
    )


def main() -> None:
    if len(sys.argv) > 1 and sys.argv[1] == "--list":
        for k, (c, _, w) in SFX.items():
            print(f"{k}\t{c}\t{w}")
        for k, (f, c, w) in BGM.items():
            print(f"bgm:{k}\t{' + '.join(c)}\t{w}")
        for a, (s, l, w) in AREA.items():
            print(f"bgm:지역 {a}\tbser_areabgm_{s} + {l}\t{w}")
        return
    if len(sys.argv) != 2:
        raise SystemExit(__doc__)
    build(Path(sys.argv[1]))


if __name__ == "__main__":
    main()
