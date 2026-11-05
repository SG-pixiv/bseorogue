/*
 * SPDX-FileCopyrightText: 2026 SG
 * SPDX-License-Identifier: AGPL-3.0-only
 */

import { speciesDataRegistry } from "#app/global-species-data-registry";
import { loadKelTeams } from "#data/bseorogue/kel";
import { BSEO_ALL_IDS, BSEO_BOSSES, BSEO_CHARACTERS, BSEO_WILD, ENEMY_MOVE_NAMES } from "#data/bseorogue/roster";
/**
 * 블서로그가 포켓로그 엔진에 끼어드는 곳들 (야생 · 보스 · 스킬 이름 · 역할군)
 */
import { allMoves } from "#data/data-lists";
import type { PokemonSpecies } from "#data/pokemon-species";
import { MoveId } from "#enums/move-id";
import type { PokemonType } from "#enums/pokemon-type";
import type { SpeciesId } from "#enums/species-id";
import { randSeedItem } from "#utils/common";
import { toCamelCase } from "#utils/strings";
import i18next from "i18next";

const BSEO_ID_SET = new Set<number>(BSEO_ALL_IDS);

/** 블서로그 종(실험체 · 동물 · 보스)인지 */
export function isBseoSpecies(id: SpeciesId): boolean {
  return BSEO_ID_SET.has(id);
}

/** 이 웨이브에 나올 수 있는 야생동물 중 하나 (보스 웨이브는 따로) */
export function bseoWildSpecies(waveIndex: number): PokemonSpecies | null {
  const pool = BSEO_WILD.filter(w => w.fromWave <= waveIndex);
  if (pool.length === 0) {
    return null;
  }
  // 최근에 열린 동물이 조금 더 자주 나와요
  const weighted = pool.flatMap((w, i) => new Array(i + 1).fill(w.id) as SpeciesId[]);
  return speciesDataRegistry.getSpecies(randSeedItem(weighted));
}

/** 10웨이브마다 나오는 보스 */
export function bseoBossSpecies(waveIndex: number): PokemonSpecies | null {
  const boss = BSEO_BOSSES.find(b => b.wave === waveIndex);
  return boss ? speciesDataRegistry.getSpecies(boss.id) : null;
}

/** 실험체 스킬: 빌려 쓰는 기술의 이름 · 상성(역할군)을 블서로그 것으로 */
export function initBseorogue(): void {
  // KEL 팀 불러오기 (기다리지 않아요. 못 불러오면 기본 팀)
  void loadKelTeams();
  for (const c of BSEO_CHARACTERS) {
    for (const s of c.skills) {
      const move = allMoves[s.move] as unknown as { _type: PokemonType; localize(): void } | undefined;
      if (!move) {
        continue;
      }
      // 이름은 글자 묶음(i18n)에 넣어 둬야 다시 불러와도 안 바뀌어요
      i18next.addResource(i18next.resolvedLanguage ?? "ko", "move", `${toCamelCase(MoveId[s.move])}.name`, s.name);
      move._type = c.role as unknown as PokemonType;
      move.localize();
    }
  }
  for (const [id, name] of Object.entries(ENEMY_MOVE_NAMES)) {
    const move = allMoves[Number(id)] as unknown as { localize(): void } | undefined;
    if (move && name) {
      i18next.addResource(i18next.resolvedLanguage ?? "ko", "move", `${toCamelCase(MoveId[Number(id)])}.name`, name);
      move.localize();
    }
  }
}
