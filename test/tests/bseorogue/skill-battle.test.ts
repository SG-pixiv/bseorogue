/*
 * SPDX-FileCopyrightText: 2026 SG
 * SPDX-License-Identifier: AGPL-3.0-only
 */

// 실험체 91명 모두 전투에서 써 보기 (11-17 검수)
// - 스킬: Q · W · E · R 을 한 번씩 써도 에러 없이 턴이 끝나요 (패시브는 잠시 끄고)
// - 패시브: 진짜 패시브를 켠 채 야생동물(특성 없음) · 실험체를 만나 스킬을 한 번 써요 (트레이스처럼 등장할 때 켜지는 것 확인)
import { bseoSpeciesId } from "#data/bseorogue/roster";
import { SHEET_SKILLS } from "#data/bseorogue/sheet-data";
import { SKILL_MOVES } from "#data/bseorogue/skill-moves";
import { AbilityId } from "#enums/ability-id";
import { BattlerIndex } from "#enums/battler-index";
import { MoveId } from "#enums/move-id";
import { SpeciesId } from "#enums/species-id";
import { GameManager } from "#test/framework/game-manager";
import Phaser from "phaser";
import { beforeAll, beforeEach, describe, expect, it } from "vitest";

const CODES = Object.keys(SKILL_MOVES).map(Number);

describe("블서로그 실험체 전투 전부 써 보기", () => {
  let phaserGame: Phaser.Game;
  let game: GameManager;

  beforeAll(() => {
    phaserGame = new Phaser.Game({ type: Phaser.HEADLESS });
  });

  beforeEach(() => {
    game = new GameManager(phaserGame);
    // 상대는 쓰러지지 않게 높은 레벨, 아무것도 안 해요
    game.override.enemyMoveset(MoveId.SPLASH).enemyLevel(100).startingWave(3).startingLevel(20);
  });

  it.each(CODES)("스킬 Q · W · E · R: ER %i 번", async code => {
    const moves = SKILL_MOVES[code];
    const sheet = SHEET_SKILLS[code];
    // 니아(무아지경: 처음 고른 스킬만) 같은 패시브가 막지 않게 패시브는 끄고 봐요
    game.override
      .moveset([...moves])
      .ability(AbilityId.BALL_FETCH)
      .enemySpecies(SpeciesId.BSEO_CHICKEN);
    // '다음 턴 쉼' 스킬은 마지막에 (쉬는 턴에는 고를 수 없어요)
    const order = [0, 1, 2, 3].sort((a, b) => Number(!!sheet[a].fx.recharge) - Number(!!sheet[b].fx.recharge));
    await game.classicMode.startBattle(bseoSpeciesId(code));
    const me = game.field.getPlayerPokemon();
    for (const [n, i] of order.entries()) {
      game.move.select(moves[i]);
      await game.setTurnOrder([BattlerIndex.PLAYER, BattlerIndex.ENEMY]);
      await game.toEndOfTurn();
      expect(me.getLastXMoves(1)[0]?.move, `${"QWER"[i]} ${sheet[i].effect} (${MoveId[moves[i]]})`).toBe(moves[i]);
      if (n < 3) {
        await game.toNextTurn();
      }
    }
    expect(me.isFainted()).toBe(false);
    expect(game.field.getEnemyPokemon().isOnField()).toBe(true);
  });

  // 상대: 야생동물(특성 없음) · 실험체(일레븐, 일레븐 차례면 재키)
  const PAIRS = CODES.flatMap(code => [
    [code, "야생동물", SpeciesId.BSEO_CHICKEN],
    [code, "실험체", bseoSpeciesId(code === 30 ? 1 : 30)],
  ]) as [number, string, SpeciesId][];

  it.each(PAIRS)("패시브: ER %i 번 · %s 상대", async (code, _, enemy) => {
    const q = SKILL_MOVES[code][0];
    game.override.moveset([q]).enemySpecies(enemy);
    await game.classicMode.startBattle(bseoSpeciesId(code));
    const me = game.field.getPlayerPokemon();
    game.move.select(q);
    await game.setTurnOrder([BattlerIndex.PLAYER, BattlerIndex.ENEMY]);
    await game.toEndOfTurn();
    expect(me.getLastXMoves(1)[0]?.move).toBe(q);
  });
});
