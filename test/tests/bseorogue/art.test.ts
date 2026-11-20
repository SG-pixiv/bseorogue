/*
 * SPDX-FileCopyrightText: 2026 SG
 * SPDX-License-Identifier: AGPL-3.0-only
 */

// 실험체 전투 그림 고르기: 도트 → 팬키트 그림 순서
import { FOOT_Y, layoutArt, measureArt, pickArtFile } from "#data/bseorogue/placeholder-art";
import { describe, expect, it } from "vitest";

/** 가짜 그림: w×h, 보이는 픽셀 칸 목록 */
function rgba(w: number, h: number, solid: (x: number, y: number) => boolean): Uint8ClampedArray {
  const data = new Uint8ClampedArray(w * h * 4);
  for (let y = 0; y < h; y++) {
    for (let x = 0; x < w; x++) {
      if (solid(x, y)) {
        data[(y * w + x) * 4 + 3] = 255;
      }
    }
  }
  return data;
}

describe("블서로그 팬키트 그림 놓기 (11-20 크기 · 발 위치 · 그림자)", () => {
  it("보이는 부분 상자와 발 쪽 좌우 끝을 재요 (아래 여백 · 무기는 빼고 발만)", () => {
    // 20×40 그림: 몸 x 8~11, y 2~35 (아래 4줄 여백), 오른쪽으로 무기 x 12~19, y 10~12
    const data = rgba(20, 40, (x, y) => (x >= 8 && x <= 11 && y >= 2 && y <= 35) || (x >= 12 && y >= 10 && y <= 12));
    const box = measureArt(data, 20, 40);
    expect(box).toEqual({ x: 8, y: 2, w: 12, h: 34, footL: 8, footR: 11 });
  });

  it("흐린 픽셀(알파 16 이하)은 그림으로 안 봐요 · 빈 그림은 전체", () => {
    const data = rgba(4, 4, () => false);
    data[3] = 10;
    expect(measureArt(data, 4, 4)).toEqual({ x: 0, y: 0, w: 4, h: 4, footL: 0, footR: 3 });
  });

  it("키는 앞 80 · 뒤 90 으로 줄이고, 발은 같은 줄, 발 가운데가 칸 가운데", () => {
    const box = { x: 0, y: 0, w: 40, h: 96, footL: 10, footR: 19 };
    const front = layoutArt(box, false);
    expect(front.h).toBe(80);
    expect(front.dy + front.h).toBe(FOOT_Y);
    expect(Math.abs(front.shadowX - 48)).toBeLessThanOrEqual(1);
    const back = layoutArt(box, true);
    expect(back.h).toBe(90);
    expect(back.dy + back.h).toBe(FOOT_Y);
  });

  it("작은 그림은 키우지 않고, 넓은 그림은 칸 밖으로 안 나가요", () => {
    const small = layoutArt({ x: 0, y: 0, w: 20, h: 44, footL: 5, footR: 14 }, false);
    expect(small.h).toBe(44);
    const wide = layoutArt({ x: 0, y: 0, w: 150, h: 60, footL: 0, footR: 30 }, false);
    expect(wide.w).toBeLessThanOrEqual(94);
    expect(wide.dx).toBeGreaterThanOrEqual(0);
    expect(wide.dx + wide.w).toBeLessThanOrEqual(96);
  });

  it("그림자 폭은 발 폭 + 10 (20 ~ 64)", () => {
    expect(layoutArt({ x: 0, y: 0, w: 40, h: 80, footL: 18, footR: 21 }, false).shadowW).toBe(20);
    expect(layoutArt({ x: 0, y: 0, w: 90, h: 80, footL: 0, footR: 89 }, false).shadowW).toBe(64);
  });
});

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
