/*
 * SPDX-FileCopyrightText: 2026 SG
 * SPDX-License-Identifier: AGPL-3.0-only
 */

/** 마우스: 시작 실험체 고르기 화면 · 필터 줄 */
import { Button } from "#enums/buttons";
import type { FilterBar } from "#ui/filter-bar";
import { isShown, localRect, type MouseTarget, objRect, peek, press, unionRect } from "#ui/mouse-targets";
import type { StarterSelectUiHandler } from "#ui/starter-select-ui-handler";
import type Phaser from "phaser";

type Obj = Phaser.GameObjects.Components.Visible & {
  getBounds: () => Phaser.Geom.Rectangle;
  parentContainer: Phaser.GameObjects.Container;
};

// ── 필터 줄 (시작 실험체 · 도감 화면에서 같이 써요)
type DropDownPeek = Phaser.GameObjects.Container & {
  window: Phaser.GameObjects.NineSlice;
  optionHeight: number;
  optionSpacing: number;
  options: Phaser.GameObjects.Container[];
  cursor: number;
  setCursor(i: number): boolean;
};
type FilterBarPeek = { labels: Phaser.GameObjects.Text[]; dropDowns: DropDownPeek[] };

interface FilterHost {
  /** 필터 줄로 들어가기 (다른 커서는 숨기기) */
  enter: () => void;
  isFilterMode: () => boolean;
  setCursor: (i: number) => boolean;
  cursor: () => number;
}

export function filterBarTargets(bar: FilterBar, host: FilterHost, prefix = "filter"): MouseTarget[] {
  const b = peek<FilterBarPeek>(bar);
  const targets: MouseTarget[] = [];
  const goColumn = (i: number) => {
    host.enter();
    if (host.cursor() !== i) {
      host.setCursor(i);
    }
  };
  b.labels.forEach((label, i) => {
    targets.push({
      label: `${prefix}:${i}`,
      rect: objRect(label, 3),
      instant: true,
      click: () => {
        const wasOpen = bar.openDropDown && host.isFilterMode() && host.cursor() === i;
        goColumn(i);
        if (wasOpen) {
          // 같은 칸을 또 누르면 닫기
          bar.toggleDropDown(i);
        } else if (!bar.openDropDown) {
          press(Button.ACTION);
        }
      },
    });
  });
  // 열린 목록의 칸 (켜기 · 끄기)
  if (bar.openDropDown && host.isFilterMode()) {
    const dd = peek<DropDownPeek>(b.dropDowns[host.cursor()]);
    if (dd && isShown(dd)) {
      const rowH = dd.optionHeight + dd.optionSpacing;
      dd.options.forEach((option, index) => {
        if (!isShown(option) || option.y < 0 || option.y + dd.optionHeight > dd.window.height) {
          return;
        }
        targets.push({
          label: `${prefix}-option:${index}`,
          rect: localRect(dd, 0, option.y - dd.optionSpacing / 2, dd.window.width, rowH),
          hover: () => {
            if (dd.cursor !== index) {
              dd.setCursor(index);
            }
          },
          click: () => {
            if (dd.cursor !== index) {
              dd.setCursor(index);
            }
            press(Button.ACTION);
          },
        });
      });
    }
  }
  return targets;
}

// ── 시작 실험체 고르기
type StarterPeek = {
  starterContainers: (Phaser.GameObjects.Container & { species?: unknown })[];
  filterBar: FilterBar;
  filterMode: boolean;
  filterBarCursor: number;
  cursor: number;
  cursorObj: Phaser.GameObjects.Image;
  partyCursorObj: Phaser.GameObjects.Image;
  startCursorObj: Phaser.GameObjects.NineSlice;
  randomCursorObj: Phaser.GameObjects.NineSlice;
  partyIcons: Phaser.GameObjects.Sprite[];
  partyStarterIds: number[];
  partyIconsCursorIndex: number;
  instructionsContainer: Phaser.GameObjects.Container & Record<string, Obj>;
  starterSelectContainer: Phaser.GameObjects.Container;
  setFilterMode(on: boolean): boolean;
  movePartyIconsCursor(i: number): void;
  setNoStarter(): void;
  showRandomCursor(): void;
  updateInstructions(): void;
};

/** 시작 버튼 · 무작위 버튼 칸 (팀 줄 안 좌표) */
const START_RECT = [289, 160, 26, 15] as const;
const RANDOM_RECT = [289, 21, 26, 15] as const;

/** 칸 (실험체 · 팀 · 시작 · 무작위 · 필터) 중 하나로 커서를 옮기기 전에 나머지 커서 숨기기 */
function leaveAll(h: StarterPeek): void {
  if (h.filterMode) {
    if (h.filterBar.openDropDown) {
      h.filterBar.toggleDropDown(h.filterBarCursor);
    }
    h.setFilterMode(false);
  }
  h.partyCursorObj.setVisible(false);
  h.startCursorObj.setVisible(false);
  h.randomCursorObj.setVisible(false);
}

