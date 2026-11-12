/*
 * SPDX-FileCopyrightText: 2026 SG
 * SPDX-License-Identifier: AGPL-3.0-only
 */

import { BSEO } from "#app/bseorogue";
import { globalScene } from "#app/global-scene";
import { speciesDataRegistry } from "#app/global-species-data-registry";
import { loadKelTeams } from "#data/bseorogue/kel";
import { applyBseoPassiveNames } from "#data/bseorogue/passive";
import { REGION_ROLES } from "#data/bseorogue/regions";
import { Role } from "#data/bseorogue/roles";
import { BSEO_ALL_IDS, BSEO_BOSSES, BSEO_CHARACTERS, BSEO_WILD, ENEMY_MOVE_NAMES } from "#data/bseorogue/roster";
import { SHEET_SKILLS } from "#data/bseorogue/sheet-data";
import { applyBseoSkillEffect } from "#data/bseorogue/skill-effect";
/**
 * 블서로그가 포켓로그 엔진에 끼어드는 곳들 (야생 · 보스 · 스킬 이름 · 역할군)
 */
import { allMoves } from "#data/data-lists";
import type { PokemonSpecies } from "#data/pokemon-species";
import { MoveCategory } from "#enums/move-category";
import { MoveId } from "#enums/move-id";
import type { PokemonType } from "#enums/pokemon-type";
import type { SpeciesId } from "#enums/species-id";
import { randSeedInt, randSeedItem } from "#utils/common";
import { toCamelCase } from "#utils/strings";
import i18next from "i18next";

const BSEO_ID_SET = new Set<number>(BSEO_ALL_IDS);

/** 블서로그 종(실험체 · 동물 · 보스)인지 */
export function isBseoSpecies(id: SpeciesId): boolean {
  return BSEO_ID_SET.has(id);
}

/**
 * 일반 웨이브의 적 하나
 * 대부분 실험체이고 (그 지역의 역할군이 3배 더 자주, regions.ts), BSEO.wildAnimalRate 확률로 동물이 나와요.
 * 실험체는 레벨에 맞춰 스킨 진화한 모습으로 나와요. 보스 웨이브는 따로예요.
 */
export function bseoWildSpecies(waveIndex: number, level: number): PokemonSpecies | null {
  const animals = BSEO_WILD.filter(w => w.fromWave <= waveIndex);
  if (animals.length > 0 && randSeedInt(1000) < BSEO.wildAnimalRate * 1000) {
    // 최근에 열린 동물이 조금 더 자주 나와요
    const weighted = animals.flatMap((w, i) => new Array(i + 1).fill(w.id) as SpeciesId[]);
    return speciesDataRegistry.getSpecies(randSeedItem(weighted));
  }
  const favored = REGION_ROLES[globalScene.arena?.biomeId] ?? [];
  const pool = BSEO_CHARACTERS.flatMap(c =>
    new Array(favored.some(r => Role[r] === c.role) ? 3 : 1).fill(c.id),
  ) as SpeciesId[];
  const base = speciesDataRegistry.getSpecies(randSeedItem(pool));
  const id = base.getWildSpeciesForLevel(level, true, false, globalScene.gameMode);
  return speciesDataRegistry.getSpecies(id);
}

/** 10웨이브마다 나오는 보스 */
export function bseoBossSpecies(waveIndex: number): PokemonSpecies | null {
  const boss = BSEO_BOSSES.find(b => b.wave === waveIndex);
  return boss ? speciesDataRegistry.getSpecies(boss.id) : null;
}

interface SkillMove {
  _type: PokemonType;
  _category: MoveCategory;
  power: number;
  accuracy: number;
  pp: number;
  priority: number;
  localize(): void;
}

/**
 * 시트의 위력 · 명중 · PP · 선공을 빌려 쓰는 기술에 넣어요.
 * 물리 ↔ 스증은 바꿔도 되지만, 변화 ↔ 공격은 기술 자체가 달라야 해서 그대로 둬요
 * (시트를 가져올 때 pick_skill_moves.py 가 분류에 맞는 기술로 바꿔 둬요. 테스트가 확인해요).
 */
function applySheetSkill(move: SkillMove, sheet: (typeof SHEET_SKILLS)[number][number] | undefined): void {
  if (!sheet) {
    return;
  }
  move.pp = sheet.pp;
  move.priority = sheet.priority;
  move.accuracy = sheet.accuracy;
  const isStatus = move._category === MoveCategory.STATUS;
  if (isStatus || sheet.category === "STATUS") {
    return;
  }
  move.power = sheet.power;
  move._category = sheet.category === "SPECIAL" ? MoveCategory.SPECIAL : MoveCategory.PHYSICAL;
}

/** 실험체 스킬: 빌려 쓰는 기술의 이름 · 상성(역할군) · 위력 · 명중 · PP · 효과 · 설명을 블서로그 것으로 */
export function initBseorogue(): void {
  // KEL 팀 불러오기 (기다리지 않아요. 못 불러오면 기본 팀)
  void loadKelTeams();
  for (const c of BSEO_CHARACTERS) {
    c.skills.forEach((s, i) => {
      const move = allMoves[s.move] as unknown as SkillMove | undefined;
      if (!move) {
        return;
      }
      // 이름 · 설명은 글자 묶음(i18n)에 넣어 둬야 다시 불러와도 안 바뀌어요
      const key = toCamelCase(MoveId[s.move]);
      const sheet = SHEET_SKILLS[c.erCode]?.[i];
      i18next.addResource(i18next.resolvedLanguage ?? "ko", "move", `${key}.name`, s.name);
      move._type = c.role as unknown as PokemonType;
      applySheetSkill(move, sheet);
      if (sheet?.desc) {
        applyBseoSkillEffect(allMoves[s.move], sheet);
        i18next.addResource(i18next.resolvedLanguage ?? "ko", "move", `${key}.effect`, sheet.desc);
      }
      move.localize();
    });
  }
  // 고유 패시브: 빌려 쓰는 특성 이름 · 설명
  applyBseoPassiveNames();
  for (const [id, name] of Object.entries(ENEMY_MOVE_NAMES)) {
    const move = allMoves[Number(id)] as unknown as { localize(): void } | undefined;
    if (move && name) {
      i18next.addResource(i18next.resolvedLanguage ?? "ko", "move", `${toCamelCase(MoveId[Number(id)])}.name`, name);
      move.localize();
    }
  }
}
