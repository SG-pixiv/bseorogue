#!/usr/bin/env node
// SPDX-FileCopyrightText: 2026 SG
// SPDX-License-Identifier: AGPL-3.0-only
//
// fetch.mjs 로 받은 er-data 폴더에서 블서로그에 쓰는 것만 골라 src/data/bseorogue/er-data.ts 를 만들어요.
//   node scripts/er-data/build.mjs <er-data 폴더>
// 만드는 것:
//   src/data/bseorogue/er-data.ts — 실험체 (이름 · 역할군 · 무기 · 20레벨 스탯 · 패시브/Q/W/E/R 이름 · 스킨 이름), 야생동물 · 보스 기본 스탯
//   src/enums/species-id.ts 의 블서로그 실험체 번호 (BSEO_ER 표시 사이) — 실험체마다 기본 · 스킨 진화 1 · 스킨 진화 2

import { readFileSync, writeFileSync } from "node:fs";
import { join } from "node:path";

const dir = process.argv[2];
if (!dir) {
  console.log("사용법: node scripts/er-data/build.mjs <er-data 폴더>");
  process.exit(1);
}
const raw = name => JSON.parse(readFileSync(join(dir, "raw", `${name}.json`), "utf8"));
const l10n = new Map();
for (const line of readFileSync(join(dir, "l10n-Korean.txt"), "utf8").split(/\r?\n/)) {
  const i = line.indexOf("┃");
  if (i > 0) {
    l10n.set(line.slice(0, i), line.slice(i + 1).trim());
  }
}
const fetchedAt = JSON.parse(readFileSync(join(dir, "manifest.json"), "utf8")).fetchedAt;

const levelUp = new Map(raw("CharacterLevelUpStat").map(x => [x.code, x]));
// ER 실험체 분류 → 블서로그 역할군 (src/data/bseorogue/roles.ts 의 Role 이름)
const ARCHETYPE = {
  Tanker: "TANK",
  Warrior: "BRUISER",
  Assasin: "ASSASSIN",
  Assassin: "ASSASSIN",
  Marksman: "MARKSMAN",
  Mage: "MAGE",
  Supporter: "SUPPORT",
};
const weaponsOf = new Map();
for (const a of raw("CharacterAttributes")) {
  if (!weaponsOf.has(a.characterCode)) {
    weaponsOf.set(a.characterCode, []);
  }
  weaponsOf.get(a.characterCode).push(l10n.get(`WeaponType/${a.mastery}`) || a.mastery);
}
const skins = raw("CharacterSkin");
const r1 = n => Math.round(n * 10) / 10;

const characters = {};
for (const c of raw("Character")) {
  const lu = levelUp.get(c.code) || {};
  const name = l10n.get(`Character/Name/${c.code}`);
  if (!name) {
    continue;
  }
  const pad = String(c.code).padStart(3, "0");
  const skill = slot => l10n.get(`Skill/Group/Name/1${pad}${slot}00`) || "";
  characters[c.code] = {
    name,
    en: c.name,
    role: ARCHETYPE[c.charArcheType1] || "BRUISER",
    weapons: weaponsOf.get(c.code) || [],
    hp20: Math.round(c.maxHp + 19 * (lu.maxHp || 0)),
    ap20: r1(c.attackPower + 19 * (lu.attackPower || 0)),
    def20: r1(c.defense + 19 * (lu.defense || 0)),
    moveSpeed: r1(c.moveSpeed),
    attackSpeed: Math.round(c.attackSpeed * 1000) / 1000,
    // [패시브, Q, W, E, R]
    skills: [1, 2, 3, 4, 5].map(skill),
    // 0번은 기본 모습, 1번부터 스킨 (진화 = 스킨)
    skins: skins
      .filter(s => s.characterCode === c.code)
      .sort((a, b) => a.index - b.index)
      .map(s => l10n.get(`Skin/Name/${s.code}`) || s.name),
  };
}

const monsters = {};
for (const m of raw("Monster")) {
  if (monsters[m.monster] || (m.mutantType && m.mutantType !== "None")) {
    continue; // 같은 동물이 모드마다 여러 줄 → 처음 것만, 변이체는 나중에
  }
  monsters[m.monster] = {
    name: l10n.get(`Monster/Name/${m.code}`) || m.monster,
    maxHp: m.maxHp,
    ap: m.attackPower,
    def: m.defense,
    moveSpeed: m.moveSpeed,
  };
}

