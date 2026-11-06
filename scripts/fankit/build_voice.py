# SPDX-FileCopyrightText: 2026 SG
# SPDX-License-Identifier: AGPL-3.0-only
"""
이터널 리턴 팬키트 음성 → 블서로그 스킬 · 등장 음성

팬키트 실험체 폴더의 "05. Voice Line/*.zip" 을 읽어서
  - 음성:      assets/er/voice/<ER번호>_<q|w|e|r|select>.m4a  (AAC · 모노 · 64kbps, 앞뒤 무음 자르기, 소리 크기 맞추기)
  - 목록:      src/data/bseorogue/voice-manifest.ts
  - 출처 기록: assets/er/voice-sources.json  (실험체마다 언어 · zip · 고른 파일)
를 만들어요.

- 언어는 한국어(KOR) > 영어(ENG) > 일본어(JPN) 순서로 하나만 써요.
- 스킬 키는 파일 이름에서 찾아요 (실험체마다 이름이 달라요):
    jackie_skillQ_1_ko.wav · aya_skillQ1_01.wav · Piolo_skillQ1-1_01.wav → q
    Bernice_PlaySkill1025200seq0_1_ko.wav → 10XX200 = q · 300 = w · 400 = e · 500 = r
    *_selected* → select (없으면 *_firstMove* 를 select 로)
  같은 키가 여러 개면 숫자가 가장 작은 것 (첫 번째 대사).
- 팬키트가 zip 17개로 나뉘어 있어서 기본은 **더하기**예요: 이미 만든 음성은 그대로 두고,
  더 좋은 언어가 생기면 그 실험체만 새로 만들고, 같은 언어면 빠진 키만 채워요.

쓰는 법:  python3 scripts/fankit/build_voice.py <팬키트 폴더> [<팬키트 폴더> ...]
          python3 scripts/fankit/build_voice.py --fresh <팬키트 폴더> ...   (전부 지우고 새로)
필요한 것: ffmpeg
검사:     python3 -m unittest discover -s scripts/fankit -p "test_*.py"
"""
import json
import re
import shutil
import subprocess
import sys
import tempfile
import zipfile
from pathlib import Path, PurePosixPath

sys.path.insert(0, str(Path(__file__).resolve().parent))
from build_art import er_characters, norm  # noqa: E402

ROOT = Path(__file__).resolve().parents[2]
OUT_DIR = ROOT / "assets/er/voice"
SOURCES = ROOT / "assets/er/voice-sources.json"
MANIFEST = ROOT / "src/data/bseorogue/voice-manifest.ts"

KEYS = ("q", "w", "e", "r", "select")
LANG_RANK = {"kor": 0, "eng": 1, "jpn": 2}
LANG_SHORT = {"kor": "ko", "eng": "en", "jpn": "ja"}
SKILL_DIGIT = {2: "q", 3: "w", 4: "e", 5: "r"}
# 스킬 대사가 없을 때 대신 쓰는 전투 대사 (앞의 것부터)
COMBAT = {"targeton": r"targeton", "attack": r"(^|_)attack(_|\d|$)", "killmonster": r"killmonster", "taunt": r"_taunt_?\d"}


def zip_lang(zip_name: str, members: list[str] | None = None) -> str | None:
    """zip 이름(없으면 안의 파일 끝 _ko · _en · _ja)으로 언어"""
    stem = Path(zip_name).stem.lower()
    for lang in LANG_RANK:
        if re.search(rf"(^|[^a-z]){lang}([^a-z]|$)", stem):
            return lang
    if members:
        tails = {"ko": "kor", "en": "eng", "ja": "jpn"}
        votes: dict[str, int] = {}
        for m in members:
            t = re.search(r"_(ko|en|ja)(?:_\d+)?$", PurePosixPath(m).stem.lower())
            if t:
                votes[tails[t.group(1)]] = votes.get(tails[t.group(1)], 0) + 1
        if votes:
            return max(votes, key=votes.get)
    return None


def clean_stem(name: str) -> str:
    """'036. magnus_firstMove_1_en.wav' → 'magnus_firstmove_1_en'"""
    stem = PurePosixPath(name.replace("\\", "/")).stem.lower().strip()
    return re.sub(r"^\d+\.\s*", "", stem)


