/*
 * SPDX-FileCopyrightText: 2026 SG
 * SPDX-License-Identifier: AGPL-3.0-only
 */

/**
 * 블서로그 마우스 조작
 *
 * - 왼쪽 클릭: 누른 칸을 골라 결정 (마우스를 올리면 그 칸으로 커서가 가요)
 * - 대사가 멈춰 있을 때 아무 데나 클릭: 다음 대사
 * - 오른쪽 클릭: 취소 · 뒤로 (키보드 B / Esc 와 같아요)
 * - 휠: 위 · 아래 (가로 휠 · Shift+휠은 왼쪽 · 오른쪽)
 * - 가운데 클릭: 메뉴
 * 터치 화면에서는 한 번 누르면 고르고, 한 번 더 누르면 결정해요.
 * 직접 누르는 칸을 아직 안 만든 화면에서는 휠로 고르고 왼쪽 클릭으로 결정해요.
 * 키보드(스페이스 · 방향키 등)는 원래대로 다 돼요.
 */
import { globalScene } from "#app/global-scene";
import { Button } from "#enums/buttons";
import { TextStyle } from "#enums/text-style";
import { UiMode } from "#enums/ui-mode";
import { MessageUiHandler } from "#ui/message-ui-handler";
import { mouseTargetsFor } from "#ui/mouse-screens";
import type { MouseTarget } from "#ui/mouse-targets";
import { objRect, press } from "#ui/mouse-targets";
import { addTextObject } from "#ui/text";
import { addWindow } from "#ui/ui-theme";
import type Phaser from "phaser";

/** 휠을 이만큼 굴리면 한 칸 */
const WHEEL_STEP = 60;

/** 화면이 바뀌는 중(어두워지는 중 등)이라 입력을 안 받을 때 */
function uiBusy(): boolean {
  return !globalScene.ui || (globalScene.ui as unknown as { overlayActive: boolean }).overlayActive;
}

/** 대사가 다 나오고 "다음"을 기다리는 중인지 (보상 고르기 같은 화면의 대기와는 달라요) */
function isPrompt(handler: unknown): boolean {
  return handler instanceof MessageUiHandler && !!(handler as unknown as Awaiting).awaitingActionInput;
}

type Awaiting = { awaitingActionInput?: boolean; tutorialActive?: boolean; pendingPrompt?: boolean };

/** 메뉴 버튼을 보여 주는 화면 (키보드 M · Esc 로 메뉴가 열리는 화면. 메뉴 안에서는 오른쪽 클릭으로 닫아요) */
const MENU_MODES: readonly UiMode[] = [UiMode.COMMAND, UiMode.MODIFIER_SELECT];

class MouseController {
  private hoverKey: string | null = null;
  private hovered: MouseTarget | null = null;
  private menuButton: Phaser.GameObjects.Container | null = null;
  private wheelX = 0;
  private wheelY = 0;
  private started = false;

  /** 씬이 UI를 다 만든 뒤 한 번 */
  init(): void {
    if (this.started) {
      return;
    }
    const input = globalScene.input;
    // 검사 환경(가짜 화면)에는 마우스 입력이 없어요
    if (typeof input?.on !== "function") {
      return;
    }
    this.started = true;
    input.mouse?.disableContextMenu();
    input.on("pointermove", (p: Phaser.Input.Pointer) => this.onMove(p));
    input.on("pointerdown", (p: Phaser.Input.Pointer, over: Phaser.GameObjects.GameObject[]) => this.onDown(p, over));
    input.on("wheel", (p: Phaser.Input.Pointer, _over: unknown, dx: number, dy: number) => this.onWheel(p, dx, dy));
    this.setupMenuButton();
    globalScene.events.on("update", () => this.updateMenuButton());
  }

  /** 왼쪽 위 "메뉴" 버튼 (마우스만 쓰는 사람도 메뉴를 열 수 있게) */
  private setupMenuButton(): void {
    const container = globalScene.add.container(1, 1).setName("bseo-menu-button").setVisible(false);
    const bg = addWindow(0, 0, 30, 14).setOrigin(0);
    const label = addTextObject(15, 7, "메뉴", TextStyle.WINDOW, { fontSize: "60px" }).setOrigin(0.5);
    container.add([bg, label]);
    globalScene.uiContainer.add(container);
    this.menuButton = container;
  }

