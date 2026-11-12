/*
 * SPDX-FileCopyrightText: 2026 SG
 * SPDX-License-Identifier: AGPL-3.0-only
 */

import { BSEO_REWARD_OFF } from "#data/bseorogue/reward-trim";

/**
 * 블서로그에서 뺀 아이템인지 (보상 · 상점 · 적이 지닌 물건 모두).
 *
 * 무엇을 뺄지는 SG 시트 '아이템 줄이기' 의 '결정' 칸 (scripts/er-sheet/item_trim.py → reward-trim.ts).
 * 포켓몬에만 맞아서 처음부터 뺀 것(스킬 기록 · 테라 · 메가 등)은 init-modifier-pools.ts 의 BSEO_NO_REWARD.
 *
 * @param id - 아이템 종류 이름 (예: "EVIOLITE")
 * @param sub - 한 종류 안에서 고르는 것 (음식 "LIECHI" · 강화제 "ACC" · 영구 강화 "HP" · 강화 모듈 타입 "NORMAL")
 */
export function bseoRewardOff(id: string | undefined, sub?: string): boolean {
  if (!id) {
    return false;
  }
  return BSEO_REWARD_OFF.has(sub ? `${id}:${sub}` : id);
}

/**
 * 여러 개 중에서 안 뺀 것만 (예: 음식 종류).
 * 전부 뺀 경우: 내 보상이면 빈 목록(그 아이템이 안 나옴), 적이 지닐 물건이면 원래 목록 그대로
 * (적 쪽은 고를 것이 그것뿐인 칸이 있어서, 비우면 다시 뽑기를 끝없이 해요).
 */
export function bseoRewardKeep<T>(
  id: string,
  all: readonly T[],
  nameOf: (v: T) => string,
  party: readonly { isPlayer(): boolean }[],
): T[] {
  const kept = all.filter(v => !bseoRewardOff(id, nameOf(v)));
  if (kept.length === 0 && !(party.length > 0 && party[0].isPlayer())) {
    return [...all];
  }
  return kept;
}
