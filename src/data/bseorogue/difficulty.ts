/*
 * SPDX-FileCopyrightText: 2026 SG
 * SPDX-License-Identifier: AGPL-3.0-only
 */

/**
 * 티어별 팀 전투 자리 · 사기 실험체 (11-19 SG 난이도 시트 메모)
 *
 * 팀 전투 웨이브(BSEO.teamWaves: 5 · 15 · 25 · 35 · 45)에 무엇이 나올지는 티어마다 달라요
 * (docs/sheets/난이도.xlsx '팀 전투 자리' → difficulty-sheet.ts 의 TEAM_SLOTS).
 * - 사기 실험체: 영입할 수 없는 보스 실험체 1명 (전설의 포켓몬 느낌). 10웨이브 보스처럼 레벨 1.2배 · 체력 여러 줄.
 *   누구인지는 시트 '사기 실험체' (SG가 적어요). 비어 있으면 아무 실험체나 보스 버전으로 나와요.
 * - 마스터즈 · KEL: 팀 3명 (kel.ts)
 * 관장 웨이브는 마스터즈 팀이에요 (leaders.ts, 시트 '마스터즈 팀').
 */
import { BSEO } from "#app/bseorogue";
import { globalScene } from "#app/global-scene";
import { speciesDataRegistry } from "#app/global-species-data-registry";
import {
  OP_DEFAULT_SEGMENTS,
  OP_EXPERIMENTS,
  type OpExperiment,
  TEAM_SLOTS,
  type TeamSlotKind,
} from "#data/bseorogue/difficulty-sheet";
import { BSEO_CHARACTERS, bseoCharacter } from "#data/bseorogue/roster";
import { getRunTier } from "#data/bseorogue/tiers";
import type { PokemonSpecies } from "#data/pokemon-species";
import { randSeedShuffle } from "#utils/common";

const teamWaveIndex = (waveIndex: number) => (BSEO.teamWaves as readonly number[]).indexOf(waveIndex);

/** 이 티어로 이 팀 전투 웨이브에 나오는 것 (팀 전투 웨이브가 아니면 null) */
export function teamSlotKind(waveIndex: number, tier = getRunTier()): TeamSlotKind | null {
  const i = teamWaveIndex(waveIndex);
  if (i < 0) {
    return null;
  }
  return TEAM_SLOTS[tier]?.[i] ?? TEAM_SLOTS[0]?.[i] ?? "kel";
}

/** 사기 실험체가 나오는 웨이브인지 (클래식인지는 부르는 쪽이 봐요) */
export function isOpWave(waveIndex: number, tier = getRunTier()): boolean {
  return teamSlotKind(waveIndex, tier) === "op";
}

/** 같은 종류(op · masters · kel)의 팀 전투 웨이브 중 몇 번째인지 (판에서 겹치지 않게 고를 때) */
export function teamSlotOrder(waveIndex: number, tier = getRunTier()): number {
  const kind = teamSlotKind(waveIndex, tier);
  return Math.max(
    0,
    BSEO.teamWaves.filter(w => teamSlotKind(w, tier) === kind).indexOf(waveIndex as (typeof BSEO.teamWaves)[number]),
  );
}

/** 이 판 · 이 웨이브의 사기 실험체 (판마다 순서가 달라요. 한 판에서 같은 실험체는 안 나와요) */
export function opExperimentForWave(waveIndex: number): OpExperiment {
  const list: readonly OpExperiment[] =
    OP_EXPERIMENTS.length > 0
      ? OP_EXPERIMENTS
      : BSEO_CHARACTERS.map(c => ({ erCode: c.erCode, segments: OP_DEFAULT_SEGMENTS }));
  const slot = teamSlotOrder(waveIndex);
  let out: OpExperiment = list[0];
  globalScene.executeWithSeedOffset(() => {
    const order = randSeedShuffle(list.map((_, i) => i));
    out = list[order[slot % order.length]];
  }, 9101);
  return out;
}

/** 사기 실험체 종 (레벨에 맞게 스킨 진화한 모습). 사기 실험체 웨이브가 아니면 null */
export function opBossSpecies(waveIndex: number, level: number): PokemonSpecies | null {
  if (!globalScene.gameMode?.isClassic || !isOpWave(waveIndex)) {
    return null;
  }
  const c = bseoCharacter(opExperimentForWave(waveIndex).erCode);
  if (!c) {
    return null;
  }
  const base = speciesDataRegistry.getSpecies(c.id);
  return speciesDataRegistry.getSpecies(base.getWildSpeciesForLevel(level, true, true, globalScene.gameMode));
}

/** 사기 실험체의 체력 줄 수 (사기 실험체 웨이브가 아니면 0) */
export function opBossSegments(waveIndex: number): number {
  if (!globalScene.gameMode?.isClassic || !isOpWave(waveIndex)) {
    return 0;
  }
  return opExperimentForWave(waveIndex).segments;
}