def voice_key(name: str) -> str | None:
    """파일 이름 → q · w · e · r · passive · select · firstmove (모르면 None)"""
    stem = clean_stem(name)
    if "weaponskill" in stem:
        return None  # 무기 스킬 배우기 · 무기 스킬 (D) 는 안 써요
    m = re.search(r"playskill(\d{6,})", stem)
    if m:
        return SKILL_DIGIT.get(int(m.group(1)) // 100 % 10)
    m = re.search(r"useskillactive([1-4])", stem)  # 예전 실험체: useSkillActive1 = Q … 4 = R
    if m:
        return "qwer"[int(m.group(1)) - 1]
    m = re.search(r"skill(q|w|e|r|passive)", stem)
    if m:
        return m.group(1)
    if "selected" in stem:
        return "select"
    if "firstmove" in stem:
        return "firstmove"
    return None


def _order(name: str) -> tuple:
    stem = clean_stem(name)
    return (tuple(int(n) for n in re.findall(r"\d+", stem)), len(stem), stem)


def pick(names: list[str]) -> dict[str, str]:
    """zip 안 파일 이름들 → {키: 고른 파일}. 키마다 첫 번째 대사(숫자가 가장 작은 것)"""
    groups: dict[str, list[str]] = {}
    for n in names:
        if not n.lower().endswith((".wav", ".ogg", ".mp3", ".m4a")) or "__macosx" in n.lower():
            continue
        k = voice_key(n)
        if k:
            groups.setdefault(k, []).append(n)
    if "select" not in groups and "firstmove" in groups:
        groups["select"] = groups["firstmove"]
    chosen = {k: sorted(groups[k], key=_order)[0] for k in KEYS if k in groups}
    # 스킬 대사가 없는 실험체(예: 쇼이치)는 전투 대사로 채워요 (키마다 다른 대사)
    pool = [n for w in COMBAT for n in sorted((n for n in names if n.lower().endswith((".wav", ".ogg", ".mp3", ".m4a")) and "__macosx" not in n.lower() and re.search(COMBAT[w], clean_stem(n))), key=_order)]
    used = set(chosen.values())
    for k in ("q", "w", "e", "r"):
        if k not in chosen:
            n = next((n for n in pool if n not in used), None)
            if n:
                chosen[k] = n
                used.add(n)
    return {k: chosen[k] for k in KEYS if k in chosen}


def run(cmd: list[str]) -> str:
    out = subprocess.run(cmd, capture_output=True, text=True, check=True)
    return out.stderr


TRIM = (
    "silenceremove=start_periods=1:start_threshold=-45dB:start_silence=0.03,"
    "areverse,silenceremove=start_periods=1:start_threshold=-45dB:start_silence=0.08,areverse"
)


def convert(src: Path, dst: Path) -> None:
    """앞뒤 무음 자르기 + 소리 크기 맞추기(2번 재기) → m4a"""
    measured = run(["ffmpeg", "-nostdin", "-hide_banner", "-i", str(src), "-af", f"{TRIM},loudnorm=I=-18:TP=-1.5:LRA=11:print_format=json", "-f", "null", "-"])
    stats = json.loads(measured[measured.rindex("{") : measured.rindex("}") + 1])
    norm_filter = (
        "loudnorm=I=-18:TP=-1.5:LRA=11:linear=true"
        f":measured_I={stats['input_i']}:measured_TP={stats['input_tp']}"
        f":measured_LRA={stats['input_lra']}:measured_thresh={stats['input_thresh']}:offset={stats['target_offset']}"
    )
    if stats["input_i"] in ("-inf", "inf"):
        norm_filter = "anull"
    run(["ffmpeg", "-nostdin", "-hide_banner", "-v", "error", "-y", "-i", str(src), "-af", f"{TRIM},{norm_filter}", "-ac", "1", "-ar", "44100", "-c:a", "aac", "-b:a", "64k", "-movflags", "+faststart", str(dst)])


def find_zips(kits: list[str], names: dict[str, int]) -> tuple[dict[int, list[tuple[str, Path, str]]], set[str]]:
    """ER 번호 → [(언어, zip 경로, 팬키트 안 상대 경로)]"""
    found: dict[int, list[tuple[str, Path, str]]] = {}
    unknown: set[str] = set()
    for kit in kits:
        for path in sorted(Path(kit).rglob("*.zip")):
            rel = path.relative_to(kit)
            # "Voice Line" 폴더 (팬키트에 "Volce Line" 오타도 있어요) 또는 zip 이름에 언어 표시
            if not any(w in p.lower() for p in rel.parts[:-1] for w in ("voice", "volce")) and not zip_lang(path.name):
                continue
            m = re.match(r"\d+\.\s*(.+)", rel.parts[0])
            label = m.group(1) if m else rel.parts[0]
            code = names.get(norm(label))
            if code is None:
                unknown.add(label)
                continue
            with zipfile.ZipFile(path) as z:
                lang = zip_lang(path.name, z.namelist())
            if lang:
                found.setdefault(code, []).append((lang, path, str(rel).replace("\\", "/")))
    return found, unknown


def write_manifest(sources: dict) -> None:
    def lines(fn) -> str:
        return "\n".join(f"  {code}: {fn(sources[code])}," for code in sorted(sources, key=int))

    MANIFEST.write_text(
        "/*\n * SPDX-FileCopyrightText: 2026 SG\n * SPDX-License-Identifier: AGPL-3.0-only\n */\n\n"
        "// 이 파일은 scripts/fankit/build_voice.py 가 만들어요. 직접 고치지 마세요.\n"
        "// 음성 파일(assets/er/voice/)은 님블뉴런 팬키트에서 가져와 줄인 것이에요.\n\n"
        "/** 스킬 Q · W · E · R (skill-moves.ts 순서) · 등장 대사 */\n"
        'export type BseoVoiceKey = "q" | "w" | "e" | "r" | "select";\n\n'
        "/** 음성이 있는 실험체 (ER 번호 → 있는 음성). 파일: er/voice/<ER번호>_<키>.m4a */\n"
        f"export const BSEO_VOICES: Readonly<Record<number, readonly BseoVoiceKey[]>> = {{\n{lines(lambda s: json.dumps([k for k in KEYS if k in s['files']]))}\n}};\n\n"
        "/** 음성 언어 (ko 한국어 · en 영어 · ja 일본어) */\n"
        f'export const BSEO_VOICE_LANG: Readonly<Record<number, "ko" | "en" | "ja">> = {{\n{lines(lambda s: json.dumps(LANG_SHORT[s["lang"]]))}\n}};\n',
        encoding="utf-8",
    )


def main(argv: list[str]) -> None:
    fresh = "--fresh" in argv
    kits = [a for a in argv if a != "--fresh"]
    if shutil.which("ffmpeg") is None:
        sys.exit("ffmpeg 이 필요해요")
    names = er_characters()
    found, unknown = find_zips(kits, names)

    sources: dict[str, dict] = {}
    if not fresh and SOURCES.exists():
        sources = json.loads(SOURCES.read_text(encoding="utf-8"))
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    if fresh:
        for old in OUT_DIR.glob("*.m4a"):
            old.unlink()

    made = 0
    with tempfile.TemporaryDirectory(prefix="bseo-voice-") as tmp:
        for code, zips in sorted(found.items()):
            best_rank = min(LANG_RANK[z[0]] for z in zips)
            cands = [z for z in zips if LANG_RANK[z[0]] == best_rank]
            old = sources.get(str(code))
            old_rank = LANG_RANK.get(old["lang"], 9) if old else 99
            if best_rank > old_rank:
                continue  # 이미 더 좋은 언어가 있어요
            if best_rank < old_rank and old:
                for k in old["files"]:
                    (OUT_DIR / f"{code}_{k}.m4a").unlink(missing_ok=True)
                old = None
            entry = old or {"lang": cands[0][0], "zip": cands[0][2], "files": {}}
            for lang, zpath, zrel in cands:
                with zipfile.ZipFile(zpath) as z:
                    chosen = pick(z.namelist())
                    used = False
                    for key, member in chosen.items():
                        if key in entry["files"]:
                            continue
                        # zip 안 이름은 믿지 않고, 내용만 꺼내서 정해진 이름으로 써요
                        raw = Path(tmp) / f"{code}_{key}{PurePosixPath(member).suffix.lower()}"
                        raw.write_bytes(z.read(member))
                        convert(raw, OUT_DIR / f"{code}_{key}.m4a")
                        raw.unlink()
                        entry["files"][key] = PurePosixPath(member).name
                        used = True
                        made += 1
                    if used and zrel != entry["zip"] and zrel not in entry.get("more", []):
                        entry.setdefault("more", []).append(zrel)
            if entry["files"]:
                entry["files"] = {k: entry["files"][k] for k in KEYS if k in entry["files"]}
                sources[str(code)] = entry

    sources = dict(sorted(sources.items(), key=lambda kv: int(kv[0])))
    SOURCES.write_text(json.dumps(sources, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    write_manifest(sources)

    print(f"이번에 만든 음성 {made}개 · 음성이 있는 실험체 {len(sources)}명")
    for code, s in sources.items():
        missing = [k for k in KEYS if k not in s["files"]]
        print(f"  {code:>3} {s['lang'].upper()} {' '.join(s['files'])}" + (f"  (없음: {' '.join(missing)})" if missing else ""))
    if unknown:
        print("이름을 못 맞춘 폴더:", ", ".join(sorted(unknown)))


if __name__ == "__main__":
    if len([a for a in sys.argv[1:] if a != "--fresh"]) < 1:
        print(__doc__)
        sys.exit(1)
    main(sys.argv[1:])
