/*
 * SPDX-FileCopyrightText: 2026 SG
 * SPDX-License-Identifier: AGPL-3.0-only
 */

import { BOSS_TYPE, WILD_TYPE } from "#data/bseorogue/roles";
import { BSEO_BOSSES, BSEO_STARTERS, BSEO_WILD, type Stats6 } from "#data/bseorogue/roster";
// 블서로그 실험체 · 야생동물 · 보스를 포켓로그 종(species) 데이터 형식으로 만들어요
import { GrowthRate } from "#data/exp";
import { PokemonSpecies } from "#data/pokemon-species";
import { AbilityId } from "#enums/ability-id";
import { EggTier } from "#enums/egg-type";
import type { MoveId } from "#enums/move-id";
import type { PokemonType } from "#enums/pokemon-type";
import type { SpeciesId } from "#enums/species-id";
import type { SpeciesDataMapConfig } from "#types/pokemon-species";
import type { StarterSpeciesId } from "#types/starter-species-id";

function makeSpecies(
  id: SpeciesId,
  type: PokemonType,
  stats: Stats6,
  opts: { catchRate: number; baseExp: number; subLegendary?: boolean },
) {
  const [hp, atk, def, spatk, spdef, spd] = stats;
  return new PokemonSpecies({
    id,
    generation: 1,
    ...(opts.subLegendary ? { subLegendary: true } : {}),
    category: "",
    type1: type as never,
    type2: null,
    height: 1.7,
    weight: 60,
    ability1: AbilityId.NONE,
    ability2: AbilityId.NONE,
    abilityHidden: AbilityId.NONE,
    baseTotal: hp + atk + def + spatk + spdef + spd,
    baseHp: hp,
    baseAtk: atk,
    baseDef: def,
    baseSpatk: spatk,
    baseSpdef: spdef,
    baseSpd: spd,
    catchRate: opts.catchRate,
    baseFriendship: 50,
    baseExp: opts.baseExp,
    growthRate: GrowthRate.MEDIUM_FAST,
    malePercent: null,
    genderDiffs: false,
  });
}

const levelMoves = (moves: readonly MoveId[]): [number, MoveId][] => moves.map(m => [1, m]);
const total = (s: Stats6) => s.reduce((a, b) => a + b, 0);
/** 쓰러뜨리면 받는 경험치: 센 동물일수록 많이 (포켓로그도 종족값이 높을수록 많아요) */
const expFor = (s: Stats6, rate: number) => Math.round(total(s) * rate);

export function initBseorogueSpecies(): SpeciesDataMapConfig {
  const data = {} as SpeciesDataMapConfig;
  for (const c of BSEO_STARTERS) {
    data[c.id] = {
      species: makeSpecies(c.id, c.role as unknown as PokemonType, c.stats, { catchRate: 45, baseExp: 64 }),
      starter: c.id as StarterSpeciesId,
      starterCost: c.cost,
      evolutions: [],
      eggTier: EggTier.COMMON,
      passives: AbilityId.NONE,
      levelMoves: c.skills.map(s => [s.level, s.move] as [number, MoveId]),
      tms: [],
    };
  }
  for (const w of BSEO_WILD) {
    data[w.id] = {
      species: makeSpecies(w.id, WILD_TYPE, w.stats, { catchRate: 0, baseExp: expFor(w.stats, 0.25) }),
      starter: w.id as unknown as StarterSpeciesId,
      evolutions: [],
      passives: AbilityId.NONE,
      levelMoves: levelMoves(w.moves),
      tms: [],
    };
  }
  for (const b of BSEO_BOSSES) {
    data[b.id] = {
      species: makeSpecies(b.id, BOSS_TYPE, b.stats, {
        catchRate: 0,
        baseExp: expFor(b.stats, 0.4),
        subLegendary: true,
      }),
      starter: b.id as unknown as StarterSpeciesId,
      evolutions: [],
      passives: AbilityId.NONE,
      levelMoves: levelMoves(b.moves),
      tms: [],
    };
  }
  return data;
}
