# SPDX-FileCopyrightText: 2026 SG
# SPDX-License-Identifier: AGPL-3.0-only
"""
스킬마다 연출(애니메이션) 틀로 빌려 쓸 포켓로그 기술 고르기 → src/data/bseorogue/skill-moves.ts

import_sheet.py 가 시트를 읽은 뒤 불러요 (혼자 돌리지 않아요).
효과는 시트 효과 칸 그대로 게임이 붙여요 (src/data/bseorogue/skill-effect.ts). 여기서는 틀만 골라요:
  - 공격 스킬 → 공격 기술, 자기에게 쓰는 변화 → 자기 변화 기술, 상대에게 쓰는 변화 → 상대 변화 기술
  - 효과가 비슷한 기술일수록 (화상이면 원래 화상 기술), 위력이 비슷할수록, 지금 쓰는 기술일수록 먼저
  - 한 기술은 한 실험체만 (야생동물 · 보스 · 추가 스킬 · 게임 코드가 이름으로 찾는 기술은 안 써요)
"""
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
MOVE_TS = ROOT / "src" / "data" / "moves" / "move.ts"
OUT = ROOT / "src" / "data" / "bseorogue" / "skill-moves.ts"
# 직접 고른 시작 6명 (엘레븐 · 유키 · 쇼이치 · 나딘 · 혜진 · 레니): 틀이 맞으면 되도록 그대로
HAND_PICKED = {30, 11, 18, 6, 12, 69}
# 게임 코드가 기술 이름으로 따로 찾는 곳 중 효과와 상관없는 목록 (여기 나오는 건 빌려 써도 돼요)
DATA_ONLY = ("src/enums/", "src/data/balance/", "src/data/bseorogue/", "src/data/moves/invalid-moves.ts",
             "src/data/trainers/", "src/data/challenge.ts", "src/ai/ai-moveset-gen.ts", "src/modifier/init-modifier-pools.ts",
             "src/data/mystery-encounters/", "src/locales/")
HEAD = re.compile(r"new (AttackMove|StatusMove|SelfStatusMove|ChargingAttackMove|ChargingSelfStatusMove)\(MoveId\.(\w+), PokemonType\.\w+, ([^)]*)\)")
# 자기 변화 스킬 틀: 자기 → 자기 편 → (모자라면) 상대에게 쓰는 기술 순서
SELF_TARGETS = {"USER": 0, "USER_SIDE": 3, "USER_AND_ALLIES": 3, "USER_OR_NEAR_ALLY": 3, "ALL": 8, "BOTH_SIDES": 8,
                "NEAR_OTHER": 12, "NEAR_ENEMY": 12, "ALL_NEAR_ENEMIES": 12, "ENEMY_SIDE": 12}
# 자기 변화 스킬 연출로 어울리는 정도 (원래 효과 기준): 강화 · 방어 · 회복 → 날씨 · 필드 → 상대에게 거는 것 → 그 밖 (튀어오르기 · 손가락 흔들기 같은 것)
BUFF_ATTRS = {"StatStageChangeAttr", "ProtectAttr", "HealAttr", "VariableHealAttr", "PlantHealAttr", "SandHealAttr",
              "AddBattlerTagAttr", "CutHpStatStageBoostAttr", "AcupressureStatStageChangeAttr", "GrowthStatStageChangeAttr",
              "HealStatusEffectAttr", "AddArenaTagAttr", "RemoveBattlerTagAttr", "EatBerryAttr", "RemoveAllSubstitutesAttr"}
# 원래 연출이 '나중에 맞음 · 미리 기 모음 · 쓰러짐' 같은 기술: 틀로는 되도록 안 써요
AWKWARD_ATTRS = {"DelayedAttackAttr", "MessageHeaderAttr", "SacrificialAttr", "SacrificialAttrOnHit", "HalfSacrificialAttr",
                 "SacrificialFullRestoreAttr", "CallMoveAttr", "RandomMoveAttr", "CopyMoveAttr", "RandomMovesetMoveAttr"}
FIELD_ATTRS = {"WeatherChangeAttr", "TerrainChangeAttr", "RestAttr", "ResetStatsAttr"}
STAT_KEY = {"ATK": "ATK", "DEF": "DEF", "SPATK": "SPATK", "SPDEF": "SPDEF", "SPD": "SPD", "ACC": "ACC", "EVA": "EVA"}


def strip_comments(src):
    src = re.sub(r"/\*.*?\*/", " ", src, flags=re.S)
    return re.sub(r"//[^\n]*", " ", src)


