# SPDX-FileCopyrightText: 2026 SG
# SPDX-License-Identifier: AGPL-3.0-only
"""
SG가 정할 것 · 바꿀 것 · 더할 것 (방법 포함) 엑셀 만들기 → docs/sheets/SG-정할-것.xlsx

시트: 읽어 주세요 · 할 일 목록 · 첫 공개 30명 · 명칭 정리 · 지역 · 역할군 · 아이템 그림
노란 칸만 SG가 채워요. 할 일이 바뀌면 TODO 표를 고치고 다시 돌려요 (SG가 채운 파일을 덮어쓰지 않게 나올 이름을 따로 줘요).
쓰는 법: python3 -B scripts/er-sheet/make_sg_todo.py [나올 파일]
"""
import json
import re
import sys
from pathlib import Path

from openpyxl import Workbook
from openpyxl.comments import Comment
from openpyxl.formatting.rule import FormulaRule
from openpyxl.styles import Alignment, Border, Font, PatternFill, Side
from openpyxl.utils import get_column_letter
from openpyxl.worksheet.datavalidation import DataValidation

ROOT = Path(__file__).resolve().parents[2]
_ARGS = [a for a in sys.argv[1:] if not a.startswith("--")]
OUT = Path(_ARGS[0]) if _ARGS else ROOT / "docs/sheets/SG-정할-것.xlsx"
F = "맑은 고딕"
thin = Side(style="thin", color="C9CED8")
B = Border(left=thin, right=thin, top=thin, bottom=thin)
HEAD = PatternFill("solid", fgColor="1F2533")
EDIT = PatternFill("solid", fgColor="FFF59D")
DONE = PatternFill("solid", fgColor="E3F2E1")
SUB = PatternFill("solid", fgColor="EEF1F6")
GREY = Font(name=F, size=9, color="7A808C")
ROLE_KO = {"TANK": "탱커", "BRUISER": "브루저", "ASSASSIN": "암살자", "MARKSMAN": "평원딜", "MAGE": "스증딜러", "SUPPORT": "서포터"}
STARTERS = {30: "일레븐", 11: "유키", 18: "쇼이치", 6: "나딘", 12: "혜진", 69: "레니"}

