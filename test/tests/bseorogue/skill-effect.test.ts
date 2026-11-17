/*
 * SPDX-FileCopyrightText: 2026 SG
 * SPDX-License-Identifier: AGPL-3.0-only
 */

// 스킬 효과: 시트 효과 칸이 빌려 쓰는 기술에 그대로 붙는지 (원래 포켓몬 효과는 지워짐)
import { getPokemonNameWithAffix } from "#app/messages";
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
import i18next from "i18next";
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
  "BseoAttackHealAttr",
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

  it("시트 효과마다 맞는 효과가 붙어요 (상태이상 · 스턴 · 능력 변화 · 흡수 · 회복 · 급소 · 반동 · 쉼)", () => {
    for (const [code, moves] of Object.entries(SKILL_MOVES)) {
      moves.forEach((id, i) => {
        const { fx } = SHEET_SKILLS[Number(code)][i];
        const where = `${code} ${"QWER"[i]} ${MoveId[id]}`;
        const names = attrNames(id);
        const has = (n: string) => names.includes(n);
        expect(has("StatusEffectAttr"), where).toBe(!!fx.status);
        if (fx.status) {
          const st = allMoves[id].getAttrs("StatusEffectAttr") as StatusEffectAttr[];
          expect(
            st.map(a => StatusEffect[a.effect]),
            where,
          ).toEqual([fx.status]);
        }
        expect(has("ConfuseAttr"), where).toBe(!!fx.confuse);
        expect(has("FlinchAttr"), where).toBe(!!fx.flinch);
        expect(has("HighCritAttr"), where).toBe(!!fx.highCrit);
        expect(has("HitHealAttr"), where).toBe(!!fx.drain);
        expect(has("HealAttr") || has("BseoAttackHealAttr"), where).toBe(!!fx.heal);
        if (fx.heal) {
          // 공격 스킬의 회복은 체력이 가득이면 조용히 건너뛰는 것으로
          expect(has("BseoAttackHealAttr"), where).toBe(allMoves[id].category !== MoveCategory.STATUS);
        }
        expect(has("RecoilAttr"), where).toBe(!!fx.recoil);
        expect(has("RechargeAttr"), where).toBe(!!fx.recharge);
        const stats = allMoves[id].getAttrs("StatStageChangeAttr") as StatStageChangeAttr[];
        expect(
          stats.map(a => [a.stats.map(x => Stat[x]), a.stages, a.selfTarget]),
          where,
        ).toEqual((fx.stats ?? []).map(x => [[...x.stats], x.stages, x.self]));
      });
    }
  });

  /** 조건에 맞는 첫 스킬 (시트 값이 바뀌어도 검사가 깨지지 않게 시트에서 찾아요) */
  function findSkill(ok: (sk: (typeof SHEET_SKILLS)[number][number]) => boolean): {
    id: MoveId;
    sk: (typeof SHEET_SKILLS)[number][number];
  } {
    for (const [code, moves] of Object.entries(SKILL_MOVES)) {
      for (let i = 0; i < moves.length; i++) {
        const sk = SHEET_SKILLS[Number(code)][i];
        if (ok(sk)) {
          return { id: moves[i], sk };
        }
      }
    }
    throw new Error("조건에 맞는 스킬이 시트에 없어요");
  }
  const onlyStats = (sk: (typeof SHEET_SKILLS)[number][number]) =>
    Object.keys(sk.fx).every(k => k === "chance" || k === "stats")
    && sk.fx.stats?.length === 1
    && sk.fx.stats[0].chance >= 100;

  it("전투에서: 자기 강화 변화 스킬은 시트에 적힌 능력만 올라요 (빌려 쓴 기술의 원래 효과는 안 나요)", async () => {
    const { id, sk } = findSkill(x => x.category === "STATUS" && onlyStats(x) && !!x.fx.stats?.[0].self);
    const want = sk.fx.stats?.[0];
    game.override.moveset([id]).enemySpecies(SpeciesId.BSEO_CHICKEN).startingWave(3).startingLevel(10).enemyLevel(5);
    await game.classicMode.startBattle(SpeciesId.BSEO_ELEVEN);
    const me = game.field.getPlayerPokemon();
    game.move.select(id);
    await game.setTurnOrder([BattlerIndex.PLAYER, BattlerIndex.ENEMY]);
    await game.toEndOfTurn();
    for (const s of [Stat.ATK, Stat.DEF, Stat.SPATK, Stat.SPDEF, Stat.SPD, Stat.ACC, Stat.EVA] as const) {
      expect(me.getStatStage(s), Stat[s]).toBe(want?.stats.includes(Stat[s] as never) ? want.stages : 0);
    }
  });

  it("전투에서: 공격 스킬의 자기 회복은 체력이 가득이면 '체력이 가득' 메시지 없이 넘어가고, 다쳤으면 회복해요", async () => {
    const { id } = findSkill(x => x.category !== "STATUS" && !!x.fx.heal);
    game.override.moveset([id]).enemySpecies(SpeciesId.BSEO_CHICKEN).startingWave(3).startingLevel(10).enemyLevel(50);
    await game.classicMode.startBattle(SpeciesId.BSEO_ELEVEN);
    const me = game.field.getPlayerPokemon();
    const full = i18next.t("battle:hpIsFull", { pokemonName: getPokemonNameWithAffix(me) });
    game.move.select(id);
    await game.setTurnOrder([BattlerIndex.PLAYER, BattlerIndex.ENEMY]);
    await game.toNextTurn();
    expect(game.textInterceptor.logs).not.toContain(full);
    expect(me.isFullHp()).toBe(true);

    me.hp = Math.floor(me.getMaxHp() / 2);
    game.move.select(id);
    await game.setTurnOrder([BattlerIndex.PLAYER, BattlerIndex.ENEMY]);
    await game.toEndOfTurn();
    expect(me.hp).toBeGreaterThan(Math.floor(me.getMaxHp() / 2));
  });

  it("전투에서: 상대 능력을 내리는 공격 스킬을 맞으면 시트에 적힌 만큼 내려가요", async () => {
    const { id, sk } = findSkill(x => x.category !== "STATUS" && onlyStats(x) && !x.fx.stats?.[0].self);
    const want = sk.fx.stats?.[0];
    game.override.moveset([id]).enemySpecies(SpeciesId.BSEO_CHICKEN).startingWave(3).startingLevel(10).enemyLevel(50);
    await game.classicMode.startBattle(SpeciesId.BSEO_ELEVEN);
    const enemy = game.field.getEnemyPokemon();
    game.move.select(id);
    await game.setTurnOrder([BattlerIndex.PLAYER, BattlerIndex.ENEMY]);
    await game.move.forceHit();
    await game.toEndOfTurn();
    for (const s of [Stat.ATK, Stat.DEF, Stat.SPATK, Stat.SPDEF, Stat.SPD, Stat.ACC, Stat.EVA] as const) {
      expect(enemy.getStatStage(s), Stat[s]).toBe(want?.stats.includes(Stat[s] as never) ? want.stages : 0);
    }
  });
});
