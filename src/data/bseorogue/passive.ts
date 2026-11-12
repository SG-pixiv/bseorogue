/*
 * SPDX-FileCopyrightText: 2026 SG
 * SPDX-License-Identifier: AGPL-3.0-only
 */

import { SHEET_PASSIVES } from "#data/bseorogue/sheet-data";
import { AbilityId } from "#enums/ability-id";
import { toCamelCase } from "#utils/strings";
import i18next from "i18next";

/**
 * 실험체 고유 패시브: 포켓로그 특성(ability)을 하나씩 빌려 쓰고 이름 · 설명만 블서로그 것으로 바꿔요 (스킬과 같은 방식).
 * 어떤 특성을 빌릴지는 시트 '패시브' (scripts/er-sheet/import_sheet.py → sheet-data.ts 의 SHEET_PASSIVES).
 * 한 특성은 한 실험체만 써요 (이름을 바꿔 끼우니까). 초안은 scripts/er-sheet/passive_draft.py
 */

/** 그 실험체가 빌려 쓰는 특성 (시트에 없으면 NONE) */
export function bseoPassiveAbility(erCode: number): AbilityId {
  const key = SHEET_PASSIVES[erCode]?.ability;
  return key ? (AbilityId[key as keyof typeof AbilityId] ?? AbilityId.NONE) : AbilityId.NONE;
}

/** 빌려 쓰는 특성의 이름 · 설명을 패시브 것으로 (글자 묶음 i18n 에 넣어 둬서 언어를 다시 불러와도 그대로) */
export function applyBseoPassiveNames(): void {
  const lng = i18next.resolvedLanguage ?? "ko";
  for (const [code, p] of Object.entries(SHEET_PASSIVES)) {
    const id = bseoPassiveAbility(Number(code));
    if (id === AbilityId.NONE) {
      continue;
    }
    const key = toCamelCase(AbilityId[id]);
    i18next.addResource(lng, "ability", `${key}.name`, p.name);
    i18next.addResource(lng, "ability", `${key}.description`, p.desc);
  }
}
