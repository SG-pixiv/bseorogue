/*
 * SPDX-FileCopyrightText: 2026 SG
 * SPDX-License-Identifier: AGPL-3.0-only
 */

import { ER_CHARACTERS, ER_MONSTERS } from "#data/bseorogue/er-data";
import { erCharacterStats, erMonsterStats } from "#data/bseorogue/er-stats";
import { Role } from "#data/bseorogue/roles";
import { MoveId } from "#enums/move-id";
/**
 * 블서로그 실험체 · 야생동물 · 보스 목록
 *
 * 실험체 이름 · 스킬 이름 · 스킨 · 동물 스탯은 ER 공식 데이터(er-data.ts)에서 가져와요.
 * 보스 스탯 · 스킬 효과는 임시예요 (기획이 정해지면 바꿔요).
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
  /** 고유 패시브 이름 (효과는 나중에) */
  passive: string;
  /** 0번 기본 모습, 1번부터 스킨 (진화 = 스킨) */
  skins: readonly string[];
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

/**
 * 실험체 한 명: 이름 · 스킬 이름 · 스킨은 ER 데이터에서, 스탯은 역할군 틀 × ER 20레벨 스탯으로 (er-stats.ts)
 * moves 는 효과를 빌려 쓰는 포켓로그 기술 [Q, W, E, R] (효과는 나중에 블서로그 것으로)
 */
function character(
  id: SpeciesId,
  erCode: number,
  weapon: string,
  role: Role,
  cost: number,
  moves: readonly [MoveId, MoveId, MoveId, MoveId],
): BseoCharacter {
  const er = ER_CHARACTERS[erCode];
  const name = er?.name ?? `실험체 ${erCode}`;
  const levels = [1, 1, 5, 10];
  const keys = ["Q", "W", "E", "R"];
  return {
    id,
    erCode,
    name,
    weapon,
    role,
    cost,
    stats: erCharacterStats(erCode, role),
    passive: er?.skills[0] ?? "",
    skins: er?.skins ?? [name],
    skills: moves.map((move, i) => ({
      move,
      name: er?.skills[i + 1] || `${name} ${keys[i]}`,
      level: levels[i],
    })) as unknown as BseoCharacter["skills"],
  };
}

/** 시작 실험체 6명 (모두 1코스트) */
export const BSEO_STARTERS: readonly BseoCharacter[] = [
  character(SpeciesId.BSEO_ELEVEN, 30, "망치", Role.TANK, 1, [
    MoveId.HAMMER_ARM,
    MoveId.IRON_DEFENSE,
    MoveId.BODY_SLAM,
    MoveId.GIGA_IMPACT,
  ]),
  character(SpeciesId.BSEO_YUKI, 11, "양손검", Role.BRUISER, 1, [
    MoveId.SLASH,
    MoveId.SWORDS_DANCE,
    MoveId.SACRED_SWORD,
    MoveId.LEAF_BLADE,
  ]),
  character(SpeciesId.BSEO_SHOICHI, 18, "단검", Role.ASSASSIN, 1, [
    MoveId.NIGHT_SLASH,
    MoveId.QUICK_ATTACK,
    MoveId.SUCKER_PUNCH,
    MoveId.PSYCHO_CUT,
  ]),
  character(SpeciesId.BSEO_NADINE, 6, "석궁", Role.MARKSMAN, 1, [
    MoveId.BULLET_SEED,
    MoveId.FOCUS_ENERGY,
    MoveId.SNIPE_SHOT,
    MoveId.HYPER_BEAM,
  ]),
  character(SpeciesId.BSEO_HYEJIN, 12, "암기", Role.MAGE, 1, [
    MoveId.SHADOW_BALL,
    MoveId.HEX,
    MoveId.CONFUSE_RAY,
    MoveId.DARK_PULSE,
  ]),
  character(SpeciesId.BSEO_LENI, 69, "권총", Role.SUPPORT, 1, [
    MoveId.FLASH_CANNON,
    MoveId.HEAL_PULSE,
    MoveId.PROTECT,
    MoveId.MOONBLAST,
  ]),
];

/** 야생동물 (영입 불가 · 웨이브가 올라갈수록 센 동물이 섞여요) · 스탯은 ER 몬스터 스탯으로 */
const wild = (id: SpeciesId, erKey: string, fromWave: number, moves: readonly MoveId[]): BseoWild => ({
  id,
  name: ER_MONSTERS[erKey]?.name ?? erKey,
  stats: erMonsterStats(erKey),
  fromWave,
  moves,
});
export const BSEO_WILD: readonly BseoWild[] = [
  wild(SpeciesId.BSEO_CHICKEN, "Chicken", 1, [MoveId.PECK, MoveId.GROWL]),
  wild(SpeciesId.BSEO_BAT, "Bat", 1, [MoveId.WING_ATTACK, MoveId.LEER]),
  wild(SpeciesId.BSEO_BOAR, "Boar", 6, [MoveId.TACKLE, MoveId.TAKE_DOWN]),
  wild(SpeciesId.BSEO_WILD_DOG, "WildDog", 11, [MoveId.BITE, MoveId.HYPER_FANG]),
  wild(SpeciesId.BSEO_WOLF, "Wolf", 21, [MoveId.CRUNCH, MoveId.FURY_SWIPES]),
  wild(SpeciesId.BSEO_BEAR, "Bear", 31, [MoveId.SLAM, MoveId.SUPERPOWER]),
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