def read_moves():
    src = strip_comments(MOVE_TS.read_text(encoding="utf-8"))
    heads = list(HEAD.finditer(src))
    moves = {}
    own_spans = []
    for i, h in enumerate(heads):
        end = heads[i + 1].start() if i + 1 < len(heads) else src.find("\n  );", h.end())
        body = src[h.end():end]
        own_spans.append((h.start(), h.start() + len(h[0])))
        cls, key, args = h[1], h[2], [a.strip() for a in h[3].split(",")]
        if cls == "AttackMove" or cls == "ChargingAttackMove":
            cat, power, chance, priority = args[0].split(".")[-1], int(args[1]), int(args[4]), int(args[5])
        else:
            cat, power, chance, priority = "STATUS", 0, int(args[2]), int(args[3])
        attrs = re.findall(r"\.attr\((\w+)(?:,\s*([^\n]*))?\)", body)
        tgt = re.search(r"\.target\(MoveTarget\.(\w+)\)", body)
        tags, other = set(), 0
        for name, a in attrs:
            a = a or ""
            if name in ("StatusEffectAttr", "MultiStatusEffectAttr"):
                if re.search(r",\s*true\s*$", a):  # 자기에게 거는 상태이상 (잠자기 등)
                    other += 1
                    continue
                for st in re.findall(r"StatusEffect\.(\w+)", a):
                    tags.add("status:" + st)
            elif name == "FlinchAttr":
                tags.add("flinch")
            elif name == "ConfuseAttr":
                tags.add("confuse")
            elif name == "StatStageChangeAttr":
                m = re.match(r"\[([^\]]*)\],\s*(-?\d+)(?:,\s*(true|false))?", a)
                if not m:
                    other += 1
                    continue
                self_ = m[3] == "true" or (cls in ("SelfStatusMove",) and m[3] is None)
                d = f"stat:{'self' if self_ else 'target'}:{'+' if int(m[2]) > 0 else '-'}"
                tags.add(d)
                for k in re.findall(r"Stat\.(\w+)", m[1]):
                    if k in STAT_KEY:
                        tags.add(f"{d}:{k}")
            elif name == "HighCritAttr":
                tags.add("highCrit")
            elif name == "HitHealAttr":
                tags.add("drain")
            elif name in ("HealAttr", "PlantHealAttr", "SandHealAttr", "WeatherHealAttr"):
                tags.add("heal")
            elif name == "RecoilAttr":
                tags.add("recoil")
            elif name == "RechargeAttr":
                tags.add("recharge")
            elif name == "HealStatusEffectAttr" and "StatusEffect.FREEZE" in a:
                pass  # 불 기술 얼음 녹이기 (모든 불 공격에 있음)
            else:
                other += 1
        other += body.count(".attr(") - len(attrs)  # 여러 줄에 걸친 효과도 '다른 효과'로 세요
        if not tags and other == 0 and cls == "AttackMove":
            tags.add("plain")
        names = set(re.findall(r"\.attr\(\s*(\w+)", body))
        tgt_key = tgt[1] if tgt else ("USER" if cls == "SelfStatusMove" else "NEAR_OTHER")
        self_side = SELF_TARGETS.get(tgt_key, 99) <= 3
        if self_side and names & BUFF_ATTRS and not any(t.startswith("stat:target") or t.startswith("status:") for t in tags):
            self_fit = 0
        elif names & FIELD_ATTRS:
            self_fit = 5
        elif not self_side:
            self_fit = 9
        else:
            self_fit = 16
        moves[key] = {
            "self_fit": self_fit,
            "awkward": bool(names & AWKWARD_ATTRS),
            "cls": cls, "cat": cat, "power": power, "chance": chance, "priority": priority,
            "target": tgt_key,
            "tags": tags, "other": other,
            "cond": ".condition(" in body or ".restriction(" in body,
            "broken": ".unimplemented()" in body or ".partial()" in body,
            "ignores": sum(f".{f}()" in body for f in ("ignoresProtect", "ignoresSubstitute", "ignoresAbilities", "triageMove")),
        }
    # move.ts 안에서 다른 기술 코드가 이름으로 찾는 기술 (예: 구르기 → 웅크리기)
    refs = set()
    pos = 0
    for a, b in own_spans:
        refs |= set(re.findall(r"MoveId\.(\w+)", src[pos:a]))
        pos = b
    refs |= set(re.findall(r"MoveId\.(\w+)", src[pos:]))
    return moves, refs


def code_refs():
    refs = set()
    for p in (ROOT / "src").rglob("*.ts"):
        rel = p.relative_to(ROOT).as_posix()
        if rel == "src/data/moves/move.ts" or rel.startswith(DATA_ONLY):
            continue
        refs |= set(re.findall(r"MoveId\.(\w+)", strip_comments(p.read_text(encoding="utf-8"))))
    return refs


