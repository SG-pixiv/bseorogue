/*
 * SPDX-FileCopyrightText: 2026 SG
 * SPDX-License-Identifier: AGPL-3.0-only
 */

/** 마우스: 전투 명령 · 스킬 고르기 · 고르기 목록(예/아니요 · 타이틀 · 메뉴 등) */
import { Button } from "#enums/buttons";
import type { OptionSelectItem } from "#types/ui-types";
import type { BaseOptionSelectUiHandler } from "#ui/base-option-select-ui-handler";
import type { CommandUiHandler } from "#ui/command-ui-handler";
import type { FightUiHandler } from "#ui/fight-ui-handler";
import { localRect, type MouseTarget, objRect, peek, press } from "#ui/mouse-targets";
import Phaser from "phaser";

/** 커서를 옮기고 결정 */
function pick(handler: { setCursor(i: number): boolean; getCursor(): number }, i: number): () => void {
  return () => {
    if (handler.getCursor() !== i) {
      handler.setCursor(i);
    }
    press(Button.ACTION);
  };
}

// ── 싸운다 · 가방 · 실험체 · 도망 (2×2)
export function commandTargets(handler: CommandUiHandler): MouseTarget[] {
  const h = peek<{ commandsContainer: Phaser.GameObjects.Container }>(handler);
  return [0, 1, 2, 3].map(c => ({
    label: `command:${c}`,
    rect: localRect(h.commandsContainer, (c % 2 === 0 ? 0 : 55.8) - 9, c < 2 ? -1 : 15, 56, 16),
    hover: () => handler.setCursor(c),
    click: pick(handler, c),
  }));
}

// ── 스킬 Q · W · E · R (2×2)
export function fightTargets(handler: FightUiHandler): MouseTarget[] {
  const h = peek<{ movesContainer: Phaser.GameObjects.Container; fieldIndex: number }>(handler);
  return [0, 1, 2, 3].map(m => ({
    label: `move:${m}`,
    rect: localRect(h.movesContainer, (m % 2 === 0 ? 0 : 114) - 9, m < 2 ? -1 : 15, 113, 16),
    hover: () => handler.setCursor(m),
    click: pick(handler, m),
  }));
}

// ── 고르기 목록 (예/아니요 · 타이틀 메뉴 · 메뉴 · 티어 고르기 등)
type OptionSelectPeek = {
  optionSelectBg: Phaser.GameObjects.NineSlice;
  optionSelectText: Phaser.GameObjects.Components.Visible & {
    getBounds: () => Phaser.Geom.Rectangle;
    parentContainer: Phaser.GameObjects.Container;
  };
  options: (OptionSelectItem & { selectable: boolean })[];
  maxOptions: number;
  scrollCursor: number;
  cursor: number;
};

export function optionSelectTargets(handler: BaseOptionSelectUiHandler<OptionSelectItem>): MouseTarget[] {
  const h = peek<OptionSelectPeek>(handler);
  if (!h.optionSelectBg || !h.options?.length) {
    return [];
  }
  const shown = Math.min(h.maxOptions, h.options.length - h.scrollCursor);
  const targets: MouseTarget[] = [];
  for (let i = 0; i < shown; i++) {
    const option = h.options[h.scrollCursor + i];
    if (!option?.selectable) {
      continue;
    }
    const go = () => {
      if (h.cursor !== i) {
        handler.setCursor(i);
      }
    };
    targets.push({
      label: `option:${h.scrollCursor + i}`,
      // 글자 줄 위치 그대로 (창 폭만큼 넓게)
      rect: () => {
        const text = objRect(h.optionSelectText)();
        const bg = objRect(h.optionSelectBg)();
        if (!text || !bg) {
          return null;
        }
        const pitch = text.height / shown;
        return new Phaser.Geom.Rectangle(bg.x + 6, text.y + pitch * i, bg.width - 12, pitch);
      },
      hover: go,
      click: () => {
        go();
        press(Button.ACTION);
      },
    });
  }
  return targets;
}
