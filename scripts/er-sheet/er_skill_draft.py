# SPDX-FileCopyrightText: 2026 SG
# SPDX-License-Identifier: AGPL-3.0-only
"""
ER 실제 스킬 설명 → 스킬 시트 초안 (분류 · 위력 · 명중 · PP · 선공 · 효과) 다시 쓰기 (11-16)

er-data 폴더(scripts/er-data/fetch.mjs 로 받은 것)의 l10n-Korean.txt 에서 실험체 Q · W · E · R 설명을 읽고,
설명에 나오는 낱말(둔화 · 기절 · 속박 · 보호막 · 회복 · 돌진 …)을 블서로그 효과 표현(skill_effect.py)으로 옮겨요.
설명 글 자체는 시트에 넣지 않고 (님블뉴런 글), 읽어 낸 낱말만 'ER 효과 (읽은 것)' 칸에 적어요.

쓰는 법:
  python3 -I -B scripts/er-sheet/er_skill_draft.py <er-data 폴더> [엑셀]      (기본 docs/sheets/실험체-스킬.xlsx)
  --check   시트는 안 바꾸고 표만 찍어요
  SG가 '효과 (초안)' 칸을 직접 고친 줄(= 'ER 초안 (자동)' 칸과 다른 줄)은 건드리지 않아요. 전부 다시 쓰려면 --force
그다음: python3 -I -B scripts/er-sheet/import_sheet.py → pnpm exec biome format --write src/data/bseorogue/ → 블서로그 테스트

옮기는 규칙 (초안이에요. SG가 시트에서 고쳐요):
  기절 · 공중에 띄움 · 제압          → 30% 스턴        밀어냄 · 끌어당김만        → 20% 스턴
  속박 · 빙결                        → 20% 속박        수면 → 30% 잠듦 · 매혹/공포/도발 → 30% 혼란
  출혈 · 중독 · 화상                 → 30% 그 상태이상
  이동 속도 감소(둔화)               → 상대 속도 1단계 ↓ (W · R 이고 다른 확률 효과가 없으면 30% 둔화)
  방어력 감소 · 받는 피해 증가       → 상대 방어 1단계 ↓   침묵 → 상대 스킬 증폭 1단계 ↓   실명 → 상대 명중 1단계 ↓
  보호막 · 받는 피해 감소            → 방어 ↑ (변화 스킬이면 방어 · 스킬 저항)   무적 · 저지 불가 → 방어 2단계 ↑ (변화)
  이동 속도 증가 → 속도 ↑ · 공격 속도/공격력 증가 → 공격 ↑ · 스킬 증폭 증가 → 스킬 증폭 ↑ · 은신 → 회피 ↑
  입힌 피해만큼 회복 → 피해의 50% 회복 · 그 밖의 체력 회복 → 체력 50% 회복(변화) / 자기 체력 25% 회복(공격)
  돌진 · 도약 · 순간이동 + 피해      → E 스킬(암살자는 Q 도)이면 선공(+1), 위력 낮춤
  치명타 → 급소에 잘 맞음 · 체력 소모 → 반동 25%
  분류: 설명에 '피해를 입' 이 없으면 변화. 계수에 '스킬 증폭의' 가 있으면 스증, '공격력의' 면 물리, 둘 다 없으면 역할군
  위력: Q 60 · W 65 · E 70 · R 120 에서 역할군(탱커 · 서포터 −10, 평원딜 +5, 스증딜러 +10)과 붙은 효과만큼 낮춰요
"""
import re
import sys
from copy import copy
from pathlib import Path

from openpyxl import load_workbook
from openpyxl.styles import Alignment, Font

sys.path.insert(0, str(Path(__file__).resolve().parent))
import skill_effect

