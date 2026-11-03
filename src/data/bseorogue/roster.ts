/*
 * SPDX-FileCopyrightText: 2026 SG
 * SPDX-License-Identifier: AGPL-3.0-only
 */

import { ER_CHARACTERS, ER_MONSTERS } from "#data/bseorogue/er-data";
import { Role } from "#data/bseorogue/roles";
import { characterStages, erMonsterStats, type Stages3, type Stats6 } from "#data/bseorogue/stats";
import { MoveId } from "#enums/move-id";
/**
 * 블서로그 실험체 · 야생동물 · 보스 목록
 *
 * 실험체 이름 · 스킬 이름 · 스킨은 ER 공식 데이터(er-data.ts)에서 가져와요.
 * 종족값은 포켓로그 진화 라인을 참고해서 정했어요 (stats.ts 설명 참고). 스킬 효과는 임시예요.
 * 스킬은 지금은 포켓로그에 있는 기술의 효과를 빌려 쓰고, 이름 · 상성만 블서로그 것으로 바꿔요.
 * 그래서 한 기술은 한 실험체만 써야 해요 (야생동물 · 보스도 실험체 스킬과 겹치면 안 돼요).
 * 스탯 순서: [체력, 공격력, 방어력, 스킬 증폭, 스킬 저항, 속도] (포켓로그 HP · 공격 · 방어 · 특공 · 특방 · 스피드)
 * 공격력은 물리 스킬(평원딜 · 브루저 등), 스킬 증폭은 특수 스킬(스증딜러 · 서포터)에 쓰여요.
 */
import { SpeciesId } from "#enums/species-id";

export type { Stats6 } from "#data/bseorogue/stats";

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
  /** 지금 모습(기본 모습) 종족값 */
  stats: Stats6;
  /** [기본, 스킨 진화 1, 스킨 진화 2] 종족값 (스킨 진화를 넣으면 써요) */
  stages: Stages3;
  /** 어디에 중점을 뒀는지 (설명용) */
  focus: string;
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
 * 실험체 한 명: 이름 · 스킬 이름 · 스킨은 ER 데이터에서
 * final 은 다 큰 모습(스킨 진화 2) 종족값이에요. 기본 모습 · 스킨 진화 1은 같은 모양으로 합만 줄여요 (stats.ts)
 * moves 는 효과를 빌려 쓰는 포켓로그 기술 [Q, W, E, R] (효과는 나중에 블서로그 것으로)
 */
function character(
  id: SpeciesId,
  erCode: number,
  weapon: string,
  role: Role,
  cost: number,
  focus: string,
  final: Stats6,
  moves: readonly [MoveId, MoveId, MoveId, MoveId],
): BseoCharacter {
  const er = ER_CHARACTERS[erCode];
  const name = er?.name ?? `실험체 ${erCode}`;
  const levels = [1, 1, 5, 10];
  const keys = ["Q", "W", "E", "R"];
  const stages = characterStages(final, cost);
  return {
    id,
    erCode,
    name,
    weapon,
    role,
    cost,
    stats: stages[0],
    stages,
    focus,
    passive: er?.skills[0] ?? "",
    skins: er?.skins ?? [name],
    skills: moves.map((move, i) => ({
      move,
      name: er?.skills[i + 1] || `${name} ${keys[i]}`,
      level: levels[i],
    })) as unknown as BseoCharacter["skills"],
  };
}

/**
 * 시작 실험체 6명 (모두 1코스트 → 기본 320 · 스킨 진화 1 410 · 스킨 진화 2 500)
 * 숫자는 다 큰 모습 기준 [체력, 공격력, 방어력, 스킬 증폭, 스킬 저항, 속도]
 */
