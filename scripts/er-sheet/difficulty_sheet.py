# SPDX-FileCopyrightText: 2026 SG
# SPDX-License-Identifier: AGPL-3.0-only
"""
난이도 시트 (docs/sheets/난이도.xlsx) ↔ 게임: 마스터즈 팀 · 팀 전투 자리 · 사기 실험체

11-19 SG (난이도.xlsx 메모):
  · 관장들을 마스터즈 팀(나중에 내가 추가할 수 있게 따로 시트)으로 배치해 특정 라운드마다 나오게. 역할군대로 관장이 나오는 게 아님
  · 티어에 따라 팀 전투(5 · 15 · 25 · 35 · 45웨이브)에 나오는 상대가 다르게:
    아이언 ~ 메테오라이트 = 옛날 사기 실험체(영입 불가, 전설의 포켓몬 느낌) · 미스릴 = 사기 실험체 + 마스터즈 팀 · 데미갓부터 = KEL 팀 위주
  · 이터니티는 어려운 조건을 해야 승급 → 추천 목록 (SG가 고름, 아직 게임에 안 넣음)

쓰는 법: python3 -I -B scripts/er-sheet/difficulty_sheet.py [엑셀]   (기본 docs/sheets/난이도.xlsx)
  1) 시트가 없으면 더해요: '마스터즈 팀' · '팀 전투 자리' · '사기 실험체' · '이터니티 조건'. 있으면 SG가 적은 값은 그대로 둬요.
  2) 세 시트('마스터즈 팀' · '팀 전투 자리' · '사기 실험체')를 읽어 src/data/bseorogue/difficulty-sheet.ts 를 써요.
  → 그 뒤: pnpm exec biome format --write src/data/bseorogue/difficulty-sheet.ts 그리고 블서로그 테스트
'이터니티 조건' 시트는 SG가 고르면 제가 게임에 넣어요 (지금은 읽지 않아요).
"""
import json
import re
import sys
from pathlib import Path

from openpyxl import load_workbook
from openpyxl.styles import Alignment, Border, Font, PatternFill, Side
from openpyxl.utils import get_column_letter
from openpyxl.worksheet.datavalidation import DataValidation

ROOT = Path(__file__).resolve().parents[2]
XLSX = ROOT / "docs/sheets/난이도.xlsx"
OUT = ROOT / "src/data/bseorogue/difficulty-sheet.ts"

TIERS = ["아이언", "브론즈", "실버", "골드", "플래티넘", "다이아몬드", "메테오라이트", "미스릴", "데미갓", "이터니티"]
TEAM_WAVES = [5, 15, 25, 35, 45]
KIND = {"사기 실험체": "op", "마스터즈": "masters", "KEL": "kel"}
OP, MA, KE = "사기 실험체", "마스터즈", "KEL"
# 11-19 SG 메모대로 처음 값 (시트 노란 칸에서 바꿔요)
DEFAULT_SLOTS = [[OP] * 5] * 7 + [[OP, MA, OP, MA, OP]] + [[MA, KE, KE, KE, KE]] * 2
DEFAULT_OP_SEGMENTS = 3

FONT = "Arial"
HEAD = Font(name=FONT, bold=True, color="FFFFFF")
HEAD_FILL = PatternFill("solid", fgColor="2F2A4A")
YELLOW = PatternFill("solid", fgColor="FFFF00")
TITLE = Font(name=FONT, bold=True, size=13)
NORMAL = Font(name=FONT)
NOTE = Font(name=FONT, color="555555")
THIN = Side(style="thin", color="BFBFBF")
BOX = Border(left=THIN, right=THIN, top=THIN, bottom=THIN)
WRAP = Alignment(wrap_text=True, vertical="top")
CENTER = Alignment(horizontal="center", vertical="center")

