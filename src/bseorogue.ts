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
  /**
   * 판 중 영입(포획). 11-12 SG: 볼은 한 종류, 일정 횟수가 되면 무조건 잡히고, 잡은 실험체는 다음 판부터 고를 수 있게 해금.
   * 보급 상자(알 뽑기)는 그대로 (src/data/bseorogue/catch.ts)
   */
  allowCatch: true,
  /** 실패가 쌓여 이 번째로 던지는 볼은 반드시 잡혀요 (판 전체에서 이어지고, 잡으면 처음부터) */
  catchGuaranteedThrow: 3,
  /** 판을 시작할 때 볼 개수 · 보상으로 볼이 나올 때 개수 */
  startBalls: 3,
  ballRewardCount: 2,
  /**
   * 처음부터 고를 수 있는 실험체 (ER 번호). 나머지는 판 중에 잡거나 보급 상자에서 얻으면 열려요.
   * 일레븐 · 유키 · 쇼이치 · 나딘 · 혜진 · 레니 (처음 직접 고른 시작 6명). 예전 저장에서 이미 열린 실험체는 그대로예요.
   */
  startUnlocked: [30, 11, 18, 6, 12, 69] as readonly number[],
  /** 클래식만 (새 게임에서 모드 고르기 없이 바로 클래식) */
  classicOnly: true,
  /** 포켓로그 최종 보스(무한다이노) 2단계 연출. 블서로그는 루미 연출을 따로 만들 때까지 끔 */
  pokerogueFinale: false,
  /**
   * 팀 전투가 나오는 웨이브 (팀마다 실험체 3명, 무명섬 관리 화면에서 정해요).
   * 그 웨이브가 어느 리그인지에 따라 마스터즈 팀 또는 KEL 팀이 나와요 (leagues)
   */
  teamWaves: [5, 15, 25, 35, 45],
  /**
   * 판 안 승단: fromWave 부터 그 리그예요. 마스터즈 구간의 팀 전투는 마스터즈 팀, 그다음은 KEL 팀
   * (src/data/bseorogue/league.ts)
   */
  leagues: [
    { key: "masters", name: "마스터즈", fromWave: 1 },
    { key: "kel", name: "KEL", fromWave: 21 },
    { key: "final", name: "KEL 결승", fromWave: 41 },
  ],
  /** 역할군 관장이 나오는 웨이브 (src/data/bseorogue/leaders.ts) */
  leaderWaves: [8, 18, 28, 38, 48],
  /** 일반 웨이브에서 동물이 나올 확률 (나머지는 실험체) */
  wildAnimalRate: 0.25,
  /** 미스터리 인카운터 (포켓몬 이야기라 꺼 둬요) */
  mysteryEncounters: false,
  /** 무명섬 (랭킹 · 소식 · 피드백) */
  mumeiUrl: import.meta.env.VITE_MUMEI_URL || "https://mumeiisland.vercel.app",
  /** 소스 코드 (AGPL-3.0: 게임을 쓰는 누구나 받을 수 있어야 해요) */
  sourceUrl: import.meta.env.VITE_GITHUB_URL || "https://github.com/SG-pixiv/bseorogue",
} as const;
