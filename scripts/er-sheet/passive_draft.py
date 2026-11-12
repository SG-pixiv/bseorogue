# SPDX-FileCopyrightText: 2026 SG
# SPDX-License-Identifier: AGPL-3.0-only
"""
고유 패시브 초안 → 실험체-스킬.xlsx 에 '패시브' 시트 더하기 (11-12 초안)

패시브는 포켓로그 특성(ability)을 하나씩 빌려 써요. 이름 · 설명은 블서로그 것으로 바꿔요 (스킬과 같은 방식).
한 특성은 한 실험체만 (이름을 바꿔 끼우니까). 역할군(타입)에 기대는 특성(타오르는불꽃 · 부유 등)은
블서로그에서 아무 일도 안 해서 안 골랐어요. 모습이 바뀌는 특성 · 손해만 보는 특성 · 날씨 특성도 뺐어요.

ER 패시브 실제 설명은 아직 없어서(er-data 폴더 필요) 이름 · 역할군 · 무기로 골랐어요. SG가 노란 칸을 고쳐요.

쓰는 법: python3 -B scripts/er-sheet/passive_draft.py [엑셀 파일]   (기본 docs/sheets/실험체-스킬.xlsx)
         이미 '패시브' 시트가 있으면 건드리지 않아요 (SG가 고친 것을 지키려고). 다시 만들려면 --force
"""
import re
import sys
from pathlib import Path

from openpyxl import load_workbook
from openpyxl.styles import Alignment, Border, Font, PatternFill, Side
from openpyxl.utils import get_column_letter

ROOT = Path(__file__).resolve().parents[2]

