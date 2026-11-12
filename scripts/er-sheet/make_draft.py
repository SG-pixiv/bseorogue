# SPDX-FileCopyrightText: 2026 SG
# SPDX-License-Identifier: AGPL-3.0-only
"""
실험체 · 스킬 초안 시트(엑셀) 새로 만들기 — 처음 초안 · 예시를 다시 뽑을 때만 써요

주의: SG가 고친 docs/sheets/실험체-스킬.xlsx 를 덮어쓰지 않게, 나올 파일 이름을 따로 줘요.
게임 데이터를 먼저 내보내야 해요 (dump.test.ts.txt 를 test/tests/bseorogue/ 에 .test.ts 로 잠깐 복사해서 돌리고 지워요):
  cp scripts/er-sheet/dump.test.ts.txt test/tests/bseorogue/zz-sheet-dump.test.ts
  pnpm exec vitest run test/tests/bseorogue/zz-sheet-dump.test.ts && rm test/tests/bseorogue/zz-sheet-dump.test.ts
  python3 -B scripts/er-sheet/make_draft.py /tmp/실험체-스킬-초안.xlsx
"""
import json, os, re, subprocess, sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from draft_examples import fmt, lines_near, move_examples, pokerogue_cost, power_ladder, shape_near, singles_near, PRESET, MOVES
from pathlib import Path
from openpyxl import Workbook
from openpyxl.comments import Comment
from openpyxl.styles import Alignment, Border, Font, PatternFill, Side
from openpyxl.utils import get_column_letter
from openpyxl.worksheet.datavalidation import DataValidation

R = Path(__file__).resolve().parents[2]
DUMP = Path(os.environ.get("SHEET_DUMP", "/tmp/bseo-sheet-dump"))
chars = json.load(open(DUMP / "characters.json"))
moves_ko = json.load(open(R / "locales/ko/move.json"))
art_src = (R / "src/data/bseorogue/art-manifest.ts").read_text()
art = {int(k): [int(x) for x in v.split(",") if x.strip()] for k, v in re.findall(r"\n  (\d+): \[([^\]]*)\]", art_src.split("BSEO_ART_SKINS")[1].split("};")[0])}

ROLE_NUM = {5: "TANK", 1: "BRUISER", 16: "ASSASSIN", 15: "MARKSMAN", 13: "MAGE", 17: "SUPPORT"}
ROLE_KO = {"TANK": "탱커", "BRUISER": "브루저", "ASSASSIN": "암살자", "MARKSMAN": "평원딜", "MAGE": "스증딜러", "SUPPORT": "서포터"}
ROLE_SHAPE = {"TANK": [110, 80, 110, 40, 100, 60], "BRUISER": [95, 110, 90, 40, 75, 90], "ASSASSIN": [70, 120, 65, 50, 65, 130],
              "MARKSMAN": [70, 125, 60, 60, 70, 115], "MAGE": [70, 50, 65, 130, 85, 100], "SUPPORT": [95, 55, 80, 100, 100, 70]}
HAND = {30, 11, 18, 6, 12, 69}  # roster.ts 에 직접 정한 6명
CAT_KO = {0: "물리", 1: "스증", 2: "변화"}
MEAN = {"hp20": 2551.1, "ap20": 118.6, "def20": 108.8, "moveSpeed": 3.6, "attackSpeed": 0.117}

def camel(name):
    p = name.lower().split("_")
    return p[0] + "".join(x.capitalize() for x in p[1:])

def scale(shape, total=500):
    raw = [v * total / sum(shape) for v in shape]
    out = [int(v) for v in raw]
    left = total - sum(out)
    for _, i in sorted(((raw[i] - out[i], i) for i in range(6)), reverse=True)[:left]:
        out[i] += 1
    return out

def draft_shape(c):
    role = ROLE_NUM[c["role"]]
    er = c["er"]
    if c["erCode"] in HAND:
        return c["stages"][2], "직접 정한 값 (roster.ts)"
    hp = (er["hp20"] / MEAN["hp20"]) ** 1.5
    ap = (er["ap20"] / MEAN["ap20"]) ** 1.5
    df = (er["def20"] / MEAN["def20"]) ** 1.5
    sp = (er["moveSpeed"] / MEAN["moveSpeed"]) ** 3 * (1 + 1.5 * (er["attackSpeed"] - MEAN["attackSpeed"]))
    f = [hp, ap if role not in ("MAGE", "SUPPORT") else 1, df, ap if role in ("MAGE", "SUPPORT") else 1, df, sp]
    return scale([s * k for s, k in zip(ROLE_SHAPE[role], f)]), "역할군 모양 × ER 체력 · 공격력 · 방어력 · 이동/공격 속도"

