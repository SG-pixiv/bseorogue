/*
 * SPDX-FileCopyrightText: 2026 SG
 * SPDX-License-Identifier: AGPL-3.0-only
 */

// 11-19 SG "기술머신 방식으로 다시": 스킬 기록 = 같은 역할군 다른 실험체의 Q W E R
import { BSEO_CHARACTERS, erCodeOfSpecies } from "#data/bseorogue/roster";
import { SKILL_MOVES } from "#data/bseorogue/skill-moves";
import { bseoSkillRecordMoves, bseoSkillRecordTier } from "#data/bseorogue/skill-record";
import { modifierTypes } from "#data/data-lists";
import { ModifierTier } from "#enums/modifier-tier";
import { MoveId } from "#enums/move-id";
import { SpeciesId } from "#enums/species-id";
import { modifierPool } from "#modifiers/modifier-pools";
import type { ModifierTypeGenerator, TmModifierType } from "#modifiers/modifier-type";
import { GameManager } from "#test/framework/game-manager";
import { readFileSync } from "node:fs";
import { resolve } from "node:path";
import Phaser from "phaser";
import { beforeAll, beforeEach, describe, expect, it } from "vitest";

describe("블서로그 스킬 기록", () => {
  let phaserGame: Phaser.Game;
  let game: GameManager;

  beforeAll(() => {
    phaserGame = new Phaser.Game({ type: Phaser.HEADLESS });
  });

  beforeEach(() => {
    game = new GameManager(phaserGame);
    game.override.enemyMoveset(MoveId.SPLASH).enemySpecies(SpeciesId.BSEO_CHICKEN).startingWave(3);
  });

  it("배울 수 있는 것 = 같은 역할군 다른 실험체들의 Q W E R, 등급은 Q·W 일반 · E 좋음 · R 희귀", () => {
    for (const c of BSEO_CHARACTERS) {
      const moves = bseoSkillRecordMoves(c.id, c.role);
      expect(moves, `${c.erCode}`).not.toBeNull();
      const sameRole = BSEO_CHARACTERS.filter(o => o.role === c.role && o.erCode !== c.erCode).flatMap(
        o => SKILL_MOVES[o.erCode] ?? [],
      );
      expect(new Set(moves)).toEqual(new Set(sameRole));
      const other = BSEO_CHARACTERS.find(o => o.role !== c.role);
      for (const m of SKILL_MOVES[other!.erCode] ?? []) {
        expect(moves).not.toContain(m);
      }
    }
    const [q, w, e, r] = SKILL_MOVES[BSEO_CHARACTERS[0].erCode];
    expect([q, w, e, r].map(bseoSkillRecordTier)).toEqual([
      ModifierTier.COMMON,
      ModifierTier.COMMON,
      ModifierTier.GREAT,
      ModifierTier.ULTRA,
    ]);
    // 포켓몬 종 · 기술은 그대로 (포켓로그 기술머신 표)
    expect(bseoSkillRecordMoves(SpeciesId.PIKACHU, BSEO_CHARACTERS[0].role)).toBeNull();
    expect(bseoSkillRecordTier(MoveId.THUNDERBOLT)).toBeUndefined();
  });

  it("보상 풀에 다시 있고, 내 실험체가 아직 모르는 같은 역할군 스킬만 나와요", async () => {
    const ids = Object.values(modifierPool)
      .flat()
      .map(w => w.modifierType.id);
    for (const id of ["TM_COMMON", "TM_GREAT", "TM_ULTRA"]) {
      expect(ids, id).toContain(id);
    }

    await game.classicMode.startBattle(SpeciesId.BSEO_ELEVEN);
    const party = game.scene.getPlayerParty();
    const me = party[0];
    const code = erCodeOfSpecies(me.species.speciesId)!;
    const role = me.species.type1;
    const known = new Set(me.getMoveset().map(m => m.moveId));
    const own = new Set(SKILL_MOVES[code]);

    const compatible = me.getCompatibleTms(true, true, true);
    expect(compatible.length).toBeGreaterThan(0);
    for (const m of compatible) {
      expect(bseoSkillRecordMoves(me.species.speciesId, role)).toContain(m);
      expect(known.has(m), `${MoveId[m]} 이미 알아요`).toBe(false);
      expect(own.has(m), `${MoveId[m]} 자기 스킬`).toBe(false);
    }

    for (const [key, tier] of [
      ["TM_COMMON", ModifierTier.COMMON],
      ["TM_GREAT", ModifierTier.GREAT],
      ["TM_ULTRA", ModifierTier.ULTRA],
    ] as const) {
      const gen = modifierTypes[key]() as ModifierTypeGenerator;
      for (let i = 0; i < 20; i++) {
        const t = gen.generateType(party) as TmModifierType | null;
        if (!t) {
          continue;
        }
        expect(compatible, key).toContain(t.moveId);
        expect(bseoSkillRecordTier(t.moveId), key).toBe(tier);
      }
    }
  });

  it("이름은 '스킬 기록: <스킬>' 이에요", () => {
    const ko = JSON.parse(readFileSync(resolve(__dirname, "../../../locales/ko/modifier-type.json"), "utf-8"));
    expect(ko.ModifierType.TmModifierType.name).toContain("스킬 기록");
  });
});
