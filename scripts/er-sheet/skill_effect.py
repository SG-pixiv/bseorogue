# SPDX-FileCopyrightText: 2026 SG
# SPDX-License-Identifier: AGPL-3.0-only
"""
스킬 시트 '효과' 칸 글자 → 게임 효과 (import_sheet.py 가 써요)

쓸 수 있는 표현 (+ 나 , 로 이어 써요. 예: "피해 + 30% 화상", "강한 피해, 쓴 뒤 스킬 증폭 2단계 ↓")
  피해 / 강한 피해            공격 스킬 (변화 스킬에는 쓰지 않아요)
  30% 화상 · 마비 · 독 · 맹독 · 잠듦 · 얼음 · 혼란 · 기절(풀죽음)   확률을 안 쓰면 반드시
  공격 · 방어 1단계 ↑          능력 변화. 능력: 공격 · 방어 · 스킬 증폭 · 스킬 저항 · 속도 · 명중 · 회피
                              ↑ 는 자기, ↓ 는 상대가 기본. "상대" · "자기" · "쓴 뒤"(자기) 로 정해요. 단계를 안 쓰면 1단계
  급소에 잘 맞음              급소 확률 ↑
  피해의 50% 회복             준 피해만큼 회복 (흡수)
  체력 50% 회복               최대 체력만큼 회복
  반동 25%                    준 피해만큼 자기가 다침
  다음 턴 쉼                  쓴 다음 턴 못 움직임
  선공(+1)                    선공 칸 값을 써요 (글자는 설명용)
"""
import re

STATS = [
    ("SPATK", r"스킬\s*증폭|스증"),
    ("SPDEF", r"스킬\s*저항|스저"),
    ("ATK", r"공격력?"),
    ("DEF", r"방어력?"),
    ("SPD", r"속도|스피드"),
    ("ACC", r"명중률?"),
    ("EVA", r"회피율?"),
]
STAT_KO = {"ATK": "공격력", "DEF": "방어력", "SPATK": "스킬 증폭", "SPDEF": "스킬 저항", "SPD": "속도", "ACC": "명중률", "EVA": "회피율"}
STAT_RE = "|".join(f"(?:{p})" for _, p in STATS)
STATUS = {"화상": "BURN", "마비": "PARALYSIS", "맹독": "TOXIC", "독": "POISON", "잠듦": "SLEEP", "수면": "SLEEP", "얼음": "FREEZE", "빙결": "FREEZE"}
STATUS_KO = {"BURN": "화상", "PARALYSIS": "마비", "TOXIC": "맹독", "POISON": "독", "SLEEP": "잠듦", "FREEZE": "얼음"}

RE_PRIORITY = re.compile(r"선공\s*\(?\s*\+?\s*(\d)\s*\)?")
RE_CHANCE_TAG = re.compile(r"(?:(\d+)\s*%\s*(?:확률로?\s*)?)?(?:상대\s*)?(화상|마비|맹독|독|잠듦|수면|얼음|빙결|혼란|기절\s*\(\s*풀죽음\s*\)|기절|풀죽음)")
RE_STAT = re.compile(
    rf"(?:(\d+)\s*%\s*(?:확률로?\s*)?)?(쓴\s*뒤\s*|자기\s*|자신의?\s*|상대의?\s*)?((?:{STAT_RE})(?:\s*[·,]\s*(?:{STAT_RE}))*)\s*(?:(\d)\s*단계\s*)?(↑|↓)"
)
RE_DRAIN = re.compile(r"피해의?\s*(\d+)\s*%\s*(?:만큼\s*)?(?:체력\s*)?회복")
RE_HEAL = re.compile(r"(?:자기\s*|자신의?\s*)?(?:최대\s*)?체력(?:의)?\s*(\d+)\s*%\s*(?:만큼\s*)?회복")
RE_RECOIL = re.compile(r"(?:피해의?\s*(\d+)\s*%\s*(?:만큼\s*)?반동|반동\s*(\d+)\s*%)")
RE_RECHARGE = re.compile(r"다음\s*턴\s*(?:쉼|쉬어요|못\s*움직임|행동\s*불가)")
RE_CRIT = re.compile(r"급소에?\s*잘\s*맞음|급소\s*↑|급소")
RE_DAMAGE = re.compile(r"(?:강한|약한|큰|작은)?\s*피해")


