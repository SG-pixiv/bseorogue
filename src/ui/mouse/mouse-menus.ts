/*
 * SPDX-FileCopyrightText: 2026 SG
 * SPDX-License-Identifier: AGPL-3.0-only
 */

/** 마우스: 저장 칸 · 실험체(파티) · 보상 고르기 · 상세 정보 · 설정 · 보급 상자 */
import { globalScene } from "#app/global-scene";
import { Button } from "#enums/buttons";
import type { EggGachaUiHandler } from "#ui/egg-gacha-ui-handler";
import type { ModifierSelectUiHandler } from "#ui/modifier-select-ui-handler";
import { isShown, localRect, type MouseTarget, objRect, peek, press, shownChildrenRect } from "#ui/mouse-targets";
import type { PartyUiHandler } from "#ui/party-ui-handler";
import type { SaveSlotSelectUiHandler } from "#ui/save-slot-select-ui-handler";
import type { SummaryUiHandler } from "#ui/summary-ui-handler";
import type { UiHandler } from "#ui/ui-handler";
import Phaser from "phaser";

type C = Phaser.GameObjects.Container;
type T = Phaser.GameObjects.Text;

/** 화면 아무 데나 누르면 결정 (다른 칸보다 아래에 깔려요) */
export function anywhere(label = "anywhere"): MouseTarget {
  return {
    label,
    rect: () => new Phaser.Geom.Rectangle(0, 0, globalScene.game.canvas.width, globalScene.game.canvas.height),
    instant: true,
    click: () => press(Button.ACTION),
  };
}

/** 버튼을 n번 누르기 (왼쪽 · 오른쪽으로 쪽 넘기기 등) */
function pressTimes(button: Button, n: number): void {
  for (let i = 0; i < n; i++) {
    press(button);
  }
}

// ── 저장 칸 고르기 (새 게임 · 불러오기)
type SaveSlotPeek = {
  sessionSlots: (C & { hasData: boolean })[];
  sessionSlotsContainer: C;
  cursorObj: C | null;
  scrollCursor: number;
  cursor: number;
};
const SLOTS_ON_SCREEN = 2;

export function saveSlotTargets(handler: SaveSlotSelectUiHandler): MouseTarget[] {
  const h = peek<SaveSlotPeek>(handler);
  const targets: MouseTarget[] = [];
  h.sessionSlots.forEach((slot, s) => {
    const onScreen = s - h.scrollCursor;
    const inView = onScreen >= 0 && onScreen < SLOTS_ON_SCREEN;
    const select = () => {
      if (h.cursor !== onScreen) {
        handler.setCursor(onScreen, h.cursor + h.scrollCursor);
      }
    };
    const rect = localRect(h.sessionSlotsContainer, slot.x, slot.y, 304, 70);
    if (inView) {
      targets.push({
        label: `slot:${s}`,
        rect,
        hover: select,
        click: () => {
          select();
          press(Button.ACTION);
        },
      });
    } else {
      // 반쯤 보이는 칸: 그쪽으로 넘기기
      targets.push({
        label: `slot:${s}`,
        rect,
        instant: true,
        click: () => press(onScreen < 0 ? Button.UP : Button.DOWN),
      });
    }
  });
  // 저장 내용 미리보기 (화살표)
  const arrow = h.cursorObj?.getByName("rightArrow") as Phaser.GameObjects.Image | undefined;
  if (arrow) {
    targets.push({ label: "slot-preview", rect: objRect(arrow, 4), instant: true, click: () => press(Button.RIGHT) });
  }
  return targets;
}

// ── 실험체 (파티) 화면
type PartyPeek = {
  partySlots: C[];
  partyCancelButton: C;
  partyDiscardModeButton: C;
  optionsMode: boolean;
  optionsContainer: C;
  optionsBg: Phaser.GameObjects.NineSlice;
  options: number[];
  optionsCursor: number;
  cursor: number;
  awaitingActionInput: boolean;
  pendingPrompt: boolean;
  blockInput: boolean;
};

