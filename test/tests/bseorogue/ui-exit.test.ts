/*
 * SPDX-FileCopyrightText: 2026 SG
 * SPDX-License-Identifier: AGPL-3.0-only
 */

// 화면마다 나가는 길: 뒤로(키보드 B · Esc = 오른쪽 클릭 = 터치 B)를 누르면 들어온 화면으로 돌아가요 (11-18 검수)
import { Button } from "#enums/buttons";
import { MoveId } from "#enums/move-id";
import { SpeciesId } from "#enums/species-id";
import { UiMode } from "#enums/ui-mode";
import { GameManager } from "#test/framework/game-manager";
import { mouseController } from "#ui/mouse-controller";
import { mouseTargetsFor } from "#ui/mouse-screens";
import type { MouseTarget } from "#ui/mouse-targets";
import { PartyOption, type PartyUiHandler } from "#ui/party-ui-handler";
import Phaser from "phaser";
import { beforeAll, beforeEach, describe, expect, it, vi } from "vitest";

describe("블서로그 화면 나가는 길", () => {
  let phaserGame: Phaser.Game;
  let game: GameManager;

  const targets = (): MouseTarget[] => mouseTargetsFor(game.scene.ui.mode, game.scene.ui.getHandler()) ?? [];
  const labels = () => targets().map(t => t.label);
  const click = (label: string) => {
    const t = targets().find(x => x.label === label);
    expect(t, `${label} 칸이 있어야 해요 (${labels().join(", ")})`).toBeDefined();
    t?.hover?.();
    t?.click();
  };
  const mode = () => UiMode[game.scene.ui.mode];
  const waitMode = (m: UiMode, step = "") => vi.waitFor(() => expect(mode(), step).toBe(UiMode[m]), { timeout: 3000 });
  /** 뒤로 (키보드 B · Esc, 오른쪽 클릭, 터치 B 가 다 이거예요) */
  const back = () => game.scene.ui.processInput(Button.CANCEL);
  /** 화면 구석 "뒤로" 버튼이 이 화면에 있어야 해요 (마우스 · 터치용) */
  const hasBackButton = () => expect(mouseController.backSpot(), `${mode()} 뒤로 버튼`).not.toBeNull();
  const tick = () => new Promise(r => setTimeout(r, 50));

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

  it("전투: 스킬 고르기 · 영입 · 실험체 화면 · 고르기 창에서 뒤로", async () => {
    await game.classicMode.startBattle(SpeciesId.BSEO_ELEVEN, SpeciesId.BSEO_YUKI);

    expect(mouseController.backSpot(), "전투 명령 화면엔 뒤로 버튼 없음").toBeNull();
    click("command:0");
    await waitMode(UiMode.FIGHT);
    hasBackButton();
    back();
    await waitMode(UiMode.COMMAND);

    click("command:1");
    await tick();
    if (game.scene.ui.mode !== UiMode.COMMAND) {
      back();
      await waitMode(UiMode.COMMAND);
    }

    click("command:2");
    await waitMode(UiMode.PARTY);
    click("party:1");
    expect(labels().some(l => l.startsWith("party-option:"))).toBe(true);
    back(); // 고르기 창 닫기
    expect(labels().some(l => l.startsWith("party-option:"))).toBe(false);
    back(); // 실험체 화면 닫기
    await waitMode(UiMode.COMMAND);
  });

  it("실험체 정보(능력 · 스킬 보기 · 스킬 고르기)와 실험체도감에서 뒤로", async () => {
    await game.classicMode.startBattle(SpeciesId.BSEO_ELEVEN, SpeciesId.BSEO_YUKI);
    click("command:2");
    await waitMode(UiMode.PARTY);
    const party = game.scene.ui.getHandler<PartyUiHandler>();
    const pick = (opt: PartyOption) => {
      click("party:0");
      const i = (party as unknown as { options: number[] }).options.indexOf(opt);
      expect(i, `party option ${opt}`).toBeGreaterThanOrEqual(0);
      click(`party-option:${i}`);
    };

    pick(PartyOption.SUMMARY);
    await waitMode(UiMode.SUMMARY, "정보 열기");
    hasBackButton();
    back();
    await waitMode(UiMode.PARTY, "정보에서 바로 뒤로");

    // 스킬 쪽 → 스킬 칸 고르기 → 바꾸기/지우기 창 → 뒤로 세 번 (창 닫기 → 스킬 칸 고르기 끝 → 정보 닫기)
    pick(PartyOption.SUMMARY);
    await waitMode(UiMode.SUMMARY, "정보 다시 열기");
    game.scene.ui.processInput(Button.RIGHT);
    game.scene.ui.processInput(Button.RIGHT);
    await tick();
    game.scene.ui.processInput(Button.ACTION);
    await waitMode(UiMode.OPTION_SELECT, "스킬 바꾸기 창");
    back();
    await waitMode(UiMode.SUMMARY, "창 닫기");
    back();
    await tick();
    expect(mode(), "스킬 칸 고르기 끝 (정보는 그대로)").toBe("SUMMARY");
    back();
    await waitMode(UiMode.PARTY, "정보 닫기");

    pick(PartyOption.POKEDEX);
    await waitMode(UiMode.POKEDEX_PAGE, "도감 열기");
    back();
    await waitMode(UiMode.PARTY, "도감에서 뒤로");
    back();
    await waitMode(UiMode.COMMAND, "실험체 화면 닫기");
  });

  it("메뉴와 메뉴 안 화면(설정 · 업적 · 기록 · 실험체도감)에서 뒤로", async () => {
    await game.classicMode.startBattle(SpeciesId.BSEO_ELEVEN);
    const openMenu = async () => {
      game.scene.uiInputs.buttonMenu();
      await waitMode(UiMode.MENU);
    };
    await openMenu();
    hasBackButton();
    back();
    await waitMode(UiMode.COMMAND);

    const menuLabels = () => labels().filter(l => l.startsWith("option:"));
    await openMenu();
    expect(menuLabels().length).toBeGreaterThan(3);
    // 0 설정 · 1 업적 · 2 기록 (메뉴로 돌아와요), 실험체도감은 메뉴를 닫고 열려서 전투로 돌아와요
    for (const [i, inside, after] of [
      [0, UiMode.SETTINGS_GENERAL, UiMode.MENU],
      [1, UiMode.ACHIEVEMENTS, UiMode.MENU],
      [2, UiMode.GAME_STATS, UiMode.MENU],
    ] as const) {
      click(`option:${i}`);
      await waitMode(inside);
      hasBackButton();
      back();
      await waitMode(after);
    }
    back();
    await waitMode(UiMode.COMMAND);
  });

  it("보상 고르기: 팀 확인 · 아이템 옮기기 화면에서 뒤로, 보상 화면에서 뒤로는 건너뛸지 물어봐요", async () => {
    await game.classicMode.startBattle(SpeciesId.BSEO_ELEVEN, SpeciesId.BSEO_YUKI);
    game.move.select(MoveId.HAMMER_ARM);
    await game.move.forceHit();
    await game.phaseInterceptor.to("SelectModifierPhase");
    await new Promise<void>(resolve => {
      game.onNextPrompt("SelectModifierPhase", UiMode.MODIFIER_SELECT, () => resolve());
    });
    await vi.waitFor(() => expect(labels()).toContain("check-team"));

    click("check-team");
    await waitMode(UiMode.PARTY, "팀 확인 열기");
    back();
    await waitMode(UiMode.MODIFIER_SELECT, "팀 확인에서 뒤로");

    if (labels().includes("transfer")) {
      click("transfer");
      await waitMode(UiMode.PARTY, "아이템 옮기기 열기");
      back();
      await waitMode(UiMode.MODIFIER_SELECT, "아이템 옮기기에서 뒤로");
    }

    // 보상 화면에서 뒤로 → "보상을 건너뛸까요?" 예/아니요 → 아니요면 보상 화면으로
    back();
    await waitMode(UiMode.CONFIRM);
    click("option:1");
    await waitMode(UiMode.MODIFIER_SELECT);
  });
});
