/*
 * SPDX-FileCopyrightText: 2026 SG
 * SPDX-License-Identifier: AGPL-3.0-only
 */

// 이 파일은 scripts/fankit/build_announce.py 가 만들어요. 직접 고치지 마세요.
// 소리 파일(assets/er/announce/)은 님블뉴런 팬키트 안내 방송(한국어)에서 가져와 줄인 것이에요.

/** 안내 방송 키 → 같은 방송 몇 개 (파일: er/announce/<키>_<0부터>.m4a) */
export const BSEO_ANNOUNCES = {
  /** 실험 시작 안내 */
  start: 2,
  /** 승리 안내 */
  win: 2,
  /** 생존자 사망 안내 */
  dead: 2,
  /** 첫 번째 금지구역 지정 */
  zone1: 2,
  /** 두 번째 금지구역 지정 */
  zone2: 2,
  /** 세 번째 금지구역 지정 */
  zone3: 2,
  /** 네 번째 금지구역 지정 */
  zone4: 2,
  /** 다섯 번째 금지구역 지정 */
  zone5: 2,
  /** 여섯 번째 금지구역 지정 */
  zone6: 2,
  /** 일곱 번째 금지구역 지정 */
  zone7: 2,
  /** 여덟 번째 금지구역 지정 */
  zone8: 2,
  /** 아홉 번째 금지구역 지정 */
  zone9: 2,
  /** 새 금지구역 지정 */
  zone: 2,
  /** 생존자가 적어 금지구역 가속 */
  hurry: 2,
  /** 생존자 10명 남음 */
  left10: 2,
  /** 생존자 5명 남음 */
  left5: 2,
  /** 최종 생존자 3명 */
  left3: 2,
  /** 최종 생존자 2명 */
  left2: 2,
  /** 임시 안전지대 해제 (더 이상 안전한 곳이 없음) */
  safe_off: 2,
  /** 시스템 비정상 접근 감지 */
  hack: 1,
  /** 누군가 연쇄 처치 중 */
  kill3: 2,
  /** 누군가 루미아 섬을 지배 중 */
  kill5: 2,
  /** 누군가 생존자의 절반을 처치 */
  kill7: 2,
  /** 전설이 탄생 중 */
  kill8: 2,
  /** 항공 보급 도착 */
  supply: 2,
  /** 1분 뒤 항공 보급 도착 */
  supply_soon: 2,
  /** 1분 뒤 마지막 금지구역 · 임시 안전지대 예고 */
  safe_soon: 2,
  /** 마지막 금지구역 지정 · 임시 안전지대 */
  safe_set: 2,
  /** 1분 뒤 임시 안전지대 해제 */
  safe_off_soon: 2,
} as const;

export type BseoAnnounceKey = keyof typeof BSEO_ANNOUNCES;