# (분류, 먼저?, 항목, 지금 상태, SG가 할 일 (방법), 받으면 제가 할 일, 관련 파일 · 화면)
TODO = [
    # ── 확인 (지금 바로) ──
    ("확인할 것", "먼저", "11-12 마무리 작업 미리보기 확인 → 병합",
     "브랜치 feat/dot-art (feat/polish 내용 포함): 기술 연출 7종 · 상태이상 이름 · 지역 배경 21곳(2026 기준) · 아이템 도트 · 상점 줄 겹침. 아직 main 에 안 합쳤어요",
     "Vercel 의 feat/dot-art 미리보기 주소에서 한 판 해 보기 → 괜찮으면 채팅에 \"병합해줘\"",
     "main 에 합치고 실제 사이트 배포 확인", "Vercel 프로젝트 bseorogue → Deployments → feat/dot-art"),
    ("확인할 것", "먼저", "아이템 도트 (팬키트 그림 → 32×32 도트)",
     "아이템 57개를 팬키트 아이템 그림으로 도트로 바꿈 + 강화 모듈 · 테라피스 · 부적은 색만 바꿔 44개. 나머지는 코드로 그린 그림 그대로",
     "이 파일 '아이템 그림' 시트: 고른 그림이 이상하면 '바꿀 팬키트 그림' 칸에 파일 이름 (예: Food/Hamburger). 코드 그림인 줄에도 적으면 그 그림으로 바꿔요",
     "build_item_dots.py 의 표를 고쳐 다시 만들기 (노트북 er 폴더 필요)", "이 파일 '아이템 그림' · docs/item-dots-preview.png"),
    ("확인할 것", "먼저", "소리 크기 · 상대 그림 크기 · 대사가 매번 바뀌는지",
     "한국어 음성 90명 (세레스 없음), 키마다 대사 최대 3개", "실제 사이트에서 스킬 몇 번 써 보고 크기 · 반복 느낌을 답 칸에",
     "소리 크기 조절 (지금 -18 LUFS) · 상대 그림 최대 높이(80) 조절", "게임 설정 → 효과음 크기"),
    ("확인할 것", "먼저", "Vercel 환경 변수 VITE_SUPABASE_ANON_KEY",
     "없으면 랭킹 올리기만 건너뛰어요", "Vercel → bseorogue → Settings → Environment Variables 에 공개 키(sb_publishable_…)가 있는지 보기. 비밀 키(sb_secret_…)는 절대 넣지 않기",
     "랭킹 올리기 확인", "Vercel 설정"),
    ("확인할 것", "보통", "기술 연출 7종 (색 · 크기 · 무기별 규칙)",
     "베기 · 타격 · 투사체 · 폭발 · 회복 · 강화 · 약화. 칼 · 도끼 · 창 → 베기, 망치 · 글러브 등 → 타격, 총 · 활 · 아르카나 등 → 투사체, R 위력 100 이상 → 폭발",
     "미리보기에서 보고 바꿀 점을 답 칸에 (예: \"폭발은 R 전부\", \"베기 더 크게\")",
     "make_fx.py · skill-anim.ts 고치기", "docs/fx-preview.png"),
    ("확인할 것", "보통", "지역 배경 21곳 (2026 기준)",
     "도트 느낌 배경 · 발판 21곳. 2026년 기준: 바지선(시즌 11) · 사과나무 · 괘종시계 · 분실물 상자 · 음식 자판기(시즌 13). 게임이 시간대 색을 덧입혀요", "마음에 안 드는 지역 · 바꿀 점을 답 칸에",
     "make_arenas.py 의 그 지역 함수 고치기", "docs/arenas-preview.png"),
    ("확인할 것", "보통", "상태이상 이름 (기획대로 바꿈)",
     "중독 · 출혈 · 화상 · 둔화 · 기절(잠듦 자리) · 속박. 쓰러진 실험체 아이콘은 '탈락'", "괜찮으면 \"OK\", 아니면 '명칭 정리' 시트에",
     "locales/ko/status-effect.json · 아이콘 다시 그리기", "전투 중 상태이상 아이콘"),
    # ── 정할 것 ──
    ("정할 것", "먼저", "실험체 · 스킬 시트 검토 (코스트 · 종족값 · 스킨 진화 · 스킬 숫자 · 효과)",
     "초안이 게임에 들어가 있어요. 효과 칸이 그대로 게임 효과 · 설명이 돼요",
     "docs/sheets/실험체-스킬.xlsx 의 노란 칸 고치기 → 채팅에 파일 보내기. 효과 칸 표현은 그 파일 '읽어 주세요' 시트에 (예: '피해 + 30% 화상', '공격 · 방어 1단계 ↑')",
     "가져오기(import_sheet.py) → 효과 · 설명 · 연출 틀 자동 → 테스트 → 미리보기", "실험체-스킬.xlsx '실험체' · '스킬' 시트"),
    ("정할 것", "먼저", "고유 패시브 91명 검토",
     "포켓몬 특성을 하나씩 빌려 쓰고 이름 · 설명은 블서로그 것. ER 설명 없이 이름 · 역할군으로 고른 초안",
     "실험체-스킬.xlsx '패시브' 시트 노란 칸 (패시브 이름 · 빌려 쓸 특성 · 효과 설명). 한 특성은 한 명만",
     "가져오기 → 테스트", "실험체-스킬.xlsx '패시브' 시트"),
    ("정할 것", "먼저", "첫 공개 실험체 30명",
     "지금은 91명 전부 고를 수 있어요 (임시, ALL_PLAYABLE)", "이 파일 '첫 공개 30명' 시트에서 고를 실험체 칸에 O",
     "roster.ts 의 BSEO_PLAYABLE 에 30명 · ALL_PLAYABLE 끄기", "이 파일 '첫 공개 30명'"),
    ("정할 것", "보통", "명칭 정리 (알 · 볼 · 도감 용어 · 풀죽음 등)",
     "11-08 \"내가 따로 할게\". 포켓몬 말이 남은 곳이 있어요", "이 파일 '명칭 정리' 시트 '새 이름' 칸",
     "locales/ko · 아이콘 같이 바꾸기", "이 파일 '명칭 정리'"),
    ("정할 것", "보통", "지역별 역할군 · 바지선 · 호텔 자리",
     "지역마다 자주 나오는 역할군(3배) 초안. 바지선(2026 시즌 11 신규 지역)은 seabed, 호텔은 snowyForest 자리에 임시로 붙였어요", "이 파일 '지역 · 역할군' 시트 노란 칸 (자리를 바꾸려면 메모에)",
     "regions.ts · biomes.json · make_arenas.py", "이 파일 '지역 · 역할군'"),
    ("정할 것", "보통", "스킨 진화 순서 · 레벨",
     "지금 ER 스킨 1번 · 2번, Lv12 · Lv24 (임시)", "실험체-스킬.xlsx '실험체' 시트 진화1/2 스킨 · 레벨 칸 (✓ 는 그림 있는 스킨)",
     "가져오기", "실험체-스킬.xlsx '실험체'"),
    ("정할 것", "보통", "관장 6명 · 보스 순서",
     "관장: 매그너스 · 재키 · 캐시 · 리오 · 자히르 · 요한. 보스: 알파 → 오메가 → 감마 → 위클라인 → 루미", "바꿀 사람 · 순서를 답 칸에",
     "leaders.ts · roster.ts", "docs/기획.md '적'"),
    ("정할 것", "보통", "UI 스타일 (창 색 · 모양)",
     "남색 판 + 금색 강조 (창 스타일 1~5 설정에서 고를 수 있어요)", "설정 → 창 스타일 바꿔 보고 마음에 드는 번호 · 바꿀 색을 답 칸에",
     "make_ui.py 맨 위 색 값 바꾸고 다시 그리기", "게임 설정 → 창 스타일"),
    ("정할 것", "나중", "야생동물 · 보스도 도트로 할지",
     "실험체만 도트면 전투에서 그림체가 섞여 보일 수 있어요", "\"동물도 도트\" / \"실험체만\" 답 칸에", "도트 규격 · 넣는 도구 넓히기", "도트 가이드 문서"),
    ("정할 것", "나중", "난이도 (50웨이브 클리어율 목표 10~20%)",
     "포켓로그 공식 · 레벨 상한 그대로, 티어마다 적 레벨 +3%", "몇 판 해 보고 \"쉬움 / 적당 / 어려움\" 과 막힌 웨이브를 답 칸에", "적 레벨 · 보스 숫자 조절",
     "docs/기획.md"),
    ("정할 것", "나중", "공개 시점 · 게임 버전",
     "무명섬 관리 화면에 블서로그 공개 스위치 · 받는 게임 버전 칸", "공개하고 싶을 때 말해 주기 (지금 버전 0.1.0)", "버전 올리기 · 공개 전 점검",
     "무명섬 관리자 화면 → 블서로그"),
    # ── 더할 것 (SG가 자료를 줘야 하는 것) ──
    ("더할 것", "먼저", "ER 스킬 · 패시브 설명 (er-data 폴더)",
     "없어서 스킬 효과 · 패시브를 이름 · 역할군으로만 정했어요", "SG PC 의 er-data 폴더(l10n-Korean.txt 가 있는 곳)를 채팅에 올리기. er-key.txt(API 키)는 절대 올리지 않기",
     "Q/W/E/R · 패시브 초안을 실제 ER 효과에 맞춰 다시 → 시트 2판", "PC 의 er-data 폴더"),
    ("더할 것", "나중", "남은 아이템 그림 (코드 그림 → 팬키트 도트)",
     "이름이 포켓몬 말인 아이템(코롱 · 부적 일부 등)은 맞는 팬키트 그림을 못 골라 코드 그림이에요", "명칭 정리로 이름이 정해지면 '아이템 그림' 시트에 쓸 팬키트 그림을 적기",
     "노트북 er 폴더에서 가져와 도트로", "이 파일 '아이템 그림'"),
    ("더할 것", "보통", "실험체 도트 (기준판 2~3명부터)",
     "넣는 도구 있음 (규격 검사 · 1배)", "님블뉴런 2차 창작 · AI 정책 확인 → 도트 가이드대로 2~3명 → 파일 이름 1_0.png 또는 재키_0.png 로 채팅에",
     "import_dot.py 로 검사 · 넣기 → 스크린샷", "도트 가이드 문서 · docs/dot-guide/"),
    ("더할 것", "보통", "최종 보스 · 안내 루미 그림",
     "지금 카드 그림", "AI 스트리머 루미 일러스트(전신, 배경 투명이면 좋음)를 채팅에", "보스 · 안내 그림으로 넣기", "assets/er/"),
    ("더할 것", "나중", "전투 BGM",
     "없음 (기획: 이리 BGM 중에 골라 올림)", "쓸 BGM 파일과 어느 화면(일반 · 보스 · 팀 전투)에 쓸지", "음량 맞추고 넣기 · 출처 기록", "assets/er/"),
    ("더할 것", "나중", "마스터즈 · KEL 팀 실험체 · 로고",
     "정하지 않은 팀은 무작위 실험체", "무명섬 관리 화면 → 블서로그 → 팀마다 실험체 3명 · 로고", "확인만 (게임이 무명섬에서 읽어요)", "무명섬 관리자 화면"),
    ("더할 것", "나중", "타이틀 로고 직접 그리기",
     "지금 코드로 그린 '블서로그' 글자", "PNG 로 보내기 (배경 투명)", "make_ui.py 의 logo() 대신 그 그림", "타이틀 화면"),
    ("더할 것", "나중", "세레스 음성",
     "팬키트에 음성 폴더가 비어 있음", "팬키트에 올라오면 알려 주기", "build_voice.py 로 더하기", "팬키트"),
    ("더할 것", "나중", "나중 기능: 무한 모드 · 금지구역 · 변이체 야생동물 · 라이벌 · ER 특성(해금 패시브) · 장비 5칸",
     "기획에 '나중에'로 정해 둔 것", "하고 싶은 순서를 답 칸에 (장비 · ER 특성은 er-data 필요)", "하나씩 브랜치에서 만들기", "docs/기획.md"),
    ("더할 것", "나중", "아직 임시 그림: 팀 · 관장 그림, 보급 상자 뽑기 화면, 로그인 버튼",
     "카드 · 단색 임시", "쓰고 싶은 그림이 있으면 보내기 (없으면 제가 코드로 그려요)", "그림 넣기 또는 코드로 그리기", "게임 화면"),
]

