/*
 * SPDX-FileCopyrightText: 2026 SG
 * SPDX-License-Identifier: AGPL-3.0-only
 */

import { BSEO_CHARACTERS } from "#data/bseorogue/roster";
import { SHEET_SKILLS, type SheetSkill } from "#data/bseorogue/sheet-data";
import { MoveId } from "#enums/move-id";

/**
 * 실험체 스킬 연출: 공용 연출 7개 중 하나 (그림 · 연출은 scripts/er-fx/make_fx.py 가 만들어요)
 * - 변화 스킬: 회복 → 회복, 상대에게 거는 것 → 약화, 그 밖 → 강화
 * - 공격 스킬: 궁극기(R) 중 위력 100 이상 → 폭발, 아니면 무기로 베기 · 타격 · 투사체
 */
export const BSEO_ANIM = {
  SLASH: MoveId.SLASH,
  STRIKE: MoveId.TACKLE,
  SHOT: MoveId.SHADOW_BALL,
  BLAST: MoveId.EXPLOSION,
  HEAL: MoveId.RECOVER,
  BUFF: MoveId.FOCUS_ENERGY,
  DEBUFF: MoveId.TAIL_WHIP,
} as const;

const BLADE = new Set(["단검", "양손검", "쌍검", "레이피어", "도끼", "창"]);
const BLUNT = new Set(["망치", "글러브", "방망이", "톤파", "쌍절곤", "채찍", "VF의수"]);
/** 궁극기(R)가 이 위력 이상이면 폭발 연출 */
const BLAST_POWER = 100;

let byMove: Map<MoveId, MoveId> | null = null;

/** 변화 스킬 연출 (skill-effect.ts 의 bseoSkillTargetsEnemy 와 같은 기준. 기술 파일과 서로 부르지 않게 따로 적어요) */
function statusAnim(sk: SheetSkill): MoveId {
  if (sk.fx.heal) {
    return BSEO_ANIM.HEAL;
  }
  const fx = sk.fx;
  const enemy = !!(fx.status || fx.confuse || fx.flinch || fx.stats?.some(st => !st.self));
  return enemy ? BSEO_ANIM.DEBUFF : BSEO_ANIM.BUFF;
}

/** 공격 스킬 연출 */
function attackAnim(sk: SheetSkill, index: number, weapon: string): MoveId {
  if (index === 3 && sk.power >= BLAST_POWER) {
    return BSEO_ANIM.BLAST;
  }
  if (BLADE.has(weapon)) {
    return BSEO_ANIM.SLASH;
  }
  return BLUNT.has(weapon) ? BSEO_ANIM.STRIKE : BSEO_ANIM.SHOT;
}

function build(): Map<MoveId, MoveId> {
  const out = new Map<MoveId, MoveId>();
  for (const c of BSEO_CHARACTERS) {
    const sheet = SHEET_SKILLS[c.erCode];
    c.skills.forEach((s, i) => {
      const sk = sheet?.[i];
      if (!sk) {
        return;
      }
      out.set(s.move, sk.category === "STATUS" ? statusAnim(sk) : attackAnim(sk, i, c.weapon));
    });
  }
  return out;
}

/** 실험체 스킬이면 쓸 공용 연출의 기술 번호 (연출 파일 battle-anims/<이름>.json), 아니면 null */
export function bseoSkillAnim(moveId: MoveId): MoveId | null {
  byMove ??= build();
  return byMove.get(moveId) ?? null;
}
