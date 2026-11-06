/*
 * SPDX-FileCopyrightText: 2026 SG
 * SPDX-License-Identifier: AGPL-3.0-only
 */

// 블서로그 마우스 조작: 화면마다 누르는 칸이 있고, 누르면 키보드로 고른 것과 같은 일이 일어나요
import { BattlerIndex } from "#enums/battler-index";
import { MoveId } from "#enums/move-id";
import { SpeciesId } from "#enums/species-id";
import { UiMode } from "#enums/ui-mode";
import { GameManager } from "#test/framework/game-manager";
import { mouseController } from "#ui/mouse-controller";
import { mouseTargetsFor } from "#ui/mouse-screens";
import { type MouseTarget, shownChildrenRect } from "#ui/mouse-targets";
import Phaser from "phaser";
import { beforeAll, beforeEach, describe, expect, it, vi } from "vitest";

describe("블서로그 마우스 조작", () => {
  let phaserGame: Phaser.Game;
  let game: GameManager;

  const targets = (): MouseTarget[] => mouseTargetsFor(game.scene.ui.mode, game.scene.ui.getHandler()) ?? [];
  const labels = () => targets().map(t => t.label);
  const click = (label: string) => {
    const t = targets().find(t => t.label === label);
    expect(t, `${label} 칸이 있어야 해요 (${labels().join(", ")})`).toBeDefined();
    t?.hover?.();
    t?.click();
  };
  const waitMode = (mode: UiMode) => vi.waitFor(() => expect(game.scene.ui.mode).toBe(mode));
  /** 오른쪽 클릭 (가짜 마우스) */
  const rightClick = () =>
    (mouseController as unknown as { onDown: (p: unknown, over: unknown[]) => void }).onDown(
      { x: 0, y: 0, wasTouch: false, rightButtonDown: () => true, middleButtonDown: () => false },
      [],
    );

  beforeAll(() => {
    phaserGame = new Phaser.Game({ type: Phaser.HEADLESS });
  });

  beforeEach(() => {
    game = new GameManager(phaserGame);
    game.override
      .moveset([MoveId.HAMMER_ARM, MoveId.SPLASH])
      .enemySpecies(SpeciesId.BSEO_CHICKEN)
      .enemyMoveset(MoveId.SPLASH)
      .startingWave(2)
      .startingLevel(30)
      .enemyLevel(2);
  });

  it("전투 명령 → 스킬 → 결정을 클릭으로", async () => {
    await game.classicMode.startBattle(SpeciesId.BSEO_ELEVEN);
    expect(game.scene.ui.mode).toBe(UiMode.COMMAND);
    expect(labels()).toEqual(["command:0", "command:1", "command:2", "command:3"]);

    click("command:0");
    await waitMode(UiMode.FIGHT);
    expect(labels()).toContain("move:1");

    // 오른쪽 클릭 = 뒤로
    rightClick();
    await waitMode(UiMode.COMMAND);

    click("command:0");
    await waitMode(UiMode.FIGHT);
    click("move:0");
    await game.setTurnOrder([BattlerIndex.PLAYER, BattlerIndex.ENEMY]);
    await game.move.forceHit();
    await game.phaseInterceptor.to("TurnEndPhase");
    expect(game.scene.currentBattle.enemyParty[0].isFainted()).toBe(true);
  });

  it("실험체 화면: 칸을 누르면 고르기 창이 뜨고, 오른쪽 클릭으로 닫혀요", async () => {
    await game.classicMode.startBattle(SpeciesId.BSEO_ELEVEN, SpeciesId.BSEO_YUKI);
    click("command:2");
    await waitMode(UiMode.PARTY);
    expect(labels()).toEqual(expect.arrayContaining(["party:0", "party:1", "party-cancel"]));

    click("party:1");
    const options = labels().filter(l => l.startsWith("party-option:"));
    expect(options.length).toBeGreaterThan(1);

    rightClick();
    expect(labels()).toContain("party:1");
    click("party-cancel");
    await waitMode(UiMode.COMMAND);
  });

  it("고르기 목록(예/아니요 등)의 줄마다 칸이 있어요", async () => {
    await game.classicMode.startBattle(SpeciesId.BSEO_ELEVEN);
    let picked = -1;
    await game.scene.ui.setOverlayMode(UiMode.OPTION_SELECT, {
      options: [
        { label: "하나", handler: () => ((picked = 0), true) },
        { label: "둘", handler: () => ((picked = 1), true) },
        { label: "셋", handler: () => ((picked = 2), true) },
      ],
    });
    await waitMode(UiMode.OPTION_SELECT);
    expect(labels()).toEqual(["option:0", "option:1", "option:2"]);
    click("option:1");
    expect(picked).toBe(1);
  });

  it("보상 고르기: 보상 칸을 누르면 가져가요", async () => {
    await game.classicMode.startBattle(SpeciesId.BSEO_ELEVEN);
    click("command:0");
    await waitMode(UiMode.FIGHT);
    click("move:0");
    await game.setTurnOrder([BattlerIndex.PLAYER, BattlerIndex.ENEMY]);
    await game.move.forceHit();

    await game.phaseInterceptor.to("SelectModifierPhase");

    let rewardLabels: string[] = [];
    await new Promise<void>(resolve => {
      game.onNextPrompt("SelectModifierPhase", UiMode.MODIFIER_SELECT, async () => {
        await vi.waitFor(() => expect(labels()).toContain("reward:0"));
        rewardLabels = labels();
        click("check-team");
        resolve();
      });
    });
    expect(rewardLabels).toEqual(expect.arrayContaining(["reward:0", "reroll", "check-team"]));
    // 팀 확인 버튼 → 실험체 화면
    await waitMode(UiMode.PARTY);
  });
});

describe("블서로그 마우스 칸 계산", () => {
  it("숨은 자식은 빼고 보이는 자식만 감싸요 (보상 칸이 숨은 몬스터볼까지 커지지 않게)", () => {
    const container = { visible: true, alpha: 1, parentContainer: null, displayList: {}, list: [] as unknown[] };
    const child = (x: number, y: number, w: number, h: number, visible = true) => ({
      visible,
      alpha: 1,
      parentContainer: container,
      getBounds: () => new Phaser.Geom.Rectangle(x, y, w, h),
    });
    container.list = [child(0, 0, 10, 10), child(0, -500, 10, 10, false), child(0, 20, 10, 5)];
    const r = shownChildrenRect(container as unknown as Phaser.GameObjects.Container, 1)();
    expect(r && [r.x, r.y, r.width, r.height]).toEqual([-6, -6, 22, 37]);

    container.visible = false;
    expect(shownChildrenRect(container as unknown as Phaser.GameObjects.Container)()).toBeNull();
  });
});