# 명칭 정리 (지금 이름, 어디에, 원래 포켓몬 말)
NAMES = [
    ("보급 상자", "알 (보급 상자 뽑기 · 부화)", "알"), ("보급 상자", "볼 1단계", "몬스터볼"), ("슈퍼볼 · 하이퍼볼 · 로그볼 · 마스터볼", "볼 등급", "같음"),
    ("커먼 · 레어 · 에픽 · 레전더리", "보급 상자 등급", "알 등급"), ("풀죽음", "한 턴 못 움직임 (스킬 효과 '기절(풀죽음)')", "풀죽음"),
    ("기절", "상태이상 (잠듦 자리, 기획)", "잠듦"), ("탈락 · 쓰러진", "쓰러진 실험체 아이콘 · 글자", "기절"), ("감염", "상태 아이콘", "포켓러스"),
    ("종족값", "도감 · 시트", "종족값"), ("자력기", "도감 (레벨로 배우는 스킬)", "자력기"), ("추가 스킬", "도감 · 시작 고르기 (알 기술)", "알 기술"),
    ("스킬 교본", "도감 (기술머신)", "기술머신"), ("바이옴", "도감 (어디서 나오나)", "바이옴"), ("성격", "시작 고르기 · 정보", "성격"),
    ("개체값", "시작 고르기", "개체값"), ("사탕 · 사탕 업그레이드", "시작 고르기", "사탕"), ("패시브 해금", "시작 고르기 (포켓로그 해금 특성, 지금 안 씀)", "패시브"),
    ("진화계보 · 진화", "도감 (스킨 진화)", "진화"), ("클리어 여부 (리본)", "도감", "리본"), ("행운", "보상 화면 오른쪽 위", "행운"),
    ("패시브", "실험체 고유 패시브 칸 (11-12 '특성'에서 바꿈)", "특성"), ("크레딧", "돈", "포켓달러"),
]


