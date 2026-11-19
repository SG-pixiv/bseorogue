/*
 * SPDX-FileCopyrightText: 2026 SG
 * SPDX-License-Identifier: AGPL-3.0-only
 */

/**
 * 스킬 기록 (포켓로그 기술머신 자리, 11-19 SG: "기술머신 방식으로 다시")
 *
 * 보상에 '스킬 기록: <스킬 이름>' 이 나와요. 쓰면 그 스킬을 배워요 (Q W E R 4칸 중 하나와 바꿔요, 포켓로그 기술 배우기 화면).
 * 배울 수 있는 스킬 = 지금 역할군(스킨 진화로 바뀌면 바뀐 역할군)이 같은 실험체들의 Q W E R.
 * 자기 스킬은 레벨로 배우니까 빼고, 이미 아는 스킬 · 이미 쓴 스킬 기록도 빼요 (포켓로그 규칙 그대로).
 * 등급: Q · W = 일반 (TM_COMMON), E = 좋음 (TM_GREAT), R = 희귀 (TM_ULTRA).
 * 스킬 효과 · 이름 · 위력은 원래 실험체 것 그대로예요 (hooks.ts 가 기술마다 넣어 둔 것).
 */
import { Role } from "#data/bseorogue/roles";
import { BSEO_CHARACTERS, erCodeOfSpecies } from "#data/bseorogue/roster";
import { SKILL_MOVES } from "#data/bseorogue/skill-moves";
import { ModifierTier } from "#enums/modifier-tier";
import type { MoveId } from "#enums/move-id";
import type { PokemonType } from "#enums/pokemon-type";
import type { SpeciesId } from "#enums/species-id";

/** Q W E R 자리 → 스킬 기록 등급 */
const SLOT_TIER = [ModifierTier.COMMON, ModifierTier.COMMON, ModifierTier.GREAT, ModifierTier.ULTRA] as const;

const tierOf = new Map<MoveId, ModifierTier>();
const roleOf = new Map<MoveId, PokemonType>();
for (const c of BSEO_CHARACTERS) {
  SKILL_MOVES[c.erCode]?.forEach((move, i) => {
    tierOf.set(move, SLOT_TIER[i]);
    roleOf.set(move, c.role);
  });
}

const BSEO_ROLES = new Set<PokemonType>(Object.values(Role));

/**
 * 이 실험체가 스킬 기록으로 배울 수 있는 스킬 (같은 역할군 다른 실험체들의 Q W E R)
 * 실험체가 아니면 null (포켓로그 기술머신 목록을 그대로 써요)
 */
export function bseoSkillRecordMoves(speciesId: SpeciesId, role: PokemonType): MoveId[] | null {
  const code = erCodeOfSpecies(speciesId);
  if (code == null) {
    return null;
  }
  if (!BSEO_ROLES.has(role)) {
    return [];
  }
  // 자기 Q W E R 은 레벨로 배우니까 빼요 (아직 레벨이 안 된 R 도)
  const own = new Set<MoveId>(SKILL_MOVES[code] ?? []);
  return [...roleOf].filter(([move, r]) => r === role && !own.has(move)).map(([move]) => move);
}

/** 스킬 기록 등급 (실험체 스킬이 아니면 undefined → 포켓로그 기술머신 등급) */
export function bseoSkillRecordTier(moveId: MoveId): ModifierTier | undefined {
  return tierOf.get(moveId);
}