# 이터니티 승급 조건 추천 (11-19 SG: "특정조건은 나중에 적당한 거 생각해서 나한테 추천해줘 그럼 내가 목록보고 결정할게")
ETERNITY = [
    ("노 데스 클리어", "★★★", "데미갓으로 50웨이브를 실험체가 한 번도 기절하지 않고 클리어 (부활 아이템을 써도 기절은 센다)"),
    ("데미갓 3번 클리어", "★★", "데미갓으로 50웨이브를 3번 클리어 (한 번 운으로는 못 올라감)"),
    ("진화 없이 클리어", "★★★", "스킨 진화를 하지 않은 실험체만으로 데미갓 클리어 (진화 레벨이 되면 진화 취소)"),
    ("시작 3명으로만", "★★★", "판 중 영입 · 보급 상자 실험체 없이, 시작한 3명만으로 데미갓 클리어"),
    ("같은 역할군 3명", "★★", "역할군이 같은 실험체 3명 파티로 데미갓 클리어 (예: 탱커 3명)"),
    ("상점 안 쓰기", "★★", "판 중 상점(크레딧으로 사기)을 한 번도 안 쓰고 데미갓 클리어"),
    ("KEL 팀 전부 이기기", "★★", "데미갓 판에서 KEL 팀 전투를 아무도 기절하지 않고 전부 이기기"),
    ("시간 안에", "★★", "데미갓을 플레이 시간 60분 안에 클리어"),
    ("루미 빨리 쓰러뜨리기", "★★★", "최종 보스 루미(경계 모드)를 5턴 안에 쓰러뜨리고 데미갓 클리어"),
    ("실험체 많이 열기", "★", "해금한 실험체 50명 이상 + 데미갓 클리어 (모으는 재미)"),
]

ROLE_ORDER = ["TANK", "BRUISER", "ASSASSIN", "MARKSMAN", "MAGE", "SUPPORT"]
# 11-18 까지 쓰던 역할군 관장 → 처음 마스터즈 팀 (에이스 = 그 관장). 이름 · 실험체 · 대사는 SG가 시트에서 바꿔요
OLD_LEADERS = [
    (4, "여기서부턴 못 지나가.$우리 팀이 얼마나 단단한지 보여 주지!", "…이걸 버텨 내다니. 지나가도 좋아.", "벽은 부수는 게 아니라 넘는 거야. 다시 와."),
    (1, "정면으로 붙자!$우리는 도망치지 않아!", "좋은 싸움이었어. 더 세져서 또 만나!", "아직 멀었네. 몸부터 다시 만들어 와!"),
    (23, "눈치챘을 땐 이미 늦었어.", "내 움직임을 다 읽다니… 인정할게.", "뒤를 조심했어야지."),
    (31, "사거리 안에 들어온 순간 끝이야.", "조준이 빗나갔네. 네가 이겼어.", "거리를 못 좁히면 이길 수 없어."),
    (5, "스킬 한 방이면 충분하다.", "계산이 틀렸군… 다음엔 지지 않는다.", "스킬 저항을 더 챙기는 게 좋을 거다."),
    (41, "우리 팀은 쉽게 쓰러지지 않아요!", "끝까지 지켜 내지 못했네요… 축하해요!", "혼자 싸우면 오래 못 버텨요."),
]


def characters() -> tuple[dict[int, str], dict[int, str]]:
    """ER 번호 → (이름, 역할군)"""
    src = (ROOT / "src/data/bseorogue/er-data.ts").read_text(encoding="utf-8")
    found = re.findall(r'\n  "(\d+)": \{\n    name: "([^"]+)",\n    en: "[^"]*",\n    role: "(\w+)"', src)
    playable = set(int(c) for c in re.findall(r"\n  (\d+): \{\n    role:", (ROOT / "src/data/bseorogue/sheet-data.ts").read_text(encoding="utf-8")))
    names = {int(c): n for c, n, _ in found if int(c) in playable}
    roles = {int(c): r for c, _, r in found if int(c) in playable}
    return names, roles