const KEY_HINTS: readonly [icon: string, label: string, button: Button][] = [
  ["shinyIconElement", "shinyLabel", Button.CYCLE_SHINY],
  ["formIconElement", "formLabel", Button.CYCLE_FORM],
  ["genderIconElement", "genderLabel", Button.CYCLE_GENDER],
  ["abilityIconElement", "abilityLabel", Button.CYCLE_ABILITY],
  ["natureIconElement", "natureLabel", Button.CYCLE_NATURE],
  ["teraIconElement", "teraLabel", Button.CYCLE_TERA],
  ["goFilterIconElement", "goFilterLabel", Button.STATS],
];

/** 화면 아래 단축키 안내 (R: 색 · F: 폼 · C: 필터 등)를 누르면 그 키를 누른 것처럼 */
export function keyHintTargets(container: Record<string, Obj>, prefix: string): MouseTarget[] {
  return KEY_HINTS.filter(([icon]) => container[icon]).map(([icon, label, button]) => ({
    label: `${prefix}:${Button[button]}`,
    rect: unionRect(container[icon], container[label]),
    instant: true,
    click: () => press(button),
  }));
}

export function starterSelectTargets(handler: StarterSelectUiHandler): MouseTarget[] {
  const h = peek<StarterPeek>(handler);
  if (!isShown(h.starterSelectContainer)) {
    return [];
  }
  const targets: MouseTarget[] = [];
  const box = h.starterContainers[0]?.parentContainer;
  const team = h.partyIcons[0]?.parentContainer;

  // 실험체 칸
  h.starterContainers.forEach((c, i) => {
    if (!c.visible) {
      return;
    }
    const go = () => {
      leaveAll(h);
      h.cursorObj.setVisible(true);
      if (h.cursor !== i) {
        handler.setCursor(i);
      }
    };
    targets.push({
      label: `starter:${i}`,
      rect: localRect(box, c.x, c.y, 18, 17),
      hover: go,
      click: () => {
        go();
        press(Button.ACTION);
      },
    });
  });

  // 팀에 넣은 실험체
  h.partyStarterIds.forEach((_, i) => {
    const go = () => {
      leaveAll(h);
      h.cursorObj.setVisible(false);
      h.partyIconsCursorIndex = i;
      h.movePartyIconsCursor(i);
    };
    targets.push({
      label: `team:${i}`,
      rect: objRect(h.partyIcons[i], 1),
      hover: go,
      click: () => {
        go();
        press(Button.ACTION);
      },
    });
  });

  // 무작위 · 시작
  targets.push(
    {
      label: "random",
      rect: localRect(team, ...RANDOM_RECT),
      hover: () => {
        leaveAll(h);
        h.cursorObj.setVisible(false);
        h.showRandomCursor();
      },
      click: () => press(Button.ACTION),
    },
    {
      label: "start",
      rect: localRect(team, ...START_RECT),
      hover: () => {
        leaveAll(h);
        h.cursorObj.setVisible(false);
        h.startCursorObj.setVisible(true);
      },
      click: () => press(Button.SUBMIT),
    },
  );

  targets.push(...keyHintTargets(h.instructionsContainer, "key"));

  // 필터 줄은 맨 위(목록이 실험체 칸을 덮어요)
  targets.push(
    ...filterBarTargets(h.filterBar, {
      enter: () => {
        if (!h.filterMode) {
          h.partyCursorObj.setVisible(false);
          h.startCursorObj.setVisible(false);
          h.randomCursorObj.setVisible(false);
          h.setFilterMode(true);
        }
      },
      isFilterMode: () => h.filterMode,
      setCursor: i => handler.setCursor(i),
      cursor: () => h.filterBarCursor,
    }),
  );
  return targets;
}

// ── 도감 (실험체 목록)
type PokedexPeek = {
  pokemonContainers: Phaser.GameObjects.Container[];
  filterBar: FilterBar;
  filterMode: boolean;
  filterTextMode: boolean;
  filterBarCursor: number;
  cursor: number;
  setFilterMode(on: boolean): boolean;
  setFilterTextMode(on: boolean): boolean;
  setCursor(i: number): boolean;
};

export function pokedexTargets(handler: unknown): MouseTarget[] {
  const h = peek<PokedexPeek>(handler);
  const targets: MouseTarget[] = [];
  const box = h.pokemonContainers[0]?.parentContainer;
  h.pokemonContainers.forEach((c, i) => {
    if (!c.visible) {
      return;
    }
    const go = () => {
      if (h.filterMode) {
        if (h.filterBar.openDropDown) {
          h.filterBar.toggleDropDown(h.filterBarCursor);
        }
        h.setFilterMode(false);
      }
      if (h.filterTextMode) {
        h.setFilterTextMode(false);
      }
      if (h.cursor !== i) {
        h.setCursor(i);
      }
    };
    targets.push({
      label: `dex:${i}`,
      rect: localRect(box, c.x, c.y, 18, 17),
      hover: go,
      click: () => {
        go();
        press(Button.ACTION);
      },
    });
  });
  targets.push(
    ...filterBarTargets(h.filterBar, {
      enter: () => {
        if (h.filterTextMode) {
          h.setFilterTextMode(false);
        }
        if (!h.filterMode) {
          h.setFilterMode(true);
        }
      },
      isFilterMode: () => h.filterMode,
      setCursor: i => h.setCursor(i),
      cursor: () => h.filterBarCursor,
    }),
  );
  return targets;
}
