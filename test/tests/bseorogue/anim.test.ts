/*
 * SPDX-FileCopyrightText: 2026 SG
 * SPDX-License-Identifier: AGPL-3.0-only
 */

import { BSEO_CHARACTERS } from "#data/bseorogue/roster";
import { SHEET_SKILLS } from "#data/bseorogue/sheet-data";
import { BSEO_ANIM, bseoSkillAnim } from "#data/bseorogue/skill-anim";
import { SKILL_MOVES } from "#data/bseorogue/skill-moves";
import { MoveId } from "#enums/move-id";
import { toKebabCase } from "#utils/strings";
// 기술 연출: 실험체 스킬마다 공용 연출 7개 중 하나, 연출 파일 · 그림이 다 있는지
import { existsSync, readFileSync } from "node:fs";
import { describe, expect, it } from "vitest";

describe("블서로그 기술 연출", () => {
  it("공용 연출 7개: 연출 파일과 그림이 있고 모든 칸이 그림 안에 있어요", () => {
    for (const id of Object.values(BSEO_ANIM)) {
      const file = `assets/battle-anims/${toKebabCase(MoveId[id])}.json`;
      expect(existsSync(file), file).toBe(true);
      const anim = JSON.parse(readFileSync(file, "utf-8"));
      expect(anim.graphic).toMatch(/^bseo-/);
      expect(existsSync(`assets/images/battle_anims/${anim.graphic}.png`)).toBe(true);
      for (const frame of anim.frames) {
        // 매 프레임 내 실험체 · 상대 칸이 있어야 연출 중에 안 사라져요
        expect(frame.filter((f: { target: number }) => f.target === 0)).toHaveLength(1);
        expect(frame.filter((f: { target: number }) => f.target === 1)).toHaveLength(1);
      }
    }
  });

  it("공용 연출 7개마다 소리가 있고, 그 소리는 임시(무음) 파일이 아니에요 (scripts/sound/make_sfx.py)", () => {
    const placeholders = new Set<string>(JSON.parse(readFileSync("assets/.placeholders.json", "utf-8")));
    for (const id of Object.values(BSEO_ANIM)) {
      const anim = JSON.parse(readFileSync(`assets/battle-anims/${toKebabCase(MoveId[id])}.json`, "utf-8"));
      const sounds = Object.values(
        anim.frameTimedEvents as Record<string, { eventType: string; resourceName: string }[]>,
      )
        .flat()
        .filter(e => e.eventType === "AnimTimedSoundEvent");
      expect(sounds, MoveId[id]).toHaveLength(1);
      const rel = `audio/battle_anims/${sounds[0].resourceName}`;
      expect(existsSync(`assets/${rel}`), rel).toBe(true);
      expect(placeholders.has(rel), rel).toBe(false);
    }
  });

  it("게임이 쓰는 효과음 · 버튼 소리가 임시(무음) 파일이 아니에요", () => {
    const placeholders = new Set<string>(JSON.parse(readFileSync("assets/.placeholders.json", "utf-8")));
    const loading = readFileSync("src/loading-scene.ts", "utf-8");
    const keys = [...loading.matchAll(/loadSe\("([a-z_0-9]+)"(?:, "(ui|se)")?/g)].map(
      m => `audio/${m[2] ?? "se"}/${m[1]}.wav`,
    );
    expect(keys.length).toBeGreaterThan(30);
    for (const rel of keys) {
      expect(existsSync(`assets/${rel}`), rel).toBe(true);
      expect(placeholders.has(rel), rel).toBe(false);
    }
  });

  it("모든 실험체 스킬이 공용 연출 중 하나", () => {
    const anims = new Set<MoveId>(Object.values(BSEO_ANIM));
    for (const moves of Object.values(SKILL_MOVES)) {
      for (const m of moves) {
        expect(anims.has(bseoSkillAnim(m) as MoveId), MoveId[m]).toBe(true);
      }
    }
    expect(bseoSkillAnim(MoveId.SPLASH)).toBeNull();
  });

  it("무기 · 분류로 고르기 (유키 양손검 → 베기, 일레븐 망치 → 타격, 나딘 석궁 → 투사체, 자기 강화 스킬 → 강화)", () => {
    const skill = (code: number, i: number) => bseoSkillAnim(SKILL_MOVES[code][i]);
    const weapon = (code: number) => BSEO_CHARACTERS.find(c => c.erCode === code)?.weapon;
    expect(weapon(11)).toBe("양손검");
    expect(skill(11, 0)).toBe(BSEO_ANIM.SLASH);
    expect(weapon(30)).toBe("망치");
    expect(skill(30, 0)).toBe(BSEO_ANIM.STRIKE);
    expect(weapon(6)).toBe("석궁");
    expect(skill(6, 0)).toBe(BSEO_ANIM.SHOT);
    // 자기 강화 변화 스킬 하나 (시트 값이 바뀌어도 되게 시트에서 찾아요): 나딘 E
    const buff = Object.entries(SHEET_SKILLS).flatMap(([code, list]) =>
      list
        .map((sk, i) => ({ code: Number(code), i, sk }))
        .filter(x => x.sk.category === "STATUS" && !x.sk.fx.heal && x.sk.fx.stats?.every(st => st.self)),
    )[0];
    expect(buff).toBeDefined();
    expect(skill(buff.code, buff.i)).toBe(BSEO_ANIM.BUFF);
    if (SHEET_SKILLS[1][3].power >= 100) {
      expect(skill(1, 3)).toBe(BSEO_ANIM.BLAST);
    }
  });
});