def default_teams(names: dict[int, str], roles: dict[int, str]) -> list[list]:
    """처음 마스터즈 팀 6개: 옛 관장을 에이스로, 다른 역할군 둘을 섞어요"""
    by_role = {r: sorted(c for c, rr in roles.items() if rr == r) for r in ROLE_ORDER}
    used = {code for code, *_ in OLD_LEADERS}
    rows = []
    for i, (ace, enc, dfe, won) in enumerate(OLD_LEADERS):
        r = ROLE_ORDER.index(roles[ace])
        mates = []
        for step in (2, 4):
            pool = [c for c in by_role[ROLE_ORDER[(r + step) % 6]] if c not in used]
            pick = pool[(i * 3) % len(pool)]
            used.add(pick)
            mates.append(pick)
        rows.append([f"마스터즈 {i + 1}팀 (임시)", names[mates[0]], names[mates[1]], names[ace], enc, dfe, won, ""])
    return rows


def header(ws, row: int, cols: list[tuple[str, int]]) -> None:
    for c, (h, w) in enumerate(cols, 1):
        cell = ws.cell(row, c, h)
        cell.font, cell.fill, cell.border = HEAD, HEAD_FILL, BOX
        cell.alignment = Alignment(horizontal="center", vertical="center", wrap_text=True)
        ws.column_dimensions[get_column_letter(c)].width = w


def put(ws, row: int, col: int, value, yellow=False, wrap=False):
    cell = ws.cell(row, col, value)
    cell.font, cell.border = NORMAL, BOX
    if yellow:
        cell.fill = YELLOW
    cell.alignment = WRAP if wrap else Alignment(vertical="top")
    return cell


def add_masters(wb, names, roles) -> None:
    if "마스터즈 팀" in wb.sheetnames:
        return
    ws = wb.create_sheet("마스터즈 팀", wb.sheetnames.index("관장") + 1 if "관장" in wb.sheetnames else None)
    ws["A1"] = "마스터즈 팀 — 관장 웨이브(8 · 18 · 28 · 38 · 48)에 나와요 (11-19 SG: 역할군 관장 대신 마스터즈 팀)"
    ws["A1"].font = TITLE
    ws["A2"] = ("· 줄을 더하면 팀이 늘어나요 (판마다 이 중에서 무작위 순서로 5팀). 실험체는 이름이나 ER 번호. 실험체 3이 에이스(관장 자리, 레벨이 더 높아요). "
                "첫 관장 웨이브는 2명(실험체 2 · 3)만 나와요 ('규칙' 시트 인원). 대사는 $ 로 나누면 여러 장. 빈칸이면 기본 대사.")
    ws["A2"].font, ws["A2"].alignment = NOTE, WRAP
    ws.merge_cells("A2:H2")
    ws.row_dimensions[2].height = 45
    header(ws, 4, [("팀 이름", 24), ("실험체 1", 12), ("실험체 2", 12), ("실험체 3 (에이스)", 14), ("나올 때 대사", 38), ("플레이어가 이겼을 때", 32), ("플레이어가 졌을 때", 32), ("메모", 30)])
    rows = default_teams(names, roles)
    for r in range(len(rows) + 14):
        vals = rows[r] if r < len(rows) else [""] * 8
        for c, v in enumerate(vals, 1):
            put(ws, 5 + r, c, v or None, yellow=True, wrap=c >= 5)
    ws.freeze_panes = "B5"


def add_slots(wb) -> None:
    if "팀 전투 자리" in wb.sheetnames:
        return
    ws = wb.create_sheet("팀 전투 자리", wb.sheetnames.index("팀 전투") + 1 if "팀 전투" in wb.sheetnames else None)
    ws["A1"] = "팀 전투 자리 — 티어마다 5 · 15 · 25 · 35 · 45웨이브에 무엇이 나올지 (11-19 SG 메모대로 처음 값)"
    ws["A1"].font = TITLE
    ws["A2"] = ("· 노란 칸에서 '사기 실험체' · '마스터즈' · 'KEL' 중 골라요. 사기 실험체 = 영입 불가 보스 실험체 1명 (전설의 포켓몬 느낌, 체력 여러 줄, '사기 실험체' 시트). "
                "마스터즈 · KEL = 팀 3명 (무명섬 관리 화면 팀, 없으면 '마스터즈 팀' 시트 · 기본 KEL 팀).")
    ws["A2"].font, ws["A2"].alignment = NOTE, WRAP
    ws.merge_cells("A2:G2")
    ws.row_dimensions[2].height = 45
    header(ws, 4, [("단계", 6), ("티어", 14)] + [(f"{w}웨이브", 13) for w in TEAM_WAVES])
    dv = DataValidation(type="list", formula1=f'"{OP},{MA},{KE}"', allow_blank=False)
    ws.add_data_validation(dv)
    for t, tier in enumerate(TIERS):
        put(ws, 5 + t, 1, t).alignment = CENTER
        put(ws, 5 + t, 2, tier)
        for i, v in enumerate(DEFAULT_SLOTS[t]):
            cell = put(ws, 5 + t, 3 + i, v, yellow=True)
            cell.alignment = CENTER
            dv.add(cell)