def forbidden():
    """야생동물 · 보스 · 적 기술 이름 (roster.ts) · 실험체 추가 스킬 (egg-moves.ts)"""
    out = set(re.findall(r"MoveId\.(\w+)", (ROOT / "src/data/bseorogue/roster.ts").read_text(encoding="utf-8")))
    for line in (ROOT / "src/data/balance/moves/egg-moves.ts").read_text(encoding="utf-8").splitlines():
        if "SpeciesId.BSEO_" in line:
            out |= set(re.findall(r"MoveId\.(\w+)", line))
    return out


def current():
    """지금 skill-moves.ts → {code: ([4 key], 이름 주석)}"""
    cur = {}
    for m in re.finditer(r"^\s*(\d+): \[([^\]]*)\],\s*//\s*(.*)$", OUT.read_text(encoding="utf-8"), re.M):
        cur[int(m[1])] = (re.findall(r"MoveId\.(\w+)", m[2]), m[3].strip())
    return cur


def fits(kind, mv):
    if mv["broken"] or mv["cls"].startswith("Charging"):
        return False
    if kind == "attack":
        return mv["cls"] == "AttackMove" and mv["target"] in ("NEAR_OTHER", "ALL_NEAR_ENEMIES", "NEAR_ENEMY", "RANDOM_NEAR_ENEMY")
    if kind == "self":  # 자기 쪽이 아닌 기술은 게임이 대상을 '자기'로 바꿔요 (skill-effect.ts)
        return mv["cls"] in ("SelfStatusMove", "StatusMove") and mv["target"] in SELF_TARGETS
    return mv["cls"] == "StatusMove" and mv["target"] in ("NEAR_OTHER", "NEAR_ENEMY")


def score(skill, key, mv, cur_key, hand):
    want = skill["tags"]
    s = 0.0
    if key == cur_key:
        s -= 15 if hand else 6
    s -= 8 * len(want & mv["tags"])
    s += 2 * len(mv["tags"] - want) + 1.5 * mv["other"]
    if skill["kind"] == "attack":
        s += abs(mv["power"] - skill["power"]) / 15
        if mv["cat"] == skill["category"]:
            s -= 2
        if skill["priority"] > 0 and mv["priority"] > 0:
            s -= 6
        if mv["target"] != "NEAR_OTHER":
            s += 3
    elif skill["kind"] == "self":
        s += SELF_TARGETS[mv["target"]] + mv["self_fit"]
    s += 2 * mv["ignores"] + (1 if mv["cond"] else 0) + (10 if mv["awkward"] else 0)
    return s


def pick(skills, names_ko=None):
    """skills: {code: [ {kind, tags, category, power, priority} ×4 ]} → skill-moves.ts 쓰고 바뀐 목록 돌려줘요"""
    moves, move_refs = read_moves()
    # 튀어오르기 · 축하는 테스트가 '아무것도 안 하는 기술'로 써요
    banned = forbidden() | move_refs | code_refs() | {"NONE", "STRUGGLE", "SPLASH", "CELEBRATE"}
    cur = current()
    pairs = []
    for code, sk in skills.items():
        cur_keys = cur.get(code, ([None] * 4, ""))[0]
        for i, skill in enumerate(sk):
            for key, mv in moves.items():
                if key in banned or not fits(skill["kind"], mv):
                    continue
                pairs.append((score(skill, key, mv, cur_keys[i] if i < len(cur_keys) else None, code in HAND_PICKED), code, i, key))
    pairs.sort()
    chosen, used = {}, set()
    for _, code, i, key in pairs:
        if (code, i) in chosen or key in used:
            continue
        chosen[(code, i)] = key
        used.add(key)
    missing = [(c, i) for c, sk in skills.items() for i in range(len(sk)) if (c, i) not in chosen]
    if missing:
        raise SystemExit(f"틀로 빌려 쓸 기술이 모자라요: {missing}")
    changed = []
    lines = OUT.read_text(encoding="utf-8")
    head = lines[: lines.index("export const SKILL_MOVES")]
    body = ["export const SKILL_MOVES: Readonly<Record<number, readonly [MoveId, MoveId, MoveId, MoveId]>> = {"]
    order = [c for c in cur if c in skills] + sorted(c for c in skills if c not in cur)
    for code in order:
        keys = [chosen[(code, i)] for i in range(4)]
        name = cur.get(code, (None, (names_ko or {}).get(code, "")))[1]
        body.append(f"  {code}: [{', '.join('MoveId.' + k for k in keys)}], // {name}")
        old = cur.get(code, ([None] * 4,))[0]
        for i, k in enumerate(keys):
            if old[i] != k:
                changed.append((code, name, "QWER"[i], old[i], k))
    body.append("};")
    OUT.write_text(head + "\n".join(body) + "\n", encoding="utf-8")
    return changed, moves
