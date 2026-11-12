/*
 * SPDX-FileCopyrightText: 2026 SG
 * SPDX-License-Identifier: AGPL-3.0-only
 */

// 실험체 전투 그림 고르기: 도트 → 팬키트 그림 순서
import { pickArtFile } from "#data/bseorogue/placeholder-art";
import { describe, expect, it } from "vitest";

describe("블서로그 실험체 그림 고르기", () => {
  const art = { 1: [0, 1, 2], 2: [0, 1], "wild:BEAR": [0] };

  it("도트가 없으면 팬키트 그림 (원하는 스킨 → 기본 모습)", () => {
    expect(pickArtFile("1", 2, art, {})).toBe("er/char/1_2.png");
    expect(pickArtFile("2", 5, art, {})).toBe("er/char/2_0.png");
    expect(pickArtFile("wild:BEAR", 0, art, {})).toBe("er/char/wild_BEAR_0.png");
    expect(pickArtFile("3", 0, art, {})).toBeNull();
  });

  it("도트가 있으면 도트가 먼저 (그 실험체는 원하는 스킨 도트가 없어도 도트 기본 모습)", () => {
    const dots = { 1: [0, 1] };
    expect(pickArtFile("1", 1, art, dots)).toBe("er/dot/1_1.png");
    expect(pickArtFile("1", 2, art, dots)).toBe("er/dot/1_0.png");
    expect(pickArtFile("2", 1, art, dots)).toBe("er/char/2_1.png");
    expect(pickArtFile("4", 0, art, { 4: [0] })).toBe("er/dot/4_0.png");
  });
});
