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
  return `se/bseo_${file.replace(/^er\/voice\//, "").replace(/\.m4a$/, "")}`;
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
  if (code == null || count === 0 || !canPlay()) {
    return null;
  }
  const slot = `${code}_${key}`;
  const index = nextBseoVoiceIndex(count, lastPlayed.get(slot));
  lastPlayed.set(slot, index);
  const file = `er/voice/${code}_${key}_${index}.m4a`;
  const sk = soundKey(file);
  if (globalScene.cache.audio.exists(sk)) {
    return audioManager.playSound(sk);
  }
  globalScene.load.once(`filecomplete-audio-${sk}`, () => audioManager.playSound(sk));
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
