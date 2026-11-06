# SPDX-FileCopyrightText: 2026 SG
# SPDX-License-Identifier: AGPL-3.0-only
"""
이터널 리턴 팬키트 음성 → 블서로그 스킬 · 등장 · 쓰러질 때 음성

팬키트 실험체 폴더의 "05. Voice Line/*.zip" (새 실험체는 "05. Voice Line/KOR/*.wav" 낱개) 을 읽어서
  - 음성:      assets/er/voice/<ER번호>_<q|w|e|r|select|die>_<0|1|2>.m4a  (키마다 최대 3개 · AAC · 모노 · 64kbps,
               앞뒤 무음 자르기, 소리 크기 맞추기)
  - 목록:      src/data/bseorogue/voice-manifest.ts
  - 출처 기록: assets/er/voice-sources.json  (실험체마다 언어 · zip · 고른 파일)
를 만들어요.

- 언어는 한국어(KOR) > 영어(ENG) > 일본어(JPN) 순서로 하나만 써요.
- 스킬 키는 파일 이름에서 찾아요 (실험체마다 이름이 달라요):
    jackie_skillQ_1_ko.wav · aya_skillQ1_01.wav · Piolo_skillQ1-1_01.wav → q
    Bernice_PlaySkill1025200seq0_1_ko.wav → 10XX200 = q · 300 = w · 400 = e · 500 = r
    *_selected* → select (모자라면 *_firstMove* 로 채워요)
    *_die* → die (모자라면 *_killedCommon* · *_lost* 로 채워요, 보스 대사는 빼요)
  키마다 숫자가 작은 것부터 최대 3개 (게임에서 매번 다른 대사를 골라요).
  스킬 대사가 3개보다 적으면 전투 대사(targetOn · attack · killMonster · taunt_숫자)로 채워요.
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

KEYS = ("q", "w", "e", "r", "select", "die")
VARIANTS = 3  # 키마다 대사 수
# 등장: selected 먼저, 모자라면 첫 이동 대사
SELECT_POOL = (r"selected", r"firstmove")
# 쓰러질 때: die > killedCommon > 패배(lost). 보스 대사(newboss · 위클라인)는 빼요
DIE_POOL = (r"(^|_)die(_|\d|$)", r"killedcommon", r"(^|_)lost(_|\d|$)")
BOSS = r"newboss|wickeline|wickleline"
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


def pick(names: list[str]) -> dict[str, list[str]]:
    """zip 안 파일 이름들 → {키: [고른 파일 최대 3개]} (숫자가 작은 것부터, 키끼리 겹치지 않게)"""
    audio = sorted(
        {n for n in names if n.lower().endswith((".wav", ".ogg", ".mp3", ".m4a")) and "__macosx" not in n.lower()},
        key=_order,
    )
    chosen: dict[str, list[str]] = {k: [] for k in KEYS}
    used: set[str] = set()

    def take(key: str, cands: list[str], limit: int = VARIANTS) -> None:
        for n in cands:
            if len(chosen[key]) >= limit:
                return
            if n not in used:
                chosen[key].append(n)
                used.add(n)

    for k in ("q", "w", "e", "r"):
        take(k, [n for n in audio if voice_key(n) == k])
    take("select", [n for pat in SELECT_POOL for n in audio if re.search(pat, clean_stem(n))])
    take("die", [n for pat in DIE_POOL for n in audio if re.search(pat, clean_stem(n)) and not re.search(BOSS, clean_stem(n))])
    # 스킬 대사가 모자라면 전투 대사로 (키를 돌아가며 하나씩 → 모든 스킬이 먼저 1개씩)
    pool = [n for pat in COMBAT.values() for n in audio if re.search(pat, clean_stem(n))]
    for size in range(1, VARIANTS + 1):
        for k in ("q", "w", "e", "r"):
            take(k, pool, size)
    return {k: chosen[k] for k in KEYS if chosen[k]}


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


AUDIO = (".wav", ".ogg", ".mp3", ".m4a")


def find_zips(kits: list[str], names: dict[str, int]) -> tuple[dict[int, list[tuple[str, object, str]]], set[str]]:
    """ER 번호 → [(언어, 소리 묶음, 팬키트 안 상대 경로)]

    소리 묶음은 zip 경로(Path) 이거나, 낱개 파일 {이름: 경로} (새 실험체는 `05. Voice Line/KOR/*.wav` 처럼
    언어 폴더에 낱개로 들어 있고, zip 여러 개에 나뉘어 있어요 → 같은 실험체 · 언어는 하나로 모아요)
    """
    found: dict[int, list[tuple[str, object, str]]] = {}
    loose: dict[tuple[int, str], tuple[dict[str, Path], str]] = {}
    unknown: set[str] = set()

    def code_of(rel: Path) -> int | None:
        m = re.match(r"\d+\.\s*(.+)", rel.parts[0])
        label = m.group(1) if m else rel.parts[0]
        code = names.get(norm(label))
        if code is None:
            unknown.add(label)
        return code

    for kit in kits:
        for path in sorted(Path(kit).rglob("*")):
            if not path.is_file():
                continue
            rel = path.relative_to(kit)
            in_voice = any(w in p.lower() for p in rel.parts[:-1] for w in ("voice", "volce"))
            if path.suffix.lower() == ".zip":
                # "Voice Line" 폴더 (팬키트에 "Volce Line" 오타도 있어요) 또는 zip 이름에 언어 표시
                if not in_voice and not zip_lang(path.name):
                    continue
                code = code_of(rel)
                if code is None:
                    continue
                with zipfile.ZipFile(path) as z:
                    lang = zip_lang(path.name, z.namelist())
                if lang:
                    found.setdefault(code, []).append((lang, path, str(rel).replace("\\", "/")))
            elif path.suffix.lower() in AUDIO and in_voice and len(rel.parts) >= 3:
                lang = zip_lang(rel.parts[-2])  # 바로 위 폴더 이름 = 언어 (KOR · ENG · JPN)
                code = code_of(rel) if lang else None
                if code is None:
                    continue
                files, _ = loose.setdefault((code, lang), ({}, str(rel.parent).replace("\\", "/") + "/"))
                files.setdefault(path.name, path)
    for (code, lang), (files, rel) in sorted(loose.items()):
        found.setdefault(code, []).append((lang, files, rel))
    return found, unknown


class Bundle:
    """zip 이나 낱개 파일 묶음을 같은 모양으로 읽어요"""

    def __init__(self, src: object) -> None:
        self.zip = zipfile.ZipFile(src) if isinstance(src, Path) else None
        self.files: dict[str, Path] = {} if self.zip else dict(src)  # type: ignore[arg-type]

    def names(self) -> list[str]:
        return self.zip.namelist() if self.zip else sorted(self.files)

    def read(self, member: str) -> bytes:
        return self.zip.read(member) if self.zip else self.files[member].read_bytes()

    def __enter__(self) -> "Bundle":
        return self

    def __exit__(self, *exc: object) -> None:
        if self.zip:
            self.zip.close()


def write_manifest(sources: dict) -> None:
    def lines(fn) -> str:
        return "\n".join(f"  {code}: {fn(sources[code])}," for code in sorted(sources, key=int))

    def counts(s: dict) -> str:
        return "{ " + ", ".join(f"{k}: {len(s['files'][k])}" for k in KEYS if k in s["files"]) + " }"

    MANIFEST.write_text(
        "/*\n * SPDX-FileCopyrightText: 2026 SG\n * SPDX-License-Identifier: AGPL-3.0-only\n */\n\n"
        "// 이 파일은 scripts/fankit/build_voice.py 가 만들어요. 직접 고치지 마세요.\n"
        "// 음성 파일(assets/er/voice/)은 님블뉴런 팬키트에서 가져와 줄인 것이에요.\n\n"
        "/** 스킬 Q · W · E · R (skill-moves.ts 순서) · 등장 대사 · 쓰러질 때 대사 */\n"
        'export type BseoVoiceKey = "q" | "w" | "e" | "r" | "select" | "die";\n\n'
        "/** 음성이 있는 실험체 (ER 번호 → 키마다 대사 수). 파일: er/voice/<ER번호>_<키>_<0부터>.m4a */\n"
        f"export const BSEO_VOICES: Readonly<Record<number, Readonly<Partial<Record<BseoVoiceKey, number>>>>> = {{\n{lines(counts)}\n}};\n\n"
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
                    for f in OUT_DIR.glob(f"{code}_{k}_*.m4a"):
                        f.unlink()
                old = None
            entry = old or {"lang": cands[0][0], "zip": cands[0][2], "files": {}}
            for lang, zpath, zrel in cands:
                with Bundle(zpath) as z:
                    chosen = pick(z.names())
                    used = False
                    for key, members in chosen.items():
                        have = entry["files"].setdefault(key, [])
                        for member in members:
                            name = PurePosixPath(member.replace("\\", "/")).name
                            if len(have) >= VARIANTS or name in have:
                                continue
                            # zip 안 이름은 믿지 않고, 내용만 꺼내서 정해진 이름으로 써요
                            i = len(have)
                            raw = Path(tmp) / f"{code}_{key}_{i}{PurePosixPath(member).suffix.lower()}"
                            raw.write_bytes(z.read(member))
                            convert(raw, OUT_DIR / f"{code}_{key}_{i}.m4a")
                            raw.unlink()
                            have.append(name)
                            used = True
                            made += 1
                    if used and zrel != entry["zip"] and zrel not in entry.get("more", []):
                        entry.setdefault("more", []).append(zrel)
            if entry["files"]:
                entry["files"] = {k: entry["files"][k] for k in KEYS if entry["files"].get(k)}
                sources[str(code)] = entry

    sources = dict(sorted(sources.items(), key=lambda kv: int(kv[0])))
    SOURCES.write_text(json.dumps(sources, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    write_manifest(sources)

    print(f"이번에 만든 음성 {made}개 · 음성이 있는 실험체 {len(sources)}명")
    for code, s in sources.items():
        missing = [k for k in KEYS if k not in s["files"]]
        counts = " ".join(f"{k}{len(v)}" for k, v in s["files"].items())
        print(f"  {code:>3} {s['lang'].upper()} {counts}" + (f"  (없음: {' '.join(missing)})" if missing else ""))
    if unknown:
        print("이름을 못 맞춘 폴더:", ", ".join(sorted(unknown)))


if __name__ == "__main__":
    if len([a for a in sys.argv[1:] if a != "--fresh"]) < 1:
        print(__doc__)
        sys.exit(1)
    main(sys.argv[1:])
