/*
 * SPDX-FileCopyrightText: 2026 SG
 * SPDX-License-Identifier: AGPL-3.0-only
 */

// 이 파일은 scripts/er-sheet/item_trim.py 가 만들어요 (SG 시트 '아이템 줄이기' 의 '뺌'). 직접 고치지 마세요.

/** 블서로그에서 뺀 아이템. "ID" 또는 "ID:하위" (음식 · 강화제 · 영구 강화 · 강화 모듈 타입) — reward-filter.ts */
export const BSEO_REWARD_OFF: ReadonlySet<string> = new Set([
  "EVIOLITE", // 진화의휘석
  "LEEK", // 대파
  "MYSTICAL_ROCK", // 신비한바위
  "TOXIC_ORB", // 출혈구슬
  "FLAME_ORB", // 화염구슬
  "ATTACK_TYPE_BOOSTER:NORMAL", // 야생 · 보스 · 그 밖 타입 강화 모듈
  "ATTACK_TYPE_BOOSTER:BUG", // 야생 · 보스 · 그 밖 타입 강화 모듈
  "ATTACK_TYPE_BOOSTER:FLYING", // 야생 · 보스 · 그 밖 타입 강화 모듈
  "ATTACK_TYPE_BOOSTER:POISON", // 야생 · 보스 · 그 밖 타입 강화 모듈
  "ATTACK_TYPE_BOOSTER:GROUND", // 야생 · 보스 · 그 밖 타입 강화 모듈
  "ATTACK_TYPE_BOOSTER:GHOST", // 야생 · 보스 · 그 밖 타입 강화 모듈
  "ATTACK_TYPE_BOOSTER:STEEL", // 야생 · 보스 · 그 밖 타입 강화 모듈
  "ATTACK_TYPE_BOOSTER:FIRE", // 야생 · 보스 · 그 밖 타입 강화 모듈
  "ATTACK_TYPE_BOOSTER:WATER", // 야생 · 보스 · 그 밖 타입 강화 모듈
  "ATTACK_TYPE_BOOSTER:GRASS", // 야생 · 보스 · 그 밖 타입 강화 모듈
  "ATTACK_TYPE_BOOSTER:ELECTRIC", // 야생 · 보스 · 그 밖 타입 강화 모듈
  "ATTACK_TYPE_BOOSTER:ICE", // 야생 · 보스 · 그 밖 타입 강화 모듈
  "GREAT_BALL", // 슈퍼볼
  "ULTRA_BALL", // 하이퍼볼
  "ROGUE_BALL", // 로그볼
  "MASTER_BALL", // 마스터볼
  "SUPER_POTION", // 눈물젖은 빵
  "MAX_POTION", // 일레븐 세트
  "SACRED_ASH", // 아글라이아의 선물
  "MAX_ETHER", // 꿀물
  "ELIXIR", // 뜨거운 물
  "PP_MAX", // 포인트맥스
  "BERRY:LIECHI", // 초콜릿
  "BERRY:GANLON", // 감자
  "BERRY:PETAYA", // 양송이 버섯
  "BERRY:APICOT", // 호박 고구마
  "BERRY:SALAC", // 후라이드 치킨
  "BERRY:LANSAT", // 트러플
  "TEMP_STAT_STAGE_BOOSTER:DEF", // 방어력 강화제
  "TEMP_STAT_STAGE_BOOSTER:SPDEF", // 스킬 저항 강화제
  "TEMP_STAT_STAGE_BOOSTER:ACC", // 명중 강화제
  "DIRE_HIT", // 치명타 강화제
  "SUPER_EXP_CHARM", // 좋은경험부적
  "MINT", // 민트 (성격 바꾸기)
  "SOUL_DEW", // 마음의물방울
  "IV_SCANNER", // 실험체 분석기
  "SOOTHE_BELL", // 평온의방울
  "SHINY_CHARM", // 빛나는 부적
  "MEMORY_MUSHROOM", // 기억버섯
  "BASE_STAT_BOOSTER:SPDEF", // 캡슐 - 생명
]);