  private canOpenMenu(): boolean {
    const ui = globalScene.ui;
    if (!ui || globalScene.disableMenu || uiBusy()) {
      return false;
    }
    if (MENU_MODES.includes(ui.mode)) {
      return true;
    }
    if (ui.mode === UiMode.MESSAGE) {
      const m = ui.getHandler<MessageUiHandler>();
      return m.pendingPrompt && !m.isTextAnimationInProgress();
    }
    return false;
  }

  private updateMenuButton(): void {
    const button = this.menuButton;
    if (!button) {
      return;
    }
    const show = this.canOpenMenu();
    if (button.visible !== show) {
      button.setVisible(show);
    }
    // 다른 화면 위에 늘 보이게
    if (show && globalScene.uiContainer.last !== button) {
      globalScene.uiContainer.bringToTop(button);
    }
  }

  /** 모든 화면에 같이 있는 칸 (메뉴 버튼 · 전투 중 정보 창) */
  private globalTargets(): MouseTarget[] {
    const targets: MouseTarget[] = [];
    const ui = globalScene.ui;
    // 전투 중 실험체 정보 창에 올리면 능력치 변화 보기 (C 키)
    if ([UiMode.COMMAND, UiMode.FIGHT, UiMode.MESSAGE].includes(ui.mode) && globalScene.currentBattle) {
      for (const pokemon of globalScene.getField()) {
        if (!pokemon?.isActive(true)) {
          continue;
        }
        const info = (pokemon as unknown as { battleInfo?: Phaser.GameObjects.Container }).battleInfo;
        targets.push({
          label: `info:${pokemon.getBattlerIndex()}`,
          rect: objRect(info),
          hover: () => globalScene.uiInputs.buttonStats(true),
          leave: () => globalScene.uiInputs.buttonStats(false),
          instant: true,
          click: () => {
            if (isPrompt(ui.getHandler())) {
              press(Button.ACTION);
            }
          },
        });
      }
    }
    if (this.menuButton?.visible) {
      targets.push({
        label: "menu-button",
        rect: objRect(this.menuButton),
        instant: true,
        click: () => globalScene.uiInputs.buttonMenu(),
      });
    }
    return targets;
  }

  /** 지금 화면에서 누를 수 있는 곳. screen 이 null 이면 이 화면은 직접 누르는 칸이 없어요 */
  private collect(): { screen: MouseTarget[] | null; all: MouseTarget[] } {
    const ui = globalScene.ui;
    if (!ui) {
      return { screen: null, all: [] };
    }
    let screen: MouseTarget[] | null;
    try {
      screen = mouseTargetsFor(ui.mode, ui.getHandler());
    } catch (e) {
      console.warn("마우스 칸 계산 실패", e);
      screen = [];
    }
    return { screen, all: [...(screen ?? []), ...this.globalTargets()] };
  }

  targets(): MouseTarget[] | null {
    return this.collect().screen;
  }

  private setHovered(t: MouseTarget | null): void {
    const key = t ? this.key(t) : null;
    if (key === this.hoverKey) {
      return;
    }
    this.hovered?.leave?.();
    this.hoverKey = key;
    this.hovered = t;
    t?.hover?.();
  }

  private key(t: MouseTarget): string {
    return `${globalScene.ui.mode}:${t.label}`;
  }

  /** 맨 위(목록 뒤쪽)부터 찾아요 */
  private hit(p: { x: number; y: number }, list: MouseTarget[] | null): MouseTarget | null {
    if (!list) {
      return null;
    }
    for (let i = list.length - 1; i >= 0; i--) {
      const r = list[i].rect();
      if (r?.contains(p.x, p.y)) {
        return list[i];
      }
    }
    return null;
  }

  private setPointerStyle(on: boolean): void {
    const canvas = globalScene.input.manager.canvas;
    if (canvas) {
      canvas.style.cursor = on ? "pointer" : "default";
    }
  }