def add_op(wb) -> None:
    if "사기 실험체" in wb.sheetnames:
        return
    ws = wb.create_sheet("사기 실험체", wb.sheetnames.index("팀 전투 자리") + 1 if "팀 전투 자리" in wb.sheetnames else None)
    ws["A1"] = "사기 실험체 — 팀 전투 자리에 나오는 영입 불가 보스 실험체 (11-19 SG: 이름은 SG가 적어요)"
    ws["A1"].font = TITLE
    ws["A2"] = (f"· 노란 칸에 실험체 이름이나 ER 번호를 적어요. 판마다 이 중에서 겹치지 않게 골라요. 체력 줄 수가 빈칸이면 {DEFAULT_OP_SEGMENTS}줄. "
                "레벨은 10웨이브 보스처럼 1.2배 · 레벨에 맞는 스킨 진화 모습. **비어 있는 동안은 아무 실험체나** 보스 버전으로 나와요.")
    ws["A2"].font, ws["A2"].alignment = NOTE, WRAP
    ws.merge_cells("A2:C2")
    ws.row_dimensions[2].height = 45
    header(ws, 4, [("실험체 (이름 또는 ER 번호)", 26), ("체력 줄 수 (빈칸 = 3)", 18), ("메모 (왜 사기였는지 등)", 50)])
    for r in range(20):
        for c in range(1, 4):
            put(ws, 5 + r, c, None, yellow=True)


def add_eternity(wb) -> None:
    if "이터니티 조건" in wb.sheetnames:
        return
    ws = wb.create_sheet("이터니티 조건", wb.sheetnames.index("티어") + 1 if "티어" in wb.sheetnames else None)
    ws["A1"] = "이터니티 승급 조건 — 추천 목록 (11-19 SG: \"목록보고 결정할게\")"
    ws["A1"].font = TITLE
    ws["A2"] = "· 쓰고 싶은 조건의 노란 칸에 O (여러 개면 전부 해야 승급). 고르면 제가 게임에 넣어요. 지금은 데미갓으로 50웨이브를 깨면 이터니티가 열려요."
    ws["A2"].font, ws["A2"].alignment = NOTE, WRAP
    ws.merge_cells("A2:F2")
    ws.row_dimensions[2].height = 30
    header(ws, 4, [("번호", 6), ("조건", 22), ("어려움", 9), ("설명", 70), ("SG 고르기 (O)", 13), ("메모", 30)])
    for i, (name, hard, desc) in enumerate(ETERNITY):
        put(ws, 5 + i, 1, i + 1).alignment = CENTER
        put(ws, 5 + i, 2, name)
        put(ws, 5 + i, 3, hard).alignment = CENTER
        put(ws, 5 + i, 4, desc, wrap=True)
        put(ws, 5 + i, 5, None, yellow=True).alignment = CENTER
        put(ws, 5 + i, 6, None, yellow=True, wrap=True)


