/*
 * SPDX-FileCopyrightText: 2026 SG
 * SPDX-License-Identifier: AGPL-3.0-only
 */

import { BSEO } from "#app/bseorogue";
import {
  type BseoAnnounceKey,
  bseoAnnounceAfterWin,
  bseoAnnounceFile,
  bseoAnnounceOnEncounter,
} from "#data/bseorogue/announce";
import { BSEO_ANNOUNCES } from "#data/bseorogue/announce-manifest";
import { BSEO_ANNOUNCE_PREFIX, bseoAnnouncing, stopBseoVoices } from "#data/bseorogue/voice";
// 블서로그 안내 방송 (팬키트 한국어 안내 방송): 어느 웨이브에 무슨 방송이 나오는지, 목록의 파일이 진짜 있는지
import { existsSync } from "node:fs";
import { resolve } from "node:path";
import { describe, expect, it, vi } from "vitest";

const ASSETS = resolve(__dirname, "../../../assets");
const FINAL = BSEO.classicFinalWave;

/** 한 번도 안 쓰러지고 1웨이브부터 이긴다고 할 때 웨이브마다 나오는 방송 */
function schedule(): Record<number, BseoAnnounceKey> {
  const out: Record<number, BseoAnnounceKey> = {};
  for (let wave = 1; wave <= FINAL; wave++) {
    const key = bseoAnnounceAfterWin(wave, wave);
    if (key) {
      out[wave] = key;
    }
  }
  return out;
}

describe("블서로그 안내 방송", () => {
  it("판 시작 · 최종 보스가 나올 때 방송이 나와요 (이어 하기로 불러온 1웨이브는 안 나와요)", () => {
    expect(bseoAnnounceOnEncounter(1, false)).toBe("start");
    expect(bseoAnnounceOnEncounter(1, true)).toBeNull();
    expect(bseoAnnounceOnEncounter(FINAL, false)).toBe("hack");
    expect(bseoAnnounceOnEncounter(FINAL, true)).toBe("hack");
    for (const wave of [2, 10, 25, 49]) {
      expect(bseoAnnounceOnEncounter(wave, false)).toBeNull();
    }
  });

  it("이긴 뒤 방송: 보스 · 남은 웨이브 · 절반 · 연승 (한 웨이브에 하나만)", () => {
    expect(FINAL).toBe(50);
    expect(schedule()).toEqual({
      5: "kill3", // 5연승: 연쇄 처치
      10: "zone1",
      15: "kill5", // 15연승: 섬을 지배
      20: "zone2",
      25: "kill7", // 판의 절반
      30: "zone3",
      35: "kill8", // 35연승: 전설이 탄생
      40: "left10",
      45: "left5",
      47: "left3",
      48: "left2",
      49: "safe_off",
    });
    // 마지막 웨이브는 판 끝 방송(승리)이라 여기선 없어요
    expect(bseoAnnounceAfterWin(FINAL, FINAL)).toBeNull();
  });

  it("쓰러져서 연승이 끊기면 연승 방송은 다시 5연승부터", () => {
    expect(bseoAnnounceAfterWin(7, 5)).toBe("kill3");
    expect(bseoAnnounceAfterWin(7, 6)).toBeNull();
    expect(bseoAnnounceAfterWin(23, 15)).toBe("kill5");
    // 보스 · 남은 웨이브 방송이 먼저예요
    expect(bseoAnnounceAfterWin(10, 5)).toBe("zone1");
    expect(bseoAnnounceAfterWin(45, 35)).toBe("left5");
  });

  it("방송이 나오는 동안은 실험체 대사를 새로 틀지 않고, 대사를 끊을 때 방송은 안 끊어요", () => {
    const sound = (key: string, isPlaying = true) => ({ key, isPlaying, stop: vi.fn(), destroy: vi.fn() });
    const ann = sound(`${BSEO_ANNOUNCE_PREFIX}start_0`);
    const voice = sound("se/bseo_1_q_0");
    expect(bseoAnnouncing([voice])).toBe(false);
    expect(bseoAnnouncing([voice, ann])).toBe(true);
    expect(bseoAnnouncing([sound(`${BSEO_ANNOUNCE_PREFIX}win_0`, false)])).toBe(false);
    expect(stopBseoVoices([voice, ann])).toBe(1);
    expect(ann.stop).not.toHaveBeenCalled();
  });

  it("게임에서 쓰는 방송은 목록에 있고, 목록(announce-manifest.ts)에 적힌 파일이 모두 있어요", () => {
    const used = new Set<BseoAnnounceKey>([...Object.values(schedule()), "start", "hack", "win", "dead", "supply"]);
    for (const key of used) {
      expect(BSEO_ANNOUNCES[key], key).toBeGreaterThan(0);
    }
    let total = 0;
    for (const [key, count] of Object.entries(BSEO_ANNOUNCES) as [BseoAnnounceKey, number][]) {
      for (let i = 0; i < count; i++) {
        const file = bseoAnnounceFile(key, i);
        expect(file).toBe(`er/announce/${key}_${i}.m4a`);
        expect(existsSync(resolve(ASSETS, file!)), file!).toBe(true);
        total++;
      }
      expect(bseoAnnounceFile(key, count)).toBeNull();
    }
    expect(total).toBe(57);
  });
});
