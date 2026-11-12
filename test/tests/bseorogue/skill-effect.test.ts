/*
 * SPDX-FileCopyrightText: 2026 SG
 * SPDX-License-Identifier: AGPL-3.0-only
 */

// 스킬 효과: 시트 효과 칸이 빌려 쓰는 기술에 그대로 붙는지 (원래 포켓몬 효과는 지워짐)
import { SHEET_SKILLS } from "#data/bseorogue/sheet-data";
import { bseoSkillTargetsEnemy } from "#data/bseorogue/skill-effect";
import { SKILL_MOVES } from "#data/bseorogue/skill-moves";
import { allMoves } from "#data/data-lists";
import { BattlerIndex } from "#enums/battler-index";
import { MoveCategory } from "#enums/move-category";
import { MoveId } from "#enums/move-id";
import { MoveTarget } from "#enums/move-target";
import { SpeciesId } from "#enums/species-id";
import { Stat } from "#enums/stat";
import { StatusEffect } from "#enums/status-effect";
import type { StatStageChangeAttr, StatusEffectAttr } from "#moves/move";
import { GameManager } from "#test/framework/game-manager";
import Phaser from "phaser";
import { beforeAll, beforeEach, describe, expect, it } from "vitest";

const KNOWN = new Set([
  "StatusEffectAttr",
  "ConfuseAttr",
  "FlinchAttr",
  "StatStageChangeAttr",
  "HighCritAttr",
  "HitHealAttr",
  "HealAttr",
  "RecoilAttr",
  "RechargeAttr",
]);

function attrNames(id: MoveId): string[] {
  return allMoves[id].attrs.map(a => a.constructor.name);
}

describe("블서로그 스킬 효과", () => {
  let phaserGame: Phaser.Game;
  let game: GameManager;

  beforeAll(() => {
    phaserGame = new Phaser.Game({ type: Phaser.HEADLESS });
  });

  beforeEach(() => {
    game = new GameManager(phaserGame);
    game.override.enemyMoveset(MoveId.SPLASH);
  });

  it("변화 스킬은 변화 기술, 공격 스킬은 공격 기술을 빌려 써요", () => {
    for (const [code, moves] of Object.entries(SKILL_MOVES)) {
      moves.forEach((id, i) => {
        const sheet = SHEET_SKILLS[Number(code)][i];
        const isStatus = allMoves[id].category === MoveCategory.STATUS;
        expect(isStatus, `${code} ${"QWER"[i]} ${MoveId[id]}`).toBe(sheet.category === "STATUS");
      });
    }
  });

  it("모든 스킬에 시트 효과만 붙고 설명도 시트 효과로 바뀌어요", () => {
    for (const [code, moves] of Object.entries(SKILL_MOVES)) {
      moves.forEach((id, i) => {
        const sheet = SHEET_SKILLS[Number(code)][i];
        const where = `${code} ${"QWER"[i]} ${MoveId[id]}`;
        expect(sheet.desc, where).not.toBe("");
        expect(allMoves[id].effect, where).toBe(sheet.desc);
        expect(
          attrNames(id).every(n => KNOWN.has(n)),
          `${where}: ${attrNames(id)}`,
        ).toBe(true);
        expect(allMoves[id].chance, where).toBe(sheet.fx.chance);
        if (sheet.category === "STATUS") {
          expect(allMoves[id].moveTarget, where).toBe(
            bseoSkillTargetsEnemy(sheet.fx) ? MoveTarget.NEAR_OTHER : MoveTarget.USER,
          );
        }
      });
    }
  });

  it("재키 · 아야 · 일레븐 예시: 시트에 적힌 효과", () => {
    const [jq, jw, je, jr] = SKILL_MOVES[1];
    const [, , ae, ar] = SKILL_MOVES[2];
    const [, , ee, er] = SKILL_MOVES[30];
    expect(attrNames(jq)).toEqual([]); // 피해
    const coil = allMoves[jw].getAttrs("StatStageChangeAttr") as StatStageChangeAttr[];
    expect(coil.map(a => [a.stats, a.stages, a.selfTarget])).toEqual([[[Stat.ATK, Stat.DEF], 1, true]]); // 공격 · 방어 1단계 ↑
    expect(attrNames(je)).toEqual(["HitHealAttr"]); // 피해의 50% 회복
    expect(attrNames(jr)).toEqual(["HighCritAttr"]); // 피해 + 급소
    const burn = allMoves[ae].getAttrs("StatusEffectAttr") as StatusEffectAttr[];
    expect(burn.map(a => a.effect)).toEqual([StatusEffect.BURN]); // 피해 + 30% 화상
    expect(allMoves[ae].chance).toBe(30);
    const drop = allMoves[ar].getAttrs("StatStageChangeAttr") as StatStageChangeAttr[];
    expect(drop.map(a => [a.stats, a.stages, a.selfTarget])).toEqual([[[Stat.SPATK], -2, true]]); // 쓴 뒤 스킬 증폭 2단계 ↓
    expect(attrNames(ee)).toEqual(["FlinchAttr"]); // 피해 + 30% 기절(풀죽음)
    const atkDown = allMoves[er].getAttrs("StatStageChangeAttr") as StatStageChangeAttr[];
    expect(atkDown.map(a => [a.stats, a.stages, a.selfTarget])).toEqual([[[Stat.ATK], -1, false]]); // 상대 공격 1단계 ↓
  });

  it("전투에서: 재키 W 를 쓰면 공격 · 방어만 1단계 올라요 (빌려 쓴 기술의 원래 효과는 안 나요)", async () => {
    const jw = SKILL_MOVES[1][1];
    game.override.moveset([jw]).enemySpecies(SpeciesId.BSEO_CHICKEN).startingWave(3).startingLevel(10).enemyLevel(5);
    await game.classicMode.startBattle(SpeciesId.BSEO_ELEVEN);
    const me = game.field.getPlayerPokemon();
    game.move.select(jw);
    await game.setTurnOrder([BattlerIndex.PLAYER, BattlerIndex.ENEMY]);
    await game.toEndOfTurn();
    expect(me.getStatStage(Stat.ATK)).toBe(1);
    expect(me.getStatStage(Stat.DEF)).toBe(1);
    for (const s of [Stat.SPATK, Stat.SPDEF, Stat.SPD, Stat.ACC, Stat.EVA] as const) {
      expect(me.getStatStage(s)).toBe(0);
    }
  });

  it("전투에서: 일레븐 R 을 맞으면 상대 공격이 1단계 내려가요", async () => {
    const er = SKILL_MOVES[30][3];
    game.override.moveset([er]).enemySpecies(SpeciesId.BSEO_CHICKEN).startingWave(3).startingLevel(10).enemyLevel(50);
    await game.classicMode.startBattle(SpeciesId.BSEO_ELEVEN);
    const enemy = game.field.getEnemyPokemon();
    game.move.select(er);
    await game.setTurnOrder([BattlerIndex.PLAYER, BattlerIndex.ENEMY]);
    await game.move.forceHit();
    await game.toEndOfTurn();
    expect(enemy.getStatStage(Stat.ATK)).toBe(-1);
  });
});
