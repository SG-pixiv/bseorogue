/*
 * SPDX-FileCopyrightText: 2026 SG
 * SPDX-License-Identifier: AGPL-3.0-only
 */

/**
 * 화면(UI 모드)마다 마우스로 누를 수 있는 곳
 *
 * 새 화면을 마우스로 누르게 하려면 아래 SCREENS 에 처리기 종류와 칸 목록 함수를 더하면 돼요.
 * 목록에 없는 화면은 null (휠로 고르고 왼쪽 클릭으로 결정)이에요.
 */
import { UiMode } from "#enums/ui-mode";
import { AchvsUiHandler } from "#ui/achvs-ui-handler";
import { BaseControlSettingsUiHandler } from "#ui/base-control-settings-ui-handler";
import { BaseOptionSelectUiHandler } from "#ui/base-option-select-ui-handler";
import { BaseSettingsUiHandler } from "#ui/base-settings-ui-handler";
import { BattleMessageUiHandler } from "#ui/battle-message-ui-handler";
import { CommandUiHandler } from "#ui/command-ui-handler";
import { EggGachaUiHandler } from "#ui/egg-gacha-ui-handler";
import { EggListUiHandler } from "#ui/egg-list-ui-handler";
import { EggSummaryUiHandler } from "#ui/egg-summary-ui-handler";
import { EvolutionSceneUiHandler } from "#ui/evolution-scene-ui-handler";
import { FightUiHandler } from "#ui/fight-ui-handler";
import { ModalUiHandler } from "#ui/modal-ui-handler";
import { ModifierSelectUiHandler } from "#ui/modifier-select-ui-handler";
import { commandTargets, fightTargets, optionSelectTargets } from "#ui/mouse-battle";
import {
  achievementsTargets,
  controlSettingsTargets,
  eggGachaTargets,
  eggListTargets,
  eggSummaryTargets,
  modifierSelectTargets,
  partyTargets,
  runHistoryTargets,
  saveSlotTargets,
  settingsTargets,
  summaryTargets,
} from "#ui/mouse-menus";
import { pokedexTargets, starterSelectTargets } from "#ui/mouse-starter";
import type { MouseTarget } from "#ui/mouse-targets";
import { PartyUiHandler } from "#ui/party-ui-handler";
import { PokedexUiHandler } from "#ui/pokedex-ui-handler";
import { RunHistoryUiHandler } from "#ui/run-history-ui-handler";
import { SaveSlotSelectUiHandler } from "#ui/save-slot-select-ui-handler";
import { StarterSelectUiHandler } from "#ui/starter-select-ui-handler";
import { SummaryUiHandler } from "#ui/summary-ui-handler";
import type { UiHandler } from "#ui/ui-handler";

type Screen = [abstract new (...args: never[]) => UiHandler, (handler: never) => MouseTarget[]];

/** 앞에서부터 처음 맞는 종류를 써요 (자식 종류를 부모보다 먼저) */
const SCREENS: readonly Screen[] = [
  // 전투
  [CommandUiHandler, commandTargets],
  [FightUiHandler, fightTargets],
  [PartyUiHandler, partyTargets],
  [ModifierSelectUiHandler, modifierSelectTargets],
  [SummaryUiHandler, summaryTargets],
  // 고르기 목록 (예/아니요 · 타이틀 · 메뉴 · 티어 고르기 등)
  [BaseOptionSelectUiHandler, optionSelectTargets],
  // 시작 · 메뉴
  [StarterSelectUiHandler, starterSelectTargets],
  [SaveSlotSelectUiHandler, saveSlotTargets],
  [BaseSettingsUiHandler, settingsTargets],
  [BaseControlSettingsUiHandler, controlSettingsTargets],
  [EggGachaUiHandler, eggGachaTargets],
  [EggListUiHandler, eggListTargets],
  [EggSummaryUiHandler, eggSummaryTargets],
  [AchvsUiHandler, achievementsTargets],
  [RunHistoryUiHandler, runHistoryTargets],
  [PokedexUiHandler, pokedexTargets],
  // 창(이름 입력 등)은 원래 게임이 버튼을 직접 누르게 해 둬서 따로 만들 게 없어요
  [ModalUiHandler, () => []],
  // 대사 창 · 진화: 칸은 없고, 대사가 멈춰 있을 때 아무 데나 누르면 넘어가요 (오른쪽 클릭 = 진화 멈추기)
  [BattleMessageUiHandler, () => []],
  [EvolutionSceneUiHandler, () => []],
];

export function mouseTargetsFor(mode: UiMode, handler: UiHandler): MouseTarget[] | null {
  if (!handler || mode === UiMode.LOADING) {
    return [];
  }
  for (const [type, fn] of SCREENS) {
    if (handler instanceof type) {
      return (fn as (h: UiHandler) => MouseTarget[])(handler);
    }
  }
  return null;
}