score = {c["erCode"]: (c["er"]["hp20"] / MEAN["hp20"] + c["er"]["ap20"] / MEAN["ap20"] + c["er"]["def20"] / MEAN["def20"]) / 3 for c in chars}
order = sorted(score, key=score.get, reverse=True)
n = len(order)
def draft_cost(code):
    r = order.index(code) / n
    return 4 if r < 0.10 else 3 if r < 0.35 else 2 if r < 0.70 else 1

PHYS = {"TANK", "BRUISER", "ASSASSIN", "MARKSMAN"}
def skill_draft(role, slot):
    cat = "물리" if role in PHYS else "스증"
    base = {"Q": (60, 100, 25), "W": (0, 0, 15), "E": (70, 95, 15), "R": (120, 90, 5)}[slot]
    adj = {"TANK": -10, "SUPPORT": -10, "MARKSMAN": 5, "MAGE": 10}.get(role, 0)
    power, acc, pp = base
    if slot != "W":
        power = power + (adj if slot != "R" else adj * 2)
    eff = {
        "TANK": {"Q": "피해", "W": "방어 · 스킬 저항 1단계 ↑", "E": "피해 + 30% 기절(풀죽음)", "R": "피해 + 상대 공격 1단계 ↓"},
        "BRUISER": {"Q": "피해", "W": "공격 · 방어 1단계 ↑", "E": "피해의 50% 회복", "R": "피해 + 급소에 잘 맞음"},
        "ASSASSIN": {"Q": "피해", "W": "속도 2단계 ↑", "E": "선공(+1) 피해", "R": "피해 + 급소에 잘 맞음"},
        "MARKSMAN": {"Q": "피해", "W": "공격 1단계 ↑ · 명중 ↑", "E": "선공(+1) 피해", "R": "강한 피해, 다음 턴 쉼"},
        "MAGE": {"Q": "피해", "W": "스킬 증폭 2단계 ↑", "E": "피해 + 30% 화상", "R": "강한 피해, 쓴 뒤 스킬 증폭 2단계 ↓"},
        "SUPPORT": {"Q": "피해", "W": "체력 50% 회복", "E": "피해 + 상대 스킬 증폭 1단계 ↓", "R": "피해 + 자기 체력 30% 회복"},
    }[role][slot]
    prio = 1 if slot == "E" and role in ("ASSASSIN", "MARKSMAN") else 0
    if slot == "R" and role == "MARKSMAN":
        power = 150
    if slot == "W":
        return "변화", "—", "—", pp, prio, eff
    return cat, power, acc, pp, prio, eff

# ── 엑셀 ──
F = "Arial"
thin = Side(style="thin", color="C9CED8")
B = Border(left=thin, right=thin, top=thin, bottom=thin)
HEAD = PatternFill("solid", fgColor="1F2533")
EDIT = PatternFill("solid", fgColor="FFF59D")
GREY = Font(name=F, size=9, color="7A808C")

def header(ws, row, names, widths):
    for c, (h, w) in enumerate(zip(names, widths), 1):
        cell = ws.cell(row, c, h)
        cell.font = Font(name=F, size=10, bold=True, color="FFFFFF")
        cell.fill = HEAD
        cell.alignment = Alignment(horizontal="center", vertical="center", wrap_text=True)
        cell.border = B
        ws.column_dimensions[get_column_letter(c)].width = w
    ws.row_dimensions[row].height = 32

def put(ws, r, c, v, edit=False, wrap=False, small=False):
    cell = ws.cell(r, c, v)
    cell.font = GREY if small else Font(name=F, size=10)
    cell.border = B
    cell.alignment = Alignment(vertical="center", wrap_text=wrap)
    if edit:
        cell.fill = EDIT
    return cell

