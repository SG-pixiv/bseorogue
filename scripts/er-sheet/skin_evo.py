# SPDX-FileCopyrightText: 2026 SG
# SPDX-License-Identifier: AGPL-3.0-only
"""
스킨 진화 시트 (11-19 SG "스킨별 진화 목록 내가 정할 수 있게 엑셀시트로 만들어줘")

docs/sheets/스킨-진화.xlsx — 실험체마다 한 줄, 오른쪽에 그 실험체의 ER 스킨 전부 (✓ = 전투 그림 있음, 초록 칸).
노란 칸만 고쳐요: 진화1 스킨(눌러서 고르기) · 진화1 레벨 · 진화1 후 역할군 · 진화2 스킨 · 진화2 레벨 · 진화2 후 역할군 · 메모.
고른 스킨은 오른쪽 목록에서 주황색으로 보여요.

쓰는 법:
  python3 -I -B scripts/er-sheet/skin_evo.py
      시트를 만들거나 새로 고쳐요 (ER 스킨이 늘면 오른쪽 목록이 늘어요).
      처음에는 실험체-스킬.xlsx '실험체' 시트의 지금 값으로 채우고, 그다음부터는 이 시트에 SG가 적은 노란 칸을 ER번호로 찾아 그대로 둬요.
  python3 -I -B scripts/er-sheet/skin_evo.py --import
      노란 칸 → 실험체-스킬.xlsx '실험체' 시트의 진화1/2 스킨 · 레벨 · 후 역할군 칸 → import_sheet.py --keep-moves (게임 데이터)
      이상한 칸(없는 스킨, 레벨 순서 등)은 줄 번호와 같이 알려 주고 아무것도 안 바꿔요.
      다 되면: pnpm exec biome format --write src/data/bseorogue/ 그리고 블서로그 테스트
"""
import re
import subprocess
import sys
from pathlib import Path

from openpyxl import Workbook, load_workbook
from openpyxl.formatting.rule import FormulaRule
from openpyxl.styles import Alignment, Border, Font, PatternFill, Side
from openpyxl.utils import get_column_letter
from openpyxl.worksheet.datavalidation import DataValidation

ROOT = Path(__file__).resolve().parents[2]
SHEET = ROOT / "docs" / "sheets" / "스킨-진화.xlsx"
MAIN = ROOT / "docs" / "sheets" / "실험체-스킬.xlsx"
ROLES = ("탱커", "브루저", "암살자", "평원딜", "스증딜러", "서포터")
ROLE_ALIAS = {"원딜": "평원딜", "스증": "스증딜러"}
# 이 시트 칸 이름 → 실험체-스킬.xlsx '실험체' 시트 칸 이름
EDIT_COLS = ("진화1 스킨", "진화1 레벨", "진화1 후 역할군", "진화2 스킨", "진화2 레벨", "진화2 후 역할군")
HEAD_COLS = ("ER번호", "이름", "기본 역할군", "스킨 수", *EDIT_COLS, "메모")
SKIN0 = len(HEAD_COLS) + 1  # 오른쪽 스킨 목록이 시작하는 칸

F = "맑은 고딕"
thin = Side(style="thin", color="C9CED8")
BORDER = Border(left=thin, right=thin, top=thin, bottom=thin)
HEAD = PatternFill("solid", fgColor="1F2533")
EDIT = PatternFill("solid", fgColor="FFF59D")
HAVE = PatternFill("solid", fgColor="D7F0D2")
PICK = PatternFill("solid", fgColor="FFB74D")


def er_skins() -> tuple[dict[int, list[str]], dict[int, set[int]]]:
    """er-data.ts 스킨 이름 (0 = 기본 모습) · art-manifest.ts 전투 그림 있는 스킨"""
    er_src = (ROOT / "src/data/bseorogue/er-data.ts").read_text(encoding="utf-8")
    skins = {
        int(k): re.findall(r'"([^"]*)"', body)
        for k, body in re.findall(r'\n  "(\d+)": \{[\s\S]*?\n    skins: \[([\s\S]*?)\]', er_src)
    }
    art_src = (ROOT / "src/data/bseorogue/art-manifest.ts").read_text(encoding="utf-8")
    art_part = art_src.split("BSEO_ART_SKINS")[1].split("};")[0]
    art = {int(k): {int(x) for x in v.split(",") if x.strip()} for k, v in re.findall(r"\n  (\d+): \[([^\]]*)\]", art_part)}
    return skins, art