def notes(wb) -> None:
    """옛 시트에 바뀐 점 한 줄씩"""
    if "관장" in wb.sheetnames:
        ws = wb["관장"]
        if not any("11-19" in str(c.value) for c in ws["A"]):
            r = ws.max_row + 2
            ws.cell(r, 1, "· 11-19 부터 관장 웨이브에는 위 역할군 관장 대신 '마스터즈 팀' 시트의 팀이 나와요 (SG 메모). 위 표는 예전 값이에요.").font = NOTE
    if "팀 전투" in wb.sheetnames:
        ws = wb["팀 전투"]
        if not any("11-19" in str(c.value) for c in ws["A"]):
            r = ws.max_row + 2
            ws.cell(r, 1, "· 11-19 부터 팀 전투 웨이브에 나오는 상대는 티어마다 '팀 전투 자리' 시트대로예요 (위 '나오는 팀' 칸은 예전 규칙).").font = NOTE
    if "읽어 주세요" in wb.sheetnames:
        ws = wb["읽어 주세요"]
        if not any("11-19" in str(c.value) for c in ws["A"]):
            r = ws.max_row + 2
            for i, line in enumerate([
                "11-19 바뀐 것 (SG 메모)",
                "· 관장 웨이브 → '마스터즈 팀' 시트의 팀 (줄을 더하면 팀이 늘어요).",
                "· 팀 전투 웨이브 → 티어마다 '팀 전투 자리' 시트 (사기 실험체 / 마스터즈 / KEL).",
                "· '사기 실험체' 시트: SG가 실험체 이름을 적어요. · '이터니티 조건' 시트: 추천 목록에서 O 로 고르기.",
                "· 이 시트들은 scripts/er-sheet/difficulty_sheet.py 가 게임에 넣어요 (파일을 보내 주면 돼요).",
            ]):
                ws.cell(r + i, 1, line).font = Font(name=FONT, bold=i == 0)


def code_of(v, names: dict[int, str], where: str, errors: list[str]) -> int | None:
    if v is None or str(v).strip() == "":
        return None
    s = str(v).strip()
    if re.fullmatch(r"\d+(\.0)?", s):
        c = int(float(s))
        if c in names:
            return c
        errors.append(f"{where}: ER 번호 {c} 실험체가 없어요")
        return None
    by_name = {n: c for c, n in names.items()}
    if s in by_name:
        return by_name[s]
    errors.append(f"{where}: '{s}' 실험체를 못 찾았어요 (이름을 시트 '실험체' 와 같게)")
    return None


def read(wb, names) -> tuple[list[dict], list[list[str]], list[dict], list[str]]:
    errors: list[str] = []
    teams = []
    ws = wb["마스터즈 팀"]
    for r, row in enumerate(ws.iter_rows(min_row=5, values_only=True), 5):
        if not row or not row[0] or not str(row[0]).strip():
            continue
        members = [code_of(row[c], names, f"마스터즈 팀 {r}줄 실험체 {c}", errors) for c in (1, 2, 3)]
        members = [m for m in members if m is not None]
        if len(members) < 2:
            errors.append(f"마스터즈 팀 {r}줄 ({row[0]}): 실험체를 2명 이상 적어 주세요")
            continue
        text = lambda v: str(v).strip() if v else ""
        teams.append({"name": str(row[0]).strip(), "members": members, "encounter": text(row[4]), "defeated": text(row[5]), "won": text(row[6])})
    if not teams:
        errors.append("마스터즈 팀: 팀이 하나도 없어요")
    slots = []
    ws = wb["팀 전투 자리"]
    for t in range(len(TIERS)):
        row = [ws.cell(5 + t, 3 + i).value for i in range(len(TEAM_WAVES))]
        kinds = []
        for i, v in enumerate(row):
            k = KIND.get(str(v or "").strip())
            if not k:
                errors.append(f"팀 전투 자리 {TIERS[t]} {TEAM_WAVES[i]}웨이브: '{v}' → 사기 실험체 / 마스터즈 / KEL 중 하나")
                k = "op"
            kinds.append(k)
        slots.append(kinds)
    ops = []
    ws = wb["사기 실험체"]
    for r, row in enumerate(ws.iter_rows(min_row=5, values_only=True), 5):
        if not row:
            continue
        c = code_of(row[0], names, f"사기 실험체 {r}줄", errors)
        if c is None:
            continue
        seg = row[1]
        try:
            seg = int(float(seg)) if seg not in (None, "") else DEFAULT_OP_SEGMENTS
        except ValueError:
            errors.append(f"사기 실험체 {r}줄: 체력 줄 수는 숫자 (지금 '{seg}')")
            seg = DEFAULT_OP_SEGMENTS
        ops.append({"erCode": c, "segments": max(1, min(6, seg))})
    return teams, slots, ops, errors


