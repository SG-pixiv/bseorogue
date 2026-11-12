/*
 * SPDX-FileCopyrightText: 2026 SG
 * SPDX-License-Identifier: AGPL-3.0-only
 */

import { ER_CHARACTERS, ER_MONSTERS, type ErRoleKey } from "#data/bseorogue/er-data";
import { Role } from "#data/bseorogue/roles";
import { SHEET_CHARACTERS, SHEET_PASSIVES, SHEET_SKILLS } from "#data/bseorogue/sheet-data";
import { SKILL_MOVES } from "#data/bseorogue/skill-moves";
import { skinEvolutionOf } from "#data/bseorogue/skin-evolution";
import { characterStages, erMonsterStats, ROLE_SHAPE, type Stages3, type Stats6 } from "#data/bseorogue/stats";
import { MoveId } from "#enums/move-id";
/**
 * 블서로그 실험체 · 야생동물 · 보스 목록
 *
 * - 실험체는 ER 실험체 전부(er-data.ts)이고, 지금은 전부 시작 실험체로 고를 수 있어요 (도감처럼 ER 번호 순서).
 *   BSEO_PLAYABLE 에 적은 실험체는 무기 · 코스트 · 종족값을 직접 정한 것이고,
 *   나머지는 역할군 기본 모양 · 1코스트로 임시로 만들어요. 나중에 BSEO_PLAYABLE 에 하나씩 추가하면 돼요.
 *   다시 일부만 고를 수 있게 하려면 ALL_PLAYABLE 을 false 로 바꿔요.
 * - 이름 · 역할군(ER 분류) · 무기 · 스킬 이름 · 스킨은 ER 공식 데이터에서 가져와요.
 * - 종족값은 포켓로그 진화 라인을 참고해서 정했어요 (stats.ts). 스킬 효과는 임시예요 (skill-moves.ts).
 * - 진화 = 스킨: 기본 모습 → 스킨 진화 1 → 스킨 진화 2 (skin-evolution.ts, 지금은 임시 순서)
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

/** 기본 모습 · 스킨 진화 1 · 스킨 진화 2 */
export interface BseoForm {
  id: SpeciesId;
  name: string;
  role: Role;
  stats: Stats6;
  /** 이 모습이 되는 레벨 (기본 모습은 0) */
  level: number;
}