class EffectError(ValueError):
    pass


def stat_keys(text):
    keys = []
    for part in re.split(r"\s*[·,]\s*", text.strip()):
        for key, pat in STATS:
            if re.fullmatch(pat, part.strip()):
                keys.append(key)
                break
    return keys


def parse(text, category, priority=0):
    """효과 글자 → (효과 dict, 설명, 경고 목록). 못 읽으면 EffectError"""
    attack = category != "STATUS"
    warns = []
    src = (text or "").strip()
    if not src:
        if attack:
            src = "피해"
        else:
            raise EffectError("변화 스킬인데 효과가 비어 있어요")
    s = src
    m = RE_PRIORITY.search(s)
    if m:
        if int(m[1]) != priority:
            warns.append(f"효과 칸은 선공 +{m[1]} 인데 선공 칸은 {priority} 예요 (선공 칸 값을 써요)")
        s = s[: m.start()] + " " + s[m.end():]
    fx = {"chance": -1}
    stat_changes = []  # (self, keys, stages, chance)
    chances = set()
    damage = False

    def take(regex, fn):
        nonlocal s
        out = []
        for mm in list(regex.finditer(s)):
            fn(mm)
            out.append(mm.span())
        for a, b in reversed(out):
            s = s[:a] + " " + s[b:]

    def on_stat(mm):
        who = (mm[2] or "").strip()
        up = mm[5] == "↑"
        if who.startswith("상대"):
            self_ = False
        elif who:
            self_ = True
        else:
            self_ = up
        stages = int(mm[4] or 1) * (1 if up else -1)
        stat_changes.append((self_, stat_keys(mm[3]), stages, int(mm[1]) if mm[1] else 100))

    def on_tag(mm):
        c = int(mm[1]) if mm[1] else 100
        word = re.sub(r"\s", "", mm[2])
        if word == "혼란":
            fx["confuse"] = True
        elif word.startswith("기절") or word == "풀죽음":
            fx["flinch"] = True
        else:
            if "status" in fx:
                raise EffectError("상태이상은 하나만 쓸 수 있어요")
            fx["status"] = STATUS[word]
        chances.add(c)

    def on_drain(mm):
        fx["drain"] = int(mm[1]) / 100

    def on_heal(mm):
        fx["heal"] = int(mm[1]) / 100

    def on_recoil(mm):
        fx["recoil"] = int(mm[1] or mm[2]) / 100

    # 순서 중요: 흡수(피해의 N% 회복) · 반동을 회복 · 피해보다 먼저
    take(RE_DRAIN, on_drain)
    take(RE_RECOIL, on_recoil)
    take(RE_HEAL, on_heal)
    take(RE_STAT, on_stat)
    take(RE_CHANCE_TAG, on_tag)
    take(RE_RECHARGE, lambda mm: fx.__setitem__("recharge", True))
    take(RE_CRIT, lambda mm: fx.__setitem__("highCrit", True))

    def on_damage(mm):
        nonlocal damage
        damage = True

    take(RE_DAMAGE, on_damage)
    left = re.sub(r"[\s+,·/()\-]|그리고|쓴\s*뒤|및", "", s)
    if left:
        raise EffectError(f"모르는 표현이 있어요: '{left}' (원래 글자: '{src}')")
    if not attack and (damage or fx.get("drain") or fx.get("recoil") or fx.get("recharge") or fx.get("highCrit")):
        raise EffectError(f"변화 스킬에 공격 효과(피해 · 흡수 · 반동 · 다음 턴 쉼 · 급소)가 있어요 → 분류를 물리/스증으로 바꾸거나 효과를 고쳐요 ('{src}')")
    if len(chances) > 1:
        raise EffectError(f"상태이상 · 혼란 · 풀죽음 확률은 하나로 맞춰요 ({sorted(chances)}, '{src}')")
    if chances:
        c = chances.pop()
        fx["chance"] = -1 if c >= 100 else c
    if fx.get("recharge") and fx["chance"] > 0:
        raise EffectError(f"'다음 턴 쉼' 은 확률 효과와 같이 못 써요 ('{src}')")
    # 같은 대상 · 단계 · 확률이면 한 줄로 (공격 1단계 ↑ · 명중 ↑ → 공격 · 명중 1단계 ↑)
    merged = {}
    for self_, keys, stages, c in stat_changes:
        merged.setdefault((self_, stages, c), [])
        for k in keys:
            if k not in merged[(self_, stages, c)]:
                merged[(self_, stages, c)].append(k)
    if merged:
        fx["stats"] = [{"self": a, "stats": ks, "stages": st, "chance": c} for (a, st, c), ks in merged.items()]
    if not attack and len(fx) == 1:
        raise EffectError(f"변화 스킬인데 효과가 없어요 ('{src}')")
    return fx, describe(fx, attack, priority), warns


