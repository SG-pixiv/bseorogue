# SPDX-FileCopyrightText: 2026 SG
# SPDX-License-Identifier: AGPL-3.0-only
"""
아이템 줄이기: SG 시트 '아이템 줄이기' ↔ 게임에서 뺄 아이템 목록 (src/data/bseorogue/reward-trim.ts)

쓰는 법: python3 -I -B scripts/er-sheet/item_trim.py [엑셀 파일]   (기본 docs/sheets/SG-정할-것.xlsx)
  1) 엑셀에 '아이템 줄이기' 시트가 없으면 더해요. 있으면 SG가 적은 '아이템'(이름) · '결정' · '메모' 는 그대로 두고 나머지(효과 · 추천)만 새로 써요.
     다른 시트는 건드리지 않아요.
  2) '결정' 칸이 '뺌' 인 아이템을 reward-trim.ts 에 써요 → 게임이 보상 · 상점 · 적이 지닌 물건에서 빼요 (reward-filter.ts).
  3) '아이템' 칸 이름이 게임 글자(locales/ko)와 다르면 게임 글자를 그 이름으로 바꿔요 (아이템 이름 바꾸기, 11-12 SG).
     그림은 따로예요: scripts/fankit/build_item_dots.py 의 ITEMS 표.
  → 그 뒤: pnpm exec biome format --write src/data/bseorogue/reward-trim.ts 그리고 블서로그 테스트

아이템을 더하거나 구분을 바꾸려면 아래 ROWS 표를 고쳐요.
'고정' 줄은 포켓몬에만 맞아서 처음부터 빠져 있는 것 (init-modifier-pools.ts 의 BSEO_NO_REWARD), 시트에서 못 바꿔요.
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
XLSX = ROOT / "docs/sheets/SG-정할-것.xlsx"
OUT = ROOT / "src/data/bseorogue/reward-trim.ts"
SHEET = "아이템 줄이기"
KEEP, CUT, FIXED = "남김", "뺌", "뺌 (고정)"

ROLE_TYPES = {"ROCK": "탱커", "FIGHTING": "브루저", "DARK": "암살자", "DRAGON": "평원딜", "PSYCHIC": "스증딜러", "FAIRY": "서포터"}
OTHER_TYPES = ["NORMAL", "BUG", "FLYING", "POISON", "GROUND", "GHOST", "STEEL", "FIRE", "WATER", "GRASS", "ELECTRIC", "ICE"]
BERRY_KEY = {"SITRUS": "sitrus", "LUM": "lum", "ENIGMA": "enigma", "LIECHI": "liechi", "GANLON": "ganlon", "PETAYA": "petaya",
             "APICOT": "apicot", "SALAC": "salac", "LANSAT": "lansat", "STARF": "starf", "LEPPA": "leppa"}
TEMP_KEY = {"ATK": "x_attack", "DEF": "x_defense", "SPATK": "x_sp_atk", "SPDEF": "x_sp_def", "SPD": "x_speed", "ACC": "x_accuracy"}
BASE_KEY = {"HP": "hp_up", "ATK": "protein", "DEF": "iron", "SPATK": "calcium", "SPDEF": "zinc", "SPD": "carbos"}
TYPE_KEY = {"ROCK": "hard_stone", "FIGHTING": "black_belt", "DARK": "black_glasses", "DRAGON": "dragon_fang", "PSYCHIC": "twisted_spoon", "FAIRY": "fairy_feather"}
# 글자 묶음(locales)에 이름이 따로 없는 것
NAMES = {"MINT": "민트 (성격 바꾸기)"}

# (구분, 키, 효과, 나오는 곳, 처음 결정, 추천, 이유)   키: "ID" · "ID:하위" · 여러 개는 쉼표
ROWS = [
    # --- SG가 정한 것 (11-12): 빼기
    ("뺀 것 (11-12 SG)", "EVIOLITE", "진화 전 실험체의 방어 · 스킬 저항 ↑", "희귀", CUT, CUT, "진화가 스킨이라 어색"),
    ("뺀 것 (11-12 SG)", "LEEK", "특정 포켓몬 전용 급소 ↑", "희귀", CUT, CUT, "포켓몬 전용"),
    ("뺀 것 (11-12 SG)", "MYSTICAL_ROCK", "날씨 · 필드 지속 +2턴", "희귀", CUT, CUT, "날씨 스킬이 없음"),
    ("뺀 것 (11-12 SG)", "TOXIC_ORB", "지니면 턴 끝에 출혈 상태가 됨", "희귀", CUT, CUT, "구슬류 제거 (SG)"),
    ("뺀 것 (11-12 SG)", "FLAME_ORB", "지니면 턴 끝에 화상 상태가 됨", "희귀", CUT, CUT, "구슬류 제거 (SG)"),
    ("뺀 것 (11-12 SG)", ",".join(f"ATTACK_TYPE_BOOSTER:{t}" for t in OTHER_TYPES), "야생 · 보스 · 블서로그에 없는 타입 스킬 위력 ↑", "희귀", CUT, CUT, "내 실험체는 그 역할군 스킬을 안 씀"),
    ("뺀 것 (11-12 SG)", "GREAT_BALL", "볼 등급 2", "좋음", CUT, CUT, "볼 하나로 통합 (4-16)"),
    ("뺀 것 (11-12 SG)", "ULTRA_BALL", "볼 등급 3", "희귀", CUT, CUT, "볼 하나로 통합"),
    ("뺀 것 (11-12 SG)", "ROGUE_BALL", "볼 등급 4", "로그", CUT, CUT, "볼 하나로 통합"),
    ("뺀 것 (11-12 SG)", "MASTER_BALL", "반드시 잡는 볼", "마스터", CUT, CUT, "볼 하나로 통합 (확정 횟수로 대신)"),
    # --- 겹치는 것: SG가 고르기
    ("회복", "POTION", "HP 20 또는 10% 회복", "일반 · 상점", KEEP, KEEP, "작은 회복"),
    ("회복", "SUPER_POTION", "HP 50 또는 25% 회복", "일반 · 상점", KEEP, CUT, "고기와 민트 초코 사이라 겹침"),
    ("회복", "HYPER_POTION", "HP 200 또는 50% 회복", "좋음", KEEP, KEEP, "큰 회복"),
    ("회복", "MAX_POTION", "HP 전부 회복", "좋음", KEEP, CUT, "만년수프와 겹침"),
    ("회복", "FULL_RESTORE", "HP 전부 + 상태이상 회복", "좋음", KEEP, KEEP, "전부 회복"),
    ("회복", "FULL_HEAL", "상태이상 회복", "좋음 · 상점", KEEP, KEEP, "상태이상만 고치는 건 이것뿐"),
    ("부활", "REVIVE", "쓰러진 실험체를 HP 절반으로 부활", "좋음 · 상점", KEEP, KEEP, ""),
    ("부활", "MAX_REVIVE", "쓰러진 실험체를 HP 전부로 부활", "좋음", KEEP, KEEP, ""),
    ("부활", "SACRED_ASH", "쓰러진 실험체 모두 부활", "좋음", KEEP, CUT, "파티가 3명이라 부활 키트와 차이가 작음"),
    ("PP", "ETHER", "스킬 1개 PP 10 회복", "일반 · 상점", KEEP, KEEP, ""),
    ("PP", "MAX_ETHER", "스킬 1개 PP 전부 회복", "일반", KEEP, CUT, "물과 겹침"),
    ("PP", "ELIXIR", "모든 스킬 PP 10 회복", "좋음", KEEP, CUT, "백일취와 겹침"),
    ("PP", "MAX_ELIXIR", "모든 스킬 PP 전부 회복", "좋음", KEEP, KEEP, ""),
    ("PP", "PP_UP", "스킬 1개 최대 PP 영구 증가", "좋음", KEEP, KEEP, ""),
    ("PP", "PP_MAX", "스킬 1개 최대 PP 영구 크게 증가", "희귀", KEEP, CUT, "포인트업과 겹침"),
    ("음식 (지니면 조건 맞을 때 자동으로 먹음)", "BERRY:SITRUS", "HP 절반 아래일 때 25% 회복", "일반", KEEP, KEEP, ""),
    ("음식 (지니면 조건 맞을 때 자동으로 먹음)", "BERRY:LUM", "상태이상 · 혼란 회복", "일반", KEEP, KEEP, ""),
    ("음식 (지니면 조건 맞을 때 자동으로 먹음)", "BERRY:LEPPA", "PP 가 0 이 되면 10 회복", "일반", KEEP, KEEP, ""),
    ("음식 (지니면 조건 맞을 때 자동으로 먹음)", "BERRY:STARF", "HP 25% 아래일 때 능력 하나 크게 ↑", "일반", KEEP, KEEP, "아래 능력 음식 5종을 대신할 수 있음"),
    ("음식 (지니면 조건 맞을 때 자동으로 먹음)", "BERRY:ENIGMA", "효과가 굉장한 스킬에 맞으면 25% 회복", "일반", KEEP, KEEP, ""),
    ("음식 (지니면 조건 맞을 때 자동으로 먹음)", "BERRY:LIECHI", "HP 25% 아래일 때 공격력 ↑", "일반", KEEP, CUT, "능력 음식 5종이 겹침 (꿀고구마로)"),
    ("음식 (지니면 조건 맞을 때 자동으로 먹음)", "BERRY:GANLON", "HP 25% 아래일 때 방어력 ↑", "일반", KEEP, CUT, "〃"),
    ("음식 (지니면 조건 맞을 때 자동으로 먹음)", "BERRY:PETAYA", "HP 25% 아래일 때 스킬 증폭 ↑", "일반", KEEP, CUT, "〃"),
    ("음식 (지니면 조건 맞을 때 자동으로 먹음)", "BERRY:APICOT", "HP 25% 아래일 때 스킬 저항 ↑", "일반", KEEP, CUT, "〃"),
    ("음식 (지니면 조건 맞을 때 자동으로 먹음)", "BERRY:SALAC", "HP 25% 아래일 때 속도 ↑", "일반", KEEP, CUT, "〃"),
    ("음식 (지니면 조건 맞을 때 자동으로 먹음)", "BERRY:LANSAT", "HP 25% 아래일 때 급소 ↑", "일반", KEEP, CUT, "쓰임이 적음"),
    ("강화제 (5웨이브 동안)", "TEMP_STAT_STAGE_BOOSTER:ATK", "공격력 ↑", "일반", KEEP, KEEP, ""),
    ("강화제 (5웨이브 동안)", "TEMP_STAT_STAGE_BOOSTER:SPATK", "스킬 증폭 ↑", "일반", KEEP, KEEP, ""),
    ("강화제 (5웨이브 동안)", "TEMP_STAT_STAGE_BOOSTER:SPD", "속도 ↑", "일반", KEEP, KEEP, ""),
    ("강화제 (5웨이브 동안)", "TEMP_STAT_STAGE_BOOSTER:DEF", "방어력 ↑", "일반", KEEP, CUT, "방어 쪽 강화제는 잘 안 고름"),
    ("강화제 (5웨이브 동안)", "TEMP_STAT_STAGE_BOOSTER:SPDEF", "스킬 저항 ↑", "일반", KEEP, CUT, "〃"),
    ("강화제 (5웨이브 동안)", "TEMP_STAT_STAGE_BOOSTER:ACC", "명중률 ↑", "일반", KEEP, CUT, "쓰임이 적음"),
    ("강화제 (5웨이브 동안)", "DIRE_HIT", "급소 ↑", "좋음", KEEP, CUT, "쓰임이 적음"),
    ("경험치", "EXP_CHARM", "받는 경험치 +25%", "희귀", KEEP, KEEP, ""),
    ("경험치", "SUPER_EXP_CHARM", "받는 경험치 +60%", "로그", KEEP, CUT, "경험부적과 겹침"),
    ("경험치", "EXP_SHARE", "전투에 안 나간 실험체도 경험치 20%", "희귀", KEEP, KEEP, "파티 3명을 같이 키우는 데 필요"),
    # --- 시스템에 달린 것: SG가 정하기
    ("시스템에 달린 것", "MINT", "성격을 바꿈", "희귀", KEEP, CUT, "성격을 숨기는 쪽을 추천 (아래 메모)"),
    ("시스템에 달린 것", "SOUL_DEW", "성격 효과 +10%", "로그", KEEP, CUT, "성격과 같이"),
    ("시스템에 달린 것", "IV_SCANNER", "적 실험체 개체값을 봄", "희귀", KEEP, CUT, "개체값을 숨기는 쪽을 추천"),
    ("시스템에 달린 것", "SOOTHE_BELL", "친밀도가 50% 더 오름", "좋음", KEEP, CUT, "친밀도를 숨기는 쪽을 추천"),
    ("시스템에 달린 것", "SHINY_CHARM", "적이 색이 다른 모습으로 나올 확률 ↑", "마스터", KEEP, CUT, "색이 다른 모습 그림이 아직 없음"),
    ("시스템에 달린 것", "MEMORY_MUSHROOM", "잊은 스킬을 다시 배움", "좋음", KEEP, CUT, "스킬이 Q/W/E/R 4개뿐. 추가 스킬을 쓰면 남김"),
    # --- 남기는 것 (11-12 SG "남기는 거는 전부 남기자")
    *[("영구 강화", f"BASE_STAT_BOOSTER:{k}", f"{n} 영구 +10%", "좋음", KEEP, KEEP, "") for k, n in
      [("HP", "HP"), ("ATK", "공격력"), ("DEF", "방어력"), ("SPATK", "스킬 증폭"), ("SPDEF", "스킬 저항"), ("SPD", "속도")]],
    *[("역할군 강화 모듈", f"ATTACK_TYPE_BOOSTER:{t}", f"{n} 스킬 위력 +20%", "희귀", KEEP, KEEP, "") for t, n in ROLE_TYPES.items()],
    ("레벨", "RARE_CANDY", "레벨 +1", "일반", KEEP, KEEP, ""),
    ("레벨", "RARER_CANDY", "파티 전원 레벨 +1", "희귀", KEEP, KEEP, ""),
    ("레벨", "CANDY_JAR", "VF 혈액 샘플이 올리는 레벨 +1", "희귀", KEEP, KEEP, ""),
    ("크레딧", "NUGGET", "크레딧 조금", "좋음", KEEP, KEEP, ""),
    ("크레딧", "BIG_NUGGET", "크레딧 많이", "희귀", KEEP, KEEP, ""),
    ("크레딧", "RELIC_GOLD", "크레딧 아주 많이", "로그", KEEP, KEEP, ""),
    ("크레딧", "AMULET_COIN", "받는 크레딧 +20%", "희귀", KEEP, KEEP, ""),
    ("크레딧", "GOLDEN_PUNCH", "준 피해의 50%만큼 크레딧", "희귀", KEEP, KEEP, ""),
    ("보급 요청권 · 지도", "VOUCHER", "보급 상자 뽑기 1번", "좋음", KEEP, KEEP, ""),
    ("보급 요청권 · 지도", "VOUCHER_PLUS", "보급 상자 뽑기 5번", "로그", KEEP, KEEP, ""),
    ("보급 요청권 · 지도", "VOUCHER_PREMIUM", "보급 상자 뽑기 10번", "마스터", KEEP, KEEP, ""),
    ("보급 요청권 · 지도", "MAP", "갈림길에서 다음 지역을 고름", "좋음", KEEP, KEEP, ""),
    ("보급 요청권 · 지도", "LOCK_CAPSULE", "보상을 갱신할 때 등급을 고정", "로그", KEEP, KEEP, ""),
    ("지닌 물건", "LEFTOVERS", "매 턴 HP 1/16 회복", "로그", KEEP, KEEP, ""),
    ("지닌 물건", "SHELL_BELL", "준 피해의 1/8 회복", "로그", KEEP, KEEP, ""),
    ("지닌 물건", "FOCUS_BAND", "10% 확률로 HP 1 로 버팀", "로그", KEEP, KEEP, ""),
    ("지닌 물건", "REVIVER_SEED", "쓰러질 때 한 번 HP 절반으로 회복", "희귀", KEEP, KEEP, ""),
    ("지닌 물건", "QUICK_CLAW", "10% 확률로 먼저 행동", "희귀", KEEP, KEEP, ""),
    ("지닌 물건", "KINGS_ROCK", "공격하면 10% 확률로 스턴", "로그", KEEP, KEEP, ""),
    ("지닌 물건", "GRIP_CLAW", "공격하면 10% 확률로 상대 물건을 빼앗음", "로그", KEEP, KEEP, ""),
    ("지닌 물건", "BATON", "교체할 때 능력 변화를 넘겨줌", "로그", KEEP, KEEP, ""),
    ("지닌 물건", "WIDE_LENS", "명중률 +5", "희귀", KEEP, KEEP, ""),
    ("지닌 물건", "SCOPE_LENS", "급소 ↑", "로그", KEEP, KEEP, ""),
    ("지닌 물건", "MULTI_LENS", "공격이 한 번 더 맞음 (약하게)", "마스터", KEEP, KEEP, ""),
    ("지닌 물건", "BERRY_POUCH", "먹은 음식이 30% 확률로 안 없어짐", "로그", KEEP, KEEP, ""),
    ("지닌 물건", "HEALING_CHARM", "회복 효과 +10%", "마스터", KEEP, KEEP, ""),
    ("볼", "POKEBALL", "실험체를 잡는 볼 (지금은 포획이 꺼져 있어 안 나옴)", "일반", KEEP, KEEP, "볼 통합 · 포획 작업 때 켜요 (4-16)"),
    # --- 처음부터 빠져 있는 것 (포켓몬 전용, 고정)
    ("포켓몬 전용 (처음부터 빠져 있음)", "스킬 기록 (기술머신)", "포켓몬 기술을 가르침", "", FIXED, "", ""),
    ("포켓몬 전용 (처음부터 빠져 있음)", "더블배틀코롱 · 실버코롱 · 골드코롱", "더블배틀 확률 ↑", "", FIXED, "", "1:1 전투만"),
    ("포켓몬 전용 (처음부터 빠져 있음)", "테라스탈오브 · 테라피스 19종", "타입(역할군)을 바꿈", "", FIXED, "", ""),
    ("포켓몬 전용 (처음부터 빠져 있음)", "메가링 · 다이맥스 밴드 · 메가스톤 등", "메가진화 · 거다이맥스", "", FIXED, "", ""),
    ("포켓몬 전용 (처음부터 빠져 있음)", "유전자쐐기", "둘을 합체", "", FIXED, "", ""),
    ("포켓몬 전용 (처음부터 빠져 있음)", "특성부적 · 흔들림없는부적", "숨은 특성 · 포획 급소", "", FIXED, "", ""),
    ("포켓몬 전용 (처음부터 빠져 있음)", "진화 아이템 · 특정 포켓몬 전용", "진화 · 전용 강화", "", FIXED, "", ""),
    ("포켓몬 전용 (처음부터 빠져 있음)", "미니 블랙홀", "매 턴 상대 물건을 빼앗음", "", FIXED, "", ""),
]

HEADERS = ["구분", "아이템", "효과", "나오는 곳", "결정 (남김 / 뺌)", "추천", "추천 이유", "메모", "키 (고치지 마세요)"]
WIDTHS = [22, 24, 40, 13, 13, 8, 34, 24, 30]
F = "맑은 고딕"
thin = Side(style="thin", color="C9CED8")
B = Border(left=thin, right=thin, top=thin, bottom=thin)
HEAD = PatternFill("solid", fgColor="1F2533")
EDIT = PatternFill("solid", fgColor="FFF59D")
GREY = PatternFill("solid", fgColor="E6E8EC")
BAND = [PatternFill("solid", fgColor="F4F6FA"), None]
FIRST_ROW = 5
README = [
    ("아이템 줄이기 시트 (11-12 추가)", True),
    ("· 보상 · 상점에 나오는 아이템을 구분별로 모았어요. 노란 '결정' 칸에 남김 / 뺌 만 고르면 돼요 (칸을 누르면 고르는 목록이 나와요).", False),
    ("· 노란 '아이템' 칸의 이름을 고치면 게임 안 이름도 그렇게 바뀌어요.", False),
    ("· '뺌' 으로 하면 보상 · 상점 · 적이 지닌 물건에서 모두 안 나와요. '추천' 은 제 의견이고, 결정 칸이 실제로 들어가는 값이에요.", False),
    ("· 맨 위 '뺀 것' 은 SG가 11-12 에 빼기로 한 것, 맨 아래 회색은 포켓몬 전용이라 처음부터 빠져 있는 것 (못 바꿔요).", False),
]


VOUCHER_KEY = {"VOUCHER": "eggVoucher", "VOUCHER_PLUS": "eggVoucherPlus", "VOUCHER_PREMIUM": "eggVoucherPremium"}
BALL_KEY = {"POKEBALL": "pokeBall", "GREAT_BALL": "greatBall", "ULTRA_BALL": "ultraBall", "ROGUE_BALL": "rogueBall", "MASTER_BALL": "masterBall"}


def name_slot(key: str):
    """그 아이템 이름이 들어 있는 곳 → (locales/ko 파일, 키 길) 또는 None"""
    if "," in key:
        return None
    head, _, sub = key.partition(":")
    if head == "BERRY":
        return "berry.json", [BERRY_KEY[sub], "name"]
    if head == "TEMP_STAT_STAGE_BOOSTER":
        return "modifier-type.json", ["TempStatStageBoosterItem", TEMP_KEY[sub]]
    if head == "BASE_STAT_BOOSTER":
        return "modifier-type.json", ["BaseStatBoosterItem", BASE_KEY[sub]]
    if head == "ATTACK_TYPE_BOOSTER":
        return "modifier-type.json", ["AttackTypeBoosterItem", TYPE_KEY[sub]]
    if head in VOUCHER_KEY:
        return "voucher.json", [VOUCHER_KEY[head]]
    if head in BALL_KEY:
        return "pokeball.json", [BALL_KEY[head]]
    if head == "MINT":
        return None
    return "modifier-type.json", ["ModifierType", head, "name"]


def apply_names(wb) -> list[str]:
    """시트 '아이템' 칸 이름을 게임 글자에 넣기 → 바뀐 것 목록"""
    files, changed = {}, []
    for row in wb[SHEET].iter_rows(min_row=FIRST_ROW, values_only=True):
        key, name = row[8], str(row[1] or "").strip()
        slot = name_slot(key) if key else None
        if not slot or not name:
            continue
        fname, path = slot
        data = files.setdefault(fname, json.loads((ROOT / "locales/ko" / fname).read_text(encoding="utf-8")))
        node = data
        for k in path[:-1]:
            node = node.setdefault(k, {})
        if node.get(path[-1]) != name:
            changed.append(f"{node.get(path[-1])} → {name}")
            node[path[-1]] = name
    if changed:
        for fname, data in files.items():
            (ROOT / "locales/ko" / fname).write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return changed


def item_name(key: str, mt: dict, berry: dict, extra: dict, vouchers: dict, balls: dict) -> str:
    if "," in key:
        return "야생 · 보스 · 그 밖 타입 강화 모듈"
    head, _, sub = key.partition(":")
    if head in VOUCHER_KEY:
        return vouchers[VOUCHER_KEY[head]]
    if head in BALL_KEY:
        return balls[BALL_KEY[head]]
    if head == "BERRY":
        return berry[BERRY_KEY[sub]]["name"]
    if head == "TEMP_STAT_STAGE_BOOSTER":
        return extra["TempStatStageBoosterItem"][TEMP_KEY[sub]]
    if head == "BASE_STAT_BOOSTER":
        return extra["BaseStatBoosterItem"][BASE_KEY[sub]]
    if head == "ATTACK_TYPE_BOOSTER":
        return extra["AttackTypeBoosterItem"][TYPE_KEY[sub]]
    return (mt.get(head) or {}).get("name") or NAMES.get(head, head)


def build_sheet(wb) -> None:
    """'아이템 줄이기' 시트를 새로 쓰기 (SG가 적은 결정 · 메모는 키로 찾아서 그대로)"""
    answers = {}
    index = None
    if SHEET in wb.sheetnames:
        old = wb[SHEET]
        index = wb.sheetnames.index(SHEET)
        for row in old.iter_rows(min_row=FIRST_ROW, values_only=True):
            if row[8]:
                answers[row[8]] = (row[4], row[7], str(row[1] or "").strip())
        del wb[SHEET]
    ws = wb.create_sheet(SHEET, index=index if index is not None else len(wb.sheetnames))
    locale = json.loads((ROOT / "locales/ko/modifier-type.json").read_text(encoding="utf-8"))
    berry = json.loads((ROOT / "locales/ko/berry.json").read_text(encoding="utf-8"))
    vouchers = json.loads((ROOT / "locales/ko/voucher.json").read_text(encoding="utf-8"))
    balls = json.loads((ROOT / "locales/ko/pokeball.json").read_text(encoding="utf-8"))
    last = FIRST_ROW + len(ROWS) - 1
    ws["A1"] = "아이템 줄이기 — 노란 '결정' 칸에 남김 / 뺌 을 골라요. 뺌 이면 보상 · 상점 · 적이 지닌 물건에서 안 나와요."
    ws["A1"].font = Font(name=F, size=11, bold=True)
    ws["A2"] = "남김"
    ws["B2"] = f'=COUNTIF($E${FIRST_ROW}:$E${last},"{KEEP}")'
    ws["C2"] = f'="뺌 "&COUNTIF($E${FIRST_ROW}:$E${last},"{CUT}")&"개 · 추천과 다른 것 "&SUMPRODUCT(($F${FIRST_ROW}:$F${last}<>"")*($E${FIRST_ROW}:$E${last}<>$F${FIRST_ROW}:$F${last}))&"개"'
    for c in ("A2", "B2", "C2"):
        ws[c].font = Font(name=F, size=10, bold=True)
    for c, (h, w) in enumerate(zip(HEADERS, WIDTHS), 1):
        cell = ws.cell(FIRST_ROW - 1, c, h)
        cell.font = Font(name=F, size=10, bold=True, color="FFFFFF")
        cell.fill = HEAD
        cell.alignment = Alignment(horizontal="center", vertical="center", wrap_text=True)
        cell.border = B
        ws.column_dimensions[get_column_letter(c)].width = w
    ws.row_dimensions[FIRST_ROW - 1].height = 30
    ws.freeze_panes = ws.cell(FIRST_ROW, 3)
    dv = DataValidation(type="list", formula1=f'"{KEEP},{CUT}"', allow_blank=True)
    ws.add_data_validation(dv)
    band, prev = 0, None
    for i, (group, key, effect, where, decision, rec, why) in enumerate(ROWS):
        r = FIRST_ROW + i
        fixed = decision == FIXED
        if group != prev:
            band, prev = band + 1, group
        said, memo, new_name = answers.get(key, (None, None, ""))
        name = key if fixed else (new_name or item_name(key, locale["ModifierType"], berry, locale, vouchers, balls))
        vals = [group, name, effect, where, decision if fixed else (said or decision), rec, why, memo or "", "" if fixed else key]
        for c, v in enumerate(vals, 1):
            cell = ws.cell(r, c, v)
            cell.font = Font(name=F, size=9 if c in (7, 9) else 10, color="7A808C" if c in (7, 9) or fixed else "000000", bold=c == 1)
            cell.border = B
            cell.alignment = Alignment(vertical="center", wrap_text=c in (1, 3, 7, 8), horizontal="center" if c in (4, 5, 6) else None)
            if fixed:
                cell.fill = GREY
            elif c in (5, 8) or (c == 2 and "," not in key and not key.startswith("MINT")):
                cell.fill = EDIT
            elif BAND[band % 2]:
                cell.fill = BAND[band % 2]
        if not fixed:
            dv.add(ws.cell(r, 5))
    if "읽어 주세요" in wb.sheetnames:
        readme = wb["읽어 주세요"]
        if not any("아이템 줄이기 시트" in str(c.value) for c in readme["A"]):
            start = readme.max_row + 2
            for i, (text, bold) in enumerate(README):
                readme.cell(start + i, 1, text).font = Font(name=F, size=11 if bold else 10, bold=bold)


def read_decisions(wb) -> tuple[list[tuple[str, str]], list[str]]:
    """→ (뺄 것 [(키, 이름)], 틀린 줄)"""
    known = {key for _, key, _, _, d, _, _ in ROWS if d != FIXED}
    off, errors = [], []
    for r, row in enumerate(wb[SHEET].iter_rows(min_row=FIRST_ROW, values_only=True), FIRST_ROW):
        key, said = row[8], str(row[4] or "").strip()
        if not key:
            continue
        if key not in known:
            errors.append(f"{r}줄: 모르는 키 '{key}' (키 칸은 고치지 않아요)")
        elif said not in (KEEP, CUT, ""):
            errors.append(f"{r}줄 ({row[1]}): 결정 칸은 '{KEEP}' 이나 '{CUT}' 만 써요 (지금 '{said}')")
        elif said == CUT:
            off.extend((k, row[1]) for k in key.split(","))
    return off, errors


def write_ts(off: list[tuple[str, str]]) -> None:
    lines = [
        "/*",
        " * SPDX-FileCopyrightText: 2026 SG",
        " * SPDX-License-Identifier: AGPL-3.0-only",
        " */",
        "",
        "// 이 파일은 scripts/er-sheet/item_trim.py 가 만들어요 (SG 시트 '아이템 줄이기' 의 '뺌'). 직접 고치지 마세요.",
        "",
        "/** 블서로그에서 뺀 아이템. \"ID\" 또는 \"ID:하위\" (음식 · 강화제 · 영구 강화 · 강화 모듈 타입) — reward-filter.ts */",
        "export const BSEO_REWARD_OFF: ReadonlySet<string> = new Set([",
        *[f'  "{k}", // {n}' for k, n in off],
        "]);",
        "",
    ]
    OUT.write_text("\n".join(lines), encoding="utf-8")


def main() -> None:
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    path = Path(args[0]) if args else XLSX
    wb = load_workbook(path)
    build_sheet(wb)
    off, errors = read_decisions(wb)
    if errors:
        raise SystemExit("\n".join(errors))
    wb.save(path)
    write_ts(off)
    renamed = apply_names(wb)
    if renamed:
        print(f"이름 {len(renamed)}개 바꿈 (locales/ko): " + " · ".join(renamed))
    groups = {}
    for group, key, *_ in ROWS:
        groups.setdefault(group, []).append(key)
    cut = {k for k, _ in off}
    print(f"{path.name}: '{SHEET}' 시트 {len(ROWS)}줄 · 뺌 {len(off)}개 → {OUT.relative_to(ROOT)}")
    for group, keys in groups.items():
        n = sum(1 for k in keys if any(x in cut for x in k.split(",")))
        if n:
            print(f"  {group}: {n} / {len(keys)} 뺌")


if __name__ == "__main__":
    if re.search(r"[^\x00-\x7f]", KEEP) is None:  # 한글 상수 확인 (인코딩 깨짐 막기)
        raise SystemExit("파일 인코딩이 깨졌어요")
    main()
