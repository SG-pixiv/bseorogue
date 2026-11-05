/*
 * SPDX-FileCopyrightText: 2026 SG
 * SPDX-License-Identifier: AGPL-3.0-only
 */

/**
 * 블서로그 규칙 (포켓로그에서 바꾼 것들을 한곳에 모아 둬요)
 * 숫자를 바꾸면 게임 전체에 적용돼요. 자세한 기획은 docs/기획.md
 */
export const BSEO = {
  /** 게임 버전 (랭킹에 같이 올라가요. 큰 밸런스 패치 때 올려요) */
  version: "0.1.0",
  /** 파티 최대 인원 (포켓로그 6) */
  partyMax: 3,
  /** 클래식 마지막 웨이브 (포켓로그 200). 이 웨이브가 최종 보스예요 */
  classicFinalWave: 50,
  /** 1:1 싱글 배틀만 (포켓로그는 더블 배틀이 섞여요) */
  singleBattlesOnly: true,
  /** 판 중 영입(포획). 블서로그는 보급 상자(가챠)로만 실험체를 만나요 */
  allowCatch: false,
  /** 클래식만 (새 게임에서 모드 고르기 없이 바로 클래식) */
  classicOnly: true,
  /** 포켓로그 최종 보스(무한다이노) 2단계 연출. 블서로그는 루미 연출을 따로 만들 때까지 끔 */
  pokerogueFinale: false,
  /** KEL 팀 전투가 나오는 웨이브 (팀마다 실험체 3명, 무명섬 관리 화면에서 정해요) */
  kelWaves: [5, 15, 25, 35, 45],
  /** 미스터리 인카운터 (포켓몬 이야기라 꺼 둬요) */
  mysteryEncounters: false,
  /** 무명섬 (랭킹 · 소식 · 피드백) */
  mumeiUrl: import.meta.env.VITE_MUMEI_URL || "https://mumeiisland.vercel.app",
  /** 소스 코드 (AGPL-3.0: 게임을 쓰는 누구나 받을 수 있어야 해요) */
  sourceUrl: import.meta.env.VITE_GITHUB_URL || "https://github.com/SG-pixiv/bseorogue",
} as const;
