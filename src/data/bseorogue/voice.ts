/*
 * SPDX-FileCopyrightText: 2026 SG
 * SPDX-License-Identifier: AGPL-3.0-only
 */

/**
 * 실험체 음성 (팬키트 음성 · scripts/fankit/build_voice.py 가 assets/er/voice/ 에 만들어요)
 *
 * - 스킬 Q · W · E · R (skill-moves.ts 순서) 을 쓰면 그 스킬 음성
 * - 실험체가 나올 때 · 고를 때는 등장 대사 (포켓몬 울음소리 대신)
 * - 쓰러질 때는 쓰러지는 대사 (pokemon.ts 의 faintCry)
 * 키마다 대사가 최대 3개라 매번 무작위로 고르고, 바로 전에 나온 대사는 다시 고르지 않아요.
 * 소리 크기는 게임 설정의 효과음 크기를 따라요. 음성 파일이 없으면 조용히 넘어가요.
 * 새 음성이 나오면 앞 음성은 끊어요 (캐릭터를 빨리 넘겨도 대사가 겹치지 않게, 11-18 SG).
 * 아직 받는 중인 음성은 그 사이 다른 음성을 틀었으면 받고 나서도 안 틀어요.
 * 안내 방송(announce.ts)이 나오는 동안은 실험체 대사를 새로 틀지 않아요 (11-18, 방송과 대사가 겹치지 않게).
 */
import { audioManager } from "#app/global-audio-manager";
import { globalScene } from "#app/global-scene";
import type { AnySound } from "#audio/audio-manager";
import { erCodeOfSpecies } from "#data/bseorogue/roster";
import { SKILL_MOVES } from "#data/bseorogue/skill-moves";
import { BSEO_VOICES, type BseoVoiceKey } from "#data/bseorogue/voice-manifest";
import type { MoveId } from "#enums/move-id";
import type { SpeciesId } from "#enums/species-id";
import { randInt } from "#utils/common";
import { getCachedUrl } from "#utils/fetch-utils";

export type { BseoVoiceKey } from "#data/bseorogue/voice-manifest";

const SKILL_KEYS: readonly BseoVoiceKey[] = ["q", "w", "e", "r"];

/** "ER번호_키" → 바로 전에 튼 대사 번호 */
const lastPlayed = new Map<string, number>();

/** 음성 소리 열쇠 앞부분 */
const VOICE_PREFIX = "se/bseo_";

/** 안내 방송 소리 열쇠 앞부분 (announce.ts). "se/bseo_" 로 시작하지 않아서 stopBseoVoices 가 끊지 않아요 */
export const BSEO_ANNOUNCE_PREFIX = "se/bseo-ann_";

/** 음성을 틀어 달라고 한 횟수 (받는 중이던 음성이 아직 마지막 요청인지 볼 때) */
let voiceRequest = 0;

type PlayingSound = { key: string; isPlaying?: boolean; stop: () => unknown; destroy: () => unknown };

function playingSounds(): readonly PlayingSound[] {
  return (
    (globalScene?.sound as unknown as { getAllPlaying?: () => PlayingSound[] } | undefined)?.getAllPlaying?.() ?? []
  );
}

/** 안내 방송이 나오고 있는지 */
export function bseoAnnouncing(sounds: readonly PlayingSound[] = playingSounds()): boolean {
  return sounds.some(s => s.key.startsWith(BSEO_ANNOUNCE_PREFIX) && s.isPlaying !== false);
}

/** 지금 나오고 있는 실험체 음성을 다 끊어요 (끊은 수) */
export function stopBseoVoices(sounds: readonly PlayingSound[] = playingSounds()): number {
  let n = 0;
  for (const s of [...sounds]) {
    if (s.key.startsWith(VOICE_PREFIX) && s.isPlaying !== false) {
      s.stop();
      // play() 로 만든 소리는 끝나야 지워지는데, 끊으면 안 끝나서 직접 지워요
      s.destroy();
      n++;
    }
  }
  return n;
}

/** 스킬 → 음성 키 (그 실험체의 Q W E R 이 아니면 null) */
export function bseoSkillVoiceKey(speciesId: SpeciesId, moveId: MoveId): BseoVoiceKey | null {
  const code = erCodeOfSpecies(speciesId);
  const index = code == null ? -1 : (SKILL_MOVES[code]?.indexOf(moveId) ?? -1);
  return index >= 0 ? SKILL_KEYS[index] : null;
}

