/*
 * SPDX-FileCopyrightText: 2026 SG
 * SPDX-License-Identifier: AGPL-3.0-only
 */

// 11-19 SG 난이도 시트: 티어별 팀 전투 자리 · 마스터즈 팀(관장 자리) · 사기 실험체
import { BSEO } from "#app/bseorogue";
import { isOpWave, teamSlotKind } from "#data/bseorogue/difficulty";
import { MASTERS_TEAMS, OP_EXPERIMENTS, TEAM_SLOTS } from "#data/bseorogue/difficulty-sheet";
import { bseoCharacter } from "#data/bseorogue/roster";
import { TIERS } from "#data/bseorogue/tiers";
import { readFileSync } from "node:fs";
import { resolve } from "node:path";
import { describe, expect, it } from "vitest";

describe("블서로그 난이도 시트", () => {
  it("팀 전투 자리: 아이언~메테오라이트 사기 실험체 · 미스릴 사기 실험체 + 마스터즈 · 데미갓부터 KEL 위주", () => {
    expect(TEAM_SLOTS.length).toBe(TIERS.length);
    for (const row of TEAM_SLOTS) {
      expect(row.length).toBe(BSEO.teamWaves.length);
    }
    for (let t = 0; t <= 6; t++) {
      expect(
        BSEO.teamWaves.every(w => teamSlotKind(w, t) === "op"),
        TIERS[t],
      ).toBe(true);
    }
    const mithril = BSEO.teamWaves.map(w => teamSlotKind(w, 7));
    expect(mithril).toContain("op");
    expect(mithril).toContain("masters");
    for (const t of [8, 9]) {
      expect(
        BSEO.teamWaves.some(w => isOpWave(w, t)),
        TIERS[t],
      ).toBe(false);
      expect(BSEO.teamWaves.filter(w => teamSlotKind(w, t) === "kel").length).toBeGreaterThan(2);
    }
    // 팀 전투 웨이브가 아니면 없음
    expect(teamSlotKind(8, 0)).toBeNull();
    expect(teamSlotKind(10, 0)).toBeNull();
  });

  it("마스터즈 팀: 실험체 2~3명 (마지막이 에이스), 진짜 실험체", () => {
    expect(MASTERS_TEAMS.length).toBeGreaterThanOrEqual(BSEO.leaderWaves.length);
    for (const t of MASTERS_TEAMS) {
      expect(t.members.length, t.name).toBeGreaterThanOrEqual(2);
      expect(t.members.length, t.name).toBeLessThanOrEqual(3);
      for (const c of t.members) {
        expect(bseoCharacter(c), `${t.name} ${c}`).toBeDefined();
      }
    }
    // 사기 실험체 시트도 진짜 실험체만
    for (const o of OP_EXPERIMENTS) {
      expect(bseoCharacter(o.erCode)).toBeDefined();
      expect(o.segments).toBeGreaterThanOrEqual(1);
    }
  });

  it("사기 실험체는 영입할 수 없다는 글자가 있어요", () => {
    const battle = JSON.parse(readFileSync(resolve(__dirname, "../../../locales/ko/battle.json"), "utf-8"));
    expect(battle.bseoNoCatchOp).toContain("사기 실험체");
    const phase = readFileSync(resolve(__dirname, "../../../src/phases/command-phase.ts"), "utf-8");
    expect(phase).toContain("battle:bseoNoCatchOp");
  });
});
