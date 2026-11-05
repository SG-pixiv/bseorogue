/*
 * SPDX-FileCopyrightText: 2026 SG
 * SPDX-License-Identifier: AGPL-3.0-only
 */

// 블서로그 한 판 흐름: 스킨 진화 · 최종 보스 승리 · 전멸 패배
import { LEADERS } from "#data/bseorogue/leaders";
import { BSEO_STARTER_IDS, bseoCharacter, erCodeOfSpecies } from "#data/bseorogue/roster";
import { Egg } from "#data/egg";
import { BattleType } from "#enums/battle-type";
import { BattlerIndex } from "#enums/battler-index";
import { EggSourceType } from "#enums/egg-source-types";
import { EggTier } from "#enums/egg-type";
import { MoveId } from "#enums/move-id";
import { SpeciesId } from "#enums/species-id";
import { TrainerType } from "#enums/trainer-type";
import { GameOverPhase } from "#phases/game-over-phase";
import { GameManager } from "#test/framework/game-manager";
import Phaser from "phaser";
import { beforeAll, beforeEach, describe, expect, it } from "vitest";

describe("블서로그 한 판 흐름", () => {
  let phaserGame: Phaser.Game;
  let game: GameManager;

  beforeAll(() => {
    phaserGame = new Phaser.Game({ type: Phaser.HEADLESS });
  });

  beforeEach(() => {
    game = new GameManager(phaserGame);
    game.override.enemyMoveset(MoveId.SPLASH);
  });

  it("레벨 12가 되면 스킨 진화 1로 진화해요", async () => {
    game.override
      .moveset([MoveId.HAMMER_ARM])
      .enemySpecies(SpeciesId.BSEO_CHICKEN)
      .startingWave(15) // 11~20웨이브는 레벨 상한 16
      .startingLevel(11)
      .enemyLevel(40);
    await game.classicMode.startBattle(SpeciesId.BSEO_ELEVEN);

    const eleven = game.field.getPlayerPokemon();
    game.field.getEnemyPokemon().hp = 1;
    game.move.select(MoveId.HAMMER_ARM);
    await game.setTurnOrder([BattlerIndex.PLAYER, BattlerIndex.ENEMY]);
    await game.move.forceHit();
    await game.phaseInterceptor.to("EndEvolutionPhase");

    expect(eleven.level).toBeGreaterThanOrEqual(12);
    expect(eleven.species.speciesId).toBe(SpeciesId.BSEO_ELEVEN_S1);
    expect(eleven.getMoveset().map(m => m.moveId)).toContain(MoveId.HAMMER_ARM);
  });

  it("5웨이브는 KEL 팀 전투 (실험체 3명)", async () => {
    game.override.moveset([MoveId.HAMMER_ARM]).startingWave(5);
    await game.classicMode.startBattle(SpeciesId.BSEO_ELEVEN);

    const battle = game.scene.currentBattle;
    expect(battle.battleType).toBe(BattleType.TRAINER);
    expect(battle.trainer?.config.trainerType).toBe(TrainerType.BSEO_KEL);
    expect(battle.trainer?.getName().length).toBeGreaterThan(0);
    const party = game.scene.getEnemyParty();
    expect(party.length).toBe(3);
    for (const p of party) {
      expect(erCodeOfSpecies(p.species.speciesId)).not.toBeNull();
    }
    expect(new Set(party.map(p => p.species.getRootSpeciesId())).size).toBe(3);
    expect(game.scene.currentBattle.double).toBe(false);
  });

  it("8웨이브는 역할군 관장 (같은 역할군 2명, 마지막이 관장 본인)", async () => {
    game.override.moveset([MoveId.HAMMER_ARM]).startingWave(8);
    await game.classicMode.startBattle(SpeciesId.BSEO_ELEVEN);

    const trainer = game.scene.currentBattle.trainer;
    expect(trainer?.config.trainerType).toBe(TrainerType.BSEO_LEADER);
    const leader = LEADERS.find(l => trainer?.getName().endsWith(bseoCharacter(l.erCode)?.name ?? "?"));
    expect(leader).toBeDefined();
    const party = game.scene.getEnemyParty();
    expect(party.length).toBe(2);
    expect(erCodeOfSpecies(party[1].species.speciesId)).toBe(leader?.erCode);
    expect(new Set(party.map(p => p.species.type1)).size).toBe(1);
  });

  it("50웨이브 루미를 이기면 클래식 클리어", async () => {
    game.override.moveset([MoveId.HAMMER_ARM]).startingWave(50).startingLevel(60);
    await game.classicMode.startBattle(SpeciesId.BSEO_ELEVEN);

    const lumi = game.field.getEnemyPokemon();
    expect(lumi.species.speciesId).toBe(SpeciesId.BSEO_LUMI);
    expect(lumi.isBoss()).toBe(true);

    lumi.hp = 1;
    lumi.bossSegmentIndex = 0;
    game.move.select(MoveId.HAMMER_ARM);
    await game.setTurnOrder([BattlerIndex.PLAYER, BattlerIndex.ENEMY]);
    await game.move.forceHit();
    await game.phaseInterceptor.to("GameOverPhase", false);
    const phase = game.scene.phaseManager.getCurrentPhase() as GameOverPhase;
    expect(phase).toBeInstanceOf(GameOverPhase);
    expect((phase as unknown as { isVictory: boolean }).isVictory).toBe(true);
  });

  it("1웨이브부터 50웨이브까지 끝까지 (동물 · KEL 팀 · 보스 · 지역 이동 · 최종 보스)", async () => {
    game.override.moveset([MoveId.BODY_SLAM]).startingWave(1).startingLevel(100);
    await game.classicMode.startBattle(SpeciesId.BSEO_ELEVEN);

    const seen = { kel: 0, leader: 0, boss: 0, character: 0, animal: 0, biomes: new Set<number>() };
    let lastWave = 0;
    for (let turn = 0; turn < 400; turn++) {
      const battle = game.scene.currentBattle;
      const wave = battle.waveIndex;
      // 검사에서는 PP가 떨어지지 않게 (한 기술만 계속 쓰니까)
      for (const m of game.field.getPlayerPokemon().getMoveset()) {
        m.ppUsed = 0;
      }
      if (wave !== lastWave) {
        lastWave = wave;
        seen.biomes.add(game.scene.arena.biomeId);
        const enemy = game.field.getEnemyPokemon();
        if (battle.battleType === BattleType.TRAINER) {
          const type = battle.trainer?.config.trainerType;
          if (type === TrainerType.BSEO_LEADER) {
            seen.leader++;
            expect(battle.trainer?.getName()).toContain("관장");
            // 관장 팀은 같은 역할군
            expect(new Set(game.scene.getEnemyParty().map(p => p.species.type1)).size).toBe(1);
          } else {
            expect(type).toBe(TrainerType.BSEO_KEL);
            expect(game.scene.getEnemyParty().length).toBe(3);
            seen.kel++;
          }
        } else if (enemy.isBoss()) {
          seen.boss++;
        } else if (erCodeOfSpecies(enemy.species.speciesId) == null) {
          seen.animal++;
        } else {
          seen.character++;
        }
        expect(battle.double).toBe(false);
      }
      if (wave === 50) {
        const lumi = game.field.getEnemyPokemon();
        expect(lumi.species.speciesId).toBe(SpeciesId.BSEO_LUMI);
        lumi.hp = 1;
        lumi.bossSegmentIndex = 0;
        game.move.select(MoveId.BODY_SLAM);
        await game.phaseInterceptor.to("GameOverPhase", false);
        break;
      }
      game.move.select(MoveId.BODY_SLAM);
      await game.toNextWave();
    }
    expect(game.scene.phaseManager.getCurrentPhase()).toBeInstanceOf(GameOverPhase);
    expect(seen.kel).toBe(5);
    expect(seen.leader).toBe(5);
    expect(seen.boss).toBe(5);
    // 일반 웨이브는 실험체가 대부분
    expect(seen.character).toBeGreaterThan(seen.animal * 2);
    process.stdout.write(
      `한 판: 실험체 ${seen.character} · 동물 ${seen.animal} · KEL ${seen.kel} · 관장 ${seen.leader} · 보스 ${seen.boss} · 지역 ${seen.biomes.size}\n`,
    );
    expect(seen.biomes.size).toBeGreaterThan(1);
  }, 240_000);

  it("보급 상자(알)에서는 블서로그 시작 실험체만 나와요", async () => {
    await game.classicMode.startBattle(SpeciesId.BSEO_ELEVEN);
    const starters = new Set<number>(BSEO_STARTER_IDS);
    for (const tier of [EggTier.COMMON, EggTier.RARE, EggTier.EPIC, EggTier.LEGENDARY]) {
      for (const sourceType of [EggSourceType.GACHA_MOVE, EggSourceType.GACHA_SHINY, EggSourceType.GACHA_LEGENDARY]) {
        for (let i = 0; i < 10; i++) {
          const egg = new Egg({ scene: game.scene, tier, sourceType });
          expect(starters.has(egg.species), `${tier} ${sourceType} → ${egg.species}`).toBe(true);
        }
      }
    }
  });

  it("전멸하면 게임 오버", async () => {
    game.override
      .moveset([MoveId.SPLASH])
      .enemySpecies(SpeciesId.BSEO_BEAR)
      .enemyMoveset(MoveId.SUPERPOWER)
      .startingWave(31)
      .startingLevel(5)
      .enemyLevel(40);
    await game.classicMode.startBattle(SpeciesId.BSEO_ELEVEN);

    game.field.getPlayerPokemon().hp = 1;
    game.move.select(MoveId.SPLASH);
    await game.phaseInterceptor.to("GameOverPhase", false);
    const phase = game.scene.phaseManager.getCurrentPhase() as GameOverPhase;
    expect(phase).toBeInstanceOf(GameOverPhase);
    expect((phase as unknown as { isVictory: boolean }).isVictory).toBe(false);
  });
});
