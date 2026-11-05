/*
 * SPDX-FileCopyrightText: 2026 SG
 * SPDX-License-Identifier: AGPL-3.0-only
 */

/**
 * 판 안 승단 (포켓로그 관장 → 사천왕 → 챔피언 자리)
 *
 * 마스터즈(1~20웨이브) → KEL 승격(21~40) → KEL 결승(41~50, 마지막은 루미)
 * 리그마다 팀 전투 상대가 바뀌고, 승격하는 웨이브에서 안내가 나와요. 구간은 BSEO.leagues 에서 바꿔요.
 */
import { BSEO } from "#app/bseorogue";

export type LeagueKey = (typeof BSEO.leagues)[number]["key"];
export interface League {
  key: LeagueKey;
  name: string;
  fromWave: number;
}

/** 이 웨이브의 리그 */
export function leagueForWave(waveIndex: number): League {
  let out: League = BSEO.leagues[0];
  for (const l of BSEO.leagues) {
    if (waveIndex >= l.fromWave) {
      out = l;
    }
  }
  return out;
}

/** 팀 전투에 나오는 팀의 리그 (마스터즈 구간 → 마스터즈 팀, 그다음 → KEL 팀) */
export function teamLeagueForWave(waveIndex: number): "masters" | "kel" {
  return leagueForWave(waveIndex).key === "masters" ? "masters" : "kel";
}

const PROMOTION: Partial<Record<LeagueKey, string>> = {
  masters: "마스터즈 리그에 참가했어요!$KEL까지 올라가 봐요!",
  kel: "축하해요! KEL로 승격했어요!$이제부터는 프로 팀이 상대예요.",
  final: "KEL 결승 진출!$마지막 10웨이브, 끝까지 힘내요!",
};

/** 리그가 바뀌는 웨이브면 루미의 안내 (아니면 null) */
export function promotionMessage(waveIndex: number): string | null {
  const l = BSEO.leagues.find(x => x.fromWave === waveIndex);
  return l ? (PROMOTION[l.key] ?? null) : null;
}
