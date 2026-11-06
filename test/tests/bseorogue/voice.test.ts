/*
 * SPDX-FileCopyrightText: 2026 SG
 * SPDX-License-Identifier: AGPL-3.0-only
 */

import { BSEO_ART_SKINS } from "#data/bseorogue/art-manifest";
import { bseoSpeciesId } from "#data/bseorogue/roster";
import { SKILL_MOVES } from "#data/bseorogue/skill-moves";
import { bseoSkillVoiceKey, bseoVoiceFile, nextBseoVoiceIndex, playBseoVoice } from "#data/bseorogue/voice";
import { BSEO_VOICES } from "#data/bseorogue/voice-manifest";
import { MoveId } from "#enums/move-id";
// 블서로그 실험체 음성 · 그림: 스킬 Q W E R → 스킬 음성, 목록에 적힌 파일이 진짜 있는지
import { existsSync } from "node:fs";
import { resolve } from "node:path";
import { describe, expect, it } from "vitest";

const ASSETS = resolve(__dirname, "../../../assets");

describe("블서로그 실험체 음성", () => {
  it("자기 스킬 Q W E R 순서대로 음성 키가 정해져요 (스킨 진화해도 같아요)", () => {
    const [q, w, e, r] = SKILL_MOVES[1]; // 재키
    for (const stage of [0, 1, 2]) {
      const id = bseoSpeciesId(1, stage);
      expect([q, w, e, r].map(m => bseoSkillVoiceKey(id, m))).toEqual(["q", "w", "e", "r"]);
    }
    // 다른 실험체의 스킬 · 없는 기술은 음성 없음
    expect(bseoSkillVoiceKey(bseoSpeciesId(1), SKILL_MOVES[2][0])).toBeNull();
    expect(bseoSkillVoiceKey(bseoSpeciesId(1), MoveId.SPLASH)).toBeNull();
  });

  it("음성 파일이 없는 키 · 실험체는 조용히 넘어가요", () => {
    expect(bseoVoiceFile(bseoSpeciesId(1), "q")).toBe("er/voice/1_q_0.m4a");
    expect(bseoVoiceFile(bseoSpeciesId(1), "die", 2)).toBe("er/voice/1_die_2.m4a");
    expect(bseoVoiceFile(bseoSpeciesId(1), "q", 3)).toBeNull(); // 대사는 키마다 최대 3개
    const noR = Object.entries(BSEO_VOICES).find(([, counts]) => (counts.r ?? 0) < 3);
    if (noR) {
      expect(bseoVoiceFile(bseoSpeciesId(Number(noR[0])), "r", 2)).toBeNull();
    }
    const silent = [...new Array(92).keys()].slice(1).find(code => !(code in BSEO_VOICES));
    if (silent) {
      expect(bseoVoiceFile(bseoSpeciesId(silent), "select")).toBeNull();
      expect(() => playBseoVoice(bseoSpeciesId(silent), "select")).not.toThrow();
    }
  });

  it("대사가 여러 개면 바로 전 대사는 다시 안 나오고, 결국 모두 나와요", () => {
    for (const count of [2, 3]) {
      const seen = new Set<number>();
      let last: number | undefined;
      for (let i = 0; i < 200; i++) {
        const next = nextBseoVoiceIndex(count, last);
        expect(next).toBeGreaterThanOrEqual(0);
        expect(next).toBeLessThan(count);
        expect(next).not.toBe(last);
        seen.add(next);
        last = next;
      }
      expect(seen.size).toBe(count);
    }
    expect(nextBseoVoiceIndex(1, 0)).toBe(0);
  });

  it("목록(voice-manifest.ts)에 적힌 음성 파일이 모두 있어요 (스킬 · 등장 · 쓰러질 때)", () => {
    let total = 0;
    for (const [code, counts] of Object.entries(BSEO_VOICES)) {
      for (const [key, count] of Object.entries(counts)) {
        expect(count).toBeGreaterThan(0);
        expect(count).toBeLessThanOrEqual(3);
        for (let i = 0; i < (count ?? 0); i++) {
          const file = `er/voice/${code}_${key}_${i}.m4a`;
          expect(existsSync(resolve(ASSETS, file)), file).toBe(true);
          total++;
        }
      }
    }
    expect(total).toBeGreaterThan(0);
  });

  it("목록(art-manifest.ts)에 적힌 전투 그림이 모두 있어요", () => {
    for (const [key, skins] of Object.entries(BSEO_ART_SKINS)) {
      for (const skin of skins) {
        const file = `er/char/${key.replace("wild:", "wild_")}_${skin}.png`;
        expect(existsSync(resolve(ASSETS, file)), file).toBe(true);
      }
    }
  });
});