# ER번호: (포켓로그 특성, 고른 이유)
DRAFT = {
    1: ("MOXIE", "피의 축제 → 쓰러뜨릴수록 강해짐"),
    2: ("NO_GUARD", "정의는 빗나가지 않음 (권총)"),
    3: ("TECHNICIAN", "뚜셰 → 펜싱 기술"),
    4: ("GUTS", "근성 그대로"),
    5: ("SUPER_LUCK", "사신의 눈 → 급소"),
    6: ("BEAST_BOOST", "야성 → 사냥할수록 강해짐"),
    7: ("STAMINA", "도그파이트 → 맞을수록 단단해짐"),
    8: ("MAGIC_BOUNCE", "Feedback → 되돌려 보냄"),
    9: ("STAKEOUT", "유격전 → 들어오는 상대를 노림"),
    10: ("HUSTLE", "취기 → 세지만 덜 맞음"),
    11: ("CLEAR_BODY", "완벽한 옷매무새 → 흐트러지지 않음"),
    12: ("CURSED_BODY", "삼재 → 저주"),
    13: ("CHEEK_POUCH", "요리사의 열정 → 열매(음식)로 더 회복"),
    14: ("POISON_TOUCH", "낙인 → 찌르면 중독"),
    15: ("INNARDS_OUT", "삶은 고통이에요 → 쓰러질 때 되갚음"),
    16: ("SPEED_BOOST", "그란투리스모 → 점점 빨라짐 (바이크)"),
    17: ("FLAME_BODY", "활활 → 닿으면 화상"),
    18: ("MAGICIAN", "부당거래 → 아이템을 가로챔"),
    19: ("COMPETITIVE", "CheerUP♥ → 깎이면 더 힘냄"),
    20: ("INTIMIDATE", "위풍당당 → 위협"),
    21: ("QUICK_DRAW", "더블샷 → 빠른 총잡이"),
    22: ("CHILLING_NEIGH", "청소 완료 → 쓰러뜨리면 공격력 ↑"),
    23: ("MERCILESS", "외과 전문의 → 약한 곳(중독)을 정확히"),
    24: ("ANALYTIC", "퀸즈 갬빗 디클라인드 → 체스, 늦게 두면 강함"),
    25: ("TINTED_LENS", "산탄 → 막혀도 뚫음"),
    26: ("ADAPTABILITY", "개조 → 자기 역할군 스킬 강화"),
    27: ("INFILTRATOR", "잠입 그대로"),
    28: ("INNER_FOCUS", "마음의 양식 → 흔들리지 않음"),
    29: ("TOUGH_CLAWS", "인간 어뢰 → 몸으로 부딪치는 공격 강화"),
    30: ("SHELL_ARMOR", "힘내자고! → 버티는 탱커 (급소 안 맞음)"),
    31: ("COMPOUND_EYES", "카이(활 쏘기 자세) → 명중"),
    32: ("KEEN_EYE", "캐치볼 → 공을 놓치지 않는 눈"),
    33: ("ANGER_POINT", "다혈질 → 급소 맞으면 폭발"),
    34: ("TRACE", "슬로우 셔터 → 사진 찍듯 따라 함"),
    35: ("DEFIANT", "열혈의 의지 → 깎이면 더 세짐"),
    36: ("MAGIC_GUARD", "텔레키네시스 → 염력 보호막"),
    37: ("SHADOW_TAG", "고독한 예술가 → 놓아주지 않음"),
    38: ("PRANKSTER", "죽음의 연기 → 연기(속임수)로 먼저"),
    39: ("WEAK_ARMOR", "올레 → 플라멩코, 맞으면 빨라짐"),
    40: ("SYNCHRONIZE", "살아 있는 마리오네트 → 똑같이 되돌림"),
    41: ("NATURAL_CURE", "빛의 가호 → 교체하면 나음"),
    42: ("GRIM_NEIGH", "흡혈귀 → 쓰러뜨리면 스킬 증폭 ↑"),
    43: ("AFTERMATH", "폭발물 전문가 → 쓰러질 때 폭발"),
    44: ("BERSERK", "카드모스의 부름 → 몰리면 폭주"),
    45: ("FUR_COAT", "오뜨꾸뛰르 → 두꺼운 옷"),
    46: ("STATIC", "과전하 → 닿으면 마비"),
    47: ("PICKPOCKET", "괴도 → 훔침"),
    48: ("SERENE_GRACE", "알록달록 컬러믹스 → 추가 효과 잘 나옴"),
    49: ("OPPORTUNIST", "연계 창술 → 상대 강화를 따라 탐"),
    50: ("ICE_SCALES", "겨울여왕의 영지 → 얼음 막"),
    51: ("GRASSY_SURGE", "자연의 응답 → 풀밭 회복"),
    52: ("WONDER_SKIN", "별읽기 → 미리 알고 피함"),
    53: ("BATTLE_ARMOR", "전사의 투지 → 갑옷"),
    54: ("ARENA_TRAP", "작살 장전 → 꿰어서 못 도망감"),
    55: ("WATER_VEIL", "사명감 → 소방관, 화상 안 됨"),
    56: ("IRON_FIST", "단련광 → 주먹 단련"),
    57: ("REGENERATOR", "재생 그대로"),
    58: ("SHEER_FORCE", "웨폰 케이스 → 화력"),
    59: ("PRESSURE", "착취 → 상대 PP를 더 씀"),
    60: ("SOUL_HEART", "아르띠지아나토 → 장인 정신"),
    61: ("LIMBER", "고양이의 습성 → 유연함"),
    62: ("ELECTRIC_SURGE", "에너지 프로토콜 → 전기 필드"),
    63: ("WANDERING_SPIRIT", "사로잡힌 육신 → 빙의, 패시브를 바꿈"),
    64: ("SHIELD_DUST", "몽환 나비 → 나비 비늘"),
    65: ("PARENTAL_BOND", "블루&레드 → 둘이서 두 번 공격"),
    66: ("UNAWARE", "유물 탐구 → 상대 강화에 흔들리지 않음"),
    67: ("MOLD_BREAKER", "티어링 블레이드 → 뚫고 벰"),
    68: ("MULTISCALE", "플라즈마 베리어 → 처음 한 방을 막음"),
    69: ("FLUFFY", "곰돌이! 공격 → 푹신푹신"),
    70: ("PERISH_BODY", "오의 - 생사 각인 → 생사를 함께"),
    71: ("ANGER_SHELL", "억압된 분노 → 몰리면 터짐"),
    72: ("SNIPER", "잿빛 사신 → 저격수"),
    73: ("QUEENLY_MAJESTY", "고결한 마음 → 기품, 선공을 막음"),
    74: ("UNNERVE", "압류 → 열매를 못 먹게"),
    75: ("PUNK_ROCK", "고통의 선율 → 소리 스킬"),
    76: ("SOLID_ROCK", "익숙한 아픔 → 큰 피해를 덜 받음"),
    77: ("SIMPLE", "도력 → 능력 변화가 커짐"),
    78: ("SHARPNESS", "검의 기억 → 베는 스킬"),
    79: ("BEADS_OF_RUIN", "아스트라 에너지 → 모두의 스킬 저항 ↓"),
    80: ("DOWNLOAD", "연산 → 상대를 계산해 강화"),
    81: ("GORILLA_TACTICS", "K.O. → 한 스킬에 몰빵"),
    82: ("STEADFAST", "결심응진 → 흔들리면 빨라짐"),
    83: ("PSYCHIC_SURGE", "시차 균열 → 선공을 막는 필드"),
    84: ("INTREPID_SWORD", "블레이드 시프트 → 등장할 때 공격력 ↑"),
    85: ("MIRROR_ARMOR", "리펄스 게이지 → 되돌려 보냄"),
    86: ("STURDY", "최후의 발악 → 한 번은 버팀"),
    87: ("CONTRARY", "인과의 이면 → 능력 변화가 반대로"),
    88: ("FLARE_BOOST", "도깨비 불 → 화상이면 강해짐"),
    89: ("SUPREME_OVERLORD", "데스페라도 → 혼자 남을수록 강해짐"),
    90: ("DAZZLING", "영애의 소양 → 기품, 선공을 막음"),
    91: ("DAUNTLESS_SHIELD", "낭만을 지키는 검 → 등장할 때 방어력 ↑"),
}

