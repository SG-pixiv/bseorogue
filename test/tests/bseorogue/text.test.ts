/*
 * SPDX-FileCopyrightText: 2026 SG
 * SPDX-License-Identifier: AGPL-3.0-only
 */

import { getNatureStatMultiplier } from "#data/nature";
import { Nature } from "#enums/nature";
import { EFFECTIVE_STATS, Stat } from "#enums/stat";
import { getEnumValues } from "#utils/enums";
import { toCamelCase } from "#utils/strings";
// 블서로그 글: 포켓몬 느낌 말(성격 · 만났다 · 가랏 · 놓아준다 …)을 이리 느낌으로 바꾼 것이 그대로 있는지 (11-18 SG)
import { readFileSync } from "node:fs";
import { resolve } from "node:path";
import { describe, expect, it } from "vitest";

const KO = resolve(__dirname, "../../../locales/ko");
const read = (name: string) => JSON.parse(readFileSync(resolve(KO, `${name}.json`), "utf8"));
const text = (name: string) => readFileSync(resolve(KO, `${name}.json`), "utf8");

const SHORT: Record<number, string> = {
  [Stat.ATK]: "atkShortened",
  [Stat.DEF]: "defShortened",
  [Stat.SPATK]: "spatkShortened",
  [Stat.SPDEF]: "spdefShortened",
  [Stat.SPD]: "spdShortened",
};

describe("블서로그 글 (이리 느낌)", () => {
  it("성향 이름이 오르는 능력 ↑ · 내리는 능력 ↓ 그대로예요 (보정 없는 5개는 서로 다른 이름)", () => {
    const names = read("nature");
    const stat = read("pokemon-info").stat;
    const neutral = new Set<string>();
    for (const nature of getEnumValues(Nature)) {
      const name: string = names[toCamelCase(Nature[nature])];
      const up = EFFECTIVE_STATS.find(s => getNatureStatMultiplier(nature, s) > 1);
      const down = EFFECTIVE_STATS.find(s => getNatureStatMultiplier(nature, s) < 1);
      if (up != null && down != null) {
        expect(name, Nature[nature]).toBe(`${stat[SHORT[up]]}↑ ${stat[SHORT[down]]}↓`);
      } else {
        expect(name, Nature[nature]).not.toMatch(/[↑↓]/);
        neutral.add(name);
      }
    }
    expect(neutral.size).toBe(5);
  });

  it("화면에 보이는 글에 '성격' · '만났다' · '가랏' · '놓아' 가 없어요", () => {
    for (const name of [
      "nature",
      "pokemon-summary",
      "starter-select-ui-handler",
      "pokedex-ui-handler",
      "pokemon-info-container",
      "settings",
      "battle",
      "party-ui-handler",
    ]) {
      const t = text(name);
      for (const word of ["성격", "만났다", "만난 것", "가랏", "놓아", "돌아와,", "야생 {{"]) {
        expect(t.includes(word), `${name}: ${word}`).toBe(false);
      }
    }
    const summary = read("pokemon-summary");
    expect(summary.metFragment.normal).toContain("합류했다");
    expect(read("battle").playerGo).toBe("나가자, {{pokemonName}}!");
  });
});