ROOT = Path(__file__).resolve().parents[2]
SLOT = {"P": 100, "Q": 200, "W": 300, "E": 400, "R": 500}
# 스킬 번호가 다른 실험체 (scripts/er-data/build.mjs 의 SKILL_CODES 와 같게)
CODE_FIX = {48: {"Q": 400, "W": 500, "E": 600, "R": 700}, 37: {"R": 510}, 55: {"Q": 220}}
ROLE = {"탱커": "TANK", "브루저": "BRUISER", "암살자": "ASSASSIN", "평원딜": "MARKSMAN", "스증딜러": "MAGE", "서포터": "SUPPORT"}
PHYS = {"TANK", "BRUISER", "ASSASSIN", "MARKSMAN"}
ROLE_ADJ = {"TANK": -10, "SUPPORT": -10, "MARKSMAN": 5, "MAGE": 10}
# 설명에서 아무것도 못 읽은 변화 스킬은 역할군 기본값
ROLE_STATUS = {"TANK": "방어 · 스킬 저항 1단계 ↑", "BRUISER": "공격 · 방어 1단계 ↑", "ASSASSIN": "속도 2단계 ↑",
               "MARKSMAN": "공격 · 명중 1단계 ↑", "MAGE": "스킬 증폭 2단계 ↑", "SUPPORT": "체력 50% 회복"}
AUTO_COL = "ER 초안 (자동)"
README = [
    ("스킬 초안 (11-16 ER 실제 설명으로 다시 씀)", True),
    ("· 스킬 시트의 분류 · 위력 · 명중 · PP · 선공 · 효과를 ER 실제 스킬 설명에 맞춰 다시 썼어요 (전에는 역할군마다 같은 초안).", False),
    ("· 맨 오른쪽 'ER 효과 (읽은 것)' 칸: ER 설명에서 읽어 낸 낱말이에요 (피해 · 돌진 · 기절 · 둔화 · 보호막 …). 이걸 보고 효과 칸을 고치면 돼요.", False),
    ("· 옮긴 규칙: 기절 · 띄움 → 30% 스턴 / 속박 → 20% 속박 / 이동 속도 감소 → 상대 속도 1단계 ↓ (W · R 은 30% 둔화) / 보호막 → 방어 ↑ / 이동 속도 증가 → 속도 ↑ /", False),
    ("  공격 속도 · 공격력 증가 → 공격 ↑ / 입힌 피해만큼 회복 → 피해의 50% 회복 / 돌진하는 E 스킬 → 선공(+1) · 위력 낮춤 / 피해가 없는 스킬 → 변화.", False),
    ("· 숫자(위력 · 확률)는 ER 수치가 아니라 블서로그 기준으로 맞춘 초안이에요. 너무 세거나 약한 스킬은 노란 칸을 고쳐 주세요.", False),
    ("· 'ER 초안 (자동)' 칸은 제가 쓴 초안을 기억해 두는 칸이에요. 효과 칸을 고친 줄은 다음에 다시 뽑아도 건드리지 않아요.", False),
    ("· '실험체' 시트 '스킨 목록' 칸도 새 ER 스킨으로 바꿨어요 (11-17, 12명에 새 스킨 1개씩, 뒤에 붙어서 원래 번호는 그대로예요).", False),
]
TAG_COL = "ER 효과 (읽은 것)"


def load_l10n(er_dir):
    out = {}
    for line in open(Path(er_dir) / "l10n-Korean.txt", encoding="utf-8"):
        line = line.rstrip("\n")
        if "┃" in line:
            k, v = line.split("┃", 1)
            out[k] = v
    return out


def clean(t):
    t = re.sub(r"<[^>]+>", "", t or "").replace("\\n", " ")
    t = re.sub(r"\{\d+\}", "N", t)
    return re.sub(r"\s+", " ", t).strip()


def er_text(l10n, code, slot):
    g = f"1{code:03d}{CODE_FIX.get(code, {}).get(slot, SLOT[slot])}"
    return clean(l10n.get(f"Skill/Group/Desc/{g}")), clean(l10n.get(f"Skill/Group/Coef/{g}")), (l10n.get(f"Skill/Group/Name/{g}") or "").strip()


def has(t, pat):
    return re.search(pat, t) is not None


