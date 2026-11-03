/*
 * SPDX-FileCopyrightText: 2026 SG
 * SPDX-License-Identifier: AGPL-3.0-only
 */

/**
 * 블서로그 종족값 (포켓로그 진화 라인을 참고해서 정했어요)
 *
 * 종족값 순서: [체력, 공격력, 방어력, 스킬 증폭, 스킬 저항, 속도]
 *
 * - 실험체는 "다 큰 모습(스킨 진화 2)"의 종족값을 실험체마다 정해요 (roster.ts).
 *   기본 모습 · 스킨 진화 1은 같은 모양에서 합만 줄여서 만들어요.
 * - 합은 코스트로 정해요 (COST_TOTALS). 같은 코스트면 합이 같고, 실험체마다 다른 건 "어디에 중점을 두는지"예요.
 * - 1코스트: 기본 320 → 스킨 진화 1 410 → 스킨 진화 2 500
 *   (포켓로그 이상해씨 318 → 이상해풀 405 → 이상해꽃 525, 파이리 309 → 리자드 405 → 리자몽 534 와 비슷해요)
 */
import { ER_MONSTERS } from "#data/bseorogue/er-data";
import { Role } from "#data/bseorogue/roles";

export type Stats6 = readonly [number, number, number, number, number, number];
export type Stages3 = readonly [Stats6, Stats6, Stats6];

/**
 * 코스트별 [기본, 스킨 진화 1, 스킨 진화 2] 합
 * 2코스트부터는 아직 실험체가 없어서 초안이에요.
 * 5코스트 이상(옛날 사기 실험체 등)은 포켓로그 전설처럼 처음부터 다 큰 모습이에요 (진화해도 합이 같아요).
 */
export const COST_TOTALS: Readonly<Record<number, readonly [number, number, number]>> = {
  1: [320, 410, 500],
  2: [330, 420, 520],
  3: [340, 435, 540],
  4: [350, 450, 560],
  5: [580, 580, 580],
  6: [600, 600, 600],
};

/**
 * 역할군 기본 모양 (다 큰 모습, 합 500)
 * 실험체마다 따로 정하지 않은 경우(예: 나중에 KEL 팀으로만 나오는 실험체)에 써요.
 */
export const ROLE_SHAPE: Readonly<Record<Role, Stats6>> = {
  [Role.TANK]: [110, 80, 110, 40, 100, 60],
  [Role.BRUISER]: [95, 110, 90, 40, 75, 90],
  [Role.ASSASSIN]: [70, 120, 65, 50, 65, 130],
  [Role.MARKSMAN]: [70, 125, 60, 60, 70, 115],
  [Role.MAGE]: [70, 50, 65, 130, 85, 100],
  [Role.SUPPORT]: [95, 55, 80, 100, 100, 70],
};

const sum = (s: readonly number[]) => s.reduce((a, b) => a + b, 0);

/** 같은 모양을 유지하면서 합을 total 로 (반올림 오차는 큰 자리부터 1씩 채워요) */
export function scaleTo(shape: Stats6, total: number): Stats6 {
  const raw = shape.map(v => (v * total) / sum(shape));
  const out = raw.map(Math.floor);
  const left = total - sum(out);
  raw
    .map((v, i) => [v - out[i], i] as const)
    .sort((a, b) => b[0] - a[0])
    .slice(0, left)
    .forEach(([, i]) => out[i]++);
  return out.map(v => Math.max(1, v)) as unknown as Stats6;
}

/** 다 큰 모습의 모양 → [기본, 스킨 진화 1, 스킨 진화 2] */
export function characterStages(finalShape: Stats6, cost: number): Stages3 {
  const totals = COST_TOTALS[cost] ?? COST_TOTALS[1];
  return totals.map(t => scaleTo(finalShape, t)) as unknown as Stages3;
}

/**
 * 야생동물 · ER 보스 몬스터: ER 몬스터 스탯(체력 · 공격력 · 방어력 · 이동 속도)으로 모양을 잡고, 합은 웨이브 단계에 맞춰요.
 * ER 숫자 그대로는 들개(11웨이브~)가 박쥐(1웨이브~)보다 약한 식이라 합은 따로 정해요.
 */
export function erMonsterStats(key: string, total: number): Stats6 {
  const m = ER_MONSTERS[key];
  if (!m) {
    return scaleTo([50, 50, 40, 30, 40, 50], total);
  }
  const atk = 30 + Math.max(m.ap, 15);
  const def = 25 + m.def * 0.8;
  return scaleTo([30 + m.maxHp / 12, atk, def, atk * 0.6, def, m.moveSpeed * 14], total);
}