wb = Workbook()
# 1) 읽어 주세요
ws0 = wb.active
ws0.title = "읽어 주세요"
lines = [
    ("블서로그 실험체 · 스킬 초안 (91명)", True),
    ("노란 칸만 고치면 돼요. 고친 파일을 채팅에 보내 주시면 제가 게임 데이터로 바꿔요.", False),
    ("", False),
    ("실험체 시트", True),
    ("· 역할군 · 무기 · 코스트 · 종족값 6칸 · 키 등급 · 스킨 진화(스킨 번호 · 레벨 · 진화 후 역할군)를 고쳐요.", False),
    ("· 종족값은 '다 큰 모습(스킨 진화 2)'의 모양이에요. 합이 500이 아니어도 괜찮아요. 게임이 코스트에 맞춰 합을 늘리거나 줄여요.", False),
    ("  코스트별 합 (기본 → 진화1 → 진화2): 1코 320 → 410 → 500 · 2코 330 → 420 → 520 · 3코 340 → 435 → 540 · 4코 350 → 450 → 560", False),
    ("· 순서: 체력 · 공격력 · 방어력 · 스킬 증폭 · 스킬 저항 · 속도. 공격력은 물리 스킬, 스킬 증폭은 스증 스킬에 쓰여요.", False),
    ("· 코스트 초안: ER 20레벨 체력 · 공격력 · 방어력 평균(ER 지수)이 높은 순서로 위 10% 4코, 다음 25% 3코, 다음 35% 2코, 나머지 1코. 시작 예산은 10이에요.", False),
    ("· 종족값 초안: 역할군 기본 모양에 ER 체력 · 공격력 · 방어력 · 이동/공격 속도 차이를 곱했어요. 일레븐 · 유키 · 쇼이치 · 나딘 · 혜진 · 레니 6명은 전에 직접 정한 값이에요.", False),
    ("· 스킨 진화: '스킨 목록' 칸의 번호를 적어요. ✓ 는 팬키트 전투 그림이 있는 스킨이에요 (없는 스킨을 고르면 그림을 따로 받아야 해요).", False),
    ("· 키 등급: 도트 그릴 때 키 (S 60px · M 68px · L 74px). 모르면 M 그대로 두세요.", False),
    ("", False),
    ("스킬 시트", True),
    ("· 분류(물리/스증/변화) · 위력 · 명중 · PP · 선공 · 효과를 고쳐요. 변화 스킬은 위력 · 명중을 비워 둬요(—).", False),
    ("· 초안 규칙: Q 위력 60 · 명중 100 · PP 25 / W 변화 · PP 15 / E 위력 70 · 명중 95 · PP 15 / R 위력 120 · 명중 90 · PP 5. 탱커 · 서포터는 조금 약하게, 스증딜러 · 평원딜은 조금 세게.", False),
    ("· 효과는 짧게 적어 주세요 (예: '피해 + 30% 화상', '속도 2단계 ↑', '선공(+1) 피해'). 포켓로그에 있는 효과로 맞춰 넣을게요. 이상한 효과는 메모에 적어 주시면 따로 만들어요.", False),
    ("· 오른쪽 회색 칸은 지금 게임에서 쓰는 값이에요 (임시로 빌려 쓴 포켓몬 기술). 비교용이라 고치지 않아도 돼요.", False),
    ("· 배우는 레벨: Q · W 1, E 5, R 10 (지금 규칙). 바꾸고 싶으면 그 칸도 고쳐요.", False),
    ("", False),
    ("포켓몬 예시 (2판에 추가)", True),
    ("· 스킬 시트 '비슷한 포켓몬 기술': 그 줄 초안의 분류 · 위력 · 명중 · PP · 효과와 가장 비슷한 포켓몬 기술 3개예요 (이름 (분류 위력/명중/PP)). 숫자는 포켓몬 원래 값이에요.", False),
    ("· '포켓몬 기술 예시' 시트: 효과 종류별로 포켓몬 기술 5개씩과 설명, 아래쪽에 효과 없는 기술을 위력별로 모아 뒀어요. 효과 칸을 쓸 때 여기 표현을 그대로 가져다 쓰면 제일 빨라요.", False),
    ("· 실험체 시트 '모양이 비슷한 포켓몬': 종족값 6칸의 비율(모양)이 가장 비슷한 최종 진화 포켓몬 2마리예요. 숫자를 고치면 이 칸은 안 바뀌니까, 다시 보고 싶으면 말씀해 주세요.", False),
    ("· 실험체 시트 '기본/진화1/진화2 합': 코스트를 바꾸면 자동으로 바뀌어요 ('코스트 · 역할군' 시트 표에서 가져와요).", False),
    ("· '코스트 · 역할군' 시트: 코스트별 합과 비슷한 포켓몬 3단 진화 라인, 포켓로그에서 같은 코스트인 포켓몬이에요. 포켓로그 코스트는 1~10 · 6마리 기준이라 블서로그(3명)와 크기가 달라서 참고만 해 주세요.", False),
]
for i, (t, bold) in enumerate(lines, 1):
    c = ws0.cell(i, 1, t)
    c.font = Font(name=F, size=13 if i == 1 else 10, bold=bold)
ws0.column_dimensions["A"].width = 150