def skin_text(k: int, name: str, have: set[int]) -> str:
    return f"{k} {name}{' ✓' if k in have else ''}"


def skin_no(v) -> int | None:
    """'3 시스템쇼크 재키 ✓' · 3 · '3' → 3, 빈칸 → None"""
    if v in (None, ""):
        return None
    m = re.match(r"\s*(\d+)", str(v))
    return int(m.group(1)) if m else -1


def main_rows() -> list[dict]:
    """실험체-스킬.xlsx '실험체' 시트: ER번호 · 이름 · 역할군 · 지금 진화 값"""
    ws = load_workbook(MAIN, data_only=True)["실험체"]
    head = [c.value for c in ws[1]]
    col = {h: i for i, h in enumerate(head)}
    out = []
    for row in ws.iter_rows(min_row=2, values_only=True):
        if row[0] in (None, ""):
            continue
        out.append({"code": int(row[0]), "name": row[1], "role": row[col["역할군"]], **{k: row[col[k]] for k in EDIT_COLS}})
    return out


def sheet_values() -> dict[int, dict]:
    """이미 있는 스킨-진화.xlsx 에서 SG가 적은 노란 칸 (ER번호로)"""
    if not SHEET.exists():
        return {}
    ws = load_workbook(SHEET)["스킨 진화"]
    head = [c.value for c in ws[1]]
    col = {h: i for i, h in enumerate(head)}
    out = {}
    for row in ws.iter_rows(min_row=2, values_only=True):
        if row[0] in (None, ""):
            continue
        out[int(row[0])] = {k: row[col[k]] for k in (*EDIT_COLS, "메모") if k in col}
    return out