/** 그 키의 대사 수 (없으면 0) */
export function bseoVoiceCount(speciesId: SpeciesId, key: BseoVoiceKey): number {
  const code = erCodeOfSpecies(speciesId);
  return code == null ? 0 : (BSEO_VOICES[code]?.[key] ?? 0);
}

/** 음성 파일 (assets 기준 경로). 없으면 null */
export function bseoVoiceFile(speciesId: SpeciesId, key: BseoVoiceKey, index = 0): string | null {
  const code = erCodeOfSpecies(speciesId);
  return code != null && index >= 0 && index < bseoVoiceCount(speciesId, key)
    ? `er/voice/${code}_${key}_${index}.m4a`
    : null;
}

/** 다음에 틀 대사 번호: 무작위, 단 대사가 2개 이상이면 바로 전 대사는 빼요 */
export function nextBseoVoiceIndex(count: number, last: number | undefined): number {
  if (count <= 1) {
    return 0;
  }
  if (last == null || last < 0 || last >= count) {
    return randInt(count);
  }
  const pick = randInt(count - 1);
  return pick >= last ? pick + 1 : pick;
}

/** Phaser 소리 열쇠. "se/" 로 시작해서 효과음 크기를 따라요 */
function soundKey(file: string): string {
  return `${VOICE_PREFIX}${file.replace(/^er\/voice\//, "").replace(/\.m4a$/, "")}`;
}

function canPlay(): boolean {
  return !!audioManager?.isAudioEnabled && typeof globalScene?.load?.audio === "function";
}

/** 그 실험체 음성을 미리 받아 두기 (그림을 받을 때 같이). 받기 시작은 부르는 쪽이 해요 */
export function loadBseoVoices(speciesId: SpeciesId): void {
  const code = erCodeOfSpecies(speciesId);
  if (code == null || !canPlay()) {
    return;
  }
  for (const [key, count] of Object.entries(BSEO_VOICES[code] ?? {})) {
    for (let i = 0; i < (count ?? 0); i++) {
      const file = `er/voice/${code}_${key}_${i}.m4a`;
      if (!globalScene.cache.audio.exists(soundKey(file))) {
        globalScene.load.audio(soundKey(file), getCachedUrl(file));
      }
    }
  }
}

/** 음성 틀기 (대사 여러 개 중 하나). 아직 안 받았으면 받고 나서 틀어요. 없으면 null */
export function playBseoVoice(speciesId: SpeciesId, key: BseoVoiceKey): AnySound | null {
  const code = erCodeOfSpecies(speciesId);
  const count = bseoVoiceCount(speciesId, key);
  if (code == null || count === 0 || !canPlay() || bseoAnnouncing()) {
    return null;
  }
  const slot = `${code}_${key}`;
  const index = nextBseoVoiceIndex(count, lastPlayed.get(slot));
  lastPlayed.set(slot, index);
  const file = `er/voice/${code}_${key}_${index}.m4a`;
  const sk = soundKey(file);
  // 앞 음성은 바로 끊어요 (새 음성을 아직 받는 중이어도)
  stopBseoVoices();
  const request = ++voiceRequest;
  if (globalScene.cache.audio.exists(sk)) {
    return audioManager.playSound(sk);
  }
  globalScene.load.once(`filecomplete-audio-${sk}`, () => {
    // 받는 사이에 다른 음성을 틀었으면 이건 안 틀어요 (늦게 받은 대사가 뒤늦게 겹쳐 나오지 않게)
    if (request === voiceRequest) {
      stopBseoVoices();
      audioManager.playSound(sk);
    }
  });
  globalScene.load.audio(sk, getCachedUrl(file));
  if (!globalScene.load.isLoading()) {
    globalScene.load.start();
  }
  return null;
}

/** 스킬을 쓸 때: 그 실험체의 Q W E R 이면 스킬 음성 */
export function playBseoSkillVoice(speciesId: SpeciesId, moveId: MoveId): void {
  const key = bseoSkillVoiceKey(speciesId, moveId);
  if (key) {
    playBseoVoice(speciesId, key);
  }
}
