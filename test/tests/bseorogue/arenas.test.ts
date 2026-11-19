/*
 * SPDX-FileCopyrightText: 2026 SG
 * SPDX-License-Identifier: AGPL-3.0-only
 */

// 11-19 SG "포켓로그방식으로 … 1번으로 하고 20곳 제작": 지역 배경 21곳을 포켓로그 방식(색 띠 배경 · 발판 · 소품)으로
import { readdirSync, readFileSync } from "node:fs";
import { resolve } from "node:path";
import { describe, expect, it } from "vitest";

const ROOT = resolve(__dirname, "../../..");
const ARENAS = resolve(ROOT, "assets/images/arenas");

/** PNG 머리에서 가로 · 세로 · 색 형식 */
function png(path: string): { w: number; h: number; type: number } {
  const buf = readFileSync(path);
  expect(buf.subarray(1, 4).toString("latin1"), path).toBe("PNG");
  return { w: buf.readUInt32BE(16), h: buf.readUInt32BE(20), type: buf[25] };
}

describe("블서로그 지역 배경 (포켓로그 방식)", () => {
  it("바이옴마다 배경 320×180 · 내 발판 · 상대 발판 320×132 (투명)", () => {
    // 바이옴 35곳 (+ 로딩 화면 배경은 따로)
    const biomes = readdirSync(ARENAS)
      .filter(f => f.endsWith("_bg.png") && f !== "loading_bg.png")
      .map(f => f.slice(0, -"_bg.png".length));
    expect(biomes.length).toBeGreaterThanOrEqual(35);
    expect(biomes).toContain("town");
    for (const b of biomes) {
      expect(png(resolve(ARENAS, `${b}_bg.png`)), b).toMatchObject({ w: 320, h: 180 });
      for (const s of ["a", "b"]) {
        expect(png(resolve(ARENAS, `${b}_${s}.png`)), `${b}_${s}`).toMatchObject({ w: 320, h: 132, type: 6 });
      }
    }
  });

  it("21곳 모두 배경 · 소품 · 발판 무늬가 있고, 빠르게 지나가는 느낌 ①(약하게)을 써요", () => {
    const src = readFileSync(resolve(ROOT, "scripts/er-ui/make_arenas.py"), "utf-8");
    const names = [...src.matchAll(/"([a-z]+)": "[가-힣 ]+"/g)].map(m => m[1]);
    expect(names.length).toBe(21);
    const regions = src.slice(src.indexOf("REGIONS = {"), src.indexOf("def decor_fn"));
    for (const n of names) {
      expect(regions, n).toContain(`"${n}": (${n}_bg, ${n}_props,`);
    }
    expect(src).toContain("k_sky=9, k_ground=15, haze_t=0.22, lines=16");
  });

  it("게임 일러스트 배경으로 바꾸던 길은 없어요 (배경은 assets/images/arenas 만)", () => {
    const scene = readFileSync(resolve(ROOT, "src/scene-base.ts"), "utf-8");
    expect(scene).not.toContain("ER_ARENA_FILES");
  });
});