export function partyTargets(handler: PartyUiHandler): MouseTarget[] {
  const h = peek<PartyPeek>(handler);
  if (h.pendingPrompt || h.blockInput || h.awaitingActionInput) {
    return [];
  }
  const go = (i: number) => () => {
    if (h.cursor !== i) {
      handler.setCursor(i);
    }
  };
  if (h.optionsMode) {
    // 실험체를 누른 뒤 뜨는 고르기 창 (교체 · 상세 정보 · 취소 등)
    const n = h.options.length;
    const bgW = h.optionsBg?.displayWidth ?? 0;
    return h.options.map((_, c) => ({
      label: `party-option:${c}`,
      rect: localRect(h.optionsContainer, -bgW + 2, -19 - 16 * (n - 1 - c) - 3, bgW - 4, 16),
      hover: () => {
        if (h.optionsCursor !== c) {
          handler.setCursor(c);
        }
      },
      click: () => {
        if (h.optionsCursor !== c) {
          handler.setCursor(c);
        }
        press(Button.ACTION);
      },
    }));
  }
  const targets: MouseTarget[] = h.partySlots.map((slot, i) => ({
    label: `party:${i}`,
    rect: objRect(slot),
    hover: go(i),
    click: () => {
      go(i)();
      press(Button.ACTION);
    },
  }));
  targets.push(
    {
      label: "party-cancel",
      rect: objRect(h.partyCancelButton),
      hover: go(6),
      click: () => {
        go(6)();
        press(Button.ACTION);
      },
    },
    {
      label: "party-discard",
      rect: objRect(h.partyDiscardModeButton),
      hover: go(7),
      click: () => {
        go(7)();
        press(Button.ACTION);
      },
    },
  );
  return targets;
}

// ── 보상 고르기
type ModifierPeek = {
  options: C[];
  shopOptionsRows: C[][];
  rowCursor: number;
  cursor: number;
  awaitingActionInput: boolean;
  rerollButtonContainer: C;
  transferButtonContainer: C;
  checkButtonContainer: C;
  lockRarityButtonContainer: C;
  continueButtonContainer: C;
};

export function modifierSelectTargets(handler: ModifierSelectUiHandler): MouseTarget[] {
  const h = peek<ModifierPeek>(handler);
  if (!h.awaitingActionInput) {
    return [];
  }
  const go = (row: number, col: number) => () => {
    if (h.rowCursor !== row || h.cursor !== col) {
      h.rowCursor = row;
      h.cursor = -1;
      handler.setCursor(col);
    }
  };
  const item = (
    label: string,
    obj: C | undefined,
    row: number,
    col: number,
    pad = 0,
    rect: MouseTarget["rect"] = objRect(obj, pad),
  ): MouseTarget => ({
    label,
    rect,
    hover: go(row, col),
    click: () => {
      go(row, col)();
      press(Button.ACTION);
    },
  });
  const targets: MouseTarget[] = [];
  // 아래 줄 버튼: 0 다시 뽑기 · 1 아이템 관리 · 2 팀 확인 · 3 등급 고정
  targets.push(
    item("reroll", h.rerollButtonContainer, 0, 0, 2),
    item("transfer", h.transferButtonContainer, 0, 1, 2),
    item("check-team", h.checkButtonContainer, 0, 2, 2),
    item("lock-rarity", h.lockRarityButtonContainer, 0, 3, 2),
  );
  if (h.options.length === 0) {
    targets.push(item("continue", h.continueButtonContainer, 1, 0, 2));
  }
  // 무료 보상
  // (보상 칸 안에는 화면 위쪽에 숨은 몬스터볼 그림이 있어서, 보이는 것만 감싸요)
  h.options.forEach((o, i) => targets.push(item(`reward:${i}`, o, 1, i, 2, shownChildrenRect(o, 2))));
  // 상점 (돈 내고 사는 줄)
  const rows = h.shopOptionsRows.length;
  h.shopOptionsRows.forEach((row, k) => {
    row.forEach((o, i) => targets.push(item(`shop:${k}:${i}`, o, rows - k + 1, i, 1, shownChildrenRect(o, 1))));
  });
  return targets;
}

// ── 상세 정보 (스킬 바꾸기 포함)
type SummaryPeek = {
  tabSprite: Phaser.GameObjects.Sprite;
  cursor: number;
  moveSelect: boolean;
  moveCursor: number;
  movesContainer: C;
  pokemon?: { moveset: unknown[] };
  newMove: unknown;
};
const SUMMARY_PAGES = 3;

export function summaryTargets(handler: SummaryUiHandler): MouseTarget[] {
  const h = peek<SummaryPeek>(handler);
  const targets: MouseTarget[] = [];
  // 위쪽 쪽 이름 (정보 · 능력치 · 스킬)
  for (let page = 0; page < SUMMARY_PAGES; page++) {
    targets.push({
      label: `summary-page:${page}`,
      rect: () => {
        const r = objRect(h.tabSprite)();
        if (!r) {
          return null;
        }
        const w = r.width / SUMMARY_PAGES;
        return new Phaser.Geom.Rectangle(r.x + w * page, r.y, w, r.height);
      },
      instant: true,
      click: () => {
        const diff = page - h.cursor;
        pressTimes(diff > 0 ? Button.RIGHT : Button.LEFT, Math.abs(diff));
      },
    });
  }
  // 스킬 쪽의 스킬 줄 (0~3, 새 스킬 4)
  if (h.cursor === 2 && h.movesContainer && isShown(h.movesContainer)) {
    const rows = (h.pokemon?.moveset ?? []).map((_, i) => i);
    if (h.newMove) {
      rows.push(4);
    }
    for (const row of rows) {
      targets.push({
        label: `summary-move:${row}`,
        rect: localRect(h.movesContainer, -2, 16 * row - 15, 196, 16),
        hover: () => {
          if (h.moveSelect && h.moveCursor !== row) {
            handler.setCursor(row);
          }
        },
        click: () => {
          if (!h.moveSelect) {
            // 스킬 고르기를 먼저 켜고 그 줄로
            press(Button.ACTION);
            handler.setCursor(row);
            return;
          }
          if (h.moveCursor !== row) {
            handler.setCursor(row);
          }
          press(Button.ACTION);
        },
      });
    }
  }
  return targets;
}

