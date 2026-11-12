# SPDX-FileCopyrightText: 2026 SG
# SPDX-License-Identifier: AGPL-3.0-only
"""실험체 · 스킬 초안 시트에 넣는 포켓몬 예시 (비슷한 기술 · 진화 라인 · 모양). make_draft.py 가 써요"""
import json, math, os, re
from pathlib import Path

R = Path(__file__).resolve().parents[2]
DUMP = Path(os.environ.get("SHEET_DUMP", "/tmp/bseo-sheet-dump"))
P = json.load(open(DUMP / "pokemon.json"))
KO_MOVE = json.load(open(R / "locales/ko/move.json"))
KO_MON = json.load(open(R / "locales/ko/pokemon.json"))

def camel(k):
    p = k.lower().split("_")
    return p[0] + "".join(x.capitalize() for x in p[1:])

# 원래 포켓몬 숫자: move.ts 에서 직접 읽어요 (게임 안에서는 실험체 스킬로 빌려 쓴 기술 숫자가 시트 값으로 바뀌어 있어요)
ORIG = {}
SRC = (R / "src/data/moves/move.ts").read_text()
for mm in re.finditer(r"new (AttackMove|ChargingAttackMove)\(MoveId\.(\w+), PokemonType\.\w+, MoveCategory\.(\w+), (-?\d+), (-?\d+), (\d+), (-?\d+), (-?\d+)", SRC):
    ORIG[mm[2]] = {"category": {"PHYSICAL": 0, "SPECIAL": 1, "STATUS": 2}[mm[3]], "power": int(mm[4]), "accuracy": int(mm[5]), "pp": int(mm[6]), "priority": int(mm[8])}
for mm in re.finditer(r"new (StatusMove|SelfStatusMove|ChargingSelfStatusMove)\(MoveId\.(\w+), PokemonType\.\w+, (-?\d+), (\d+), (-?\d+), (-?\d+)", SRC):
    ORIG[mm[2]] = {"category": 2, "power": -1, "accuracy": int(mm[3]), "pp": int(mm[4]), "priority": int(mm[6])}
MOVES = []
for m in P["moves"]:
    if m["key"] in ORIG:
        m = {**m, **ORIG[m["key"]]}
    loc = KO_MOVE.get(camel(m["key"]))
    if not loc or m["unimpl"] or m["pp"] <= 1 or re.match(r"(G_)?MAX_|.*_Z$", m["key"]):
        continue
    MOVES.append({**m, "name": loc["name"], "effect": loc["effect"]})

PRESET = {
    "피해": None,
    "방어 · 스킬 저항 1단계 ↑": r"자신의 방어, 특수방어를 1단계 올린다",
    "공격 · 방어 1단계 ↑": r"자신의 공격, 방어를 1단계 올린다",
    "속도 2단계 ↑": r"자신의 스피드를 2단계 올린다",
    "공격 1단계 ↑ · 명중 ↑": r"자신의 공격과 명중률을 올린다",
    "스킬 증폭 2단계 ↑": r"자신의 특수공격을 2단계 올린다",
    "체력 50% 회복": r"최대 HP의 1/2만큼 회복",
    "피해 + 30% 스턴": r"확률로 상대를 풀죽게",
    "피해의 50% 회복": r"대미지의 1/2만큼 자신의 HP를 회복",
    "선공(+1) 피해": "PRIORITY",
    "피해 + 급소에 잘 맞음": r"급소업",
    "강한 피해, 다음 턴 쉼": r"1턴 동안 행동할 수 없다",
    "피해 + 30% 화상": r"확률로 상대를 화상",
    "강한 피해, 쓴 뒤 스킬 증폭 2단계 ↓": r"자신의 특수공격을 2단계 떨어뜨린다",
    "피해 + 상대 스킬 증폭 1단계 ↓": r"상대의 특수공격을 1단계 떨어뜨린다",
    "피해 + 상대 공격 1단계 ↓": r"상대의 공격을 (1단계 )?떨어뜨린다",
    "피해 + 자기 체력 30% 회복": r"만큼 자신의 HP를 회복",
}
SECONDARY = re.compile(r"확률|단계|회복|급소|선제|반동|행동할 수 없|떨어뜨|올린다|위력이|연속|2배|해제|교체|바뀐다")
CAT = {"물리": 0, "스증": 1, "변화": 2}

