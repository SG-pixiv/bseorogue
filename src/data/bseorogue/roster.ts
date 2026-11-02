/*
 * SPDX-FileCopyrightText: 2026 SG
 * SPDX-License-Identifier: AGPL-3.0-only
 */

import { Role } from "#data/bseorogue/roles";
import { MoveId } from "#enums/move-id";
/**
 * 블서로그 실험체 · 야생동물 · 보스 목록 (임시 숫자)
 *
 * 스탯 · 스킬은 ER 데이터(scripts/er-data)와 SG 기획이 오면 바꿔요.
 * 스킬은 지금은 포켓로그에 있는 기술의 효과를 빌려 쓰고, 이름 · 상성만 블서로그 것으로 바꿔요.
 * 스탯 순서: [체력, 공격력, 방어력, 스킬 증폭, 스킬 저항, 속도] (포켓로그 HP · 공격 · 방어 · 특공 · 특방 · 스피드)
 */
import { SpeciesId } from "#enums/species-id";

export type Stats6 = readonly [number, number, number, number, number, number];

export interface BseoSkill {
  /** 효과를 빌려 쓰는 포켓로그 기술 */
  move: MoveId;
  /** 화면에 보이는 이름 */
  name: string;
  /** 배우는 레벨 */
  level: number;
}

export interface BseoCharacter {
  id: SpeciesId;
  /** ER 실험체 번호 (무명섬 er_characters.code 와 같아요. 모르면 null) */
  erCode: number | null;
  name: string;
  weapon: string;
  role: Role;
  cost: number;
  stats: Stats6;
  /** Q · W · E · R */
  skills: readonly [BseoSkill, BseoSkill, BseoSkill, BseoSkill];
}

export interface BseoWild {
  id: SpeciesId;
  name: string;
  stats: Stats6;
  /** 이 웨이브부터 나와요 */
  fromWave: number;
  moves: readonly MoveId[];
}

export interface BseoBoss {
  id: SpeciesId;
  name: string;
  stats: Stats6;
  /** 나오는 웨이브 (10 · 20 · 30 · 40 · 50) */
  wave: number;
  moves: readonly MoveId[];
}

const sk = (move: MoveId, name: string, level = 1): BseoSkill => ({ move, name, level });

/** 시작 실험체 6명 (모두 1코스트) */
export const BSEO_STARTERS: readonly BseoCharacter[] = [
  {
    id: SpeciesId.BSEO_ELEVEN,
    erCode: 50,
    name: "일레븐",
    weapon: "망치",
    role: Role.TANK,
    cost: 1,
    stats: [90, 70, 85, 40, 70, 45],
    skills: [
      sk(MoveId.HAMMER_ARM, "일레븐 Q"),
      sk(MoveId.IRON_DEFENSE, "일레븐 W"),
      sk(MoveId.BODY_SLAM, "일레븐 E", 5),
      sk(MoveId.GIGA_IMPACT, "일레븐 R", 10),
    ],
  },
  {
    id: SpeciesId.BSEO_YUKI,
    erCode: 21,
    name: "유키",
    weapon: "양손검",
    role: Role.BRUISER,
    cost: 1,
    stats: [75, 85, 70, 40, 60, 70],
    skills: [
      sk(MoveId.SLASH, "유키 Q"),
      sk(MoveId.SWORDS_DANCE, "유키 W"),
      sk(MoveId.SACRED_SWORD, "유키 E", 5),
      sk(MoveId.LEAF_BLADE, "유키 R", 10),
    ],
  },
  {
    id: SpeciesId.BSEO_SHOICHI,
    erCode: null,
    name: "쇼이치",
    weapon: "단검",
    role: Role.ASSASSIN,
    cost: 1,
    stats: [60, 90, 55, 45, 55, 95],
    skills: [
      sk(MoveId.NIGHT_SLASH, "쇼이치 Q"),
      sk(MoveId.QUICK_ATTACK, "쇼이치 W"),
      sk(MoveId.SUCKER_PUNCH, "쇼이치 E", 5),
      sk(MoveId.PSYCHO_CUT, "쇼이치 R", 10),
    ],
  },
  {
    id: SpeciesId.BSEO_NADINE,
    erCode: 16,
    name: "나딘",
    weapon: "석궁",
    role: Role.MARKSMAN,
    cost: 1,
    stats: [60, 95, 50, 50, 55, 85],
    skills: [
      sk(MoveId.BULLET_SEED, "나딘 Q"),
      sk(MoveId.FOCUS_ENERGY, "나딘 W"),
      sk(MoveId.SNIPE_SHOT, "나딘 E", 5),
      sk(MoveId.HYPER_BEAM, "나딘 R", 10),
    ],
  },
  {
    id: SpeciesId.BSEO_HYEJIN,
    erCode: 22,
    name: "혜진",
    weapon: "암기",
    role: Role.MAGE,
    cost: 1,
    stats: [60, 45, 55, 95, 70, 75],
    skills: [
      sk(MoveId.SHADOW_BALL, "혜진 Q"),
      sk(MoveId.HEX, "혜진 W"),
      sk(MoveId.CONFUSE_RAY, "혜진 E", 5),
      sk(MoveId.DARK_PULSE, "혜진 R", 10),
    ],
  },
  {
    id: SpeciesId.BSEO_LENI,
    erCode: null,
    name: "레니",
    weapon: "권총",
    role: Role.SUPPORT,
    cost: 1,
    stats: [75, 50, 65, 80, 80, 65],
    skills: [
      sk(MoveId.FLASH_CANNON, "레니 Q"),
      sk(MoveId.HEAL_PULSE, "레니 W"),
      sk(MoveId.PROTECT, "레니 E", 5),
      sk(MoveId.MOONBLAST, "레니 R", 10),
    ],
  },
];