def read_tags(desc):
    """설명 → 읽은 낱말 목록 (순서 = 시트에 적는 순서)"""
    t = desc
    tags = []

    def add(name, pat):
        if has(t, pat):
            tags.append(name)

    add("피해", r"스킬 피해|고정 피해|피해를 (?:추가로 |최대 N회 )?(?:입|주|가)")
    add("돌진", r"돌진|도약|점프하|뛰어|뜁니다|순간이동|순간 이동|이동합니다|이동하며|이동한 (?:이후|후)|방향으로 날아가|파고들|구르|굴러|물러나")
    add("기절", r"기절")
    add("띄움", r"공중에 띄|띄웁|띄워|에어본")
    add("제압", r"제압(?!부)")  # 제압부(혜진 부적 이름)는 빼요
    add("밀어냄", r"밀어(?:내|냅|낸|버)|밀쳐|넉백|날려 ?보")  # "카드를 날려"(쏘는 것)는 빼요
    add("끌어당김", r"끌어(?:당|오|옵|와)|당겨")  # 끌어올려 · 끌어모은 · (자기가) 끌려가며 는 빼요
    add("속박", r"속박|빙결|결박")
    add("수면", r"수면")
    add("매혹", r"매혹(?!적)")
    add("공포", r"공포(?!탄)")
    add("도발", r"도발")
    add("출혈", r"출혈")
    add("중독", r"중독|독 ")
    add("화상", r"화상")
    add("둔화", r"이동 속도(?:를|가)? ?N? ?(?:만큼 )?(?:감소|느려)|둔화|이동 속도 감소")
    add("방어 감소", r"방어력(?:을|이)? ?N? ?(?:만큼 )?감소|방어력 감소|받는 피해(?:가|를|량이)? ?N? ?(?:만큼 )?증가")
    add("침묵", r"침묵")
    add("실명", r"실명|시야를 (?:잃|차단)")
    add("보호막", r"보호막")
    add("피해 감소", r"받는 (?:모든 )?피해(?:가|를|량이)? ?N? ?(?:만큼 )?감소|피해 감소|방어력(?:이|을)? ?N? ?(?:만큼 )?증가")
    add("무적", r"무적|저지 불가|피해를 받지 않|대상으로 지정되지 않|피해 면역")
    add("흡수", r"입힌 피해(?:량)?의 ?N? ?(?:만큼 )?(?:체력을 )?회복")
    add("회복", r"체력을 ?N? ?(?:만큼 )?회복|체력이 ?N? ?(?:만큼 )?회복|회복(?:합니다|시킵니다|시킨|하며|하고)")
    add("이속 증가", r"이동 속도(?:가|를)? ?N? ?(?:만큼 )?(?:증가|상승|빨라)|이동 속도 N(?:,| 증가)")
    add("공속 증가", r"공격 속도(?:가|를)? ?N? ?(?:만큼 )?(?:증가|상승)|공격 속도 N")
    add("공격 증가", r"공격력(?:이|을)? ?N? ?(?:만큼 )?(?:증가|상승)")
    add("스증 증가", r"스킬 증폭(?:이|을)? ?N? ?(?:만큼 )?(?:증가|상승)")
    add("은신", r"은신")
    add("치명타", r"치명타(?:가| 확률이?| 피해(?:가|량이)?) ?N? ?(?:만큼 )?(?:증가|발생)|반드시 치명타")
    add("체력 소모", r"체력을 ?N? ?(?:만큼 )?소모")
    if "흡수" in tags and not has(re.sub(r"입힌 피해(?:량)?의 ?N? ?(?:만큼 )?(?:체력을 )?회복", "", t), r"회복"):
        tags = [x for x in tags if x != "회복"]
    return tags