def write_ts(teams, slots, ops, names) -> None:
    q = lambda s: json.dumps(s, ensure_ascii=False)
    lines = [
        "/*",
        " * SPDX-FileCopyrightText: 2026 SG",
        " * SPDX-License-Identifier: AGPL-3.0-only",
        " */",
        "",
        "// 이 파일은 scripts/er-sheet/difficulty_sheet.py 가 만들어요 (docs/sheets/난이도.xlsx). 직접 고치지 마세요.",
        "",
        '/** 팀 전투 자리에 나오는 것: 사기 실험체(영입 불가 보스) · 마스터즈 팀 · KEL 팀 */',
        'export type TeamSlotKind = "op" | "masters" | "kel";',
        "",
        "export interface MastersTeam {",
        "  name: string;",
        "  /** 실험체 ER 번호 (마지막이 에이스) */",
        "  members: readonly number[];",
        "  encounter: string;",
        "  /** 플레이어가 이겼을 때 */",
        "  defeated: string;",
        "  /** 플레이어가 졌을 때 */",
        "  won: string;",
        "}",
        "",
        "/** 시트 '마스터즈 팀': 관장 웨이브에 나오는 팀 */",
        "export const MASTERS_TEAMS: readonly MastersTeam[] = [",
    ]
    for t in teams:
        lines.append(f"  {{ name: {q(t['name'])}, members: {json.dumps(t['members'])}, encounter: {q(t['encounter'])}, defeated: {q(t['defeated'])}, won: {q(t['won'])} }}, // {' · '.join(names[m] for m in t['members'])}")
    lines += [
        "];",
        "",
        "/** 시트 '팀 전투 자리': [티어 0 아이언 ~ 9 이터니티][팀 전투 웨이브 순서 (BSEO.teamWaves)] */",
        "export const TEAM_SLOTS: readonly (readonly TeamSlotKind[])[] = [",
        *[f"  {json.dumps(s)}, // {TIERS[i]}" for i, s in enumerate(slots)],
        "];",
        "",
        "export interface OpExperiment {",
        "  erCode: number;",
        "  /** 보스 체력 줄 수 */",
        "  segments: number;",
        "}",
        "",
        "/** 시트 '사기 실험체' (비어 있으면 아무 실험체나 보스 버전으로) */",
        "export const OP_EXPERIMENTS: readonly OpExperiment[] = [",
        *[f"  {{ erCode: {o['erCode']}, segments: {o['segments']} }}, // {names[o['erCode']]}" for o in ops],
        "];",
        "",
        f"/** '사기 실험체' 시트에 체력 줄 수를 안 적었을 때 · 목록이 비어 아무 실험체나 나올 때 */",
        f"export const OP_DEFAULT_SEGMENTS = {DEFAULT_OP_SEGMENTS};",
        "",
    ]
    OUT.write_text("\n".join(lines), encoding="utf-8")


def main() -> None:
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    path = Path(args[0]) if args else XLSX
    wb = load_workbook(path)
    names, roles = characters()
    add_masters(wb, names, roles)
    add_slots(wb)
    add_op(wb)
    add_eternity(wb)
    notes(wb)
    teams, slots, ops, errors = read(wb, names)
    if errors:
        raise SystemExit("\n".join(errors))
    wb.save(path)
    write_ts(teams, slots, ops, names)
    print(f"{path.name}: 마스터즈 팀 {len(teams)}개 · 팀 전투 자리 {len(slots)}티어 · 사기 실험체 {len(ops)}명 → {OUT.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
