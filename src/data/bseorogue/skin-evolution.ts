/*
 * SPDX-FileCopyrightText: 2026 SG
 * SPDX-License-Identifier: AGPL-3.0-only
 */

import type { ErRoleKey } from "#data/bseorogue/er-data";

/**
 * 스킨 진화 (진화 = 스킨) — 임시 순서예요. 완성 뒤에 SG가 정하는 대로 이 표만 고치면 돼요.
 *
 * 실험체마다 기본 모습 → 스킨 진화 1 → 스킨 진화 2 로 진화해요.
 * - skins: 스킨 진화 1 · 2 에 쓸 스킨 번호. ER 스킨 목록 순서(er-data.ts 의 skins)이고, 0번이 기본 모습이에요.
 * - levels: 스킨 진화 1 · 2 가 되는 레벨
 * - roles: 스킨 진화하면서 역할군이 바뀌면 적어요 (null = 그대로). 예: [null, "BRUISER"]
 *
 * 표에 없는 실험체는 기본값(DEFAULT)을 써요: ER 스킨 목록 1번 · 2번 스킨, Lv12 · Lv24, 역할군 그대로.
 * 스킨이 모자라면 이름 뒤에 ★ 를 붙여요.
 */
export interface SkinEvolution {
  skins: readonly [number, number];
  levels: readonly [number, number];
  roles: readonly [ErRoleKey | null, ErRoleKey | null];
}

export const SKIN_EVOLUTION_DEFAULT: SkinEvolution = {
  skins: [1, 2],
  levels: [12, 24],
  roles: [null, null],
};

/** ER 실험체 번호 → 스킨 진화 (적은 것만 기본값 대신 써요) */
export const SKIN_EVOLUTION: Readonly<Partial<Record<number, Partial<SkinEvolution>>>> = {
  // 예) 일레븐: 선샤인 마린(3번) → 스위트(1번), Lv15 · Lv30, 마지막에 브루저로
  // 30: { skins: [3, 1], levels: [15, 30], roles: [null, "BRUISER"] },
};

export function skinEvolutionOf(erCode: number): SkinEvolution {
  return { ...SKIN_EVOLUTION_DEFAULT, ...SKIN_EVOLUTION[erCode] };
}
