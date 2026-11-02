/*
 * SPDX-FileCopyrightText: 2026 SG
 * SPDX-License-Identifier: AGPL-3.0-only
 */

// 블서로그 규칙: 파티 3명 · 클래식 50웨이브 · 1:1 싱글만 · 판 중 영입 없음 · 미스터리 인카운터 없음
import { BSEO } from "#app/bseorogue";
import { PLAYER_PARTY_MAX_SIZE } from "#app/constants";
import { getGameMode } from "#app/game-mode";
import { speciesDataRegistry } from "#app/global-species-data-registry";
import { bseoBossSpecies, bseoWildSpecies } from "#data/bseorogue/hooks";
import { bseoTypeMultiplier, Role } from "#data/bseorogue/roles";
import { BSEO_STARTER_IDS, BSEO_STARTERS, BSEO_WILD } from "#data/bseorogue/roster";
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

describe("블서로그 데이터 (임시 숫자)", () => {
  beforeAll(() => {
    new Phaser.Game({ type: Phaser.HEADLESS }); // 종 데이터 준비
  });

  it("시작 실험체는 블서로그 6명만", () => {
    expect([...speciesDataRegistry.getAllStarters()].sort()).toEqual([...BSEO_STARTER_IDS].sort());
  });

  it("ER 데이터: 실험체 이름 · 스킬 이름 · 스킨 · 스탯 환산", () => {
    const eleven = BSEO_STARTERS.find(c => c.erCode === 30)!;
    expect(eleven.name).toBe("일레븐");
    expect(eleven.skills.map(s => s.name)).toEqual(["방해하지마!", "자~ 집중!", "나 불렀어?", "다 덤벼보라구!"]);
    expect(eleven.skins[0]).toBe("일레븐");
    for (const c of [...BSEO_STARTERS, ...BSEO_WILD]) {
      expect(c.stats.every(v => v >= 20 && v <= 200)).toBe(true);
    }
    console.log(
      BSEO_STARTERS.map(c => `${c.name} ${c.stats.join("/")} 합 ${c.stats.reduce((a, b) => a + b, 0)}`).join("\n"),
    );
    console.log(
      BSEO_WILD.map(c => `${c.name} ${c.stats.join("/")} 합 ${c.stats.reduce((a, b) => a + b, 0)}`).join("\n"),
    );
  });

  it("야생은 블서로그 동물, 10웨이브마다 보스", () => {
    expect(bseoWildSpecies(1)?.speciesId).toBeGreaterThanOrEqual(1601);
    expect(bseoBossSpecies(10)?.speciesId).toBe(1701); // 알파
    expect(bseoBossSpecies(50)?.speciesId).toBe(1705); // 루미
    expect(bseoBossSpecies(15)).toBeNull();
  });

  it("역할군 상성: 암살자 → 평원딜 2배, 탱커 → 브루저 0.5배, 그 밖 1배", () => {
    expect(bseoTypeMultiplier(Role.ASSASSIN, Role.MARKSMAN)).toBe(2);
    expect(bseoTypeMultiplier(Role.TANK, Role.BRUISER)).toBe(0.5);
    expect(bseoTypeMultiplier(Role.SUPPORT, Role.TANK)).toBe(1);
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
    game.override.enemySpecies(SpeciesId.BSEO_CHICKEN);
    await game.classicMode.startBattle(SpeciesId.BSEO_ELEVEN);
    expect(game.scene.currentBattle.double).toBe(false);
    expect(game.scene.getEnemyField().length).toBe(1);
  });
});
