/*
 * SPDX-FileCopyrightText: 2026 SG
 * SPDX-License-Identifier: AGPL-3.0-only
 */

/**
 * ER 스탯 → 블서로그 종족값 환산 (초안)
 *
 * ER 실험체끼리는 기본 스탯 차이가 10% 안팎이라 그대로 옮기면 다 비슷해져요.
 * 그래서 역할군마다 기본 틀(평균 실험체일 때의 종족값)을 두고, ER 20레벨 스탯이 평균보다
 * 높고 낮은 만큼(세제곱으로 키워서) 틀을 늘리고 줄여요. 숫자는 SG가 손보는 초안이에요.
 * 종족값 순서: [체력, 공격력, 방어력, 스킬 증폭, 스킬 저항, 속도]
 */
import { ER_CHARACTERS, ER_MEANS, ER_MONSTERS } from "#data/bseorogue/er-data";
import { Role } from "#data/bseorogue/roles";

type Stats6 = readonly [number, number, number, number, number, number];

/** 역할군 기본 틀 */
export const ROLE_TEMPLATE: Readonly<Record<Role, Stats6>> = {
  [Role.TANK]: [90, 70, 85, 40, 70, 45],
  [Role.BRUISER]: [75, 85, 70, 40, 60, 70],
  [Role.ASSASSIN]: [60, 90, 55, 45, 55, 95],
  [Role.MARKSMAN]: [60, 95, 50, 50, 55, 85],
  [Role.MAGE]: [60, 45, 55, 95, 70, 75],
  [Role.SUPPORT]: [75, 50, 65, 80, 80, 65],
};

/** ER 차이를 얼마나 크게 볼지 (1 = 그대로, 3 = 세제곱) */
export const ER_STAT_AMPLIFY = 3;

const clamp = (v: number) => Math.max(20, Math.min(200, Math.round(v)));
const ratio = (v: number, mean: number, k: number) => (mean > 0 ? (v / mean) ** k : 1);

export function erCharacterStats(erCode: number, role: Role): Stats6 {
  const t = ROLE_TEMPLATE[role];
  const c = ER_CHARACTERS[erCode];
  if (!c) {
    return t;
  }
  const hp = ratio(c.hp20, ER_MEANS.hp20, ER_STAT_AMPLIFY);
  const ap = ratio(c.ap20, ER_MEANS.ap20, ER_STAT_AMPLIFY);
  const def = ratio(c.def20, ER_MEANS.def20, ER_STAT_AMPLIFY);
  const spd = ratio(c.moveSpeed, ER_MEANS.moveSpeed, 4) * ratio(c.attackSpeed, ER_MEANS.attackSpeed, 0.5);
  return [
    clamp(t[0] * hp),
    clamp(t[1] * ap),
    clamp(t[2] * def),
    clamp(t[3]),
    clamp(t[4] * Math.sqrt(def)),
    clamp(t[5] * spd),
  ];
}

/** 야생동물: ER 몬스터 체력 · 공격력 · 방어력 · 이동 속도로 */
export function erMonsterStats(key: string): Stats6 {
  const m = ER_MONSTERS[key];
  if (!m) {
    return [50, 50, 40, 30, 40, 50];
  }
  const atk = 30 + Math.max(m.ap, 15);
  const def = 25 + m.def * 0.8;
  return [clamp(30 + m.maxHp / 12), clamp(atk), clamp(def), clamp(atk * 0.6), clamp(def), clamp(m.moveSpeed * 14)];
}
