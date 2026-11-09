# SPDX-FileCopyrightText: 2026 SG
# SPDX-License-Identifier: AGPL-3.0-only
"""
실험체 · 스킬 시트(엑셀) → 게임 데이터 (src/data/bseorogue/sheet-data.ts)

SG가 고친 엑셀을 docs/sheets/실험체-스킬.xlsx 에 덮어쓰고 이 파일을 돌려요.
노란 칸만 읽어요: 역할군 · 무기 · 코스트 · 종족값 6칸 · 키 등급 · 스킨 진화 / 스킬 분류 · 위력 · 명중 · PP · 선공 · 배우는 레벨 · 효과

쓰는 법: python3 -I -B scripts/er-sheet/import_sheet.py [엑셀 경로]
  → 이상한 칸(없는 역할군, 0 이하 숫자, 없는 스킨 번호 등)은 줄 번호와 같이 알려 주고 멈춰요.
  → 효과 칸은 아직 글자만 저장해요 (효과를 실제로 바꾸는 건 효과가 정해진 뒤에 따로 해요).
"""
import json
import sys
from pathlib import Path

from openpyxl import load_workbook

ROOT = Path(__file__).resolve().parents[2]
SRC = Path(sys.argv[1]) if len(sys.argv) > 1 else ROOT / "docs" / "sheets" / "실험체-스킬.xlsx"
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
        skills.setdefault(code, []).append({
            "category": cat,
            "power": 0 if status else num(row[col["위력"]], at + " 위력", 1, 250),
            "accuracy": num(row[col["명중"]], at + " 명중", 1, 100, blank=-1),  # 비우면 반드시 맞음
            "pp": num(row[col["PP"]], at + " PP", 1, 64),
            "priority": num(row[col["선공"]], at + " 선공", -7, 5, blank=0),
            "level": num(row[col["배우는 레벨"]], at + " 배우는 레벨", 1, 100),
            "effect": str(row[col["효과 (초안)"]] or "").strip(),
        })
    for code, s in skills.items():
        if len(s) != 4:
            errors.append(f"실험체 {code}: 스킬이 4개가 아니에요 ({len(s)}개)")
    missing = set(chars) ^ set(skills)
    if missing:
        errors.append(f"실험체 시트와 스킬 시트의 ER 번호가 달라요: {sorted(missing)}")
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
        "  /** 원하는 효과 (아직 글자만, 실제 효과는 빌려 쓴 기술 것) */",
        "  effect: string;",
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
    lines += ["};", ""]
    OUT.write_text("\n".join(lines), encoding="utf-8")
    print(f"{OUT.relative_to(ROOT)}: 실험체 {len(chars)}명 · 스킬 {sum(len(s) for s in skills.values())}개")


if __name__ == "__main__":
    main()
