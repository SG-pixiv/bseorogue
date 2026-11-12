# SPDX-FileCopyrightText: 2026 SG
# SPDX-License-Identifier: AGPL-3.0-only
"""
실험체 · 스킬 시트(엑셀) → 게임 데이터 (src/data/bseorogue/sheet-data.ts)

SG가 고친 엑셀을 docs/sheets/실험체-스킬.xlsx 에 덮어쓰고 이 파일을 돌려요.
노란 칸만 읽어요: 역할군 · 무기 · 코스트 · 종족값 6칸 · 키 등급 · 스킨 진화 / 스킬 분류 · 위력 · 명중 · PP · 선공 · 배우는 레벨 · 효과

쓰는 법: python3 -I -B scripts/er-sheet/import_sheet.py [엑셀 경로]
  → 이상한 칸(없는 역할군, 0 이하 숫자, 없는 스킨 번호 등)은 줄 번호와 같이 알려 주고 멈춰요.
  → 효과 칸 글자를 읽어 게임 효과로 바꿔요 (쓸 수 있는 표현은 skill_effect.py 맨 위). 못 읽는 글자도 줄 번호와 같이 알려 줘요.
  → 스킬마다 연출(애니메이션) 틀로 빌려 쓸 포켓로그 기술도 다시 골라 skill-moves.ts 에 써요 (pick_skill_moves.py).
     틀을 안 바꾸려면 --keep-moves
  → 다 되면: pnpm exec biome format --write src/data/bseorogue/ 그리고 블서로그 테스트
"""
import json
import re
import sys
from pathlib import Path

from openpyxl import load_workbook

sys.path.insert(0, str(Path(__file__).resolve().parent))  # -I 로 돌려도 같은 폴더 모듈을 읽게
import pick_skill_moves  # noqa: E402
import skill_effect  # noqa: E402

ROOT = Path(__file__).resolve().parents[2]
ARGS = [a for a in sys.argv[1:] if not a.startswith("--")]
KEEP_MOVES = "--keep-moves" in sys.argv
SRC = Path(ARGS[0]) if ARGS else ROOT / "docs" / "sheets" / "실험체-스킬.xlsx"
OUT = ROOT / "src" / "data" / "bseorogue" / "sheet-data.ts"
ROLE = {"탱커": "TANK", "브루저": "BRUISER", "암살자": "ASSASSIN", "평원딜": "MARKSMAN", "원딜": "MARKSMAN",
        "스증딜러": "MAGE", "스증": "MAGE", "서포터": "SUPPORT"}
CAT = {"물리": "PHYSICAL", "스증": "SPECIAL", "특수": "SPECIAL", "변화": "STATUS"}
errors: list[str] = []
warnings: list[str] = []


def num(v, where, lo=None, hi=None, blank=None):
    if v in (None, "", "—", "-"):
        if blank is not None:
            return blank
        errors.append(f"{where}: 비어 있어요")
        return 0
    try:
        n = int(round(float(v)))
    except (TypeError, ValueError):
        errors.append(f"{where}: 숫자가 아니에요 ({v})")
        return 0
    if (lo is not None and n < lo) or (hi is not None and n > hi):
        errors.append(f"{where}: {lo}~{hi} 사이여야 해요 ({n})")
    return n


def role(v, where, blank_ok=False):
    if v in (None, ""):
        if blank_ok:
            return None
        errors.append(f"{where}: 역할군이 비어 있어요")
        return "BRUISER"
    r = ROLE.get(str(v).strip())
    if not r:
        errors.append(f"{where}: 없는 역할군이에요 ({v}) — 탱커 · 브루저 · 암살자 · 평원딜 · 스증딜러 · 서포터")
        return "BRUISER"
    return r


# 패시브로 못 쓰는 특성: 블서로그에 없는 것(모습 바꾸기 · 타입 · 날씨)이 대부분이지만, 확실히 막을 것만
BAD_ABILITIES = {"NONE", "WONDER_GUARD", "IMPOSTER", "ILLUSION", "STANCE_CHANGE", "ZEN_MODE", "SCHOOLING", "DISGUISE",
                 "BATTLE_BOND", "POWER_CONSTRUCT", "SHIELDS_DOWN", "ICE_FACE", "GULP_MISSILE", "HUNGER_SWITCH", "ZERO_TO_HERO",
                 "FORECAST", "FLOWER_GIFT", "MULTITYPE", "RKS_SYSTEM", "TERA_SHIFT", "PROTEAN", "LIBERO", "COLOR_CHANGE"}


