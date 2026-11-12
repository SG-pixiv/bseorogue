/*
 * SPDX-FileCopyrightText: 2026 SG
 * SPDX-License-Identifier: AGPL-3.0-only
 */

import { BSEO } from "#app/bseorogue";
import { globalScene } from "#app/global-scene";
import { erCodeOfSpecies } from "#data/bseorogue/roster";
import type { SpeciesId } from "#enums/species-id";

/**
 * 판 중 영입 (11-12 SG):
 * - 볼은 한 종류 (포켓로그 몬스터볼 자리). 볼 고르는 창 없이 '영입' 을 누르면 바로 던져요.
 * - 확률은 포켓로그 식 그대로 (체력이 낮을수록 · 상태이상이면 더 잘 잡힘).
 * - 실패 횟수가 판 전체에서 쌓이고, BSEO.catchGuaranteedThrow 번째는 반드시 잡혀요. 잡으면 0 으로.
 * - 실험체만 잡을 수 있어요 (야생동물 · 보스 · 팀 전투는 안 됨).
 * - 잡은 실험체는 다음 판부터 시작 실험체로 고를 수 있어요 (포켓로그의 포획 기록 그대로).
 *
 * 실패 횟수는 battle-scene.ts 의 bseoCatchFails (판 저장 파일에도 같이 저장).
 */

/** 다음에 던지는 볼이 반드시 잡히는지 */
export function bseoNextThrowGuaranteed(): boolean {
  return globalScene.bseoCatchFails >= BSEO.catchGuaranteedThrow - 1;
}

/** 확정까지 남은 횟수 (1 이면 다음 볼이 확정) */
export function bseoThrowsUntilGuaranteed(): number {
  return Math.max(1, BSEO.catchGuaranteedThrow - globalScene.bseoCatchFails);
}

/** 영입할 수 있는 상대인지: 실험체만 (야생동물 · 보스는 종 번호가 실험체 범위 밖) */
export function bseoCanCatchSpecies(speciesId: SpeciesId): boolean {
  return erCodeOfSpecies(speciesId) != null;
}