export const BSEO_STARTERS: readonly BseoCharacter[] = [
  // 탱커: 체력이 제일 높고 방어 · 스킬 저항도 높아요. 대신 느려요
  character(
    SpeciesId.BSEO_ELEVEN,
    30,
    "망치",
    Role.TANK,
    1,
    "체력",
    [125, 80, 105, 40, 95, 55],
    [MoveId.HAMMER_ARM, MoveId.IRON_DEFENSE, MoveId.BODY_SLAM, MoveId.GIGA_IMPACT],
  ),
  // 브루저: 공격력과 방어력이 함께 높은 정면 싸움꾼
  character(
    SpeciesId.BSEO_YUKI,
    11,
    "양손검",
    Role.BRUISER,
    1,
    "공격력 · 방어력",
    [90, 115, 100, 40, 70, 85],
    [MoveId.SLASH, MoveId.SWORDS_DANCE, MoveId.SACRED_SWORD, MoveId.LEAF_BLADE],
  ),
  // 암살자: 제일 빨라서 먼저 때리지만, 맞으면 약해요
  character(
    SpeciesId.BSEO_SHOICHI,
    18,
    "단검",
    Role.ASSASSIN,
    1,
    "속도",
    [65, 120, 60, 50, 60, 145],
    [MoveId.NIGHT_SLASH, MoveId.QUICK_ATTACK, MoveId.SUCKER_PUNCH, MoveId.PSYCHO_CUT],
  ),
  // 평원딜: 공격력이 제일 높은 원거리 딜러. 방어가 낮아요
  character(
    SpeciesId.BSEO_NADINE,
    6,
    "석궁",
    Role.MARKSMAN,
    1,
    "공격력",
    [65, 135, 55, 55, 70, 120],
    [MoveId.BULLET_SEED, MoveId.FOCUS_ENERGY, MoveId.THOUSAND_ARROWS, MoveId.STONE_EDGE],
  ),
  // 스증딜러: 스킬 증폭이 제일 높아요. 체력 · 공격력은 낮아요
  character(
    SpeciesId.BSEO_HYEJIN,
    12,
    "암기",
    Role.MAGE,
    1,
    "스킬 증폭",
    [65, 45, 60, 140, 85, 105],
    [MoveId.SHADOW_BALL, MoveId.HEX, MoveId.CONFUSE_RAY, MoveId.DARK_PULSE],
  ),
  // 서포터: 스킬 저항이 제일 높고 오래 버텨요. 공격력은 낮아요
  character(
    SpeciesId.BSEO_LENI,
    69,
    "권총",
    Role.SUPPORT,
    1,
    "스킬 저항",
    [90, 55, 80, 95, 115, 65],
    [MoveId.FLASH_CANNON, MoveId.HEAL_PULSE, MoveId.PROTECT, MoveId.MOONBLAST],
  ),
];

/**
 * 야생동물 (영입 불가 · 웨이브가 올라갈수록 센 동물이 섞여요)
 * 모양은 ER 몬스터 스탯, 합은 나오는 웨이브에 맞춰요 (포켓로그 초반 야생 구구 251 ~ 최종 진화 500 정도)
 */
const wild = (id: SpeciesId, erKey: string, fromWave: number, total: number, moves: readonly MoveId[]): BseoWild => ({
  id,
  name: ER_MONSTERS[erKey]?.name ?? erKey,
  stats: erMonsterStats(erKey, total),
  fromWave,
  moves,
});
export const BSEO_WILD: readonly BseoWild[] = [
  wild(SpeciesId.BSEO_CHICKEN, "Chicken", 1, 220, [MoveId.PECK, MoveId.GROWL]),
  wild(SpeciesId.BSEO_BAT, "Bat", 1, 250, [MoveId.WING_ATTACK, MoveId.LEER]),
  wild(SpeciesId.BSEO_BOAR, "Boar", 6, 320, [MoveId.TACKLE, MoveId.TAKE_DOWN]),
  wild(SpeciesId.BSEO_WILD_DOG, "WildDog", 11, 360, [MoveId.BITE, MoveId.HYPER_FANG]),
  wild(SpeciesId.BSEO_WOLF, "Wolf", 21, 430, [MoveId.CRUNCH, MoveId.FURY_SWIPES]),
  wild(SpeciesId.BSEO_BEAR, "Bear", 31, 500, [MoveId.SLAM, MoveId.SUPERPOWER]),
];

/**
 * 보스 (10웨이브마다 · 알파 → 오메가 → 감마 → 위클라인 → 최종 보스 안내 로봇 루미 경계 모드)
 * 합 420 → 480 → 540 → 600 → 680. 루미는 포켓로그 뮤츠 · 루기아(680)급이고, 670이 넘어서 체력 칸이 하나 더 붙어요.
 */
export const BSEO_BOSSES: readonly BseoBoss[] = [
  {
    id: SpeciesId.BSEO_ALPHA,
    name: "알파",
    stats: [85, 80, 75, 50, 65, 65],
    wave: 10,
    moves: [MoveId.IRON_HEAD, MoveId.HEADBUTT, MoveId.TAKE_DOWN],
  },
  {
    id: SpeciesId.BSEO_OMEGA,
    name: "오메가",
    stats: [95, 95, 80, 60, 70, 80],
    wave: 20,
    moves: [MoveId.METEOR_MASH, MoveId.CRUNCH, MoveId.EXTREME_SPEED],
  },
  {
    id: SpeciesId.BSEO_GAMMA,
    name: "감마",
    stats: [100, 80, 90, 105, 90, 75],
    wave: 30,
    moves: [MoveId.MIRROR_SHOT, MoveId.TRI_ATTACK, MoveId.GYRO_BALL],
  },
  {
    id: SpeciesId.BSEO_WICKELINE,
    name: "위클라인",
    stats: [110, 120, 95, 95, 90, 90],
    wave: 40,
    moves: [MoveId.SUPERPOWER, MoveId.AURA_SPHERE, MoveId.EXTREME_SPEED, MoveId.IRON_HEAD],
  },
  {
    id: SpeciesId.BSEO_LUMI,
    name: "루미 (경계 모드)",
    stats: [130, 80, 110, 140, 120, 100],
    wave: 50,
    moves: [MoveId.THUNDERBOLT, MoveId.DAZZLING_GLEAM, MoveId.PSYCHIC, MoveId.CALM_MIND],
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
