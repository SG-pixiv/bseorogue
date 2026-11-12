/*
 * SPDX-FileCopyrightText: 2026 SG
 * SPDX-License-Identifier: AGPL-3.0-only
 */

import type { SheetSkill, SheetSkillEffect, SheetStat } from "#data/bseorogue/sheet-data";
import { MoveCategory } from "#enums/move-category";
import { MoveTarget } from "#enums/move-target";
import { type BattleStat, Stat } from "#enums/stat";
import { StatusEffect } from "#enums/status-effect";
import {
  ConfuseAttr,
  FlinchAttr,
  HealAttr,
  HighCritAttr,
  HitHealAttr,
  type Move,
  RechargeAttr,
  RecoilAttr,
  StatStageChangeAttr,
  StatusEffectAttr,
} from "#moves/move";

/**
 * 실험체 스킬 효과: 시트 효과 칸(sheet-data.ts 의 fx)을 빌려 쓰는 기술에 그대로 붙여요.
 *
 * 빌려 쓰는 포켓로그 기술은 연출(애니메이션) · 분류 틀만 쓰고, 원래 효과 · 쓰는 조건은 모두 지워요.
 * 틀은 scripts/er-sheet/pick_skill_moves.py 가 골라요 (공격 → 공격 기술, 변화 → 변화 기술).
 */

const STAT: Readonly<Record<SheetStat, BattleStat>> = {
  ATK: Stat.ATK,
  DEF: Stat.DEF,
  SPATK: Stat.SPATK,
  SPDEF: Stat.SPDEF,
  SPD: Stat.SPD,
  ACC: Stat.ACC,
  EVA: Stat.EVA,
};

const STATUS: Readonly<Record<NonNullable<SheetSkillEffect["status"]>, StatusEffect>> = {
  BURN: StatusEffect.BURN,
  PARALYSIS: StatusEffect.PARALYSIS,
  POISON: StatusEffect.POISON,
  TOXIC: StatusEffect.TOXIC,
  SLEEP: StatusEffect.SLEEP,
  FREEZE: StatusEffect.FREEZE,
};

/** 원래 기술의 효과 · 조건 칸 (포켓로그 Move 안쪽 칸이라 이름으로 꺼내요) */
interface MoveInsides {
  attrs: unknown[];
  conditions: unknown[];
  conditionsSeq2: unknown[];
  conditionsSeq3: unknown[];
  restrictions: unknown[];
}

/** 상대에게 거는 효과가 있으면 상대에게, 아니면 자기에게 쓰는 변화 스킬 */
export function bseoSkillTargetsEnemy(fx: SheetSkillEffect): boolean {
  return !!(fx.status || fx.confuse || fx.flinch || fx.stats?.some(s => !s.self));
}

export function applyBseoSkillEffect(move: Move, sheet: SheetSkill): void {
  const fx = sheet.fx;
  const inside = move as unknown as MoveInsides;
  inside.attrs.length = 0;
  inside.conditions.length = 0;
  inside.conditionsSeq2.length = 0;
  inside.conditionsSeq3.length = 0;
  inside.restrictions.length = 0;
  move.chance = fx.chance;
  if (move.category === MoveCategory.STATUS) {
    move.moveTarget = bseoSkillTargetsEnemy(fx) ? MoveTarget.NEAR_OTHER : MoveTarget.USER;
  }

  if (fx.status) {
    move.attr(StatusEffectAttr, STATUS[fx.status]);
  }
  if (fx.confuse) {
    move.attr(ConfuseAttr);
  }
  if (fx.flinch) {
    move.attr(FlinchAttr);
  }
  for (const s of fx.stats ?? []) {
    // 능력 변화 확률은 따로 (상태이상 확률과 섞이지 않게)
    move.attr(
      StatStageChangeAttr,
      s.stats.map(k => STAT[k]),
      s.stages,
      s.self,
      { effectChanceOverride: s.chance },
    );
  }
  if (fx.highCrit) {
    move.attr(HighCritAttr);
  }
  if (fx.drain) {
    move.attr(HitHealAttr, fx.drain);
  }
  if (fx.heal) {
    // 공격 스킬의 회복은 체력이 가득이어도 공격은 해요
    move.attr(HealAttr, fx.heal, false, true, move.category === MoveCategory.STATUS);
  }
  if (fx.recoil) {
    move.attr(RecoilAttr, false, fx.recoil);
  }
  if (fx.recharge) {
    move.attr(RechargeAttr);
  }
}