# 화면에 나올 설명 (블서로그 말로)
DESC = {
    "MOXIE": "상대를 쓰러뜨리면 공격력이 1단계 올라간다.",
    "NO_GUARD": "자신과 상대의 스킬이 반드시 맞는다.",
    "TECHNICIAN": "위력 60 이하 스킬의 위력이 1.5배가 된다.",
    "GUTS": "상태 이상일 때 공격력이 1.5배가 된다. 화상으로 공격력이 줄지 않는다.",
    "SUPER_LUCK": "급소에 맞기 쉬워진다.",
    "BEAST_BOOST": "상대를 쓰러뜨리면 가장 높은 능력이 1단계 올라간다.",
    "STAMINA": "공격을 받으면 방어력이 1단계 올라간다.",
    "MAGIC_BOUNCE": "상대가 거는 변화 스킬을 되돌려 보낸다.",
    "STAKEOUT": "이번 턴에 교체되어 나온 상대에게 주는 피해가 2배가 된다.",
    "HUSTLE": "공격력이 1.5배가 되지만 물리 스킬이 잘 빗나간다.",
    "CLEAR_BODY": "상대가 자신의 능력을 떨어뜨릴 수 없다.",
    "CURSED_BODY": "공격을 받으면 30% 확률로 그 스킬을 봉인한다.",
    "CHEEK_POUCH": "열매를 먹으면 최대 체력의 1/3만큼 더 회복한다.",
    "POISON_TOUCH": "직접 공격하면 30% 확률로 상대를 중독 상태로 만든다.",
    "INNARDS_OUT": "쓰러질 때 마지막으로 받은 피해만큼 상대에게 피해를 준다.",
    "SPEED_BOOST": "매 턴이 끝날 때 속도가 1단계 올라간다.",
    "FLAME_BODY": "직접 공격을 받으면 30% 확률로 상대를 화상 상태로 만든다.",
    "MAGICIAN": "공격한 상대의 아이템을 빼앗는다.",
    "COMPETITIVE": "능력이 떨어지면 스킬 증폭이 2단계 올라간다.",
    "INTIMIDATE": "등장하면 상대의 공격력을 1단계 떨어뜨린다.",
    "QUICK_DRAW": "30% 확률로 먼저 행동한다.",
    "CHILLING_NEIGH": "상대를 쓰러뜨리면 공격력이 1단계 올라간다.",
    "MERCILESS": "중독 상태인 상대를 공격하면 반드시 급소에 맞는다.",
    "ANALYTIC": "상대보다 늦게 행동하면 스킬 위력이 1.3배가 된다.",
    "TINTED_LENS": "효과가 별로인 상대에게 주는 피해가 2배가 된다.",
    "ADAPTABILITY": "자기 역할군과 같은 스킬이 더 강해진다 (1.5배 → 2배).",
    "INFILTRATOR": "상대의 벽 · 대타를 무시하고 공격한다.",
    "INNER_FOCUS": "풀죽지 않고, 위협에 공격력이 떨어지지 않는다.",
    "TOUGH_CLAWS": "직접 공격하는 스킬의 위력이 1.3배가 된다.",
    "SHELL_ARMOR": "급소에 맞지 않는다.",
    "COMPOUND_EYES": "스킬 명중률이 1.3배가 된다.",
    "KEEN_EYE": "명중률이 떨어지지 않고, 상대의 회피율을 무시한다.",
    "ANGER_POINT": "급소에 맞으면 공격력이 최대로 올라간다.",
    "TRACE": "등장하면 상대의 패시브를 따라 한다.",
    "DEFIANT": "상대가 능력을 떨어뜨리면 공격력이 2단계 올라간다.",
    "MAGIC_GUARD": "공격 말고는 피해를 받지 않는다.",
    "SHADOW_TAG": "상대가 교체할 수 없다.",
    "PRANKSTER": "변화 스킬을 먼저 쓸 수 있다.",
    "WEAK_ARMOR": "물리 공격을 받으면 방어력이 1단계 떨어지고 속도가 2단계 올라간다.",
    "SYNCHRONIZE": "중독 · 둔화 · 화상이 되면 상대도 같은 상태로 만든다.",
    "NATURAL_CURE": "교체해서 들어가면 상태 이상이 낫는다.",
    "GRIM_NEIGH": "상대를 쓰러뜨리면 스킬 증폭이 1단계 올라간다.",
    "AFTERMATH": "직접 공격에 쓰러지면 상대에게 최대 체력의 1/4만큼 피해를 준다.",
    "BERSERK": "공격을 받아 체력이 절반 아래가 되면 스킬 증폭이 1단계 올라간다.",
    "FUR_COAT": "물리 공격으로 받는 피해가 절반이 된다.",
    "STATIC": "직접 공격을 받으면 30% 확률로 상대를 둔화 상태로 만든다.",
    "PICKPOCKET": "직접 공격을 받으면 상대의 아이템을 빼앗는다.",
    "SERENE_GRACE": "스킬 추가 효과가 나올 확률이 2배가 된다.",
    "OPPORTUNIST": "상대의 능력이 올라가면 자신도 똑같이 올린다.",
    "ICE_SCALES": "스증 공격으로 받는 피해가 절반이 된다.",
    "GRASSY_SURGE": "등장하면 5턴 동안 그래스필드를 만든다 (매 턴 체력을 조금 회복).",
    "WONDER_SKIN": "상대의 변화 스킬이 잘 맞지 않는다.",
    "BATTLE_ARMOR": "급소에 맞지 않는다.",
    "ARENA_TRAP": "상대가 교체할 수 없다.",
    "WATER_VEIL": "화상 상태가 되지 않는다.",
    "IRON_FIST": "주먹 스킬의 위력이 1.2배가 된다.",
    "REGENERATOR": "교체해서 들어가면 최대 체력의 1/3만큼 회복한다.",
    "SHEER_FORCE": "추가 효과가 있는 스킬은 추가 효과가 없어지는 대신 위력이 1.3배가 된다.",
    "PRESSURE": "상대가 스킬을 쓰면 PP가 1 더 줄어든다.",
    "SOUL_HEART": "누군가 쓰러질 때마다 스킬 증폭이 1단계 올라간다.",
    "LIMBER": "둔화 상태가 되지 않는다.",
    "ELECTRIC_SURGE": "등장하면 5턴 동안 일렉트릭필드를 만든다 (기절 상태가 되지 않음).",
    "WANDERING_SPIRIT": "직접 공격을 받으면 상대와 패시브를 바꾼다.",
    "SHIELD_DUST": "상대 스킬의 추가 효과를 받지 않는다.",
    "PARENTAL_BOND": "공격 스킬이 두 번 맞는다 (두 번째는 위력 1/4).",
    "UNAWARE": "상대의 능력 변화를 무시하고 싸운다.",
    "MOLD_BREAKER": "상대의 패시브를 무시하고 공격한다.",
    "MULTISCALE": "체력이 가득일 때 받는 피해가 절반이 된다.",
    "FLUFFY": "직접 공격으로 받는 피해가 절반이 된다.",
    "PERISH_BODY": "직접 공격을 받으면 자신과 상대 모두 3턴 뒤에 쓰러진다 (교체하면 풀림).",
    "ANGER_SHELL": "공격을 받아 체력이 절반 아래가 되면 공격력 · 스킬 증폭 · 속도가 오르고 방어력 · 스킬 저항이 떨어진다.",
    "SNIPER": "급소에 맞으면 피해가 더 커진다 (1.5배 → 2.25배).",
    "QUEENLY_MAJESTY": "상대가 선공 스킬로 자신을 공격할 수 없다.",
    "UNNERVE": "상대가 열매를 먹지 못한다.",
    "PUNK_ROCK": "소리 스킬의 위력이 1.3배가 되고, 소리 스킬로 받는 피해가 절반이 된다.",
    "SOLID_ROCK": "효과가 굉장한 공격으로 받는 피해가 줄어든다.",
    "SIMPLE": "능력 변화가 2배가 된다.",
    "SHARPNESS": "베는 스킬의 위력이 1.5배가 된다.",
    "BEADS_OF_RUIN": "자신 말고 모두의 스킬 저항이 0.75배가 된다.",
    "DOWNLOAD": "등장하면 상대의 방어력 · 스킬 저항을 비교해 공격력이나 스킬 증폭을 1단계 올린다.",
    "GORILLA_TACTICS": "공격력이 1.5배가 되지만 처음 고른 스킬만 쓸 수 있다.",
    "STEADFAST": "풀죽으면 속도가 1단계 올라간다.",
    "PSYCHIC_SURGE": "등장하면 5턴 동안 사이코필드를 만든다 (선공 스킬을 막음).",
    "INTREPID_SWORD": "처음 등장하면 공격력이 1단계 올라간다.",
    "MIRROR_ARMOR": "상대가 능력을 떨어뜨리려 하면 되돌려 보낸다.",
    "STURDY": "체력이 가득일 때 한 번에 쓰러지지 않는다 (체력 1로 버팀).",
    "CONTRARY": "능력 변화가 반대로 된다.",
    "FLARE_BOOST": "화상 상태일 때 스킬 증폭이 1.5배가 된다.",
    "SUPREME_OVERLORD": "쓰러진 동료 수만큼 공격력 · 스킬 증폭이 올라간다.",
    "DAZZLING": "상대가 선공 스킬로 자신을 공격할 수 없다.",
    "DAUNTLESS_SHIELD": "처음 등장하면 방어력이 1단계 올라간다.",
}