def header(ws, row, names, widths, height=30):
    for c, (h, w) in enumerate(zip(names, widths), 1):
        cell = ws.cell(row, c, h)
        cell.font = Font(name=F, size=10, bold=True, color="FFFFFF")
        cell.fill = HEAD
        cell.alignment = Alignment(horizontal="center", vertical="center", wrap_text=True)
        cell.border = B
        ws.column_dimensions[get_column_letter(c)].width = w
    ws.row_dimensions[row].height = height


def put(ws, r, c, v, edit=False, wrap=True, small=False, bold=False, fill=None):
    cell = ws.cell(r, c, v)
    cell.font = GREY if small else Font(name=F, size=10, bold=bold)
    cell.border = B
    cell.alignment = Alignment(vertical="center", wrap_text=wrap)
    if edit:
        cell.fill = EDIT
    elif fill:
        cell.fill = fill
    return cell


def characters():
    er = (ROOT / "src/data/bseorogue/er-data.ts").read_text(encoding="utf-8")
    names = {int(c): n for c, n in re.findall(r'"(\d+)": \{\s*name: "([^"]+)"', er)}
    sheet = (ROOT / "src/data/bseorogue/sheet-data.ts").read_text(encoding="utf-8")
    chars = {}
    block = sheet[sheet.index("SHEET_CHARACTERS"):sheet.index("SHEET_SKILLS")]
    for code, body in re.findall(r"^  (\d+): \{(.*?)^  \},", block, re.M | re.S):
        m = re.search(r'role: "(\w+)".*?weapon: "([^"]*)".*?cost: (\d+)', body, re.S)
        chars[int(code)] = (m[1], m[2], int(m[3]))
    voice = set(int(c) for c in re.findall(r"^  (\d+): \{", (ROOT / "src/data/bseorogue/voice-manifest.ts").read_text(encoding="utf-8"), re.M))
    return names, chars, voice


