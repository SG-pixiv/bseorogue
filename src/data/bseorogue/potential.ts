/*
 * SPDX-FileCopyrightText: 2026 SG
 * SPDX-License-Identifier: AGPL-3.0-only
 */

/**
 * 잠재력: 포켓로그의 개체값(능력 6개 × 0~31)을 화면에는 등급 한 줄로만 보여 줘요 (11-12 SG "추천대로").
 *
 * 개체값 자체는 안에서 그대로 돌아요: 같은 실험체를 다시 얻으면(보급 상자 · 포획) 능력마다 더 좋은 값으로 갱신되고,
 * 그래서 겹쳐 얻을수록 등급이 올라가요. 숫자 6개 · 육각형 그림 · 실험체 분석기는 안 써요.
 */

export type BseoPotentialGrade = "S" | "A" | "B" | "C" | "D";

/** 등급 → 6개 합(0~186)이 이 값 이상. 한 번 얻으면 보통 C~B, 두세 번 겹치면 A, 여러 번 겹쳐야 S */
const GRADE_FLOOR: readonly [BseoPotentialGrade, number][] = [
  ["S", 168],
  ["A", 140],
  ["B", 103],
  ["C", 66],
  ["D", 0],
];

/** 등급 글자 색 (S 금 · A 파랑 · B 초록 · C 흰색 · D 회색) */
export const BSEO_POTENTIAL_COLOR: Readonly<Record<BseoPotentialGrade, string>> = {
  S: "#f8d030",
  A: "#78c8f8",
  B: "#98d8a0",
  C: "#f8f8f8",
  D: "#a0a0a8",
};

export function bseoPotentialGrade(ivs: readonly number[]): BseoPotentialGrade {
  const sum = ivs.reduce((a, b) => a + b, 0);
  return GRADE_FLOOR.find(([, floor]) => sum >= floor)?.[0] ?? "D";
}

/** 새로 얻은 값이 지금 기록보다 나은 능력이 하나라도 있는지 (얻으면 잠재력이 오름) */
export function bseoPotentialImproves(ivs: readonly number[], recorded: readonly number[]): boolean {
  return ivs.some((v, i) => v > (recorded[i] ?? 0));
}