const list = Object.values(characters);
const mean = k => r1(list.reduce((s, c) => s + c[k], 0) / list.length);
const means = {
  hp20: mean("hp20"),
  ap20: mean("ap20"),
  def20: mean("def20"),
  moveSpeed: mean("moveSpeed"),
  attackSpeed: Math.round((list.reduce((s, c) => s + c.attackSpeed, 0) / list.length) * 1000) / 1000,
};

const out = `/*
 * SPDX-FileCopyrightText: Nimble Neuron
 * SPDX-License-Identifier: LicenseRef-NimbleNeuron
 */

// 이 파일은 scripts/er-data/build.mjs 가 만들어요. 직접 고치지 마세요.
// 출처: 이터널 리턴 공식 API (${fetchedAt} 받음) · 이름과 숫자의 권리는 님블뉴런에 있어요.

export type ErRoleKey = "TANK" | "BRUISER" | "ASSASSIN" | "MARKSMAN" | "MAGE" | "SUPPORT";

export interface ErCharacter {
  name: string;
  en: string;
  /** ER 실험체 분류(charArcheType1)에서 바꾼 역할군 */
  role: ErRoleKey;
  /** 쓸 수 있는 무기 (ER 순서) */
  weapons: readonly string[];
  /** 20레벨 기준 (기본 + 레벨업 × 19) */
  hp20: number;
  ap20: number;
  def20: number;
  moveSpeed: number;
  attackSpeed: number;
  /** [패시브, Q, W, E, R] */
  skills: readonly [string, string, string, string, string];
  /** 0번 기본 모습, 1번부터 스킨 */
  skins: readonly string[];
}

export interface ErMonster {
  name: string;
  maxHp: number;
  ap: number;
  def: number;
  moveSpeed: number;
}

/** 전체 실험체 평균 (스탯 환산 기준) */
export const ER_MEANS = ${JSON.stringify(means)} as const;

export const ER_CHARACTERS: Readonly<Record<number, ErCharacter>> = ${JSON.stringify(characters, null, 1)};

export const ER_MONSTERS: Readonly<Record<string, ErMonster>> = ${JSON.stringify(monsters, null, 1)};
`;
writeFileSync(join(process.cwd(), "src/data/bseorogue/er-data.ts"), out);

// 실험체 종 번호: 1030 + ER 번호 × 3 + 단계 (0 기본 · 1 스킨 진화 1 · 2 스킨 진화 2)
// 포켓로그는 2000 이상 번호를 지역 폼(알로라 등)으로 보니까 2000 아래 빈 자리(1030~1599)를 써요
const enumPath = join(process.cwd(), "src/enums/species-id.ts");
const enumSrc = readFileSync(enumPath, "utf8");
const START = "  // BSEO_ER 시작 (scripts/er-data/build.mjs 가 만들어요. 직접 고치지 마세요)";
const END = "  // BSEO_ER 끝";
const lines = [START, "  // 1030 + ER 실험체 번호 × 3 + 단계 (0 기본 모습 · 1 스킨 진화 1 · 2 스킨 진화 2)"];
const used = new Set();
for (const [code, c] of Object.entries(characters).sort((a, b) => a[0] - b[0])) {
  const key = `BSEO_${c.en.toUpperCase().replace(/[^A-Z0-9]+/g, "_")}`;
  if (used.has(key)) {
    throw new Error(`실험체 영어 이름이 겹쳐요: ${key}`);
  }
  used.add(key);
  const base = 1030 + Number(code) * 3;
  if (base + 2 >= 1600) {
    throw new Error(`ER 번호 ${code} 는 종 번호 자리가 모자라요 (1600부터는 야생동물)`);
  }
  lines.push(`  ${key} = ${base},`, `  ${key}_S1 = ${base + 1},`, `  ${key}_S2 = ${base + 2},`);
}
lines.push(END);
const block = lines.join("\n");
const a = enumSrc.indexOf(START);
const b = enumSrc.indexOf(END);
if (a < 0 || b < a) {
  throw new Error("species-id.ts 에 BSEO_ER 표시가 없어요");
}
const next = enumSrc.slice(0, a) + block + enumSrc.slice(b + END.length);
writeFileSync(enumPath, next);
console.log(
  `실험체 ${list.length}명 · 몬스터 ${Object.keys(monsters).length}종 → src/data/bseorogue/er-data.ts · src/enums/species-id.ts`,
);
