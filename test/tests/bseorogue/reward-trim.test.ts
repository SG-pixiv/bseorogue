/*
 * SPDX-FileCopyrightText: 2026 SG
 * SPDX-License-Identifier: AGPL-3.0-only
 */

// 아이템 줄이기: SG 시트에서 '뺌' 인 아이템은 보상 · 상점 · 적이 지닌 물건에 안 나와요
import { bseoRewardKeep, bseoRewardOff } from "#data/bseorogue/reward-filter";
import { BSEO_REWARD_OFF } from "#data/bseorogue/reward-trim";
import { modifierTypes } from "#data/data-lists";
import { BerryType } from "#enums/berry-type";
import { MoveId } from "#enums/move-id";
import { PokemonType } from "#enums/pokemon-type";
import { SpeciesId } from "#enums/species-id";
import { modifierPool, trainerModifierPool, wildModifierPool } from "#modifiers/modifier-pools";
import {
  type AttackTypeBoosterModifierType,
  getPlayerShopModifierTypeOptionsForWave,
  type ModifierTypeGenerator,
} from "#modifiers/modifier-type";
import { GameManager } from "#test/framework/game-manager";
import Phaser from "phaser";
import { afterEach, beforeAll, beforeEach, describe, expect, it } from "vitest";

/** 테스트 동안만 '뺌' 목록에 더하기 */
const OFF = BSEO_REWARD_OFF as Set<string>;

describe("블서로그 아이템 줄이기", () => {
  let phaserGame: Phaser.Game;
  let game: GameManager;
  const added: string[] = [];

  function cut(...keys: string[]): void {
    for (const k of keys) {
      if (!OFF.has(k)) {
        OFF.add(k);
        added.push(k);
      }
    }
  }

  beforeAll(() => {
    phaserGame = new Phaser.Game({ type: Phaser.HEADLESS });
  });

  beforeEach(() => {
    game = new GameManager(phaserGame);
    game.override.enemyMoveset(MoveId.SPLASH).enemySpecies(SpeciesId.BSEO_CHICKEN).startingWave(3);
  });

  afterEach(() => {
    for (const k of added.splice(0)) {
      OFF.delete(k);
    }
  });

  it("SG가 뺀 것(진화의휘석 · 구슬 · 신비한바위 · 대파 · 볼 등급)은 보상 풀에 없어요", () => {
    const ids = (pool: typeof modifierPool) =>
      Object.values(pool)
        .flat()
        .map(w => w.modifierType.id);
    for (const id of ["EVIOLITE", "TOXIC_ORB", "FLAME_ORB", "MYSTICAL_ROCK", "LEEK", "GREAT_BALL", "MASTER_BALL"]) {
      expect(bseoRewardOff(id), id).toBe(true);
      expect(ids(modifierPool), id).not.toContain(id);
    }
    for (const pool of [modifierPool, wildModifierPool, trainerModifierPool]) {
      for (const id of ids(pool)) {
        expect(bseoRewardOff(id), id).toBe(false);
      }
    }
    // 남기기로 한 것은 그대로
    for (const id of ["POTION", "LEFTOVERS", "BASE_STAT_BOOSTER", "VOUCHER", "MAP", "BERRY"]) {
      expect(ids(modifierPool), id).toContain(id);
    }
  });

  it("전부 뺀 종류: 내 보상은 빈 목록, 적이 지닐 물건은 원래 목록", () => {
    cut("X:A", "X:B");
    const player = [{ isPlayer: () => true }];
    const enemy = [{ isPlayer: () => false }];
    expect(bseoRewardKeep("X", ["A", "B"], v => v, player)).toEqual([]);
    expect(bseoRewardKeep("X", ["A", "B"], v => v, enemy)).toEqual(["A", "B"]);
    expect(bseoRewardKeep("X", ["A", "B", "C"], v => v, enemy)).toEqual(["C"]);
  });

  it("전투에서: 뺀 음식 · 강화 모듈 · 상점 물건이 안 나와요", async () => {
    await game.classicMode.startBattle(SpeciesId.BSEO_ELEVEN);
    const party = game.scene.getPlayerParty();

    cut("BERRY:LIECHI", "BERRY:GANLON", "BERRY:PETAYA", "BERRY:APICOT", "BERRY:SALAC", "BERRY:LANSAT");
    const berries = modifierTypes.BERRY() as ModifierTypeGenerator;
    for (let i = 0; i < 200; i++) {
      const b = berries.generateType(party) as unknown as { berryType: BerryType };
      expect(bseoRewardOff("BERRY", BerryType[b.berryType]), BerryType[b.berryType]).toBe(false);
    }

    // 야생 · 보스 강화 모듈은 내 보상에 안 나와요 (역할군 것만)
    const boosters = modifierTypes.ATTACK_TYPE_BOOSTER() as ModifierTypeGenerator;
    for (let i = 0; i < 50; i++) {
      const t = boosters.generateType(party) as AttackTypeBoosterModifierType | null;
      if (t) {
        expect([PokemonType.NORMAL, PokemonType.BUG]).not.toContain(t.moveType);
      }
    }

    const shop = (wave: number) => getPlayerShopModifierTypeOptionsForWave(wave, 100).map(o => o.type.id);
    // 50웨이브 판에서 상점에 나오는 것은 두 묶음뿐 (고기 · 물 · 가젯 에너지 팩 / 눈물젖은 빵 · 구급상자)
    expect(shop(45)).toEqual(["POTION", "ETHER", "REVIVE", "SUPER_POTION", "FULL_HEAL"]);
    cut("SUPER_POTION", "REVIVE");
    expect(shop(45)).toEqual(["POTION", "ETHER", "FULL_HEAL"]);
  });
});
