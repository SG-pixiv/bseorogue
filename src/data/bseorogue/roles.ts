/*
 * SPDX-FileCopyrightText: 2026 SG
 * SPDX-License-Identifier: AGPL-3.0-only
 */

/**
 * 블서로그 역할군 상성 (포켓로그 타입 자리)
 *
 * 포켓로그의 타입 중 특별한 규칙(상태이상 면역 등)이 적은 것을 골라 역할군 자리로 써요.
 * 화면에 보이는 이름은 locales/ko/pokemon-info.json 의 type 에서 바꿔요.
 * 상성표는 임시예요. 기획이 정해지면 ROLE_CHART 숫자만 고치면 돼요.
 */
import { PokemonType } from "#enums/pokemon-type";

export const Role = {
  TANK: PokemonType.ROCK,
  BRUISER: PokemonType.FIGHTING,
  ASSASSIN: PokemonType.DARK,
  MARKSMAN: PokemonType.DRAGON,
  MAGE: PokemonType.PSYCHIC,
  SUPPORT: PokemonType.FAIRY,
} as const;
export type Role = (typeof Role)[keyof typeof Role];

/** 야생동물 · 보스 자리 (상성 없음) */
export const WILD_TYPE = PokemonType.NORMAL;
export const BOSS_TYPE = PokemonType.BUG;

/** 공격 역할군 → 맞는 역할군 → 배율 (없으면 1배) */
const ROLE_CHART: Partial<Record<Role, Partial<Record<Role, number>>>> = {
  [Role.TANK]: { [Role.ASSASSIN]: 2, [Role.BRUISER]: 0.5 },
  [Role.BRUISER]: { [Role.TANK]: 2, [Role.MARKSMAN]: 0.5 },
  [Role.ASSASSIN]: { [Role.MARKSMAN]: 2, [Role.MAGE]: 2, [Role.TANK]: 0.5 },
  [Role.MARKSMAN]: { [Role.BRUISER]: 2, [Role.ASSASSIN]: 0.5 },
  [Role.MAGE]: { [Role.TANK]: 2, [Role.SUPPORT]: 0.5 },
  [Role.SUPPORT]: { [Role.MAGE]: 2, [Role.BRUISER]: 0.5 },
};

const BSEO_TYPES = new Set<PokemonType>([...Object.values(Role), WILD_TYPE, BOSS_TYPE]);

/**
 * 블서로그 상성 배율. 맞는 쪽이 블서로그 타입이면 숫자(역할군끼리만 상성, 나머지 1배),
 * 아니면 null (포켓로그 표를 그대로 써요)
 */
export function bseoTypeMultiplier(attackType: PokemonType, defType: PokemonType): number | null {
  if (!BSEO_TYPES.has(defType)) {
    return null;
  }
  if (!BSEO_TYPES.has(attackType)) {
    return 1;
  }
  return ROLE_CHART[attackType as Role]?.[defType as Role] ?? 1;
}
