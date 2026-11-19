/*
 * SPDX-FileCopyrightText: 2026 SG
 * SPDX-License-Identifier: AGPL-3.0-only
 */

// 이 파일은 scripts/er-ui/make_arenas.py 가 만들어요. 직접 고치지 마세요.
// 그림(assets/er/arena)은 이터널 리턴 스토리 모드 배경 그림을 도트로 줄인 것이에요 (님블뉴런 저작물).

/** 전투 배경 열쇠(<바이옴>_bg) → 대신 받을 파일 (assets 기준). 여기 없는 배경은 assets/images/arenas 의 코드 그림 */
export const ER_ARENA_FILES: Readonly<Record<string, string>> = {
  abyss_bg: "er/arena/lab_bg.png",
  beach_bg: "er/arena/beach_bg.png",
  construction_site_bg: "er/arena/factory_bg.png",
  default_bg: "er/arena/lab_bg.png",
  desert_bg: "er/arena/beach_bg.png",
  end_bg: "er/arena/lab_bg.png",
  factory_bg: "er/arena/factory_bg.png",
  forest_bg: "er/arena/forest_bg.png",
  graveyard_bg: "er/arena/cemetery_bg.png",
  island_bg: "er/arena/beach_bg.png",
  jungle_bg: "er/arena/forest_bg.png",
  laboratory_bg: "er/arena/lab_bg.png",
  power_plant_bg: "er/arena/factory_bg.png",
  rockycoast_bg: "er/arena/harbor_bg.png",
  ruins_bg: "er/arena/chapel_bg.png",
  sea_bg: "er/arena/harbor_bg.png",
  slum_bg: "er/arena/alley_bg.png",
  snowy_forest_bg: "er/arena/hotel_bg.png",
  space_bg: "er/arena/lab_bg.png",
  tall_grass_bg: "er/arena/forest_bg.png",
  town_bg: "er/arena/alley_bg.png",
  wasteland_bg: "er/arena/cemetery_bg.png",
};