HEADERS = ["ER번호", "이름", "역할군", "패시브 이름", "빌려 쓸 특성", "효과 설명 (화면에 나와요)", "고른 이유 (초안)", "특성 원래 이름 (참고)", "메모"]
WIDTHS = [7, 12, 9, 20, 20, 60, 34, 16, 24]
F = "맑은 고딕"
thin = Side(style="thin", color="C9CED8")
B = Border(left=thin, right=thin, top=thin, bottom=thin)
HEAD = PatternFill("solid", fgColor="1F2533")
EDIT = PatternFill("solid", fgColor="FFF59D")
README = [
    ("패시브 시트 (11-12 추가)", True),
    ("· 실험체마다 고유 패시브 하나. 포켓로그 특성(ability)을 하나씩 빌려 쓰고, 이름 · 설명은 블서로그 것으로 바꿔요 (스킬과 같은 방식).", False),
    ("· 노란 칸: 패시브 이름 · 빌려 쓸 특성 (영어 이름 예: GUTS, 또는 한국어 원래 이름 예: 근성) · 효과 설명.", False),
    ("· 한 특성은 한 실험체만 쓸 수 있어요. 역할군(타입)에 기대는 특성(타오르는불꽃 · 부유 같은 것)은 블서로그에서 아무 일도 안 해요.", False),
    ("· 초안은 ER 패시브 설명 없이 이름 · 역할군 · 무기로 골랐어요. ER 패시브 설명(er-data 폴더)을 주시면 실제 효과에 맞춰 다시 골라요.", False),
    ("· 원하는 효과가 포켓로그 특성에 없으면 메모에 적어 주세요. 따로 만들어요.", False),
    ("", False),
    ("스킬 효과 (11-12 바뀜)", True),
    ("· 스킬 시트 효과 칸이 이제 그대로 게임에 들어가요. 쓸 수 있는 표현: '피해', '피해 + 30% 화상'(중독 · 출혈 · 화상 · 둔화 · 기절 · 속박 · 혼란 · 풀죽음),", False),
    ("  '공격 · 방어 1단계 ↑', '상대 공격 1단계 ↓', '쓴 뒤 스킬 증폭 2단계 ↓', '급소에 잘 맞음', '피해의 50% 회복', '체력 50% 회복', '반동 25%', '다음 턴 쉼'.", False),
    ("· 오른쪽 회색 '지금 효과 (빌려 쓴 기술)' 칸은 이제 안 써요 (빌려 쓴 기술은 연출만 써요).", False),
]


