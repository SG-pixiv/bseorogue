/*
 * SPDX-FileCopyrightText: 2026 SG
 * SPDX-License-Identifier: AGPL-3.0-only
 */

// 잠재력: 개체값 6개 → 등급 한 줄
import { bseoPotentialGrade, bseoPotentialImproves } from "#data/bseorogue/potential";
import { describe, expect, it } from "vitest";

describe("블서로그 잠재력 등급", () => {
  it("합이 클수록 높은 등급 (S 168 · A 140 · B 103 · C 66 이상)", () => {
    expect(bseoPotentialGrade([31, 31, 31, 31, 31, 31])).toBe("S");
    expect(bseoPotentialGrade([28, 28, 28, 28, 28, 28])).toBe("S");
    expect(bseoPotentialGrade([27, 28, 28, 28, 28, 28])).toBe("A");
    expect(bseoPotentialGrade([24, 24, 24, 24, 24, 20])).toBe("A");
    expect(bseoPotentialGrade([20, 20, 20, 20, 20, 20])).toBe("B");
    expect(bseoPotentialGrade([15, 15, 15, 15, 15, 15])).toBe("C");
    expect(bseoPotentialGrade([10, 10, 10, 10, 10, 10])).toBe("D");
    expect(bseoPotentialGrade([0, 0, 0, 0, 0, 0])).toBe("D");
  });

  it("능력 하나라도 기록보다 높으면 오름", () => {
    expect(bseoPotentialImproves([10, 10, 10, 10, 10, 11], [10, 10, 10, 10, 10, 10])).toBe(true);
    expect(bseoPotentialImproves([10, 10, 10, 10, 10, 10], [10, 10, 10, 10, 10, 10])).toBe(false);
    expect(bseoPotentialImproves([5, 5, 5, 5, 5, 5], [10, 10, 10, 10, 10, 10])).toBe(false);
  });
});