def ability_table():
    """AbilityId 이름 · 한국어 원래 이름 → AbilityId 이름, 그리고 미구현 목록"""
    src = (ROOT / "src/data/abilities/init-abilities.ts").read_text(encoding="utf-8")
    ko = json.loads((ROOT / "locales/ko/ability.json").read_text(encoding="utf-8"))
    keys = re.findall(r"^\s+([A-Z0-9_]+),", (ROOT / "src/enums/ability-id.ts").read_text(encoding="utf-8"), re.M)
    names = {}
    for k in keys:
        names[k] = k
        camel = re.sub(r"_([a-z0-9])", lambda m: m[1].upper(), k.lower())
        if ko.get(camel, {}).get("name"):
            names.setdefault(re.sub(r"\s", "", ko[camel]["name"]), k)
    heads = list(re.finditer(r"new AbBuilder\(AbilityId\.(\w+)", src))
    broken = set()
    for i, h in enumerate(heads):
        body = src[h.end():heads[i + 1].start() if i + 1 < len(heads) else len(src)]
        if ".unimplemented()" in body or ".partial()" in body:
            broken.add(h[1])
    return names, broken


def read_passives(wb, chars, errors):
    ws = wb["패시브"]
    col = {c.value: i for i, c in enumerate(ws[1])}
    names, broken = ability_table()
    out, used = {}, {}
    for r, row in enumerate(ws.iter_rows(min_row=2, values_only=True), 2):
        if row[col["ER번호"]] is None:
            continue
        code = int(row[col["ER번호"]])
        at = f"패시브 {r}줄 ({row[col['이름']]})"
        raw = re.sub(r"\s", "", str(row[col["빌려 쓸 특성"]] or ""))
        key = names.get(raw.upper()) or names.get(raw)
        if not key:
            errors.append(f"{at}: '{raw}' 라는 특성이 없어요 (영어 이름 예: GUTS, 또는 한국어 원래 이름 예: 근성)")
            continue
        if key in BAD_ABILITIES or key in broken:
            errors.append(f"{at}: {key} 는 블서로그에서 못 써요 (모습이 바뀌거나 미구현인 특성)")
        if key in used:
            errors.append(f"{at}: {key} 를 {used[key]} 도 써요 (한 특성은 한 실험체만)")
        used[key] = row[col["이름"]]
        if code not in chars:
            errors.append(f"{at}: 실험체 시트에 없는 ER 번호 {code}")
        out[code] = {
            "name": str(row[col["패시브 이름"]] or "").strip(),
            "ability": key,
            "desc": str(row[col["효과 설명 (화면에 나와요)"]] or "").strip(),
        }
        if not out[code]["name"] or not out[code]["desc"]:
            errors.append(f"{at}: 패시브 이름 · 효과 설명을 채워 주세요")
    return out