def ko_ability_names() -> dict[str, str]:
    import json

    ko = json.loads((ROOT / "locales/ko/ability.json").read_text(encoding="utf-8"))
    out = {}
    for key in re.findall(r"^\s+([A-Z0-9_]+),", (ROOT / "src/enums/ability-id.ts").read_text(encoding="utf-8"), re.M):
        camel = re.sub(r"_([a-z0-9])", lambda m: m[1].upper(), key.lower())
        out[key] = ko.get(camel, {}).get("name", "")
    return out


def add_sheet(path: Path, force: bool = False) -> bool:
    wb = load_workbook(path)
    if "패시브" in wb.sheetnames:
        if not force:
            return False
        del wb["패시브"]
    chars = wb["실험체"]
    col = {c.value: i for i, c in enumerate(chars[1])}
    er = (ROOT / "src/data/bseorogue/er-data.ts").read_text(encoding="utf-8")
    passive_name = {int(c): re.findall(r'"([^"]*)"', sk)[0] for c, sk in re.findall(r'"(\d+)": \{.*?skills: \[([^\]]*)\]', er, re.S)}
    ko = ko_ability_names()
    ws = wb.create_sheet("패시브", index=wb.sheetnames.index("스킬") + 1)
    for c, (h, w) in enumerate(zip(HEADERS, WIDTHS), 1):
        cell = ws.cell(1, c, h)
        cell.font = Font(name=F, size=10, bold=True, color="FFFFFF")
        cell.fill = HEAD
        cell.alignment = Alignment(horizontal="center", vertical="center", wrap_text=True)
        cell.border = B
        ws.column_dimensions[get_column_letter(c)].width = w
    ws.row_dimensions[1].height = 32
    ws.freeze_panes = "C2"
    r = 2
    for row in chars.iter_rows(min_row=2, values_only=True):
        code = row[col["ER번호"]]
        if code is None:
            continue
        key, why = DRAFT[int(code)]
        vals = [int(code), row[col["이름"]], row[col["역할군"]], passive_name.get(int(code), ""), key, DESC[key], why, ko.get(key, ""), ""]
        for c, v in enumerate(vals, 1):
            cell = ws.cell(r, c, v)
            cell.font = Font(name=F, size=9 if c in (7, 8) else 10, color="7A808C" if c in (7, 8) else "000000")
            cell.border = B
            cell.alignment = Alignment(vertical="center", wrap_text=c == 6)
            if c in (4, 5, 6, 9):
                cell.fill = EDIT
        r += 1
    readme = wb["읽어 주세요"]
    if not any("패시브 시트" in str(c.value) for c in readme["A"]):
        start = readme.max_row + 2
        for i, (text, bold) in enumerate(README):
            cell = readme.cell(start + i, 1, text)
            cell.font = Font(name=F, size=11 if bold else 10, bold=bold)
    wb.save(path)
    return True


if __name__ == "__main__":
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    target = Path(args[0]) if args else ROOT / "docs/sheets/실험체-스킬.xlsx"
    missing = [k for k, _ in DRAFT.values() if k not in DESC]
    if missing or len({k for k, _ in DRAFT.values()}) != len(DRAFT):
        raise SystemExit(f"초안 확인: 설명 없음 {missing} 또는 겹치는 특성")
    print("더함" if add_sheet(target, "--force" in sys.argv) else "이미 '패시브' 시트가 있어요 (다시 만들려면 --force)", target)
