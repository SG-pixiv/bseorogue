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
]);