def kind_of(fx, category):
    """빌려 쓸 기술 종류: attack(공격) · self(자기에게 쓰는 변화) · target(상대에게 쓰는 변화)"""
    if category != "STATUS":
        return "attack"
    if fx.get("status") or fx.get("confuse") or fx.get("flinch") or any(not s["self"] for s in fx.get("stats", [])):
        return "target"
    return "self"


def tags_of(fx, category):
    """연출 고를 때 비교하는 꼬리표"""
    t = set()
    if fx.get("status"):
        t.add("status:" + fx["status"])
    for k in ("confuse", "flinch", "highCrit", "recharge"):
        if fx.get(k):
            t.add(k)
    if fx.get("drain"):
        t.add("drain")
    if fx.get("heal"):
        t.add("heal")
    if fx.get("recoil"):
        t.add("recoil")
    for s in fx.get("stats", []):
        d = f"stat:{'self' if s['self'] else 'target'}:{'+' if s['stages'] > 0 else '-'}"
        t.add(d)
        for k in s["stats"]:
            t.add(f"{d}:{k}")
    if not t and category != "STATUS":
        t.add("plain")
    return t


def _pct(c):
    return "" if c < 0 or c >= 100 else f"{c}% 확률로 "


def _stats_sentence(s, attack):
    names = ", ".join(STAT_KO[k] for k in s["stats"])
    n = abs(s["stages"])
    who = "자신" if s["self"] else "상대"
    if s["stages"] > 0:
        return f"{_pct(s['chance'])}{who}의 {names}을 {n}단계 올린다."
    if s["self"] and attack:
        return f"쓴 뒤 {_pct(s['chance'])}자신의 {names}이 {n}단계 떨어진다."
    return f"{_pct(s['chance'])}{who}의 {names}을 {n}단계 떨어뜨린다."


def describe(fx, attack, priority=0):
    """실험체 정보 화면에 나오는 스킬 설명"""
    out = []
    if attack:
        out.append("반드시 먼저 공격할 수 있다." if priority > 0 else "상대를 공격한다.")
    elif priority > 0:
        out.append("반드시 먼저 쓸 수 있다.")
    c = fx.get("chance", -1)
    if fx.get("status"):
        out.append(f"{_pct(c)}상대를 {STATUS_KO[fx['status']]} 상태로 만든다.")
    if fx.get("confuse"):
        out.append(f"{_pct(c)}상대를 혼란에 빠뜨린다.")
    if fx.get("flinch"):
        out.append(f"{_pct(c)}상대를 풀죽게 한다.")
    stats = fx.get("stats", [])
    for s in stats:
        if not s["self"]:
            out.append(_stats_sentence(s, attack))
    if fx.get("highCrit"):
        out.append("급소에 맞기 쉽다.")
    if fx.get("drain"):
        out.append(f"준 피해의 {round(fx['drain'] * 100)}%만큼 체력을 회복한다.")
    if fx.get("heal"):
        out.append(f"최대 체력의 {round(fx['heal'] * 100)}%만큼 체력을 회복한다.")
    for s in stats:
        if s["self"]:
            out.append(_stats_sentence(s, attack))
    if fx.get("recoil"):
        out.append(f"준 피해의 {round(fx['recoil'] * 100)}%만큼 반동을 받는다.")
    if fx.get("recharge"):
        out.append("쓴 다음 턴은 움직일 수 없다.")
    return " ".join(out)


if __name__ == "__main__":  # 빠른 확인: python3 -B scripts/er-sheet/skill_effect.py "피해 + 30% 화상" 물리
    import sys

    fx, desc, w = parse(sys.argv[1], sys.argv[2] if len(sys.argv) > 2 else "PHYSICAL")
    print(fx)
    print(desc)
    for x in w:
        print("(참고)", x)
