/*
 * SPDX-FileCopyrightText: 2026 SG
 * SPDX-License-Identifier: AGPL-3.0-only
 */

// 11-19 SG "게임 파일 안의 지역 그림, 일러스트 찾아서 넣어줘": 이터널 리턴 스토리 모드 배경 그림 → 전투 배경
import { ER_ARENA_FILES } from "#data/bseorogue/er-arena-manifest";
import { readFileSync } from "node:fs";
import { resolve } from "node:path";
import { describe, expect, it } from "vitest";

const ASSETS = resolve(__dirname, "../../../assets");

/** PNG 머리에서 가로 · 세로 */
function pngSize(path: string): [number, number] {
  const buf = readFileSync(path);
  expect(buf.subarray(1, 4).toString("latin1"), path).toBe("PNG");
  return [buf.readUInt32BE(16), buf.readUInt32BE(20)];
}

describe("블서로그 지역 배경 (게임 일러스트)", () => {
  it("게임 일러스트 배경 파일이 다 있고 320×180, 코드 그림 예비도 그대로 있어요", () => {
    const keys = Object.keys(ER_ARENA_FILES);
    expect(keys.length).toBeGreaterThanOrEqual(9);
    for (const [key, file] of Object.entries(ER_ARENA_FILES)) {
      expect(key, key).toMatch(/_bg$/);
      expect(file, key).toMatch(/^er\/arena\/[a-z]+_bg\.png$/);
      expect(pngSize(resolve(ASSETS, file)), file).toEqual([320, 180]);
      expect(pngSize(resolve(ASSETS, "images/arenas", `${key}.png`)), key).toEqual([320, 180]);
    }
    // 시작 지역(town = 골목길)도 게임 일러스트
    expect(ER_ARENA_FILES.town_bg).toBe("er/arena/alley_bg.png");
  });

  it("배경 그림은 어느 게임 그림에서 왔는지 출처가 있어요", () => {
    const sources = JSON.parse(readFileSync(resolve(ASSETS, "er/area-illust-sources.json"), "utf-8"));
    for (const name of ["alley_day", "cemetery_day", "chapel_day", "factory_day", "forest_day", "harbor_day"]) {
      expect(sources[name]?.game, name).toMatch(/^Img_BG_Lumia_/);
    }
  });

  it("배경을 받을 때 게임 일러스트 파일을 먼저 써요 (scene-base.ts)", () => {
    const src = readFileSync(resolve(__dirname, "../../../src/scene-base.ts"), "utf-8");
    expect(src).toContain('folder === "arenas" ? ER_ARENA_FILES[key]');
  });
});
