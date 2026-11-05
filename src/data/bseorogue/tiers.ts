/*
 * SPDX-FileCopyrightText: 2026 SG
 * SPDX-License-Identifier: AGPL-3.0-only
 */

/**
 * 판 밖 티어 (이터널 리턴 랭크처럼, 승급만 있고 강등은 없어요)
 *
 * 아이언부터 시작해서, 그 티어로 클래식(50웨이브)을 깨면 다음 티어가 열려요.
 * 새 게임에서 열린 티어 중 하나를 골라요. 티어가 높을수록 적 레벨이 올라가요.
 * 열린 티어는 이 브라우저에 저장돼요. 판의 티어는 저장 파일에도 같이 저장돼요.
 * 무명섬 랭킹은 티어가 높은 기록이 먼저예요.
 */

export const TIERS = [
  "아이언",
  "브론즈",
  "실버",
  "골드",
  "플래티넘",
  "다이아몬드",
  "메테오라이트",
  "미스릴",
  "데미갓",
  "이터니티",
] as const;

/** 티어 하나 오를 때마다 적 레벨 +3% (이터니티 +27%) */
export const TIER_LEVEL_BONUS = 0.03;

const UNLOCK_KEY = "bseo.tier.unlocked";

let runTier = 0;

const clampTier = (t: number) => Math.max(0, Math.min(TIERS.length - 1, Math.floor(Number(t) || 0)));

/** 지금 판의 티어 */
export function getRunTier(): number {
  return runTier;
}

export function setRunTier(tier: number): void {
  runTier = clampTier(tier);
}

export function tierName(tier = runTier): string {
  return TIERS[clampTier(tier)];
}

/** 열린 가장 높은 티어 */
export function unlockedTier(): number {
  try {
    return clampTier(Number(localStorage.getItem(UNLOCK_KEY) ?? 0));
  } catch {
    return 0;
  }
}

/** 지금 판의 티어로 클래식을 깼을 때: 다음 티어를 열고, 새로 열렸으면 그 티어를 돌려줘요 */
export function unlockNextTier(): number | null {
  const next = clampTier(runTier + 1);
  if (next <= unlockedTier() || next === runTier) {
    return null;
  }
  try {
    localStorage.setItem(UNLOCK_KEY, String(next));
  } catch {
    // 저장이 안 되는 브라우저(시크릿 창 등)
  }
  return next;
}

/** 적 레벨 배율 */
export function tierLevelMultiplier(tier = runTier): number {
  return 1 + TIER_LEVEL_BONUS * clampTier(tier);
}

/** 적 레벨에 티어를 적용 */
export function applyTierToLevel(level: number): number {
  return Math.max(1, Math.round(level * tierLevelMultiplier()));
}