def draft(role, slot, desc, coef, force_attack=False):
    """→ dict(cat, power, acc, pp, prio, effect, tags). force_attack: 공격 스킬이 모자란 실험체는 변화 스킬도 공격으로"""
    tags = read_tags(desc)
    T = set(tags)
    attack = "피해" in T or force_attack
    if attack:
        amp, ad = coef.count("스킬 증폭의"), coef.count("공격력의")
        cat = "스증" if amp > ad else "물리" if ad > amp else ("물리" if role in PHYS else "스증")
    else:
        cat = "변화"

    chance = None  # 확률 효과는 하나만 (skill_effect 규칙)
    if T & {"기절", "띄움", "제압"}:
        chance = "30% 스턴"
    elif "속박" in T:
        chance = "20% 속박"
    elif "수면" in T:
        chance = "30% 잠듦"
    elif T & {"매혹", "공포", "도발"}:
        chance = "30% 혼란"
    elif "출혈" in T:
        chance = "30% 출혈"
    elif "중독" in T:
        chance = "30% 중독"
    elif "화상" in T:
        chance = "30% 화상"
    elif T & {"밀어냄", "끌어당김"}:
        chance = "20% 스턴"

    foe, me = [], []  # 능력 변화
    if "둔화" in T:
        if chance is None and slot in ("W", "R"):
            chance = "30% 둔화"
        else:
            foe.append("속도")
    if "방어 감소" in T:
        foe.append("방어")
    if "침묵" in T:
        foe.append("스킬 증폭")
    if "실명" in T:
        foe.append("명중")
    if T & {"보호막", "피해 감소"}:
        me.append("방어")
    if "이속 증가" in T:
        me.append("속도")
    if T & {"공속 증가", "공격 증가"}:
        me.append("공격")
    if "스증 증가" in T:
        me.append("스킬 증폭")
    if "은신" in T:
        me.append("회피")

    parts = []
    power = acc = None
    prio = 0
    if attack:
        base = {"Q": 60, "W": 65, "E": 70, "R": 120}[slot]
        adj = ROLE_ADJ.get(role, 0)
        power = base + (adj * 2 if slot == "R" else adj)
        acc = {"Q": 100, "W": 100, "E": 95, "R": 90}[slot]
        pp = {"Q": 25, "W": 20, "E": 15, "R": 5}[slot]
        foe, me = foe[:1], me[:1]  # 공격 스킬은 상대 쪽 하나 · 자기 쪽 하나까지
        dash = "돌진" in T and (slot == "E" or (slot == "Q" and role == "ASSASSIN"))
        if dash:
            prio = 1
            power = min(power, 60) - 10
        parts.append("선공(+1) 피해" if dash else "피해")
        if chance:
            parts.append(chance)
            power -= 5
        if foe:
            parts.append(f"상대 {foe[0]} 1단계 ↓")
            power -= 10
        if "흡수" in T:
            parts.append("피해의 50% 회복")
            power -= 5 if slot != "R" else 10
        elif "회복" in T:
            parts.append("자기 체력 25% 회복")
            power -= 10 if slot != "R" else 15
        if me:
            parts.append(f"쓴 뒤 {me[0]} 1단계 ↑")
            power -= 15 if slot != "R" else 10
        if "치명타" in T:
            parts.append("급소에 잘 맞음")
        if "체력 소모" in T:
            parts.append("반동 25%")
            power += 10
        power = max(90 if slot == "R" else 40, min(150, power))
    else:
        pp = {"Q": 20, "W": 15, "E": 15, "R": 10}[slot]
        heal = bool(T & {"회복", "흡수"})
        if "무적" in T:
            parts.append("방어 2단계 ↑")
            me = [x for x in me if x != "방어"]
        elif T & {"보호막", "피해 감소"}:
            parts.append("방어 · 스킬 저항 1단계 ↑")
            me = [x for x in me if x != "방어"]
        if me:
            two = len(me) == 1 and not parts and not heal
            parts.append(f"{' · '.join(me[:2])} {2 if two else 1}단계 ↑")
        if heal:
            parts.append("체력 50% 회복" if not parts else "체력 25% 회복")
        if not parts:
            # 자기에게 거는 효과가 없으면 상대에게 거는 변화 스킬 (확률 없이 반드시). 스턴 · 속박만 있는 스킬은 둔화로
            if chance:
                word = chance.split()[-1]
                parts.append("둔화" if word in ("스턴", "속박") else word)
                acc = 75 if word == "잠듦" else 90
                foe = [x for x in foe if x != "속도"] if parts[0] == "둔화" else foe
            if foe:
                parts.append(f"상대 {' · '.join(foe[:2])} {1 if parts else 2}단계 ↓")
                acc = acc or 100
        if not parts:
            parts.append("속도 2단계 ↑" if "돌진" in T else ROLE_STATUS[role])
    return {"cat": cat, "power": power, "acc": acc, "pp": pp, "prio": prio, "effect": " + ".join(parts), "tags": tags}