export interface BseoCharacter {
  /** 기본 모습의 종 번호 */
  id: SpeciesId;
  /** ER 실험체 번호 (무명섬 er_characters.code 와 같아요) */
  erCode: number;
  name: string;
  weapon: string;
  /** 기본 모습의 역할군 */
  role: Role;
  cost: number;
  /** 시작 실험체로 고를 수 있는지 (아니면 KEL 팀 같은 적으로만 나와요) */
  playable: boolean;
  /** 기본 모습 종족값 */
  stats: Stats6;
  /** [기본, 스킨 진화 1, 스킨 진화 2] 종족값 */
  stages: Stages3;
  /** 어디에 중점을 뒀는지 (설명용) */
  focus: string;
  /** [기본, 스킨 진화 1, 스킨 진화 2] */
  forms: readonly [BseoForm, BseoForm, BseoForm];
  /** Q · W · E · R */
  skills: readonly [BseoSkill, BseoSkill, BseoSkill, BseoSkill];
  /** 고유 패시브 이름 (효과는 빌려 쓰는 특성, passive.ts) */
  passive: string;
  /** ER 스킨 목록 (0번 기본 모습) */
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
 * 실험체 종 번호: 1030 + ER 번호 × 3 + 단계 (0 기본 · 1 스킨 진화 1 · 2 스킨 진화 2)
 * 포켓로그는 2000 이상 번호를 지역 폼(알로라 등)으로 봐서, 포켓몬(~1025)과 야생동물(1601~) 사이 빈 자리를 써요
 */
export function bseoSpeciesId(erCode: number, stage = 0): SpeciesId {
  return (1030 + erCode * 3 + stage) as SpeciesId;
}

/** 종 번호 → ER 실험체 번호 (실험체가 아니면 null) */
export function erCodeOfSpecies(id: SpeciesId): number | null {
  return id >= 1030 && id < 1600 ? Math.floor((id - 1030) / 3) : null;
}

interface PlayableConfig {
  erCode: number;
  weapon: string;
  cost: number;
  /** 어디에 중점을 두는지 (설명용) */
  focus: string;
  /** 다 큰 모습(스킨 진화 2) 종족값. 기본 모습 · 스킨 진화 1은 합만 줄여서 같은 모양으로 만들어요 */
  final: Stats6;
  /** 역할군을 ER 분류와 다르게 쓰고 싶을 때만 */
  role?: ErRoleKey;
}

/** 지금은 ER 실험체 전부를 고를 수 있게 (임시). false 면 BSEO_PLAYABLE 에 적은 실험체만 */
export const ALL_PLAYABLE = true;

/**
 * 무기 · 코스트 · 종족값을 직접 정한 실험체.
 * 1코스트 → 기본 320 · 스킨 진화 1 410 · 스킨 진화 2 500. 숫자는 다 큰 모습 기준 [체력, 공격력, 방어력, 스킬 증폭, 스킬 저항, 속도]
 */
export const BSEO_PLAYABLE: readonly PlayableConfig[] = [
  // 탱커: 체력이 제일 높고 방어 · 스킬 저항도 높아요. 대신 느려요
  { erCode: 30, weapon: "망치", cost: 1, focus: "체력", final: [125, 80, 105, 40, 95, 55] }, // 일레븐
  // 브루저: 공격력과 방어력이 함께 높은 정면 싸움꾼
  { erCode: 11, weapon: "양손검", cost: 1, focus: "공격력 · 방어력", final: [90, 115, 100, 40, 70, 85] }, // 유키
  // 암살자: 제일 빨라서 먼저 때리지만, 맞으면 약해요
  { erCode: 18, weapon: "단검", cost: 1, focus: "속도", final: [65, 120, 60, 50, 60, 145] }, // 쇼이치
  // 평원딜: 공격력이 제일 높은 원거리 딜러. 방어가 낮아요
  { erCode: 6, weapon: "석궁", cost: 1, focus: "공격력", final: [65, 135, 55, 55, 70, 120] }, // 나딘
  // 스증딜러: 스킬 증폭이 제일 높아요. 체력 · 공격력은 낮아요
  { erCode: 12, weapon: "암기", cost: 1, focus: "스킬 증폭", final: [65, 45, 60, 140, 85, 105] }, // 혜진
  // 서포터: 스킬 저항이 제일 높고 오래 버텨요. 공격력은 낮아요
  { erCode: 69, weapon: "권총", cost: 1, focus: "스킬 저항", final: [90, 55, 80, 95, 115, 65] }, // 레니
];

const SKILL_KEYS = ["Q", "W", "E", "R"] as const;
const SKILL_LEVELS = [1, 1, 5, 10] as const;

function buildCharacter(erCode: number, cfg: PlayableConfig | undefined): BseoCharacter | null {
  const er = ER_CHARACTERS[erCode];
  const moves = SKILL_MOVES[erCode];
  if (!er || !moves) {
    return null;
  }
  // 시트(docs/sheets/실험체-스킬.xlsx → sheet-data.ts)가 있으면 시트 값이 먼저예요
  const sheet = SHEET_CHARACTERS[erCode];
  const role = Role[sheet?.role ?? cfg?.role ?? er.role];
  const cost = sheet?.cost ?? cfg?.cost ?? 1;
  const stages = characterStages(sheet?.final ?? cfg?.final ?? ROLE_SHAPE[role], cost);
  const evo = skinEvolutionOf(erCode);
  const roles: Role[] = [role];
  for (const r of evo.roles) {
    roles.push(r ? Role[r] : (roles.at(-1) ?? role));
  }
  const formName = (stage: number) =>
    stage === 0 ? er.name : (er.skins[evo.skins[stage - 1]] ?? `${er.name}${"★".repeat(stage)}`);
  const forms = [0, 1, 2].map(stage => ({
    id: bseoSpeciesId(erCode, stage),
    name: formName(stage),
    role: roles[stage],
    stats: stages[stage],
    level: stage === 0 ? 0 : evo.levels[stage - 1],
  })) as unknown as BseoCharacter["forms"];
  return {
    id: forms[0].id,
    erCode,
    name: er.name,
    weapon: sheet?.weapon || cfg?.weapon || er.weapons[0] || "",
    role,
    cost,
    playable: ALL_PLAYABLE || !!cfg,
    stats: stages[0],
    stages,
    focus: cfg?.focus ?? (sheet ? "시트" : "역할군 기본"),
    forms,
    passive: SHEET_PASSIVES[erCode]?.name || (er.skills[0] ?? ""),
    skins: er.skins,
    skills: moves.map((move, i) => ({
      move,
      name: er.skills[i + 1] || `${er.name} ${SKILL_KEYS[i]}`,
      level: SHEET_SKILLS[erCode]?.[i]?.level ?? SKILL_LEVELS[i],
    })) as unknown as BseoCharacter["skills"],
  };
}

const PLAYABLE_BY_CODE = new Map(BSEO_PLAYABLE.map(c => [c.erCode, c]));

/** ER 실험체 전부 (고를 수 있는 실험체 + 적으로만 나오는 실험체) */
export const BSEO_CHARACTERS: readonly BseoCharacter[] = Object.keys(ER_CHARACTERS)
  .map(Number)
  .sort((a, b) => a - b)
  .map(code => buildCharacter(code, PLAYABLE_BY_CODE.get(code)))
  .filter((c): c is BseoCharacter => c != null);

const BY_CODE = new Map(BSEO_CHARACTERS.map(c => [c.erCode, c]));

/** ER 번호 → 실험체 */
export function bseoCharacter(erCode: number): BseoCharacter | undefined {
  return BY_CODE.get(erCode);
}

/** 시작 실험체 (도감처럼 ER 번호 순서) */
export const BSEO_STARTERS: readonly BseoCharacter[] = BSEO_CHARACTERS.filter(c => c.playable);

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

/** 야생동물 · 보스 스킬 이름 (효과는 빌려 쓰는 포켓로그 기술 그대로) */
export const ENEMY_MOVE_NAMES: Readonly<Partial<Record<MoveId, string>>> = {
  [MoveId.PECK]: "쪼기",
  [MoveId.GROWL]: "꼬꼬댁",
  [MoveId.WING_ATTACK]: "날개 치기",
  [MoveId.LEER]: "초음파",
  [MoveId.TACKLE]: "들이받기",
  [MoveId.TAKE_DOWN]: "돌진",
  [MoveId.BITE]: "물어뜯기",
  [MoveId.HYPER_FANG]: "송곳니",
  [MoveId.CRUNCH]: "깨물기",
  [MoveId.FURY_SWIPES]: "할퀴기",
  [MoveId.SLAM]: "앞발 내려찍기",
  [MoveId.SUPERPOWER]: "괴력",
  [MoveId.IRON_HEAD]: "강철 박치기",
  [MoveId.HEADBUTT]: "박치기",
  [MoveId.METEOR_MASH]: "강철 주먹",
  [MoveId.EXTREME_SPEED]: "순간 가속",
  [MoveId.MIRROR_SHOT]: "반사 광선",
  [MoveId.TRI_ATTACK]: "3연속 사격",
  [MoveId.GYRO_BALL]: "회전 돌격",
  [MoveId.AURA_SPHERE]: "파동",
  [MoveId.THUNDERBOLT]: "경계 방전",
  [MoveId.DAZZLING_GLEAM]: "경고등",
  [MoveId.PSYCHIC]: "시스템 간섭",
  [MoveId.CALM_MIND]: "연산 집중",
};

export const BSEO_STARTER_IDS = BSEO_STARTERS.map(c => c.id);
/** 실험체의 모든 모습 (기본 · 스킨 진화 1 · 2) */
export const BSEO_FORM_IDS: readonly SpeciesId[] = BSEO_CHARACTERS.flatMap(c => c.forms.map(f => f.id));
export const BSEO_ALL_IDS: readonly SpeciesId[] = [
  ...BSEO_FORM_IDS,
  ...BSEO_WILD.map(w => w.id),
  ...BSEO_BOSSES.map(b => b.id),
];
/** 적으로만 나오는 실험체의 기본 모습 */
export const BSEO_ENEMY_CHARACTER_IDS: readonly SpeciesId[] = BSEO_CHARACTERS.filter(c => !c.playable).map(c => c.id);
/**
 * 고를 수는 없지만 기록 칸(starterData)이 필요한 블서로그 종: 적으로만 나오는 실험체 · 야생동물 · 보스
 * (스킨 진화한 모습은 기본 모습의 기록 칸을 같이 써요)
 */
export const BSEO_NON_STARTER_IDS: readonly SpeciesId[] = [
  ...BSEO_ENEMY_CHARACTER_IDS,
  ...BSEO_WILD.map(w => w.id),
  ...BSEO_BOSSES.map(b => b.id),
];
