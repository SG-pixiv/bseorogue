# SPDX-FileCopyrightText: 2026 SG
# SPDX-License-Identifier: AGPL-3.0-only
"""
난이도 정리 엑셀 만들기 (11-18 SG: "관장 및 티어 - 마스터즈 - kel 난이도 단계 … 엑셀로 기존 난이도 책정 정리해서 주면 내가 수정해서 줄게")

  python3 -I -B scripts/er-sheet/make_difficulty.py [출력 파일]   (기본 docs/sheets/난이도.xlsx)

지금 게임에 들어간 숫자(src/bseorogue.ts · tiers.ts · leaders.ts · kel.ts · src/battle.ts · src/field/trainer.ts)를
그대로 옮겨 적고, 레벨은 수식으로 계산해요. SG는 노란 칸만 고치면 돼요.
게임이 바뀌면 아래 숫자도 같이 고쳐요 (이 파일은 게임에서 읽지 않아요. SG가 보내 주면 제가 코드에 옮겨요).
"""

import re
import sys
from pathlib import Path

from openpyxl import Workbook
from openpyxl.comments import Comment
from openpyxl.styles import Alignment, Border, Font, PatternFill, Side
from openpyxl.utils import get_column_letter
from openpyxl.worksheet.datavalidation import DataValidation

ROOT = Path(__file__).resolve().parents[2]
OUT = Path(sys.argv[1]) if len(sys.argv) > 1 else ROOT / "docs/sheets/난이도.xlsx"

FONT = "Arial"
BLUE = Font(name=FONT, color="0000FF")
BLACK = Font(name=FONT, color="000000")
GREEN = Font(name=FONT, color="008000")
BOLD = Font(name=FONT, bold=True)
HEAD = Font(name=FONT, bold=True, color="FFFFFF")
TITLE = Font(name=FONT, bold=True, size=14)
HEAD_FILL = PatternFill("solid", fgColor="2F2A4A")
YELLOW = PatternFill("solid", fgColor="FFFF00")
SOFT = PatternFill("solid", fgColor="F2F2F2")
THIN = Side(style="thin", color="BFBFBF")
BOX = Border(left=THIN, right=THIN, top=THIN, bottom=THIN)
WRAP = Alignment(wrap_text=True, vertical="top")
CENTER = Alignment(horizontal="center", vertical="center")

TIERS = ["아이언", "브론즈", "실버", "골드", "플래티넘", "다이아몬드", "메테오라이트", "미스릴", "데미갓", "이터니티"]
ROLE_KO = {"TANK": "탱커", "BRUISER": "브루저", "ASSASSIN": "암살자", "MARKSMAN": "평원딜", "MAGE": "스증딜러", "SUPPORT": "서포터"}


def with_ro(word: str) -> str:
    """받침이 있으면 '으로', 없거나 ㄹ 받침이면 '로' (아이언으로 · 미스릴로 · 골드로)"""
    code = ord(word[-1]) - 0xAC00
    jong = code % 28 if 0 <= code < 11172 else 0
    return word + ("로" if jong in (0, 8) else "으로")


def read_leaders() -> list[tuple[str, int, str, str, str, str]]:
    src = (ROOT / "src/data/bseorogue/leaders.ts").read_text(encoding="utf-8")
    pat = r'role: "(\w+)",\s*erCode: (\d+), // (\S+)\s*encounter: "([^"]*)",\s*defeated: "([^"]*)",\s*won: "([^"]*)"'
    return [(r, int(c), n, e, d, w) for r, c, n, e, d, w in re.findall(pat, src)]


def read_bseo() -> dict:
    src = (ROOT / "src/bseorogue.ts").read_text(encoding="utf-8")

    def arr(name: str) -> list[int]:
        return [int(x) for x in re.search(rf"{name}: \[([^\]]*)\]", src).group(1).split(",")]

    leagues = {k: int(w) for k, w in re.findall(r'key: "(\w+)", name: "[^"]*", fromWave: (\d+)', src)}
    return {
        "final": int(re.search(r"classicFinalWave: (\d+)", src).group(1)),
        "teamWaves": arr("teamWaves"),
        "leaderWaves": arr("leaderWaves"),
        "wildAnimalRate": float(re.search(r"wildAnimalRate: ([\d.]+)", src).group(1)),
        "kel": leagues["kel"],
        "kelFinal": leagues["final"],
        "tierBonus": float(
            re.search(r"TIER_LEVEL_BONUS = ([\d.]+)", (ROOT / "src/data/bseorogue/tiers.ts").read_text()).group(1)
        ),
    }