# 2) 실험체
ws = wb.create_sheet("실험체")
cols = ["ER번호", "이름", "ER 분류", "역할군", "무기", "쓸 수 있는 무기", "코스트", "ER 지수", "체력", "공격력", "방어력", "스킬 증폭", "스킬 저항", "속도", "모양 합",
        "기본 합", "진화1 합", "진화2 합", "모양이 비슷한 포켓몬 (최종 진화)",
        "키 등급", "진화1 스킨", "진화1 레벨", "진화2 스킨", "진화2 레벨", "진화1 후 역할군", "진화2 후 역할군", "스킨 목록 (번호 이름, ✓ 그림 있음)", "종족값 초안 근거", "메모"]
widths = [7, 10, 9, 10, 9, 22, 7, 8, 6, 7, 7, 8, 8, 6, 8, 7, 7, 7, 44, 7, 9, 9, 9, 9, 11, 11, 60, 26, 24]
header(ws, 1, cols, widths)
role_dv = DataValidation(type="list", formula1='"탱커,브루저,암살자,평원딜,스증딜러,서포터"', allow_blank=True)
size_dv = DataValidation(type="list", formula1='"S,M,L"', allow_blank=True)
cost_dv = DataValidation(type="whole", operator="between", formula1="1", formula2="6")
for dv in (role_dv, size_dv, cost_dv):
    ws.add_data_validation(dv)
for i, c in enumerate(chars):
    r = i + 2
    role = ROLE_NUM[c["role"]]
    shape, why = draft_shape(c)
    skins = c["er"]["skins"]
    have = set(art.get(c["erCode"], []))
    skin_txt = " / ".join(f"{k} {n}{' ✓' if k in have else ''}" for k, n in enumerate(skins) if k > 0)
    vals = [c["erCode"], c["name"], ROLE_KO[c["erRole"]], ROLE_KO[role], c["weapon"], ", ".join(c["weapons"]),
            c["cost"] if c["erCode"] in HAND else draft_cost(c["erCode"]), round(score[c["erCode"]], 3), *shape, None,
            None, None, None, shape_near(shape),
            "M", c["evo"]["skins"][0], c["evo"]["levels"][0], c["evo"]["skins"][1], c["evo"]["levels"][1], "", "", skin_txt, why, ""]
    for col, v in enumerate(vals, 1):
        edit = col in (4, 5, 7, 9, 10, 11, 12, 13, 14, 20, 21, 22, 23, 24, 25, 26, 29)
        put(ws, r, col, v, edit=edit, wrap=(col in (19, 27)), small=(col in (8, 19, 28)))
    ws.cell(r, 15).value = f"=SUM(I{r}:N{r})"
    for k, colx in enumerate(("P", "Q", "R")):
        ws[f"{colx}{r}"] = f"=IFERROR(VLOOKUP(G{r},'코스트 · 역할군'!$A$2:$D$7,{k + 2},FALSE),\"\")"
    role_dv.add(f"D{r}"); role_dv.add(f"Y{r}"); role_dv.add(f"Z{r}")
    size_dv.add(f"T{r}")
    cost_dv.add(f"G{r}")
    ws.row_dimensions[r].height = 30
ws.freeze_panes = "C2"
ws.cell(1, 8).comment = Comment("ER 20레벨 체력 · 공격력 · 방어력을 전체 평균으로 나눈 값의 평균. 1보다 크면 평균보다 튼튼하고 세요. 코스트 초안의 근거예요.", "Claude")

# 3) 스킬
ws2 = wb.create_sheet("스킬")
cols2 = ["ER번호", "이름", "키", "스킬 이름", "배우는 레벨", "분류", "위력", "명중", "PP", "선공", "효과 (초안)", "비슷한 포켓몬 기술 (예시)", "메모",
         "지금 분류", "지금 위력", "지금 명중", "지금 PP", "지금 효과 (빌려 쓴 기술)"]