  private onMove(p: Phaser.Input.Pointer): void {
    if (p.wasTouch || uiBusy() || (globalScene.ui.getHandler() as unknown as Awaiting).tutorialActive) {
      return;
    }
    const t = this.hit(p, this.collect().all);
    this.setPointerStyle(!!t && !t.label.startsWith("info:"));
    this.setHovered(t);
  }

  private onDown(p: Phaser.Input.Pointer, over: Phaser.GameObjects.GameObject[]): void {
    const ui = globalScene.ui;
    if (uiBusy()) {
      return;
    }
    // 원래 게임에서 따로 누르게 만든 것(창 버튼 등)은 그쪽이 처리해요 (설명 풍선만 있는 것은 빼고)
    if (over?.some(o => o.listenerCount("pointerdown") + o.listenerCount("pointerup") > 0)) {
      return;
    }
    if (p.rightButtonDown()) {
      press(Button.CANCEL);
      return;
    }
    if (p.middleButtonDown()) {
      globalScene.uiInputs.buttonMenu();
      return;
    }
    // 튜토리얼 설명 중에는 어디를 눌러도 다음 설명으로
    const handler = ui.getHandler() as unknown as Awaiting;
    if (handler.tutorialActive) {
      press(Button.ACTION);
      return;
    }
    const { screen, all } = this.collect();
    const t = this.hit(p, all);
    if (t) {
      const key = this.key(t);
      // 터치: 처음 누르면 고르기만, 같은 칸을 한 번 더 누르면 결정
      if (p.wasTouch && !t.instant && this.hoverKey !== key) {
        this.setHovered(t);
        return;
      }
      this.setHovered(t);
      t.click();
      // 화면이 바뀌었을 수 있으니 다음 움직임에서 다시 찾아요
      this.hovered?.leave?.();
      this.hovered = null;
      this.hoverKey = null;
      return;
    }
    // 빈 곳: 대사가 멈춰 있으면 넘기고, 직접 누르는 칸이 없는 화면이면 지금 커서로 결정
    if (screen === null || isPrompt(handler)) {
      press(Button.ACTION);
    }
  }

  private onWheel(p: Phaser.Input.Pointer, dx: number, dy: number): void {
    if (uiBusy()) {
      return;
    }
    const e = p.event as WheelEvent | undefined;
    // 줄 단위로 오는 브라우저(파이어폭스 등)는 픽셀로 바꿔요
    if (e?.deltaMode === 1) {
      dx *= 33;
      dy *= 33;
    }
    if (e?.shiftKey && !dx) {
      [dx, dy] = [dy, 0];
    }
    this.wheelX += dx;
    this.wheelY += dy;
    while (Math.abs(this.wheelY) >= WHEEL_STEP) {
      press(this.wheelY > 0 ? Button.DOWN : Button.UP);
      this.wheelY -= Math.sign(this.wheelY) * WHEEL_STEP;
    }
    while (Math.abs(this.wheelX) >= WHEEL_STEP) {
      press(this.wheelX > 0 ? Button.RIGHT : Button.LEFT);
      this.wheelX -= Math.sign(this.wheelX) * WHEEL_STEP;
    }
    // 반대로 굴리기 시작하면 남은 양은 버려요
    if (Math.sign(dy) !== Math.sign(this.wheelY)) {
      this.wheelY = 0;
    }
    if (Math.sign(dx) !== Math.sign(this.wheelX)) {
      this.wheelX = 0;
    }
  }

  /** 브라우저 확인용: 지금 화면 */
  debugState(): { mode: string; handler: string; covered: boolean; awaiting: boolean; tutorial: boolean } {
    const ui = globalScene.ui;
    const handler = ui.getHandler() as unknown as Awaiting & { constructor: { name: string } };
    return {
      mode: UiMode[ui.mode],
      handler: handler.constructor.name,
      covered: this.targets() !== null,
      awaiting: isPrompt(handler),
      tutorial: !!handler.tutorialActive,
    };
  }

  /** 브라우저 확인용: 지금 누를 수 있는 칸 (게임 좌표) */
  debugTargets(): { label: string; x: number; y: number; w: number; h: number }[] {
    return this.collect().all.flatMap(t => {
      const r = t.rect();
      return r ? [{ label: t.label, x: r.x, y: r.y, w: r.width, h: r.height }] : [];
    });
  }
}

export const mouseController = new MouseController();