// ── 설정 (일반 · 화면 · 소리)
type TabMenuPeek = C & {
  headerTitles: T[];
  selectedIndex: number;
  onChangeCallback: (i: number) => void;
  updateTabs(): void;
  navigationIcons: Record<string, Phaser.GameObjects.Sprite>;
};

export function tabMenuTargets(tabMenu: TabMenuPeek | undefined): MouseTarget[] {
  if (!tabMenu) {
    return [];
  }
  const targets: MouseTarget[] = tabMenu.headerTitles.map((title, i) => ({
    label: `tab:${i}`,
    rect: objRect(title, 3),
    instant: true,
    click: () => {
      if (tabMenu.selectedIndex !== i) {
        tabMenu.selectedIndex = i;
        tabMenu.updateTabs();
        tabMenu.onChangeCallback(i);
      }
    },
  }));
  const prev = tabMenu.navigationIcons.BUTTON_CYCLE_FORM;
  const next = tabMenu.navigationIcons.BUTTON_CYCLE_SHINY;
  targets.push(
    { label: "tab-prev", rect: objRect(prev, 2), instant: true, click: () => press(Button.CYCLE_FORM) },
    { label: "tab-next", rect: objRect(next, 2), instant: true, click: () => press(Button.CYCLE_SHINY) },
  );
  return targets;
}

type SettingsPeek = {
  tabMenu: TabMenuPeek;
  optionsContainer: C;
  settingLabels: T[];
  optionValueLabels: T[][];
  optionCursors: number[];
  scrollCursor: number;
  rowsToDisplay: number;
  cursor: number;
  setOptionCursor(settingIndex: number, cursor: number, save?: boolean): boolean;
};

export function settingsTargets(handler: UiHandler): MouseTarget[] {
  const h = peek<SettingsPeek>(handler);
  const targets = tabMenuTargets(h.tabMenu);
  const width = globalScene.scaledCanvas.width - 14;
  for (let s = h.scrollCursor; s < Math.min(h.settingLabels.length, h.scrollCursor + h.rowsToDisplay); s++) {
    const label = h.settingLabels[s];
    const row = s - h.scrollCursor;
    const goRow = () => {
      if (h.cursor !== row) {
        handler.setCursor(row);
      }
    };
    targets.push({
      label: `setting:${s}`,
      rect: localRect(h.optionsContainer, 4, label.y - 2, width, 16),
      hover: goRow,
      // 줄을 누르면 다음 값으로
      click: () => {
        goRow();
        press(Button.RIGHT);
      },
    });
    h.optionValueLabels[s].forEach((value, j) => {
      targets.push({
        label: `setting:${s}:${j}`,
        rect: objRect(value, 2),
        hover: goRow,
        click: () => {
          goRow();
          if (h.optionCursors[s] !== j && h.setOptionCursor(s, j, true)) {
            globalScene.ui.playSelect();
          }
        },
      });
    });
  }
  return targets;
}

/** 키 설정 화면: 위쪽 쪽 이름만 누르고, 나머지는 휠 · 클릭 */
export function controlSettingsTargets(handler: UiHandler): MouseTarget[] {
  return [anywhere(), ...tabMenuTargets(peek<SettingsPeek>(handler).tabMenu)];
}

// ── 보급 상자 뽑기
type GachaPeek = {
  transitioning: boolean;
  eggGachaSummaryContainer: C;
  eggGachaOptionsContainer: C;
  eggGachaOptionSelectBg: Phaser.GameObjects.NineSlice;
  gachaContainers: C[];
  gachaCursor: number;
  cursor: number;
};
const GACHA_ROWS = 6;