widths2 = [7, 10, 4, 18, 8, 7, 6, 6, 5, 5, 30, 52, 22, 8, 8, 8, 7, 70]
header(ws2, 1, cols2, widths2)
cat_dv = DataValidation(type="list", formula1='"물리,스증,변화"', allow_blank=True)
ws2.add_data_validation(cat_dv)
r = 2
for c in chars:
    role = ROLE_NUM[c["role"]]
    for slot, s in zip("QWER", c["skills"]):
        cat, power, acc, pp, prio, eff = skill_draft(role, slot)
        mk = camel(s["move"])
        now_eff = moves_ko.get(mk, {}).get("effect", "")
        now_name = moves_ko.get(mk, {}).get("name", s["move"])
        ex = " · ".join(fmt(m) for m in move_examples(cat, power if isinstance(power, int) else 0, acc if isinstance(acc, int) else 100, pp, eff))
        vals = [c["erCode"], c["name"], slot, s["name"], s["level"], cat, power, acc, pp, prio, eff, ex, "",
                CAT_KO[s["category"]], s["power"] if s["power"] > 0 else "—", s["accuracy"] if s["accuracy"] > 0 else "—", s["pp"],
                f"[{now_name}] {now_eff}"]
        for col, v in enumerate(vals, 1):
            put(ws2, r, col, v, edit=col in (5, 6, 7, 8, 9, 10, 11, 13), wrap=(col in (11, 12, 18)), small=col >= 14 or col == 12)
        cat_dv.add(f"F{r}")
        ws2.row_dimensions[r].height = 30
        r += 1
ws2.freeze_panes = "E2"

# 4) 표
ws3 = wb.create_sheet("코스트 · 역할군")
header(ws3, 1, ["코스트", "기본 합", "진화1 합", "진화2 합", "합이 비슷한 포켓몬 (진화 라인 · 합)", "포켓로그에서 같은 코스트 (참고)"], [10, 10, 10, 10, 70, 44])
for i, (k, t) in enumerate({1: (320, 410, 500), 2: (330, 420, 520), 3: (340, 435, 540), 4: (350, 450, 560), 5: (580, 580, 580), 6: (600, 600, 600)}.items()):
    near = lines_near(t) if t[0] != t[2] else singles_near(t[2])
    for col, v in enumerate((k, *t, "\n".join(near), ", ".join(pokerogue_cost(k))), 1):
        put(ws3, i + 2, col, v, wrap=col >= 5)
    ws3.row_dimensions[i + 2].height = 62
ws3.cell(9, 1, "역할군 기본 모양 (다 큰 모습, 합 500) — 실험체별 초안의 출발점").font = Font(name=F, size=10, bold=True)
header(ws3, 10, ["역할군", "체력", "공격력", "방어력", "스킬 증폭", "스킬 저항", "속도"], [10, 10, 10, 10, 10, 10, 10])
for i, (k, v) in enumerate(ROLE_SHAPE.items()):
    for col, x in enumerate((ROLE_KO[k], *v), 1):
        put(ws3, 11 + i, col, x)
ws3.cell(18, 1, "상성 (공격 → 맞는 쪽): 탱커→암살자 2배 · 브루저→탱커 2배 · 암살자→평원딜 · 스증딜러 2배 · 평원딜→브루저 2배 · 스증딜러→탱커 2배 · 서포터→스증딜러 2배 (반대는 0.5배, roles.ts)").font = Font(name=F, size=10)

ws4 = wb.create_sheet("포켓몬 기술 예시")
header(ws4, 1, ["효과 종류 (초안 표현)", "포켓몬 기술", "분류", "위력", "명중", "PP", "선공", "포켓몬 설명"], [30, 14, 7, 6, 6, 5, 5, 90])
r = 2
for eff in PRESET:
    status = any(k in eff for k in ("↑", "회복")) and "피해" not in eff
    for m in move_examples("변화" if status else "물리", 70, 95, 15, eff, n=5) + ([] if status else move_examples("스증", 70, 95, 15, eff, n=3)):
        vals = [eff, m["name"], {0: "물리", 1: "스증", 2: "변화"}[m["category"]], m["power"] if m["power"] > 0 else "—",
                m["accuracy"] if m["accuracy"] > 0 else "—", m["pp"], m["priority"] or "", m["effect"]]
        for col, v in enumerate(vals, 1):
            put(ws4, r, col, v, wrap=col == 8)
        r += 1
r += 1
ws4.cell(r, 1, "효과 없는 기술 — 위력별 (명중 · PP 감 잡기용)").font = Font(name=F, size=11, bold=True)
r += 1
for cat, label in ((0, "물리"), (1, "스증")):
    for p, ms in power_ladder(cat):
        for m in ms:
            vals = [f"{label} 위력 {p}", m["name"], label, m["power"], m["accuracy"] if m["accuracy"] > 0 else "—", m["pp"], m["priority"] or "", m["effect"]]
            for col, v in enumerate(vals, 1):
                put(ws4, r, col, v, wrap=col == 8)
            r += 1
ws4.freeze_panes = "B2"

out = sys.argv[1] if len(sys.argv) > 1 else "실험체-스킬-초안.xlsx"
wb.save(out)
print(out)