def make() -> None:
    skins, art = er_skins()
    rows = main_rows()
    kept = sheet_values()
    most = max(len(skins.get(r["code"], [])) - 1 for r in rows)

    wb = Workbook()
    rd = wb.active
    rd.title = "읽어 주세요"
    lines = [
        ("스킨 진화 정하기 (11-19)", True),
        ("· '스킨 진화' 시트에서 노란 칸만 고쳐요. 한 줄 = 실험체 한 명.", False),
        ("· 진화1 스킨 · 진화2 스킨: 칸을 누르면 그 실험체의 ER 스킨 목록이 나와요. 번호만 적어도 돼요 (예: 3).", False),
        ("· ✓ · 초록 칸 = 팬키트 전투 그림이 있는 스킨. 그림이 없는 스킨을 고르면 게임에서는 이름 뒤 ★, 그림은 기본 모습이에요.", False),
        ("· 고른 스킨은 오른쪽 스킨 목록에서 주황색으로 보여요.", False),
        ("· 진화를 한 번만 하려면 진화2 스킨 · 진화2 레벨을 비워요 (지금 스킨이 1개뿐인 실험체가 그래요).", False),
        ("· 레벨: 진화1 은 2~99, 진화2 는 진화1 보다 커야 해요.", False),
        ("· 진화하며 역할군이 바뀌면 '후 역할군' 을 골라요. 그대로면 비워요.", False),
        ("· 처음 값은 지금 게임 값이에요 (대부분 스킨 1번 Lv12 · 2번 Lv24, 임시).", False),
        ("· 다 고치면 이 파일을 채팅에 올려 주세요. Claude 가 'skin_evo.py --import' 로 게임에 넣어요.", False),
    ]
    for i, (t, bold) in enumerate(lines, 1):
        rd.cell(i, 1, t).font = Font(name=F, size=13 if bold else 10, bold=bold)
    rd.column_dimensions["A"].width = 110

    ws = wb.create_sheet("스킨 진화")
    names = [*HEAD_COLS, *(f"스킨 {k}" for k in range(1, most + 1))]
    widths = [7, 10, 10, 7, 24, 9, 12, 24, 9, 12, 22, *([22] * most)]
    for c, (h, w) in enumerate(zip(names, widths), 1):
        cell = ws.cell(1, c, h)
        cell.font = Font(name=F, size=10, bold=True, color="FFFFFF")
        cell.fill = HEAD
        cell.alignment = Alignment(horizontal="center", vertical="center", wrap_text=True)
        cell.border = BORDER
        ws.column_dimensions[get_column_letter(c)].width = w
    ws.row_dimensions[1].height = 30
    ws.freeze_panes = "C2"

    role_dv = DataValidation(type="list", formula1='"' + ",".join(ROLES) + '"', allow_blank=True)
    lv1_dv = DataValidation(type="whole", operator="between", formula1="2", formula2="99", allow_blank=True)
    lv2_dv = DataValidation(type="whole", operator="between", formula1="3", formula2="100", allow_blank=True)
    for dv in (role_dv, lv1_dv, lv2_dv):
        ws.add_data_validation(dv)
    c_of = {h: i for i, h in enumerate(HEAD_COLS, 1)}
    last = get_column_letter(SKIN0 + most - 1)
    for r, row in enumerate(rows, 2):
        code = row["code"]
        names_ = skins.get(code, [])
        have = art.get(code, set())
        texts = [skin_text(k, n, have) for k, n in enumerate(names_) if k > 0]
        val = kept.get(code) or row
        cells = {
            "ER번호": code,
            "이름": row["name"],
            "기본 역할군": row["role"],
            "스킨 수": len(texts),
            "메모": (kept.get(code) or {}).get("메모"),
        }
        for k in EDIT_COLS:
            v = val.get(k)
            if k.endswith("스킨"):
                n = skin_no(v)
                v = texts[n - 1] if n and 0 < n <= len(texts) else v
            cells[k] = v
        for h, c in c_of.items():
            cell = ws.cell(r, c, cells[h])
            cell.font = Font(name=F, size=10)
            cell.border = BORDER
            cell.alignment = Alignment(vertical="center")
            if h in EDIT_COLS or h == "메모":
                cell.fill = EDIT
        for i, t in enumerate(texts):
            cell = ws.cell(r, SKIN0 + i, t)
            cell.font = Font(name=F, size=9)
            cell.border = BORDER
            if (i + 1) in have:
                cell.fill = HAVE
        # 진화 스킨 고르기: 그 줄의 스킨 목록
        if texts:
            dv = DataValidation(
                type="list",
                formula1=f"${get_column_letter(SKIN0)}${r}:${get_column_letter(SKIN0 + len(texts) - 1)}${r}",
                allow_blank=True,
                showErrorMessage=False,  # 번호만 적어도 돼요
            )
            ws.add_data_validation(dv)
            dv.add(f"{get_column_letter(c_of['진화1 스킨'])}{r}")
            dv.add(f"{get_column_letter(c_of['진화2 스킨'])}{r}")
        role_dv.add(f"{get_column_letter(c_of['진화1 후 역할군'])}{r}")
        role_dv.add(f"{get_column_letter(c_of['진화2 후 역할군'])}{r}")
        lv1_dv.add(f"{get_column_letter(c_of['진화1 레벨'])}{r}")
        lv2_dv.add(f"{get_column_letter(c_of['진화2 레벨'])}{r}")
    # 고른 스킨 주황 (번호로 비교해서 '3' 만 적어도 보여요)
    e1, e2 = get_column_letter(c_of["진화1 스킨"]), get_column_letter(c_of["진화2 스킨"])
    first = get_column_letter(SKIN0)
    n_of = lambda ref: f'IFERROR(VALUE(LEFT({ref},FIND(" ",{ref}&" ")-1)),-1)'  # noqa: E731
    ws.conditional_formatting.add(
        f"{first}2:{last}{len(rows) + 1}",
        FormulaRule(
            formula=[f'AND({first}2<>"",OR({n_of(first + "2")}={n_of("$" + e1 + "2")},{n_of(first + "2")}={n_of("$" + e2 + "2")}))'],
            fill=PICK,
            font=Font(name=F, size=9, bold=True),
        ),
    )
    SHEET.parent.mkdir(parents=True, exist_ok=True)
    wb.save(SHEET)
    print(f"{SHEET.relative_to(ROOT)}: 실험체 {len(rows)}명 · 스킨 칸 {most}개 (SG 값 그대로 {len(kept)}명)")