export function eggGachaTargets(handler: EggGachaUiHandler): MouseTarget[] {
  const h = peek<GachaPeek>(handler);
  // 뽑는 중 · 결과 화면: 아무 데나 누르면 넘기기
  if (h.transitioning || h.eggGachaSummaryContainer.visible) {
    return [anywhere()];
  }
  const targets: MouseTarget[] = [];
  h.gachaContainers.forEach((c, i) => {
    if (i === h.gachaCursor) {
      return;
    }
    targets.push({
      label: `gacha:${i}`,
      rect: objRect(c),
      instant: true,
      click: () => pressTimes(i < h.gachaCursor ? Button.LEFT : Button.RIGHT, Math.abs(i - h.gachaCursor)),
    });
  });
  const bg = h.eggGachaOptionSelectBg;
  if (bg) {
    const left = bg.x - bg.displayWidth * bg.originX;
    const top = bg.y - bg.displayHeight * bg.originY;
    const pitch = handler.getOptionPitch();
    for (let i = 0; i < GACHA_ROWS; i++) {
      const go = () => {
        if (h.cursor !== i) {
          handler.setCursor(i);
        }
      };
      targets.push({
        label: `gacha-option:${i}`,
        rect: localRect(h.eggGachaOptionsContainer, left + 2, top + 9 + pitch * i, bg.displayWidth - 4, pitch),
        hover: go,
        click: () => {
          go();
          press(Button.ACTION);
        },
      });
    }
  }
  return targets;
}

// ── 아이콘 격자 (업적 · 보급 상자 목록): 올리면 그 칸 설명
function hoverGrid(
  icons: (Phaser.GameObjects.Sprite | C)[],
  handler: UiHandler,
  prefix: string,
  count = icons.length,
): MouseTarget[] {
  return icons.slice(0, count).map((icon, i) => {
    const go = () => {
      if (handler.getCursor() !== i) {
        handler.setCursor(i);
        globalScene.ui.playSelect();
      }
    };
    return { label: `${prefix}:${i}`, rect: objRect(icon, 1), hover: go, click: go };
  });
}

type AchvsPeek = {
  icons: Phaser.GameObjects.Sprite[];
  currentTotal: number;
  scrollCursor: number;
  COLS: number;
  headerActionText: T;
  headerActionButton: Phaser.GameObjects.Sprite;
};

/** 업적 · 보급 요청권: 아이콘에 올리면 설명, 위쪽 버튼을 누르면 쪽 바꾸기 */
export function achievementsTargets(handler: UiHandler): MouseTarget[] {
  const h = peek<AchvsPeek>(handler);
  const shown = Math.max(0, Math.min(h.icons.length, h.currentTotal - h.scrollCursor * h.COLS));
  return [
    ...hoverGrid(h.icons, handler, "achv", shown),
    {
      label: "achv-page",
      rect: () => {
        const a = objRect(h.headerActionText, 2)();
        const b = objRect(h.headerActionButton, 2)();
        return a && b ? Phaser.Geom.Rectangle.Union(a, b) : (a ?? b);
      },
      instant: true,
      click: () => press(Button.ACTION),
    },
  ];
}

type RunHistoryPeek = { runs: C[]; runsContainer: C; scrollCursor: number; cursor: number; maxRows: number };

/** 플레이 이력: 줄을 누르면 그 판 자세히 보기 */
export function runHistoryTargets(handler: UiHandler): MouseTarget[] {
  const h = peek<RunHistoryPeek>(handler);
  return h.runs.map((run, s) => {
    const onScreen = s - h.scrollCursor;
    const inView = onScreen >= 0 && onScreen < h.maxRows;
    const rect = localRect(h.runsContainer, 0, run.y, 304, 52);
    if (!inView) {
      return { label: `run:${s}`, rect, instant: true, click: () => press(onScreen < 0 ? Button.UP : Button.DOWN) };
    }
    const go = () => {
      if (h.cursor !== onScreen) {
        handler.setCursor(onScreen);
      }
    };
    return {
      label: `run:${s}`,
      rect,
      hover: go,
      click: () => {
        go();
        press(Button.ACTION);
      },
    };
  });
}

type EggListPeek = { eggIcons: Phaser.GameObjects.Sprite[] };

/** 보급 상자 목록: 상자에 올리면 설명 */
export function eggListTargets(handler: UiHandler): MouseTarget[] {
  const icons = peek<EggListPeek>(handler).eggIcons ?? [];
  return hoverGrid(
    icons.filter(i => i.visible),
    handler,
    "egg",
  );
}

type EggSummaryPeek = { pokemonContainers: C[] };

/** 보급 상자에서 나온 실험체: 올리면 그 실험체 정보 (오른쪽 클릭으로 닫기) */
export function eggSummaryTargets(handler: UiHandler): MouseTarget[] {
  return hoverGrid(peek<EggSummaryPeek>(handler).pokemonContainers ?? [], handler, "hatched");
}
