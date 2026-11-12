/*
 * SPDX-FileCopyrightText: 2026 SG
 * SPDX-License-Identifier: AGPL-3.0-only
 */

// 판 중 영입: 볼 한 종류 · 실패가 쌓이면 확정 · 실험체만 · 잡으면 해금
import { BSEO } from "#app/bseorogue";
import { defaultStarterSpecies } from "#app/constants";
import { bseoCanCatchSpecies, bseoNextThrowGuaranteed, bseoThrowsUntilGuaranteed } from "#data/bseorogue/catch";
import { bseoSpeciesId } from "#data/bseorogue/roster";
import { Button } from "#enums/buttons";
import { Command } from "#enums/command";
import { MoveId } from "#enums/move-id";
import { PokeballType } from "#enums/pokeball";
import { SpeciesId } from "#enums/species-id";
import { UiMode } from "#enums/ui-mode";
import type { CommandPhase } from "#phases/command-phase";
import { GameManager } from "#test/framework/game-manager";
import type { CommandUiHandler } from "#ui/command-ui-handler";
import Phaser from "phaser";
import { beforeAll, beforeEach, describe, expect, it, vi } from "vitest";

describe("블서로그 판 중 영입", () => {
  let phaserGame: Phaser.Game;
  let game: GameManager;

  beforeAll(() => {
    phaserGame = new Phaser.Game({ type: Phaser.HEADLESS });
  });

  beforeEach(() => {
    game = new GameManager(phaserGame);
    game.override.enemyMoveset(MoveId.SPLASH).startingWave(3).startingLevel(50).enemyLevel(5);
  });

  /**
   * '영입' 을 눌러 바로 던지기. 테스트 틀의 `game.doThrowPokeball` 은 볼 고르는 창을 기다리는데,
   * 블서로그에는 그 창이 없어서 다음 입력이 막혀요 → 여기서는 명령 화면에서 바로 눌러요.
   */
  function throwBall(): void {
    game.onNextPrompt("CommandPhase", UiMode.COMMAND, () => {
      const handler = game.scene.ui.getHandler() as CommandUiHandler;
      handler.setCursor(Command.BALL);
      handler.processInput(Button.ACTION);
    });
  }

  it("처음부터 열린 실험체는 시작 6명뿐 (나머지는 잡거나 뽑아야 열림)", () => {
    expect([...defaultStarterSpecies].sort()).toEqual(BSEO.startUnlocked.map(c => bseoSpeciesId(c)).sort());
    expect(defaultStarterSpecies).toContain(SpeciesId.BSEO_ELEVEN);
    expect(defaultStarterSpecies).not.toContain(SpeciesId.BSEO_JACKIE);
  });

  it("실험체만 영입할 수 있어요 (야생동물 · 보스는 안 됨)", () => {
    expect(bseoCanCatchSpecies(SpeciesId.BSEO_JACKIE)).toBe(true);
    expect(bseoCanCatchSpecies(SpeciesId.BSEO_CHICKEN)).toBe(false);
    expect(bseoCanCatchSpecies(SpeciesId.BSEO_ALPHA)).toBe(false);
  });

  it("전투에서: 야생동물에게는 볼을 못 던져요", async () => {
    game.override.enemySpecies(SpeciesId.BSEO_CHICKEN);
    await game.classicMode.startBattle(SpeciesId.BSEO_ELEVEN);
    const balls = game.scene.pokeballCounts[PokeballType.POKEBALL];
    const phase = game.scene.phaseManager.getCurrentPhase() as CommandPhase;
    expect(phase.handleCommand(Command.BALL, PokeballType.POKEBALL)).toBe(false);
    expect(game.scene.pokeballCounts[PokeballType.POKEBALL]).toBe(balls);
  });

  it("전투에서: 두 번 실패하면 세 번째 볼은 반드시 잡히고, 잡은 실험체는 시작 실험체로 열려요", async () => {
    game.override.enemySpecies(SpeciesId.BSEO_JACKIE);
    await game.classicMode.startBattle(SpeciesId.BSEO_ELEVEN);
    const enemy = game.field.getEnemyPokemon();
    // 절대 안 잡히는 상대로 만들어요 (확정만 통하게)
    vi.spyOn(enemy.species, "catchRate", "get").mockReturnValue(0);
    const dex = game.scene.gameData.dexData[SpeciesId.BSEO_JACKIE];
    dex.caughtAttr = 0n;
    const balls = game.scene.pokeballCounts[PokeballType.POKEBALL];
    expect(game.scene.bseoCatchFails).toBe(0);
    expect(bseoThrowsUntilGuaranteed()).toBe(BSEO.catchGuaranteedThrow);
    // 테스트 틀의 가짜 트윈은 흔들림 검사(onRepeat)를 건너뛰고 바로 '잡힘' 으로 가요 → 검사를 실제처럼 돌려요
    vi.spyOn(game.scene.tweens, "addCounter").mockImplementation(((data: {
      repeat?: number;
      onRepeat?: () => void;
      onComplete?: () => void;
    }) => {
      let stopped = false;
      queueMicrotask(() => {
        for (let i = 0; i < (data.repeat ?? 0) && !stopped; i++) {
          data.onRepeat?.();
        }
        if (!stopped) {
          data.onComplete?.();
        }
      });
      return { stop: () => (stopped = true) };
    }) as never);

    for (let fails = 1; fails < BSEO.catchGuaranteedThrow; fails++) {
      throwBall();
      await game.toNextTurn();
      expect(game.scene.bseoCatchFails).toBe(fails);
      expect(game.scene.getPlayerParty().length).toBe(1);
    }
    expect(bseoNextThrowGuaranteed()).toBe(true);

    throwBall();
    await game.toEndOfTurn();
    expect(game.scene.bseoCatchFails).toBe(0);
    expect(game.scene.getPlayerParty().map(p => p.species.speciesId)).toEqual([
      SpeciesId.BSEO_ELEVEN,
      SpeciesId.BSEO_JACKIE,
    ]);
    expect(game.scene.pokeballCounts[PokeballType.POKEBALL]).toBe(balls - BSEO.catchGuaranteedThrow);
    expect(dex.caughtAttr).not.toBe(0n);
  });
});
