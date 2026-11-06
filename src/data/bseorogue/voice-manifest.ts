/*
 * SPDX-FileCopyrightText: 2026 SG
 * SPDX-License-Identifier: AGPL-3.0-only
 */

// 이 파일은 scripts/fankit/build_voice.py 가 만들어요. 직접 고치지 마세요.
// 음성 파일(assets/er/voice/)은 님블뉴런 팬키트에서 가져와 줄인 것이에요.

/** 스킬 Q · W · E · R (skill-moves.ts 순서) · 등장 대사 */
export type BseoVoiceKey = "q" | "w" | "e" | "r" | "select";

/** 음성이 있는 실험체 (ER 번호 → 있는 음성). 파일: er/voice/<ER번호>_<키>.m4a */
export const BSEO_VOICES: Readonly<Record<number, readonly BseoVoiceKey[]>> = {
  1: ["q", "w", "e", "r", "select"],
  2: ["q", "w", "e", "r", "select"],
  3: ["select"],
  4: ["q", "w", "e", "r", "select"],
  9: ["q", "w", "e", "r", "select"],
  20: ["w", "e", "r", "select"],
  25: ["q", "w", "e", "r", "select"],
  42: ["q", "w", "e", "r", "select"],
  46: ["w", "e", "r", "select"],
  56: ["q", "w", "e", "r", "select"],
  57: ["q", "w", "e", "r", "select"],
  73: ["q", "w", "e", "r", "select"],
  83: ["q", "w", "e", "r", "select"],
  88: ["q", "w", "e", "r", "select"],
};

/** 음성 언어 (ko 한국어 · en 영어 · ja 일본어) */
export const BSEO_VOICE_LANG: Readonly<Record<number, "ko" | "en" | "ja">> = {
  1: "ko",
  2: "en",
  3: "ja",
  4: "en",
  9: "ko",
  20: "ja",
  25: "ko",
  42: "ko",
  46: "ko",
  56: "en",
  57: "en",
  73: "en",
  83: "ko",
  88: "ja",
};