def refresh_skins(wb):
    """'실험체' 시트 '스킨 목록' 칸을 새 er-data.ts 스킨으로 (ER 이 새 스킨을 뒤에 붙여서 번호는 그대로예요). 바꾼 실험체 이름 목록"""
    er_src = (ROOT / "src/data/bseorogue/er-data.ts").read_text(encoding="utf-8")
    skins = {
        int(k): re.findall(r'"([^"]*)"', body)
        for k, body in re.findall(r'\n  "(\d+)": \{[\s\S]*?\n    skins: \[([\s\S]*?)\]', er_src)
    }
    art_src = (ROOT / "src/data/bseorogue/art-manifest.ts").read_text(encoding="utf-8")
    art_part = art_src.split("BSEO_ART_SKINS")[1].split("};")[0]
    art = {int(k): {int(x) for x in v.split(",") if x.strip()} for k, v in re.findall(r"\n  (\d+): \[([^\]]*)\]", art_part)}
    ws = wb["실험체"]
    head = [c.value for c in ws[1]]
    col = head.index("스킨 목록 (번호 이름, ✓ 그림 있음)") + 1
    done = []
    for r in range(2, ws.max_row + 1):
        code = ws.cell(r, 1).value
        if not code or int(code) not in skins:
            continue
        have = art.get(int(code), set())
        txt = " / ".join(f"{k} {n}{' ✓' if k in have else ''}" for k, n in enumerate(skins[int(code)]) if k > 0)
        if ws.cell(r, col).value != txt:
            ws.cell(r, col).value = txt
            done.append(ws.cell(r, 2).value)
    return done