def main():
    wb = load_workbook(SRC, data_only=True)
    chars, skins_of = {}, {}
    ws = wb["실험체"]
    head = [c.value for c in ws[1]]
    col = {h: i for i, h in enumerate(head)}
    for r, row in enumerate(ws.iter_rows(min_row=2, values_only=True), 2):
        if row[0] in (None, ""):
            continue
        code = int(row[0])
        at = f"실험체 {r}줄 ({row[1]})"
        skin_list = str(row[col["스킨 목록 (번호 이름, ✓ 그림 있음)"]] or "")
        n_skins = len([s for s in skin_list.split(" / ") if s.strip()])
        evo_skins = [num(row[col["진화1 스킨"]], at + " 진화1 스킨", 1, 99), num(row[col["진화2 스킨"]], at + " 진화2 스킨", 1, 99)]
        for k, sk in enumerate(evo_skins, 1):
            if sk > n_skins:
                warnings.append(f"{at}: 진화{k} 스킨 {sk}번이 ER 스킨 목록에 없어요 (스킨 {n_skins}개) → 게임에서는 이름 뒤 ★, 그림은 기본 모습")
        levels = [num(row[col["진화1 레벨"]], at + " 진화1 레벨", 2, 99), num(row[col["진화2 레벨"]], at + " 진화2 레벨", 3, 100)]
        if levels[0] >= levels[1]:
            errors.append(f"{at}: 진화2 레벨이 진화1 레벨보다 커야 해요")
        size = str(row[col["키 등급"]] or "M").strip().upper()
        if size not in ("S", "M", "L"):
            errors.append(f"{at}: 키 등급은 S · M · L ({size})")
        chars[code] = {
            "role": role(row[col["역할군"]], at),
            "weapon": str(row[col["무기"]] or "").strip(),
            "cost": num(row[col["코스트"]], at + " 코스트", 1, 6),
            "final": [num(row[col[k]], f"{at} {k}", 1, 255) for k in ("체력", "공격력", "방어력", "스킬 증폭", "스킬 저항", "속도")],
            "size": size,
            "skins": evo_skins,
            "levels": levels,
            "roles": [role(row[col["진화1 후 역할군"]], at, True), role(row[col["진화2 후 역할군"]], at, True)],
        }
    skills: dict[int, list] = {}
    ws = wb["스킬"]
    head = [c.value for c in ws[1]]
    col = {h: i for i, h in enumerate(head)}
    for r, row in enumerate(ws.iter_rows(min_row=2, values_only=True), 2):
        if row[0] in (None, ""):
            continue
        code = int(row[0])
        at = f"스킬 {r}줄 ({row[1]} {row[2]})"
        cat = CAT.get(str(row[col["분류"]] or "").strip())
        if not cat:
            errors.append(f"{at}: 분류는 물리 · 스증 · 변화 ({row[col['분류']]})")
            cat = "PHYSICAL"
        status = cat == "STATUS"
        sk = {
            "category": cat,
            "power": 0 if status else num(row[col["위력"]], at + " 위력", 1, 250),
            "accuracy": num(row[col["명중"]], at + " 명중", 1, 100, blank=-1),  # 비우면 반드시 맞음
            "pp": num(row[col["PP"]], at + " PP", 1, 64),
            "priority": num(row[col["선공"]], at + " 선공", -7, 5, blank=0),
            "level": num(row[col["배우는 레벨"]], at + " 배우는 레벨", 1, 100),
            "effect": str(row[col["효과 (초안)"]] or "").strip(),
        }
        try:
            sk["fx"], sk["desc"], warns = skill_effect.parse(sk["effect"], cat, sk["priority"])
            warnings.extend(f"{at}: {w}" for w in warns)
        except skill_effect.EffectError as e:
            errors.append(f"{at}: 효과 — {e}")
            sk["fx"], sk["desc"] = {"chance": -1}, ""
        skills.setdefault(code, []).append(sk)
    for code, s in skills.items():
        if len(s) != 4:
            errors.append(f"실험체 {code}: 스킬이 4개가 아니에요 ({len(s)}개)")
    missing = set(chars) ^ set(skills)
    if missing:
        errors.append(f"실험체 시트와 스킬 시트의 ER 번호가 달라요: {sorted(missing)}")
    passives = read_passives(wb, chars, errors) if "패시브" in wb.sheetnames else {}
    for w in warnings:
        print("  (참고)", w)
    if errors:
        print("시트에 고칠 곳이 있어요:")
        for e in errors:
            print("  -", e)
        sys.exit(1)

    def js(o):
        return json.dumps(o, ensure_ascii=False)

    lines = [
        "/*",
        " * SPDX-FileCopyrightText: 2026 SG",
        " * SPDX-License-Identifier: AGPL-3.0-only",
        " */",
        "",
        "// 이 파일은 scripts/er-sheet/import_sheet.py 가 docs/sheets/실험체-스킬.xlsx 에서 만들어요. 직접 고치지 마세요.",
        "",
        'import type { ErRoleKey } from "#data/bseorogue/er-data";',
        'import type { Stats6 } from "#data/bseorogue/stats";',
        "",
        "export interface SheetCharacter {",
        "  role: ErRoleKey;",
        "  weapon: string;",
        "  cost: number;",
        "  /** 다 큰 모습(스킨 진화 2) 종족값 모양 [체력, 공격력, 방어력, 스킬 증폭, 스킬 저항, 속도] */",
        "  final: Stats6;",
        "  /** 도트 키 등급 (S 60 · M 68 · L 74px) */",
        '  size: "S" | "M" | "L";',
        "  skins: readonly [number, number];",
        "  levels: readonly [number, number];",
        "  roles: readonly [ErRoleKey | null, ErRoleKey | null];",
        "}",
        "",
        "export interface SheetSkill {",
        '  category: "PHYSICAL" | "SPECIAL" | "STATUS";',
        "  power: number;",
        "  /** -1 = 반드시 맞음 */",
        "  accuracy: number;",
        "  pp: number;",
        "  priority: number;",
        "  level: number;",
        "  /** 시트 효과 칸 글자 그대로 */",
        "  effect: string;",
        "  /** 효과 칸을 읽은 게임 효과 (skill-effect.ts 가 빌려 쓴 기술에 붙여요) */",
        "  fx: SheetSkillEffect;",
        "  /** 실험체 정보 화면 스킬 설명 */",
        "  desc: string;",
        "}",
        "",
        'export type SheetStat = "ATK" | "DEF" | "SPATK" | "SPDEF" | "SPD" | "ACC" | "EVA";',
        "",
        "export interface SheetSkillEffect {",
        "  /** 상태이상 · 혼란 · 풀죽음 확률 (%), -1 = 반드시 */",
        "  chance: number;",
        '  status?: "BURN" | "PARALYSIS" | "POISON" | "TOXIC" | "SLEEP" | "FREEZE";',
        "  confuse?: boolean;",
        "  flinch?: boolean;",
        "  /** 능력 변화 (self: 자기, 아니면 상대 · chance: 확률 %) */",
        "  stats?: readonly { self: boolean; stats: readonly SheetStat[]; stages: number; chance: number }[];",
        "  highCrit?: boolean;",
        "  /** 준 피해의 이 비율만큼 회복 */",
        "  drain?: number;",
        "  /** 최대 체력의 이 비율만큼 회복 */",
        "  heal?: number;",
        "  /** 준 피해의 이 비율만큼 반동 */",
        "  recoil?: number;",
        "  /** 쓴 다음 턴 못 움직임 */",
        "  recharge?: boolean;",
        "}",
        "",
        "/** ER 번호 → 실험체 (시트) */",
        "export const SHEET_CHARACTERS: Readonly<Record<number, SheetCharacter>> = {",
    ]
    for code in sorted(chars):
        lines.append(f"  {code}: {js(chars[code])},")
    lines += ["};", "", "/** ER 번호 → [Q, W, E, R] (시트) */", "export const SHEET_SKILLS: Readonly<Record<number, readonly [SheetSkill, SheetSkill, SheetSkill, SheetSkill]>> = {"]
    for code in sorted(skills):
        lines.append(f"  {code}: [")
        for s in skills[code]:
            lines.append(f"    {js(s)},")
        lines.append("  ],")
    lines += [
        "};",
        "",
        "/** ER 번호 → 고유 패시브 (시트 '패시브'). ability 는 빌려 쓰는 포켓로그 특성 AbilityId 이름 */",
        "export const SHEET_PASSIVES: Readonly<Record<number, { name: string; ability: string; desc: string }>> = {",
    ]
    for code in sorted(passives):
        lines.append(f"  {code}: {js(passives[code])},")
    lines += ["};", ""]
    OUT.write_text("\n".join(lines), encoding="utf-8")
    print(f"{OUT.relative_to(ROOT)}: 실험체 {len(chars)}명 · 스킬 {sum(len(s) for s in skills.values())}개 · 패시브 {len(passives)}개")
    if KEEP_MOVES:
        return
    want = {
        code: [{"kind": skill_effect.kind_of(s["fx"], s["category"]), "tags": skill_effect.tags_of(s["fx"], s["category"]),
                "category": s["category"], "power": s["power"], "priority": s["priority"]} for s in sk]
        for code, sk in skills.items()
    }
    changed, moves = pick_skill_moves.pick(want)
    print(f"{pick_skill_moves.OUT.relative_to(ROOT)}: 연출 틀 {len(changed)}개 바뀜")
    for code, name, qwer, old, new in changed:
        print(f"  {name} {qwer}: {old} → {new} ({' · '.join(sorted(moves[new]['tags'])) or '-'})")


if __name__ == "__main__":
    main()
