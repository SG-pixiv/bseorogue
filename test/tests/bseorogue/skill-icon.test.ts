/*
 * SPDX-FileCopyrightText: 2026 SG
 * SPDX-License-Identifier: AGPL-3.0-only
 */

import { bseoSkillIconFile, bseoSkillIconName, bseoSkillIconNames } from "#data/bseorogue/skill-icon";
import { BSEO_SKILL_ICONS } from "#data/bseorogue/skill-icon-manifest";
import { SKILL_MOVES } from "#data/bseorogue/skill-moves";
import { MoveId } from "#enums/move-id";
// 블서로그 스킬 아이콘: 스킬 Q W E R → 그 실험체 아이콘, 목록에 적힌 파일이 진짜 있는지
import { existsSync } from "node:fs";
import { resolve } from "node:path";
import { describe, expect, it } from "vitest";

const ASSETS = resolve(__dirname, "../../../assets");

describe("블서로그 스킬 아이콘", () => {
  it("실험체 스킬 Q W E R 순서대로 아이콘이 정해져요", () => {
    const [q, w, e, r] = SKILL_MOVES[1]; // 재키
    expect([q, w, e, r].map(m => bseoSkillIconName(m))).toEqual(["1_q", "1_w", "1_e", "1_r"]);
    expect(bseoSkillIconName(SKILL_MOVES[72][3])).toBe("72_r"); // 카티야 R
    // 실험체 스킬이 아닌 기술은 아이콘 없음
    expect(bseoSkillIconName(MoveId.SPLASH)).toBeNull();
  });

  it("스킬이 있는 실험체는 전원 Q W E R 아이콘이 있어요", () => {
    const missing = Object.keys(SKILL_MOVES).filter(code => {
      const have = BSEO_SKILL_ICONS[Number(code)] ?? "";
      return ![..."qwer"].every(k => have.includes(k));
    });
    expect(missing).toEqual([]);
  });

  it("스킬마다 아이콘이 서로 달라요 (한 기술 = 한 실험체)", () => {
    const names = Object.values(SKILL_MOVES)
      .flat()
      .map(m => bseoSkillIconName(m));
    expect(new Set(names).size).toBe(names.length);
  });

  it("목록에 적힌 아이콘 파일이 다 있어요 (패시브 포함)", () => {
    for (const code of Object.keys(BSEO_SKILL_ICONS)) {
      for (const name of bseoSkillIconNames(Number(code))) {
        const file = bseoSkillIconFile(name);
        expect(existsSync(resolve(ASSETS, file)), file).toBe(true);
      }
    }
  });
});