def read_teams() -> list[tuple[str, str]]:
    src = (ROOT / "src/data/bseorogue/kel.ts").read_text(encoding="utf-8")
    return re.findall(r'\["([^"]+)", "([^"]+)"\]', src)


def header(ws, row: int, names: list[str], widths: list[int] | None = None) -> None:
    for i, n in enumerate(names, 1):
        c = ws.cell(row, i, n)
        c.font, c.fill, c.alignment, c.border = HEAD, HEAD_FILL, CENTER, BOX
    if widths:
        for i, w in enumerate(widths, 1):
            ws.column_dimensions[get_column_letter(i)].width = w


def put(ws, row: int, col: int, value, font=BLACK, fill=None, fmt=None, wrap=False):
    c = ws.cell(row, col, value)
    c.font, c.border = font, BOX
    if fill:
        c.fill = fill
    if fmt:
        c.number_format = fmt
    if wrap:
        c.alignment = WRAP
    return c


def main() -> None:
    b = read_bseo()
    leaders = read_leaders()
    teams = read_teams()
    wb = Workbook()

    # ── 읽어 주세요 ──
    ws = wb.active
    ws.title = "읽어 주세요"
    ws.column_dimensions["A"].width = 110
    lines = [
        ("블서로그 난이도 정리 (11-18, 지금 게임에 들어간 숫자)", TITLE),
        ("", None),
        ("고치는 법", BOLD),
        ("· 노란 칸만 고쳐 주세요. 노란 칸에는 지금 값이 들어 있어요 (그대로 두면 지금처럼).", None),
        ("· 파란 글자 = 지금 게임에 들어간 숫자 (참고용, 안 고쳐도 돼요). 검은 글자 = 계산 (자동). 초록 글자 = 다른 시트에서 가져온 값.", None),
        ("· 다 고치면 이 파일을 그대로 보내 주세요. 제가 게임 코드에 옮겨요 (이 파일을 게임이 바로 읽지는 않아요).", None),
        ("· 숫자 말고 생각을 적고 싶으면 각 시트 오른쪽 '메모' 칸에 적어 주세요.", None),
        ("", None),
        ("지금 난이도가 정해지는 방식", BOLD),
        (f"1. 한 판은 {b['final']}웨이브. 리그: 마스터즈(1~{b['kel'] - 1}) → KEL 승격({b['kel']}~{b['kelFinal'] - 1}) → KEL 결승({b['kelFinal']}~{b['final']}).", None),
        (f"2. 적 레벨 = 웨이브로 정해지는 기본 레벨 × 티어 배율. 기본 레벨 = 1 + 웨이브/2 + (웨이브/25)². 10 · 20 · 30 … 웨이브는 보스(× 보스 배율).", None),
        (f"3. 티어(아이언 → 이터니티, 10단계)는 판 밖 랭크예요. 그 티어로 {b['final']}웨이브를 깨면 다음 티어가 열려요. 한 단계 오를 때마다 적 레벨 +{b['tierBonus']:.0%}.", None),
        (f"4. 팀 전투(마스터즈 · KEL 팀, 실험체 3명): {', '.join(map(str, b['teamWaves']))}웨이브. 마스터즈 구간이면 마스터즈 팀, 그 뒤는 KEL 팀.", None),
        (f"5. 관장(역할군마다 1명, 6명 중 5명이 판마다 무작위 순서): {', '.join(map(str, b['leaderWaves']))}웨이브. 첫 관장은 2명, 그다음은 3명 팀 (마지막이 관장 본인).", None),
        (f"6. 일반 웨이브는 실험체 또는 동물 (동물 {b['wildAnimalRate']:.0%}). 일반 웨이브 레벨은 기본 레벨에서 조금(0~2) 위로 흔들려요.", None),
        ("", None),
        ("지금 숫자에서 눈여겨볼 것 (제가 본 것)", BOLD),
        ("· 티어 배율은 지금 일반 웨이브 · 보스에만 붙고, 관장 · 마스터즈 · KEL 팀에는 안 붙어요 (포켓로그 트레이너 레벨 계산을 그대로 써서). "
         "'규칙' 시트의 '티어를 관장 · 팀에도' 칸을 '예'로 바꾸면 붙였을 때 레벨을 볼 수 있어요.", None),
        ("· 그래서 이터니티(+27%)에서는 일반 웨이브 적이 관장 · 팀보다 레벨이 높아지는 구간이 있어요 ('웨이브' 시트에서 확인).", None),
        ("· 관장 · 팀의 실험체는 레벨에 맞춰 스킨 진화한 모습으로 나와요 (Lv12 · 24, 진화 한 번 실험체는 18).", None),
        ("", None),
        ("시트", BOLD),
        ("· 규칙: 공통 숫자 (배율 · 인원 · 리그 시작 웨이브).  · 티어: 10단계 배율.  · 웨이브: 1~50웨이브 전투 종류와 적 레벨 (아이언 · 골드 · 이터니티).", None),
        ("· 관장: 관장 6명 (역할군 · 실험체 · 대사) + 관장 웨이브.  · 팀 전투: 마스터즈 · KEL 웨이브 + 팀 이름 (실제 팀은 무명섬 관리 화면에서 정해요).", None),
    ]
    for i, (t, f) in enumerate(lines, 1):
        c = ws.cell(i, 1, t)
        c.font = f or Font(name=FONT)
        c.alignment = Alignment(wrap_text=True, vertical="top")
    ex = len(lines) + 2
    ws.cell(ex, 1, "칸 색 예시").font = BOLD
    for j, (txt, font, fill) in enumerate(
        [("노란 칸: SG가 고치는 값", BLACK, YELLOW), ("파란 글자: 지금 게임 값", BLUE, None), ("검은 글자: 계산", BLACK, None), ("초록 글자: 다른 시트 값", GREEN, None)],
        1,
    ):
        put(ws, ex + j, 1, txt, font, fill)

    # ── 규칙 ──
    ws = wb.create_sheet("규칙")
    header(ws, 1, ["항목", "지금 값", "SG 값 (노란 칸)", "설명 · 코드 위치"], [34, 12, 16, 80])
    rules = [
        ("티어 한 단계마다 적 레벨 +", b["tierBonus"], "0%", "src/data/bseorogue/tiers.ts TIER_LEVEL_BONUS (아이언 0단계 · 이터니티 9단계)"),
        ("보스 웨이브(10의 배수) 레벨 배율", 1.2, "0.00", "src/battle.ts bossMultiplier"),
        ("팀 전투 · 관장 팀원 레벨 배율", 1.12, "0.000", "src/field/trainer.ts AVERAGE (팀 전투 3명 · 관장 팀원)"),
        ("25웨이브마다 팀원 배율 +", 0.025, "0.000", "src/field/trainer.ts (25웨이브부터 +0.025)"),
        ("팀원 배율 최대", 1.225, "0.000", "src/field/trainer.ts"),
        ("관장 본인 레벨 배율", 1.22, "0.000", "src/field/trainer.ts STRONG (관장 팀의 마지막)"),
        ("일반 웨이브 동물 비율", b["wildAnimalRate"], "0%", "src/bseorogue.ts wildAnimalRate (나머지는 실험체)"),
        ("마지막 웨이브", b["final"], "0", "src/bseorogue.ts classicFinalWave (최종 보스: 루미)"),
        ("KEL 승격 웨이브", b["kel"], "0", "src/bseorogue.ts leagues (마스터즈 → KEL)"),
        ("KEL 결승 웨이브", b["kelFinal"], "0", "src/bseorogue.ts leagues"),
        ("첫 관장 팀 인원", 2, "0", "src/data/bseorogue/leaders.ts (관장 본인 포함)"),
        ("그다음 관장 팀 인원", 3, "0", "src/data/bseorogue/leaders.ts"),
        ("팀 전투 인원", 3, "0", "src/data/bseorogue/kel.ts"),
        ("티어를 관장 · 팀에도 (예/아니요)", "아니요", "@", "지금은 '아니요' (일반 웨이브 · 보스에만 티어 배율). '예'로 바꾸면 웨이브 시트가 붙였을 때 레벨로 바뀌어요"),
    ]
    for i, (name, cur, fmt, note) in enumerate(rules, 2):
        put(ws, i, 1, name)
        put(ws, i, 2, cur, BLUE, fmt=fmt)
        put(ws, i, 3, cur, BLACK, YELLOW, fmt=fmt)
        put(ws, i, 4, note, wrap=True)
    dv = DataValidation(type="list", formula1='"예,아니요"', allow_blank=False)
    ws.add_data_validation(dv)
    dv.add("C15")
    ws.freeze_panes = "A2"
    R = {k: f"규칙!$C${i}" for i, k in enumerate(
        ["bonus", "boss", "avg", "avgStep", "avgMax", "strong", "animal", "final", "kel", "kelFinal", "lead1", "lead2", "team", "tierAll"], 2)}

    # ── 티어 ──
    ws = wb.create_sheet("티어")
    header(ws, 1, ["단계", "티어", "지금 적 레벨 배율", "SG 배율 (노란 칸)", "해금 조건 (지금)", "메모"], [7, 14, 16, 18, 40, 40])
    for i, t in enumerate(TIERS):
        r = i + 2
        put(ws, r, 1, i, BLUE)
        put(ws, r, 2, t, BLUE)
        put(ws, r, 3, f"=1+{R['bonus']}*A{r}", GREEN, fmt="0.00")
        put(ws, r, 4, f"=C{r}", BLACK, YELLOW, fmt="0.00")
        put(ws, r, 5, "처음부터 열림" if i == 0 else f"{with_ro(TIERS[i - 1])} {b['final']}웨이브 클리어", BLUE)
        put(ws, r, 6, None, fill=YELLOW)
    ws.cell(13, 1, "SG 배율 칸은 지금 배율을 따라가요 (=C 칸). 티어마다 따로 정하고 싶으면 숫자를 직접 적어 주세요 (예: 1.05).").font = Font(name=FONT, italic=True)
    ws.freeze_panes = "A2"

    # ── 웨이브 ──
    ws = wb.create_sheet("웨이브")
    cols = ["웨이브", "리그", "전투", "기본 레벨", "배율", "보정", "레벨 (티어 전)", "아이언", "골드", "이터니티", "관장 본인 (아이언)", "메모"]
    header(ws, 1, cols, [8, 11, 20, 10, 8, 8, 13, 9, 9, 10, 16, 40])
    for w in range(1, b["final"] + 1):
        r = w + 1
        if w in b["teamWaves"]:
            kind = "팀 전투"
        elif w in b["leaderWaves"]:
            kind = "관장"
        elif w == b["final"]:
            kind = "최종 보스"
        elif w % 10 == 0:
            kind = "보스"
        else:
            kind = "일반"
        put(ws, r, 1, w, BLUE)
        put(ws, r, 2, f'=IF(A{r}>={R["kelFinal"]},"KEL 결승",IF(A{r}>={R["kel"]},"KEL","마스터즈"))')
        put(ws, r, 3, kind, BLUE)
        put(ws, r, 4, f"=1+A{r}/2+(A{r}/25)^2", fmt="0.0")
        trainer = f'OR(C{r}="팀 전투",C{r}="관장")'
        boss = f'OR(C{r}="보스",C{r}="최종 보스")'
        put(ws, r, 5, f"=IF({boss},{R['boss']},IF({trainer},MIN({R['avg']}+{R['avgStep']}*INT(A{r}/25),{R['avgMax']}),1))", fmt="0.000")
        put(ws, r, 6, f"=IF({trainer},-INT(A{r}/50),0)", fmt="0")
        put(ws, r, 7, f"=IF({trainer},CEILING(D{r}*E{r},1)+F{r},IF({boss},INT(D{r}*E{r}),MAX(1,ROUND(D{r},0))))", fmt="0")
        for col, tier_row in ((8, 2), (9, 5), (10, 11)):
            put(ws, r, col, f'=MAX(1,ROUND(G{r}*IF(AND({trainer},{R["tierAll"]}<>"예"),1,티어!$D${tier_row}),0))', fmt="0")
        if kind == "관장":
            put(ws, r, 11, f'=MAX(1,ROUND(CEILING(D{r}*{R["strong"]},1)*IF({R["tierAll"]}="예",티어!$D$2,1),0))', fmt="0")
        else:
            put(ws, r, 11, None)
        put(ws, r, 12, None, fill=YELLOW)
        if kind != "일반":
            for c in range(1, 12):
                ws.cell(r, c).fill = SOFT
    ws.cell(2, 7).comment = Comment("일반 웨이브는 이 값에서 0~2 정도 위로 흔들려요 (무작위). 보스는 ±(웨이브/10) 흔들려요 (마지막 웨이브는 안 흔들림).", "Claude")
    ws.cell(2, 11).comment = Comment("관장 팀의 마지막(관장 본인) 레벨. 팀원은 '아이언' 칸 레벨이에요.", "Claude")
    ws.freeze_panes = "B2"

    # ── 관장 ──
    ws = wb.create_sheet("관장")
    header(ws, 1, ["역할군", "관장 ER번호", "관장 이름 (지금)", "나올 때 대사 ($ = 다음 장)", "플레이어가 이겼을 때", "플레이어가 졌을 때", "메모"], [10, 12, 14, 44, 36, 36, 30])
    for i, (role, code, name, enc, dfd, won) in enumerate(leaders, 2):
        put(ws, i, 1, ROLE_KO.get(role, role), BLUE)
        put(ws, i, 2, code, BLACK, YELLOW)
        put(ws, i, 3, name, BLUE)
        put(ws, i, 4, enc, BLACK, YELLOW, wrap=True)
        put(ws, i, 5, dfd, BLACK, YELLOW, wrap=True)
        put(ws, i, 6, won, BLACK, YELLOW, wrap=True)
        put(ws, i, 7, None, fill=YELLOW)
    top = len(leaders) + 4
    ws.cell(top - 1, 1, "관장 웨이브 (판마다 6명 중 5명이 무작위 순서로 나와요)").font = BOLD
    names = ["웨이브", "몇 번째", "리그", "팀 인원", "팀원 레벨 (아이언)", "관장 레벨 (아이언)", "팀원 레벨 (이터니티)", "보상 (지금)", "SG: 보상 · 바꿀 것"]
    for i, n in enumerate(names, 1):
        c = ws.cell(top, i, n)
        c.font, c.fill, c.alignment, c.border = HEAD, HEAD_FILL, CENTER, BOX
    ws.column_dimensions["H"].width = 30
    ws.column_dimensions["I"].width = 30
    for k, w in enumerate(b["leaderWaves"]):
        r = top + 1 + k
        put(ws, r, 1, w, BLUE)
        put(ws, r, 2, k + 1, BLUE)
        put(ws, r, 3, f"=INDEX(웨이브!$B:$B,MATCH(A{r},웨이브!$A:$A,0))", GREEN)
        put(ws, r, 4, f"={R['lead1'] if k == 0 else R['lead2']}", GREEN, fmt="0")
        put(ws, r, 5, f"=INDEX(웨이브!$H:$H,MATCH(A{r},웨이브!$A:$A,0))", GREEN, fmt="0")
        put(ws, r, 6, f"=INDEX(웨이브!$K:$K,MATCH(A{r},웨이브!$A:$A,0))", GREEN, fmt="0")
        put(ws, r, 7, f"=INDEX(웨이브!$J:$J,MATCH(A{r},웨이브!$A:$A,0))", GREEN, fmt="0")
        put(ws, r, 8, "확정 보상 GREAT 2개" if k == 0 else "확정 보상 ULTRA 1 + GREAT 2", BLUE)
        put(ws, r, 9, None, fill=YELLOW)
    ws.freeze_panes = "A2"

    # ── 팀 전투 ──
    ws = wb.create_sheet("팀 전투")
    header(ws, 1, ["웨이브", "리그", "나오는 팀", "인원", "팀원 레벨 (아이언)", "팀원 레벨 (골드)", "팀원 레벨 (이터니티)", "메모"], [8, 10, 14, 6, 16, 16, 18, 40])
    for k, w in enumerate(b["teamWaves"]):
        r = k + 2
        put(ws, r, 1, w, BLUE)
        put(ws, r, 2, f"=INDEX(웨이브!$B:$B,MATCH(A{r},웨이브!$A:$A,0))", GREEN)
        put(ws, r, 3, f'=IF(B{r}="마스터즈","마스터즈 팀","KEL 팀")')
        put(ws, r, 4, f"={R['team']}", GREEN, fmt="0")
        for col, src in ((5, "H"), (6, "I"), (7, "J")):
            put(ws, r, col, f"=INDEX(웨이브!${src}:${src},MATCH(A{r},웨이브!$A:$A,0))", GREEN, fmt="0")
        put(ws, r, 8, None, fill=YELLOW)
    top = len(b["teamWaves"]) + 4
    ws.cell(top - 1, 1, "팀 이름 (무명섬과 연결이 안 될 때 쓰는 기본 이름. 실제 팀 · 실험체는 무명섬 관리 화면 → 블서로그 → 팀에서 정해요)").font = BOLD
    for i, n in enumerate(["리그", "팀 이름", "지역", "메모"], 1):
        c = ws.cell(top, i, n)
        c.font, c.fill, c.alignment, c.border = HEAD, HEAD_FILL, CENTER, BOX
    r = top + 1
    for name, region in teams:
        put(ws, r, 1, "KEL", BLUE)
        put(ws, r, 2, name, BLUE)
        put(ws, r, 3, region, BLUE)
        put(ws, r, 4, None, fill=YELLOW)
        r += 1
    for i in range(8):
        put(ws, r, 1, "마스터즈", BLUE)
        put(ws, r, 2, f"마스터즈 {i + 1}팀 (임시)", BLUE)
        put(ws, r, 3, "")
        put(ws, r, 4, None, fill=YELLOW)
        r += 1
    ws.freeze_panes = "A2"

    OUT.parent.mkdir(parents=True, exist_ok=True)
    wb.save(OUT)
    print(OUT)


if __name__ == "__main__":
    main()