def move_examples(cat_ko, power, acc, pp, effect, n=3):
    cat = CAT.get(cat_ko, 0)
    pat = PRESET.get(effect, None)
    out = []
    for m in MOVES:
        if cat == 2 and m["category"] != 2:
            continue
        if cat != 2 and m["category"] == 2:
            continue
        if pat == "PRIORITY":
            ok = m["priority"] == 1 and m["power"] > 0
        elif pat:
            ok = re.search(pat, m["effect"]) is not None
        else:
            ok = not SECONDARY.search(m["effect"])
        score = (0 if ok else 100) + (0 if m["category"] == cat else 15)
        if cat != 2:
            p = power if isinstance(power, int) else 60
            a = acc if isinstance(acc, int) else 100
            score += abs(m["power"] - p) / 5 + abs((m["accuracy"] if m["accuracy"] > 0 else 100) - a) / 4
        score += abs(m["pp"] - pp) / 3
        out.append((score, m))
    out.sort(key=lambda x: (x[0], x[1]["id"]))
    exact = [m for sc, m in out if sc < 100]
    if pat and exact:  # 효과가 맞는 기술이 있으면 그것만
        return exact[:n]
    return [m for _, m in out[:n]]

def fmt(m):
    if m["category"] == 2:
        return f"{m['name']} (변화 · PP {m['pp']})"
    acc = m["accuracy"] if m["accuracy"] > 0 else "—"
    cat = "물리" if m["category"] == 0 else "스증"
    pr = f" · 선공+{m['priority']}" if m["priority"] > 0 else ""
    return f"{m['name']} ({cat} {m['power']}/{acc}/{m['pp']}{pr})"

SPECIES = {s["id"]: s for s in P["species"]}
def mon_name(s):
    return KO_MON.get(camel(s["key"]), s["key"])

def lines_near(totals, n=4):
    """3단 진화 라인 중 [기본, 중간, 최종] 합이 비슷한 것"""
    res = []
    for s in P["species"]:
        if s["id"] != s["starter"] or s["legendary"] or len(s["evo"]) != 2:
            continue
        mid, fin = SPECIES.get(s["evo"][0]), SPECIES.get(s["evo"][1])
        if not mid or not fin or s["evo"][1] not in mid["evo"]:
            continue
        t = (s["total"], mid["total"], fin["total"])
        res.append((sum(abs(a - b) for a, b in zip(t, totals)), s["id"], f"{mon_name(s)} → {mon_name(mid)} → {mon_name(fin)} ({t[0]} → {t[1]} → {t[2]}, 포켓로그 {s['starterCost']}코)"))
    res.sort()
    return [r[2] for r in res[:n]]

def singles_near(total, n=4):
    res = [(abs(s["total"] - total), s["id"], f"{mon_name(s)} ({s['total']}{', 전설/환상' if s['legendary'] else ''})")
           for s in P["species"] if not s["evo"] and s["total"] >= total - 15]
    res.sort()
    return [r[2] for r in res[:n]]

def pokerogue_cost(cost, n=5):
    res = [s for s in P["species"] if s["starterCost"] == cost and s["id"] == s["starter"]]
    res.sort(key=lambda s: s["id"])
    return [mon_name(s) for s in res[:n]]

FINALS = [s for s in P["species"] if not s["evo"] and not s["legendary"] and s["total"] >= 400]
def shape_near(stats, n=2):
    def cos(a, b):
        return sum(x * y for x, y in zip(a, b)) / (math.sqrt(sum(x * x for x in a)) * math.sqrt(sum(y * y for y in b)))
    res = sorted(FINALS, key=lambda s: -cos(stats, s["stats"]))[:n]
    return " · ".join(f"{mon_name(s)} {'/'.join(map(str, s['stats']))} (합 {s['total']})" for s in res)



def power_ladder(cat):
    """효과 없는 기술을 위력별로 (참고용)"""
    rows = []
    for p in (40, 50, 60, 70, 80, 90, 100, 120, 150):
        ms = [m for m in MOVES if m["category"] == cat and m["power"] == p and not SECONDARY.search(m["effect"])]
        ms.sort(key=lambda m: (-(m["accuracy"] if m["accuracy"] > 0 else 101), m["id"]))
        rows.append((p, ms[:3]))
    return rows
