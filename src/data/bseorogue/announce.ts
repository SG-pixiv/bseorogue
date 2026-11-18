/*
 * SPDX-FileCopyrightText: 2026 SG
 * SPDX-License-Identifier: AGPL-3.0-only
 */

/**
 * 루미아 섬 안내 방송 (팬키트 한국어 안내 방송 · scripts/fankit/build_announce.py 가 assets/er/announce/ 에 만들어요)
 *
 * 트는 곳 (클래식 50웨이브 기준, 11-18):
 * - 판 시작 (1웨이브가 처음 나올 때): 실험 시작 안내
 * - 전투에서 이긴 뒤 (`bseoAnnounceAfterWin`, 한 웨이브에 하나만):
 *   49 → 임시 안전지대 해제 · 48/47/45/40 → 생존자 2/3/5/10명 남음 · 10/20/30 → N번째 금지구역 지정 ·
 *   25 → 생존자의 절반 처치 · 쓰러진 실험체 없이 5/15/35연승 → 연쇄 처치 / 섬을 지배 / 전설이 탄생
 *   (연승 수는 10의 배수 · 25 와 안 겹치게 골랐어요. 처음부터 안 쓰러지면 5 · 15 · 35웨이브)
 * - 최종 보스(50웨이브 루미)가 나올 때: 시스템 비정상 접근 감지
 * - 판 끝: 이기면 "승리했습니다" · 지면 "생존자가 사망했습니다"
 * - 보급 요청(뽑기)에서 보급 상자가 나올 때: 항공 보급 도착
 *
 * 같은 방송이 2개씩 있어서 무작위로 하나를 골라요 (시드 없는 randInt 라 전투 결과에 영향 없음).
 * 방송이 나오는 동안은 실험체 대사를 새로 틀지 않아요 (voice.ts). 소리 크기는 효과음 크기를 따라요.
 * 소리 파일이 없거나 소리가 꺼져 있으면 조용히 넘어가요.
 */
import { BSEO } from "#app/bseorogue";
import { audioManager } from "#app/global-audio-manager";
import { globalScene } from "#app/global-scene";
import { BSEO_ANNOUNCES, type BseoAnnounceKey } from "#data/bseorogue/announce-manifest";
import { BSEO_ANNOUNCE_PREFIX } from "#data/bseorogue/voice";
import { randInt } from "#utils/common";
import { getCachedUrl } from "#utils/fetch-utils";

export type { BseoAnnounceKey } from "#data/bseorogue/announce-manifest";

/** 남은 웨이브 수 → 방송 (그 웨이브를 이겼을 때) */
const LEFT: Readonly<Record<number, BseoAnnounceKey>> = {
  1: "safe_off",
  2: "left2",
  3: "left3",
  5: "left5",
  10: "left10",
};

/** 연승 수 → 방송 (쓰러진 실험체 없이 이긴 전투 수) */
const STREAK: Readonly<Record<number, BseoAnnounceKey>> = { 5: "kill3", 15: "kill5", 35: "kill8" };

/** 쓰러진 실험체 없이 이어서 이긴 전투 수 (판마다 0부터, 저장하지 않아요) */
let winStreak = 0;

/** 방송을 틀어 달라고 한 횟수 (받는 중이던 방송이 아직 마지막 요청인지 볼 때) */
let announceRequest = 0;

/** 전투에서 이긴 뒤 나올 방송. 없으면 null (마지막 웨이브는 판 끝 방송이라 null) */
export function bseoAnnounceAfterWin(
  wave: number,
  streak: number,
  finalWave: number = BSEO.classicFinalWave,
): BseoAnnounceKey | null {
  const left = finalWave - wave;
  if (left <= 0) {
    return null;
  }
  if (LEFT[left]) {
    return LEFT[left];
  }
  if (wave % 10 === 0) {
    const n = wave / 10;
    return n <= 9 ? (`zone${n}` as BseoAnnounceKey) : "zone";
  }
  if (wave * 2 === finalWave) {
    return "kill7";
  }
  return STREAK[streak] ?? null;
}

