/*
 * SPDX-FileCopyrightText: 2026 SG
 * SPDX-License-Identifier: AGPL-3.0-only
 */

import { BSEO_ART_SKINS } from "#data/bseorogue/art-manifest";
import { bseoSpeciesId } from "#data/bseorogue/roster";
import { SKILL_MOVES } from "#data/bseorogue/skill-moves";
import { bseoSkillVoiceKey, bseoVoiceFile, playBseoVoice } from "#data/bseorogue/voice";
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
    expect(bseoVoiceFile(bseoSpeciesId(1), "q")).toBe("er/voice/1_q.m4a");
    const noQ = Object.entries(BSEO_VOICES).find(([, keys]) => !keys.includes("q"));
    if (noQ) {
      expect(bseoVoiceFile(bseoSpeciesId(Number(noQ[0])), "q")).toBeNull();
    }
    const silent = [...new Array(92).keys()].slice(1).find(code => !(code in BSEO_VOICES));
    if (silent) {
      expect(bseoVoiceFile(bseoSpeciesId(silent), "select")).toBeNull();
      expect(() => playBseoVoice(bseoSpeciesId(silent), "select")).not.toThrow();
    }
  });

  it("목록(voice-manifest.ts)에 적힌 음성 파일이 모두 있어요", () => {
    for (const [code, keys] of Object.entries(BSEO_VOICES)) {
      for (const key of keys) {
        expect(existsSync(resolve(ASSETS, `er/voice/${code}_${key}.m4a`)), `${code}_${key}.m4a`).toBe(true);
      }
    }
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
