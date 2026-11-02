/*
 * SPDX-FileCopyrightText: 2026 SG
 * SPDX-License-Identifier: AGPL-3.0-only
 */

// 블서로그 규칙: 파티 3명 · 클래식 50웨이브 · 1:1 싱글만 · 판 중 영입 없음 · 미스터리 인카운터 없음
import { BSEO } from "#app/bseorogue";
import { PLAYER_PARTY_MAX_SIZE } from "#app/constants";
import { getGameMode } from "#app/game-mode";
import { GameModes } from "#enums/game-modes";
import { MoveId } from "#enums/move-id";
import { SpeciesId } from "#enums/species-id";
import { GameManager } from "#test/framework/game-manager";
import Phaser from "phaser";
import { beforeAll, beforeEach, describe, expect, it } from "vitest";

describe("블서로그 규칙", () => {
  it("파티는 최대 3명", () => {
    expect(BSEO.partyMax).toBe(3);
    expect(PLAYER_PARTY_MAX_SIZE).toBe(3);
  });

  it("클래식은 50웨이브가 마지막 (10웨이브마다 보스)", () => {
    const classic = getGameMode(GameModes.CLASSIC);
    expect(classic.isWaveFinal(50)).toBe(true);
    expect(classic.isWaveFinal(200)).toBe(false);
    expect(classic.isBattleClassicFinalBoss(50)).toBe(true);
    for (const wave of [10, 20, 30, 40, 50]) {
      expect(classic.isBoss(wave)).toBe(true);
    }
  });

  it("판 중 영입 · 미스터리 인카운터는 꺼져 있어요", () => {
    expect(BSEO.allowCatch).toBe(false);
    expect(BSEO.mysteryEncounters).toBe(false);
    expect(BSEO.singleBattlesOnly).toBe(true);
  });
});

describe("블서로그 규칙 - 전투", () => {
  let phaserGame: Phaser.Game;
  let game: GameManager;

  beforeAll(() => {
    phaserGame = new Phaser.Game({ type: Phaser.HEADLESS });
  });

  beforeEach(() => {
    game = new GameManager(phaserGame);
    game.override.startingWave(5).enemyMoveset(MoveId.SPLASH).moveset([MoveId.TACKLE]);
  });

  it("야생 전투는 늘 1:1 이에요", async () => {
    game.override.enemySpecies(SpeciesId.RATTATA);
    await game.classicMode.startBattle(SpeciesId.BULBASAUR);
    expect(game.scene.currentBattle.double).toBe(false);
    expect(game.scene.getEnemyField().length).toBe(1);
  });
});