/** 야생동물 (영입 불가 · 웨이브가 올라갈수록 센 동물이 섞여요) */
export const BSEO_WILD: readonly BseoWild[] = [
  {
    id: SpeciesId.BSEO_CHICKEN,
    name: "닭",
    stats: [40, 45, 35, 30, 30, 55],
    fromWave: 1,
    moves: [MoveId.PECK, MoveId.GROWL],
  },
  {
    id: SpeciesId.BSEO_BAT,
    name: "박쥐",
    stats: [45, 50, 35, 35, 40, 70],
    fromWave: 1,
    moves: [MoveId.WING_ATTACK, MoveId.LEER],
  },
  {
    id: SpeciesId.BSEO_BOAR,
    name: "멧돼지",
    stats: [70, 70, 60, 30, 40, 45],
    fromWave: 6,
    moves: [MoveId.TACKLE, MoveId.TAKE_DOWN],
  },
  {
    id: SpeciesId.BSEO_WILD_DOG,
    name: "들개",
    stats: [60, 70, 50, 30, 45, 70],
    fromWave: 11,
    moves: [MoveId.BITE, MoveId.HYPER_FANG],
  },
  {
    id: SpeciesId.BSEO_WOLF,
    name: "늑대",
    stats: [70, 85, 60, 35, 55, 85],
    fromWave: 21,
    moves: [MoveId.CRUNCH, MoveId.FURY_SWIPES],
  },
  {
    id: SpeciesId.BSEO_BEAR,
    name: "곰",
    stats: [100, 95, 80, 35, 60, 45],
    fromWave: 31,
    moves: [MoveId.SLAM, MoveId.SUPERPOWER],
  },
];

/** 보스 (10웨이브마다 · 알파 → 오메가 → 감마 → 위클라인 → 최종 보스 안내 로봇 루미 경계 모드) */
export const BSEO_BOSSES: readonly BseoBoss[] = [
  {
    id: SpeciesId.BSEO_ALPHA,
    name: "알파",
    stats: [95, 85, 80, 60, 70, 65],
    wave: 10,
    moves: [MoveId.IRON_HEAD, MoveId.HEADBUTT, MoveId.TAKE_DOWN],
  },
  {
    id: SpeciesId.BSEO_OMEGA,
    name: "오메가",
    stats: [105, 95, 90, 75, 80, 70],
    wave: 20,
    moves: [MoveId.METEOR_MASH, MoveId.CRUNCH, MoveId.EXTREME_SPEED],
  },
  {
    id: SpeciesId.BSEO_GAMMA,
    name: "감마",
    stats: [110, 85, 95, 105, 95, 75],
    wave: 30,
    moves: [MoveId.FLASH_CANNON, MoveId.SHADOW_BALL, MoveId.GYRO_BALL],
  },
  {
    id: SpeciesId.BSEO_WICKELINE,
    name: "위클라인",
    stats: [120, 115, 100, 100, 100, 90],
    wave: 40,
    moves: [MoveId.SUPERPOWER, MoveId.DARK_PULSE, MoveId.EXTREME_SPEED, MoveId.IRON_HEAD],
  },
  {
    id: SpeciesId.BSEO_LUMI,
    name: "루미 (경계 모드)",
    stats: [150, 110, 110, 130, 110, 100],
    wave: 50,
    moves: [MoveId.HYPER_BEAM, MoveId.FLASH_CANNON, MoveId.MOONBLAST, MoveId.PROTECT],
  },
];

export const BSEO_STARTER_IDS = BSEO_STARTERS.map(c => c.id);
export const BSEO_ALL_IDS: readonly SpeciesId[] = [
  ...BSEO_STARTER_IDS,
  ...BSEO_WILD.map(w => w.id),
  ...BSEO_BOSSES.map(b => b.id),
];
/** 고를 수 없는 블서로그 종 (야생동물 · 보스) */
export const BSEO_NON_STARTER_IDS: readonly SpeciesId[] = [...BSEO_WILD.map(w => w.id), ...BSEO_BOSSES.map(b => b.id)];