def main():
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    check, force = "--check" in sys.argv, "--force" in sys.argv
    if not args:
        sys.exit(__doc__)
    l10n = load_l10n(args[0])
    xlsx = Path(args[1]) if len(args) > 1 else ROOT / "docs/sheets/실험체-스킬.xlsx"
    wb = load_workbook(xlsx)
    role_of = {r[0]: ROLE[r[3]] for r in wb["실험체"].iter_rows(min_row=2, values_only=True) if r[0]}
    ws = wb["스킬"]
    head = [c.value for c in ws[1]]
    for name in (TAG_COL, AUTO_COL):
        if name not in head:
            head.append(name)
            c = ws.cell(1, len(head), name)
            src = ws.cell(1, 1)
            c.font, c.fill, c.alignment, c.border = copy(src.font), copy(src.fill), copy(src.alignment), copy(src.border)
            ws.column_dimensions[c.column_letter].width = 34
    col = {h: i + 1 for i, h in enumerate(head)}
    try:
        from draft_examples import fmt, move_examples
    except Exception:  # 게임 데이터 내보내기가 없으면 예시 칸은 그대로 둬요
        fmt = move_examples = None
        print("(참고) /tmp/bseo-sheet-dump 가 없어서 '비슷한 포켓몬 기술' 칸은 그대로 둬요 (make_draft.py 맨 위 참고)")
    grey = Font(name="Arial", size=9, color="7A808C")
    kept = changed = 0
    attacks = {}
    rows = []
    # 공격 스킬이 2개가 안 되는 실험체는 변화 스킬을 Q → R → E → W 순서로 공격으로 바꿔요
    forced = set()
    by_char = {}
    for r in range(2, ws.max_row + 1):
        code = ws.cell(r, col["ER번호"]).value
        if code:
            slot = ws.cell(r, col["키"]).value
            desc, coef, _ = er_text(l10n, code, slot)
            by_char.setdefault(code, {})[slot] = draft(role_of[code], slot, desc, coef)["cat"] != "변화" if desc else True
    for code, m in by_char.items():
        n = sum(m.values())
        for slot in "QREW":
            if n >= 2:
                break
            if not m.get(slot, True):
                forced.add((code, slot))
                n += 1
    for r in range(2, ws.max_row + 1):
        code = ws.cell(r, col["ER번호"]).value
        if not code:
            continue
        slot = ws.cell(r, col["키"]).value
        role = role_of[code]
        desc, coef, er_name = er_text(l10n, code, slot)
        if not desc:
            print(f"(참고) {ws.cell(r, col['이름']).value} {slot}: ER 설명이 없어요 → 그대로 둬요")
            continue
        d = draft(role, slot, desc, coef, (code, slot) in forced)
        try:
            skill_effect.parse(d["effect"], {"물리": "PHYSICAL", "스증": "SPECIAL", "변화": "STATUS"}[d["cat"]], d["prio"])
        except skill_effect.EffectError as e:
            sys.exit(f"{code} {slot}: 만든 효과를 못 읽어요 — {e}")
        attacks[code] = attacks.get(code, 0) + (d["cat"] != "변화")
        rows.append((code, ws.cell(r, col["이름"]).value, slot, er_name, d))
        now, auto = ws.cell(r, col["효과 (초안)"]).value, ws.cell(r, col[AUTO_COL]).value
        if auto is not None and now != auto and not force:
            kept += 1  # SG가 고친 줄
            continue
        if check:
            continue
        if er_name:
            ws.cell(r, col["스킬 이름"]).value = re.sub(r"\s+-\s+(노란색|빨간색|파란색|무색)$", "", er_name)
        vals = {"분류": d["cat"], "위력": d["power"] if d["power"] else "—", "명중": d["acc"] if d["acc"] else "—", "PP": d["pp"], "선공": d["prio"],
                "효과 (초안)": d["effect"], TAG_COL: " · ".join(d["tags"]), AUTO_COL: d["effect"]}
        for k, v in vals.items():
            c = ws.cell(r, col[k])
            if c.value != v:
                changed += k == "효과 (초안)"
            c.value = v
        for k in (TAG_COL, AUTO_COL):
            c = ws.cell(r, col[k])
            c.font, c.border, c.alignment = grey, copy(ws.cell(r, 1).border), Alignment(vertical="center", wrap_text=True)
        if move_examples:
            ex = move_examples(d["cat"], d["power"] or 0, d["acc"] or 100, d["pp"], d["effect"])
            ws.cell(r, col["비슷한 포켓몬 기술 (예시)"]).value = " · ".join(fmt(m) for m in ex)
    few = sorted(c for c, n in attacks.items() if n < 2)
    if "--table" in sys.argv or check:
        for code, name, slot, er_name, d in rows:
            print(f"{code:>2} {name} {slot} {er_name[:14]:<14} | {d['cat']} {d['power'] or '—'}/{d['acc'] or '—'}/{d['pp']}{' 선공' if d['prio'] else ''} | {d['effect']}  ← {' · '.join(d['tags'])}")
    if forced:
        print("(참고) 공격 스킬이 모자라서 공격으로 바꾼 변화 스킬:", sorted(forced))
    if few:
        print("(참고) 공격 스킬이 1개 이하인 실험체:", few)
    if not check:
        new_skins = refresh_skins(wb)
        if new_skins:
            print(f"'실험체' 시트 스킨 목록 새로 ({len(new_skins)}명):", " · ".join(new_skins))
        readme = wb["읽어 주세요"]
        if not any("스킬 초안 (11-16" in str(c.value) for c in readme["A"]):
            start = readme.max_row + 2
            for i, (text, bold) in enumerate(README):
                c = readme.cell(start + i, 1, text)
                c.font = Font(name="맑은 고딕", size=11 if bold else 10, bold=bold)
        wb.save(xlsx)
        print(f"{xlsx.name}: 효과 {changed}줄 바꿈 · SG가 고친 {kept}줄은 그대로")


if __name__ == "__main__":
    main()
