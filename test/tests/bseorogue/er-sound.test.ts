/*
 * SPDX-FileCopyrightText: 2026 SG
 * SPDX-License-Identifier: AGPL-3.0-only
 */

import { BSEO } from "#app/bseorogue";
import { ER_BGM_FILES, ER_BGM_LOOP, ER_SKILL_SFX, ER_SOUND_FILES } from "#data/bseorogue/er-sound-manifest";
import { createLeaderTrainer } from "#data/bseorogue/leaders";
import { REGION_ROLES } from "#data/bseorogue/regions";
import { bseoSpeciesId } from "#data/bseorogue/roster";
import { SKILL_MOVES } from "#data/bseorogue/skill-moves";
import { bseoSkillSfxFile, bseoSkillSfxKey } from "#data/bseorogue/skill-sfx";
import type { BiomeId } from "#enums/biome-id";
import { MoveId } from "#enums/move-id";
import { getBiomeKey } from "#field/arena";
// 블서로그 이터널 리턴 게임 소리 (scripts/sound/build_er_sound.py): 목록의 파일이 진짜 있는지 · 자리마다 들어갔는지
import { existsSync, readFileSync } from "node:fs";
import { resolve } from "node:path";
import { describe, expect, it } from "vitest";

const ASSETS = resolve(__dirname, "../../../assets");

describe("블서로그 이터널 리턴 소리", () => {
  it("효과음 · BGM 목록의 파일이 다 있어요 (assets/er 아래)", () => {
    const files = [...Object.values(ER_SOUND_FILES), ...Object.values(ER_BGM_FILES)];
    expect(files.length).toBeGreaterThan(40);
    for (const file of files) {
      expect(file.startsWith("er/"), file).toBe(true);
      expect(existsSync(resolve(ASSETS, file)), file).toBe(true);
    }
  });

  it("게임이 처음에 받는 효과음 · 버튼 소리 · 스킬 연출 7종이 다 게임 소리예요", () => {
    const loading = readFileSync(resolve(__dirname, "../../../src/loading-scene.ts"), "utf-8");
    const keys = [...loading.matchAll(/\.loadSe\("([^"]+)"(?:, "(ui|se)")?\)/g)].map(
      m => `${m[2] ?? "se"}/${m[1]}.wav`,
    );
    expect(keys.length).toBeGreaterThan(30);
    for (const key of keys) {
      expect(ER_SOUND_FILES[key], key).toBeDefined();
    }
    for (const anim of ["slash", "strike", "shot", "blast", "heal", "buff", "debuff"]) {
      expect(ER_SOUND_FILES[`battle_anims/bseo-${anim}.wav`]).toBeDefined();
    }
  });

  it("지역 21곳(바이옴 35개)마다 지역 곡이 있고, 지역 곡이 끝난 뒤부터 반복해요", () => {
    const biomes = Object.keys(REGION_ROLES).map(id => getBiomeKey(Number(id) as BiomeId));
    expect(biomes.length).toBe(35);
    for (const key of biomes) {
      expect(ER_BGM_FILES[key], key).toMatch(/^er\/audio\/bgm\/area_/);
      expect(ER_BGM_LOOP[key], key).toBeGreaterThan(5);
    }
    // 같은 지역은 같은 곡
    expect(ER_BGM_FILES.town).toBe(ER_BGM_FILES.slum);
  });

  it("타이틀 · 메뉴 · 전투 · 관장 · 최종 보스 · 회복 · 진화 곡이 있어요", () => {
    for (const key of [
      "title",
      "menu",
      "battle_wild",
      "battle_trainer",
      "bseo_leader",
      "bseo_final",
      "bw/heal",
      "bw/evolution",
      "bw/evolution_fanfare",
      "bw/victory_trainer",
    ]) {
      expect(ER_BGM_FILES[key], key).toBeDefined();
    }
    // 포켓로그 타이틀 곡의 반복점(46.5초)을 쓰지 않아요
    expect(ER_BGM_LOOP.title).toBeUndefined();
  });

  it("관장 전투는 관장 곡을 틀어요", () => {
    const trainer = createLeaderTrainer(BSEO.leaderWaves[0]);
    expect(trainer.config.battleBgm).toBe("bseo_leader");
    expect(trainer.config.mixedBattleBgm).toBe("bseo_leader");
  });

  it("실험체 스킬 Q W E R 효과음: 자기 스킬만, 파일이 진짜 있어요", () => {
    const codes = Object.keys(ER_SKILL_SFX).map(Number);
    expect(codes.length).toBeGreaterThan(80);
    for (const code of codes) {
      const moves = SKILL_MOVES[code];
      "qwer".split("").forEach((key, i) => {
        const file = bseoSkillSfxFile(bseoSpeciesId(code), moves[i]);
        if (ER_SKILL_SFX[code].includes(key)) {
          expect(file).toBe(`er/sfx/${code}_${key}.m4a`);
          expect(existsSync(resolve(ASSETS, file!)), file!).toBe(true);
        } else {
          expect(file).toBeNull();
        }
      });
    }
    // 아야(2)의 Q · 재키 스킬을 아야가 쓰거나 다른 기술이면 없음
    expect(bseoSkillSfxFile(bseoSpeciesId(2), SKILL_MOVES[2][0])).toBe("er/sfx/2_q.m4a");
    expect(bseoSkillSfxFile(bseoSpeciesId(2), SKILL_MOVES[1][1])).toBeNull();
    expect(bseoSkillSfxFile(bseoSpeciesId(2), MoveId.SPLASH)).toBeNull();
    // 소리 열쇠는 필드 크기(battle_anims)를 따르고, 음성 끊기(se/bseo_)와 안 겹쳐요
    expect(bseoSkillSfxKey("er/sfx/2_q.m4a")).toBe("battle_anims/bseo_sfx_2_q");
  });
});