/** 웨이브가 시작될 때 나올 방송 (판 시작 · 최종 보스). 없으면 null */
export function bseoAnnounceOnEncounter(
  wave: number,
  loaded: boolean,
  finalWave: number = BSEO.classicFinalWave,
): BseoAnnounceKey | null {
  if (wave === 1 && !loaded) {
    return "start";
  }
  return wave === finalWave ? "hack" : null;
}

/** 지금 연승 수 */
export function bseoWinStreak(): number {
  return winStreak;
}

/** 방송 파일 (assets 기준 경로). 없으면 null */
export function bseoAnnounceFile(key: BseoAnnounceKey, index = 0): string | null {
  const count: number = BSEO_ANNOUNCES[key] ?? 0;
  return index >= 0 && index < count ? `er/announce/${key}_${index}.m4a` : null;
}

function canPlay(): boolean {
  return !!audioManager?.isAudioEnabled && typeof globalScene?.load?.audio === "function";
}

type PlayingSound = { key: string; isPlaying?: boolean; stop: () => unknown; destroy: () => unknown };

/** 나오고 있던 방송을 끊어요 */
function stopAnnouncements(): void {
  const sounds =
    (globalScene?.sound as unknown as { getAllPlaying?: () => PlayingSound[] } | undefined)?.getAllPlaying?.() ?? [];
  for (const s of [...sounds]) {
    if (s.key.startsWith(BSEO_ANNOUNCE_PREFIX)) {
      s.stop();
      s.destroy();
    }
  }
}

/** 방송 틀기 (같은 방송 2개 중 하나). 아직 안 받았으면 받고 나서 틀어요. 틀었거나 받기 시작했으면 true */
export function bseoAnnounce(key: BseoAnnounceKey): boolean {
  const count: number = BSEO_ANNOUNCES[key] ?? 0;
  if (count === 0 || !canPlay()) {
    return false;
  }
  const index = count > 1 ? randInt(count) : 0;
  const file = `er/announce/${key}_${index}.m4a`;
  const sk = `${BSEO_ANNOUNCE_PREFIX}${key}_${index}`;
  stopAnnouncements();
  const request = ++announceRequest;
  if (globalScene.cache.audio.exists(sk)) {
    audioManager.playSound(sk);
    return true;
  }
  globalScene.load.once(`filecomplete-audio-${sk}`, () => {
    // 받는 사이에 다른 방송을 틀었으면 이건 안 틀어요
    if (request === announceRequest) {
      stopAnnouncements();
      audioManager.playSound(sk);
    }
  });
  globalScene.load.audio(sk, getCachedUrl(file));
  if (!globalScene.load.isLoading()) {
    globalScene.load.start();
  }
  return true;
}

/** 클래식 판인지 (방송은 클래식 50웨이브 기준) */
function isClassic(): boolean {
  return !!globalScene?.gameMode?.isClassic;
}

/** encounter-phase.ts: 웨이브가 시작될 때 */
export function bseoAnnounceEncounterStart(wave: number, loaded: boolean): void {
  if (wave === 1 && !loaded) {
    winStreak = 0;
  }
  const key = isClassic() ? bseoAnnounceOnEncounter(wave, loaded) : null;
  if (key) {
    bseoAnnounce(key);
  }
}

/** battle-end-phase.ts: 전투가 끝났을 때 (이겼으면 연승을 세고 방송) */
export function bseoAnnounceBattleEnd(victory: boolean, wave: number, playerFainted: boolean): void {
  if (!victory) {
    return;
  }
  winStreak = playerFainted ? 0 : winStreak + 1;
  const key = isClassic() ? bseoAnnounceAfterWin(wave, winStreak) : null;
  if (key) {
    bseoAnnounce(key);
  }
}

/** game-over-phase.ts: 판이 끝났을 때 */
export function bseoAnnounceGameOver(victory: boolean): void {
  winStreak = 0;
  bseoAnnounce(victory ? "win" : "dead");
}
