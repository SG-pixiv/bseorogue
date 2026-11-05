/*
 * SPDX-FileCopyrightText: 2026 SG
 * SPDX-License-Identifier: AGPL-3.0-only
 */

/**
 * 지역마다 자주 나오는 역할군 (초안이에요. SG가 지역 분류를 정하면 이 표만 고치면 돼요)
 *
 * 일반 웨이브의 적은 대부분 실험체이고, 그 지역의 역할군이 3배 더 자주 나와요.
 * 지역 이름은 locales/ko/biomes.json 에서 바꿔요 (포켓로그 지역 35곳을 루미아 섬 20곳에 나눠 붙였어요).
 */
import type { ErRoleKey } from "#data/bseorogue/er-data";
import { BiomeId } from "#enums/biome-id";

const AREA = {
  alley: ["ASSASSIN", "BRUISER"], // 골목길
  archery: ["MARKSMAN"], // 양궁장
  stream: ["MARKSMAN", "BRUISER"], // 개울
  forest: ["ASSASSIN", "MARKSMAN"], // 숲
  uptown: ["SUPPORT", "MAGE"], // 고급 주택가
  harbor: ["BRUISER", "MARKSMAN"], // 항구
  pond: ["SUPPORT", "MAGE"], // 연못
  beach: ["MARKSMAN", "SUPPORT"], // 모래사장
  temple: ["BRUISER", "MAGE"], // 절
  gasStation: ["BRUISER", "TANK"], // 주유소
  warehouse: ["TANK", "BRUISER"], // 창고
  school: ["MAGE", "SUPPORT"], // 학교
  factory: ["TANK", "BRUISER"], // 공장
  fireStation: ["TANK", "SUPPORT"], // 소방서
  cemetery: ["MAGE", "ASSASSIN"], // 묘지
  police: ["MARKSMAN", "TANK"], // 경찰서
  chapel: ["SUPPORT", "MAGE"], // 성당
  hospital: ["SUPPORT", "TANK"], // 병원
  lab: [], // 연구소 (골고루)
} satisfies Record<string, ErRoleKey[]>;

export const REGION_ROLES: Readonly<Partial<Record<BiomeId, readonly ErRoleKey[]>>> = {
  [BiomeId.TOWN]: AREA.alley,
  [BiomeId.SLUM]: AREA.alley,
  [BiomeId.PLAINS]: AREA.archery,
  [BiomeId.GRASS]: AREA.stream,
  [BiomeId.TALL_GRASS]: AREA.forest,
  [BiomeId.FOREST]: AREA.forest,
  [BiomeId.JUNGLE]: AREA.forest,
  [BiomeId.SNOWY_FOREST]: AREA.forest,
  [BiomeId.METROPOLIS]: AREA.uptown,
  [BiomeId.SEA]: AREA.harbor,
  [BiomeId.SEABED]: AREA.harbor,
  [BiomeId.SWAMP]: AREA.pond,
  [BiomeId.LAKE]: AREA.pond,
  [BiomeId.BEACH]: AREA.beach,
  [BiomeId.DESERT]: AREA.beach,
  [BiomeId.ISLAND]: AREA.beach,
  [BiomeId.MOUNTAIN]: AREA.temple,
  [BiomeId.TEMPLE]: AREA.temple,
  [BiomeId.BADLANDS]: AREA.gasStation,
  [BiomeId.CAVE]: AREA.warehouse,
  [BiomeId.ICE_CAVE]: AREA.warehouse,
  [BiomeId.MEADOW]: AREA.school,
  [BiomeId.POWER_PLANT]: AREA.factory,
  [BiomeId.FACTORY]: AREA.factory,
  [BiomeId.CONSTRUCTION_SITE]: AREA.factory,
  [BiomeId.VOLCANO]: AREA.fireStation,
  [BiomeId.GRAVEYARD]: AREA.cemetery,
  [BiomeId.WASTELAND]: AREA.cemetery,
  [BiomeId.DOJO]: AREA.police,
  [BiomeId.RUINS]: AREA.chapel,
  [BiomeId.FAIRY_CAVE]: AREA.hospital,
  [BiomeId.ABYSS]: AREA.lab,
  [BiomeId.SPACE]: AREA.lab,
  [BiomeId.LABORATORY]: AREA.lab,
  [BiomeId.END]: AREA.lab,
};