def main():
    # SG가 채운 파일(답 · '아이템 줄이기' 시트)을 지우지 않게: 이미 있으면 --force 가 있어야 덮어써요
    if OUT.exists() and "--force" not in sys.argv:
        raise SystemExit(f"{OUT.name} 이 이미 있어요. SG가 채운 답이 지워질 수 있어요 → 다른 이름을 주거나 --force")
    wb = Workbook()
    # 1) 읽어 주세요
    ws = wb.active
    ws.title = "읽어 주세요"
    ws.column_dimensions["A"].width = 120
    lines = [
        ("블서로그 · SG가 정할 것 · 바꿀 것 · 더할 것 (2026-11-12)", True),
        ("노란 칸만 채우면 돼요. 다 채우지 않아도 괜찮아요 — 채운 만큼 채팅에 파일을 보내 주시면 제가 이어서 해요.", False),
        ("", False),
        ("시트 5개", True),
        ("· 할 일 목록: 확인할 것 · 정할 것 · 더할 것 전부. '먼저' 부터 봐 주세요. 'SG 답' 칸에 답을 적어요 (예: OK / 병합해줘 / 바꿀 점).", False),
        ("· 첫 공개 30명: 처음 공개할 때 고를 수 있게 할 실험체. '고르기' 칸에 O. 지금 시작 6명은 O 가 미리 들어 있어요 (예시). 위쪽에 고른 수 · 역할군별 수가 자동으로 세져요.", False),
        ("· 명칭 정리: 포켓몬 말이 남은 이름들. '새 이름' 칸에 적으면 게임 글자 · 아이콘을 같이 바꿔요. 그대로 두려면 비워요.", False),
        ("· 지역 · 역할군: 지역마다 자주 나오는 역할군(3배)과 바지선 · 호텔 자리. 바꿀 것만 노란 칸에.", False),
        ("· 아이템 그림: 아이템마다 지금 쓰는 그림(팬키트 도트 또는 코드 그림). 바꾸고 싶은 것만 '바꿀 팬키트 그림' 칸에.", False),
        ("", False),
        ("어떻게 보내요?", True),
        ("· 이 파일(SG-정할-것.xlsx)을 고쳐서 채팅에 올리고 \"정할 것 시트 보냈어\" 라고 적어 주세요. 실험체-스킬.xlsx 도 같이 고쳤으면 같이 올려요.", False),
        ("· 비밀값(API 키 · 비밀 키 · 토큰 · er-key.txt)은 파일에도 채팅에도 넣지 않아요. 공개 저장소예요.", False),
        ("", False),
        ("예시 (할 일 목록 1번 줄): SG 답 = '병합해줘' · 메모 = '모바일은 나중에'", False),
    ]
    for i, (t, bold) in enumerate(lines, 1):
        c = ws.cell(i, 1, t)
        c.font = Font(name=F, size=12 if i == 1 else (11 if bold else 10), bold=bold)
        c.alignment = Alignment(wrap_text=True, vertical="center")
    ws.cell(len(lines) + 2, 1, "노란 칸 = SG가 채우는 칸").fill = EDIT
    ws.cell(len(lines) + 2, 1).font = Font(name=F, size=10)

    # 2) 할 일 목록
    ws = wb.create_sheet("할 일 목록")
    put(ws, 1, 1, "요약", bold=True, fill=SUB)
    kinds = ["확인할 것", "정할 것", "더할 것"]
    first = 5
    last = first + len(TODO) - 1
    # 요약은 넓은 칸(D~I)에: 분류마다 몇 개 · 답한 수
    for i, k in enumerate(kinds):
        put(ws, 1, 4 + i * 2, k, bold=True, fill=SUB)
        put(ws, 1, 5 + i * 2, f'=COUNTIF($B${first}:$B${last},"{k}")&"개 · 답 "&COUNTIFS($B${first}:$B${last},"{k}",$I${first}:$I${last},"<>")&"개"', fill=SUB)
    put(ws, 2, 4, "먼저 볼 것", bold=True, fill=SUB)
    put(ws, 2, 5, f'=COUNTIF($C${first}:$C${last},"먼저")&"개 · 답 "&COUNTIFS($C${first}:$C${last},"먼저",$I${first}:$I${last},"<>")&"개"', fill=SUB)
    header(ws, 4, ["번호", "분류", "먼저?", "항목", "지금 상태", "SG가 할 일 (방법)", "받으면 제가 할 일", "어디서 · 파일", "SG 답", "메모"],
           [6, 10, 7, 30, 42, 52, 34, 26, 22, 22])
    for i, row in enumerate(TODO):
        r = first + i
        put(ws, r, 1, i + 1).alignment = Alignment(horizontal="center", vertical="center")
        for c, v in enumerate(row, 2):
            put(ws, r, c, v, bold=c == 4)
        put(ws, r, 9, "", edit=True)
        put(ws, r, 10, "", edit=True)
        ws.row_dimensions[r].height = 62
    ws.freeze_panes = "E5"
    ws.auto_filter.ref = f"A4:J{last}"
    # 답이 있으면 줄을 연두색
    ws.conditional_formatting.add(f"A{first}:H{last}", FormulaRule(formula=[f"$I{first}<>\"\""], fill=DONE))
    ws["I4"].comment = Comment("여기에 답을 적어요. 예: OK · 병합해줘 · 바꿀 점", "Claude")

    # 3) 첫 공개 30명
    names, chars, voice = characters()
    ws = wb.create_sheet("첫 공개 30명")
    put(ws, 1, 1, "고른 수", bold=True, fill=SUB)
    n_first, n_last = 5, 5 + len(chars) - 1
    put(ws, 1, 2, f'=COUNTIF($H${n_first}:$H${n_last},"O")', bold=True, fill=SUB)
    put(ws, 1, 3, f'=IF(B1=30,"딱 30명!",IF(B1<30,(30-B1)&"명 더 골라요",(B1-30)&"명 많아요"))', fill=SUB)
    ws.merge_cells(start_row=1, start_column=3, end_row=1, end_column=4)
    for i, (k, ko) in enumerate(ROLE_KO.items()):
        put(ws, 2, 1 + i, ko, bold=True, fill=SUB)
        put(ws, 3, 1 + i, f'=COUNTIFS($C${n_first}:$C${n_last},"{ko}",$H${n_first}:$H${n_last},"O")', fill=SUB)
    header(ws, 4, ["ER번호", "이름", "역할군", "무기", "코스트", "음성", "시작 6명", "고르기 (O)", "메모"], [8, 14, 10, 12, 7, 7, 9, 11, 30])
    for i, code in enumerate(sorted(chars)):
        r = n_first + i
        role, weapon, cost = chars[code]
        put(ws, r, 1, code)
        put(ws, r, 2, names.get(code, ""))
        put(ws, r, 3, ROLE_KO.get(role, role))
        put(ws, r, 4, weapon)
        put(ws, r, 5, cost)
        put(ws, r, 6, "있음" if code in voice else "없음", small=code not in voice)
        put(ws, r, 7, "시작" if code in STARTERS else "")
        put(ws, r, 8, "O" if code in STARTERS else "", edit=True, wrap=False).alignment = Alignment(horizontal="center", vertical="center")
        put(ws, r, 9, "", edit=True)
    dv = DataValidation(type="list", formula1='"O"', allow_blank=True)
    ws.add_data_validation(dv)
    dv.add(f"H{n_first}:H{n_last}")
    ws.freeze_panes = "C5"
    ws.auto_filter.ref = f"A4:I{n_last}"
    ws.conditional_formatting.add(f"A{n_first}:G{n_last}", FormulaRule(formula=[f'$H{n_first}="O"'], fill=DONE))

    # 4) 명칭 정리
    ws = wb.create_sheet("명칭 정리")
    header(ws, 1, ["지금 이름", "어디에 나와요", "원래 포켓몬 말", "새 이름 (비우면 그대로)", "메모"], [26, 40, 16, 26, 30])
    for i, (now, where, orig) in enumerate(NAMES, 2):
        put(ws, i, 1, now, bold=True)
        put(ws, i, 2, where)
        put(ws, i, 3, orig, small=True)
        put(ws, i, 4, "", edit=True)
        put(ws, i, 5, "", edit=True)
    ws.freeze_panes = "B2"

    # 5) 지역 · 역할군
    ws = wb.create_sheet("지역 · 역할군")
    src = (ROOT / "src/data/bseorogue/regions.ts").read_text(encoding="utf-8")
    area = {k: (re.findall(r'"(\w+)"', roles), ko.split(" (")[0]) for k, roles, ko in re.findall(r"^  (\w+): \[([^\]]*)\], // (.+)$", src, re.M)}
    biome_ko = json.loads((ROOT / "locales/ko/biomes.json").read_text(encoding="utf-8"))
    by_region = {}
    for key, ko in biome_ko.items():
        by_region.setdefault(ko, []).append(key)
    header(ws, 1, ["지역", "붙은 포켓로그 바이옴", "자주 나오는 역할군 (지금)", "바꿀 역할군 (노란 칸)", "메모"], [14, 40, 26, 26, 34])
    regions = [(ko, roles) for roles, ko in area.values()]
    for i, (ko, roles) in enumerate(regions, 2):
        put(ws, i, 1, ko, bold=True)
        biomes = ", ".join(b for b in by_region.get(ko, []))
        put(ws, i, 2, biomes or "없음 — 붙일 바이옴을 메모에 (예: metropolis 를 호텔로)", small=not biomes)
        put(ws, i, 3, " · ".join(ROLE_KO.get(r, r) for r in roles) or "골고루")
        put(ws, i, 4, "", edit=True)
        put(ws, i, 5, "임시 자리 (11-12). 다른 바이옴으로 옮기려면 여기에" if ko in ("바지선", "호텔") else "", edit=True)
    ws.freeze_panes = "B2"

    # 6) 아이템 그림
    ws = wb.create_sheet("아이템 그림")
    header(ws, 1, ["번호", "나오는 정도", "게임 이름", "그림 파일 (items/)", "지금 그림", "팬키트 파일 (지금)", "바꿀 팬키트 그림 (노란 칸)", "메모"],
           [6, 10, 22, 22, 12, 46, 34, 26])
    sources = json.loads((ROOT / "assets/er/item-sources.json").read_text(encoding="utf-8"))
    from openpyxl import load_workbook

    listed = load_workbook(ROOT / "docs/sheets/아이템-팬키트-목록.xlsx")["게임에 나오는 아이템"]
    r = 2
    for row in listed.iter_rows(min_row=7, values_only=True):
        if not isinstance(row[0], int):
            continue
        num, freq, _tier, name, file = row[:5]
        key = str(file).replace(".png", "")
        if "*" in key:  # tm_* · *_tera_shard · mint_*
            src = next((v for k, v in sources.items() if k.endswith(key.replace("*", "")) or k.startswith(key.replace("*", ""))), None)
        else:
            src = sources.get(key)
        put(ws, r, 1, num)
        put(ws, r, 2, freq, small=True)
        put(ws, r, 3, name, bold=True)
        put(ws, r, 4, file, small=True)
        put(ws, r, 5, ("팬키트 도트 (색 바꿈)" if src and src.get("tint") else "팬키트 도트") if src else "코드 그림")
        put(ws, r, 6, src["file"] if src else "", small=True)
        put(ws, r, 7, "", edit=True)
        put(ws, r, 8, "", edit=True)
        r += 1
    ws.freeze_panes = "D2"

    for sh in wb.worksheets:
        sh.sheet_view.zoomScale = 100
    OUT.parent.mkdir(parents=True, exist_ok=True)
    wb.save(OUT)
    print(OUT, "할 일", len(TODO), "· 실험체", len(chars), "· 명칭", len(NAMES), "· 지역", len(regions), "· 아이템", r - 2)


if __name__ == "__main__":
    main()
