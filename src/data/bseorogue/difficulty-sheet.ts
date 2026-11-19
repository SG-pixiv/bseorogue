/*
 * SPDX-FileCopyrightText: 2026 SG
 * SPDX-License-Identifier: AGPL-3.0-only
 */

// 이 파일은 scripts/er-sheet/difficulty_sheet.py 가 만들어요 (docs/sheets/난이도.xlsx). 직접 고치지 마세요.

/** 팀 전투 자리에 나오는 것: 사기 실험체(영입 불가 보스) · 마스터즈 팀 · KEL 팀 */
export type TeamSlotKind = "op" | "masters" | "kel";

export interface MastersTeam {
  name: string;
  /** 실험체 ER 번호 (마지막이 에이스) */
  members: readonly number[];
  encounter: string;
  /** 플레이어가 이겼을 때 */
  defeated: string;
  /** 플레이어가 졌을 때 */
  won: string;
}

/** 시트 '마스터즈 팀': 관장 웨이브에 나오는 팀 */
export const MASTERS_TEAMS: readonly MastersTeam[] = [
  {
    name: "마스터즈 1팀 (임시)",
    members: [18, 2, 4],
    encounter: "여기서부턴 못 지나가.$우리 팀이 얼마나 단단한지 보여 주지!",
    defeated: "…이걸 버텨 내다니. 지나가도 좋아.",
    won: "벽은 부수는 게 아니라 넘는 거야. 다시 와.",
  }, // 쇼이치 · 아야 · 매그너스
  {
    name: "마스터즈 2팀 (임시)",
    members: [21, 73, 1],
    encounter: "정면으로 붙자!$우리는 도망치지 않아!",
    defeated: "좋은 싸움이었어. 더 세져서 또 만나!",
    won: "아직 멀었네. 몸부터 다시 만들어 와!",
  }, // 로지 · 샬럿 · 재키
  {
    name: "마스터즈 3팀 (임시)",
    members: [26, 55, 23],
    encounter: "눈치챘을 땐 이미 늦었어.",
    defeated: "내 움직임을 다 읽다니… 인정할게.",
    won: "뒤를 조심했어야지.",
  }, // 바바라 · 에스텔 · 캐시
  {
    name: "마스터즈 4팀 (임시)",
    members: [51, 33, 31],
    encounter: "사거리 안에 들어온 순간 끝이야.",
    defeated: "조준이 빗나갔네. 네가 이겼어.",
    won: "거리를 못 좁히면 이길 수 없어.",
  }, // 프리야 · 니키 · 리오
  {
    name: "마스터즈 5팀 (임시)",
    members: [30, 37, 5],
    encounter: "스킬 한 방이면 충분하다.",
    defeated: "계산이 틀렸군… 다음엔 지지 않는다.",
    won: "스킬 저항을 더 챙기는 게 좋을 거다.",
  }, // 일레븐 · 다니엘 · 자히르
  {
    name: "마스터즈 6팀 (임시)",
    members: [56, 25, 41],
    encounter: "우리 팀은 쉽게 쓰러지지 않아요!",
    defeated: "끝까지 지켜 내지 못했네요… 축하해요!",
    won: "혼자 싸우면 오래 못 버텨요.",
  }, // 피올로 · 버니스 · 요한
];

/** 시트 '팀 전투 자리': [티어 0 아이언 ~ 9 이터니티][팀 전투 웨이브 순서 (BSEO.teamWaves)] */
export const TEAM_SLOTS: readonly (readonly TeamSlotKind[])[] = [
  ["op", "op", "op", "op", "op"], // 아이언
  ["op", "op", "op", "op", "op"], // 브론즈
  ["op", "op", "op", "op", "op"], // 실버
  ["op", "op", "op", "op", "op"], // 골드
  ["op", "op", "op", "op", "op"], // 플래티넘
  ["op", "op", "op", "op", "op"], // 다이아몬드
  ["op", "op", "op", "op", "op"], // 메테오라이트
  ["op", "masters", "op", "masters", "op"], // 미스릴
  ["masters", "kel", "kel", "kel", "kel"], // 데미갓
  ["masters", "kel", "kel", "kel", "kel"], // 이터니티
];

export interface OpExperiment {
  erCode: number;
  /** 보스 체력 줄 수 */
  segments: number;
}

/** 시트 '사기 실험체' (비어 있으면 아무 실험체나 보스 버전으로) */
export const OP_EXPERIMENTS: readonly OpExperiment[] = [];

/** '사기 실험체' 시트에 체력 줄 수를 안 적었을 때 · 목록이 비어 아무 실험체나 나올 때 */
export const OP_DEFAULT_SEGMENTS = 3;