def do_import() -> None:
    skins, _art = er_skins()
    ws = load_workbook(SHEET, data_only=True)["스킨 진화"]
    head = [c.value for c in ws[1]]
    col = {h: i for i, h in enumerate(head)}
    errors, picked = [], {}
    for r, row in enumerate(ws.iter_rows(min_row=2, values_only=True), 2):
        if row[0] in (None, ""):
            continue
        code = int(row[0])
        at = f"스킨 진화 {r}줄 ({row[1]})"
        n = len(skins.get(code, [])) - 1
        s1, s2 = skin_no(row[col["진화1 스킨"]]), skin_no(row[col["진화2 스킨"]])
        lv = []
        for k in ("진화1 레벨", "진화2 레벨"):
            v = row[col[k]]
            try:
                lv.append(None if v in (None, "") else int(round(float(v))))
            except (TypeError, ValueError):
                errors.append(f"{at}: {k} 가 숫자가 아니에요 ({v})")
                lv.append(None)
        l1, l2 = lv
        if s1 is None or not (1 <= s1 <= n):
            errors.append(f"{at}: 진화1 스킨은 1~{n}번 중에서 골라요 ({row[col['진화1 스킨']]})")
        if l1 is None or not (2 <= l1 <= 99):
            errors.append(f"{at}: 진화1 레벨은 2~99 ({l1})")
        if s2 is not None and not (1 <= s2 <= n):
            errors.append(f"{at}: 진화2 스킨은 1~{n}번 중에서 골라요 ({row[col['진화2 스킨']]})")
        if s2 is not None and s2 == s1:
            errors.append(f"{at}: 진화1 · 진화2 스킨이 같아요")
        if (s2 is None) != (l2 is None):
            errors.append(f"{at}: 진화2 는 스킨 · 레벨을 둘 다 적거나 둘 다 비워요")
        if l1 is not None and l2 is not None and l2 <= l1:
            errors.append(f"{at}: 진화2 레벨이 진화1 레벨보다 커야 해요")
        roles = []
        for k in ("진화1 후 역할군", "진화2 후 역할군"):
            v = str(row[col[k]] or "").strip()
            v = ROLE_ALIAS.get(v, v)
            if v and v not in ROLES:
                errors.append(f"{at}: {k} '{v}' 는 없는 역할군이에요 ({' · '.join(ROLES)})")
            roles.append(v or None)
        if s2 is None and roles[1]:
            errors.append(f"{at}: 진화가 한 번이면 진화2 후 역할군은 비워요")
        picked[code] = dict(zip(EDIT_COLS, (s1, l1, roles[0], s2, l2, roles[1])))
    if errors:
        print("고칠 칸이 있어서 아무것도 안 바꿨어요:")
        for e in errors:
            print("  -", e)
        sys.exit(1)

    wb = load_workbook(MAIN)
    ws = wb["실험체"]
    head = [c.value for c in ws[1]]
    col = {h: i + 1 for i, h in enumerate(head)}
    changed = []
    for r in range(2, ws.max_row + 1):
        code = ws.cell(r, 1).value
        if code in (None, "") or int(code) not in picked:
            continue
        for k, v in picked[int(code)].items():
            cell = ws.cell(r, col[k])
            if (cell.value if cell.value != "" else None) != v:
                cell.value = v
                changed.append(f"{ws.cell(r, 2).value} {k}")
    missing = set(picked) - {int(ws.cell(r, 1).value) for r in range(2, ws.max_row + 1) if ws.cell(r, 1).value not in (None, "")}
    if missing:
        print("  (실험체-스킬.xlsx 에 없는 ER번호)", sorted(missing))
    wb.calculation.fullCalcOnLoad = True  # 합 칸 수식은 엑셀이 열 때 다시 계산
    wb.save(MAIN)
    print(f"{MAIN.relative_to(ROOT)} '실험체' 진화 칸 {len(changed)}개 바꿈")
    for c in changed[:40]:
        print("  ·", c)
    subprocess.run([sys.executable, "-I", "-B", str(ROOT / "scripts/er-sheet/import_sheet.py"), "--keep-moves"], check=True)


if __name__ == "__main__":
    if "--import" in sys.argv:
        do_import()
    else:
        make()
