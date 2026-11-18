/*
 * SPDX-FileCopyrightText: 2026 SG
 * SPDX-License-Identifier: AGPL-3.0-only
 */

/**
 * 실험체 스킬 효과음 (이터널 리턴 게임 소리, scripts/sound/build_er_sound.py 가 assets/er/sfx/ 에 만들어요)
 *
 * 실험체가 자기 스킬(Q W E R = skill-moves.ts 순서)을 쓰면, 공용 연출(베기 · 타격 · 투사체 …)의 소리 대신
 * 그 스킬의 게임 소리를 틀어요 (battle-anims.ts 의 AnimTimedSoundEvent).
 * 소리는 그 실험체 그림 · 음성을 받을 때 같이 받아요. 없거나 아직 못 받았으면 공용 연출 소리 그대로예요.
 * 소리 열쇠가 "battle_anims/" 로 시작해서 게임 설정의 '필드' 크기를 따라요 (음성 끊기 stopBseoVoices 와도 안 겹쳐요).
 */
import { audioManager } from "#app/global-audio-manager";
import { globalScene } from "#app/global-scene";
import { ER_SKILL_SFX } from "#data/bseorogue/er-sound-manifest";
import { erCodeOfSpecies } from "#data/bseorogue/roster";
import { SKILL_MOVES } from "#data/bseorogue/skill-moves";
import type { MoveId } from "#enums/move-id";
import type { SpeciesId } from "#enums/species-id";
import { getCachedUrl } from "#utils/fetch-utils";

const SKILL_KEYS = ["q", "w", "e", "r"] as const;

/** 그 실험체의 그 스킬 효과음 파일 (assets 기준). 실험체 스킬이 아니거나 소리가 없으면 null */
export function bseoSkillSfxFile(speciesId: SpeciesId, moveId: MoveId): string | null {
  const code = erCodeOfSpecies(speciesId);
  if (code == null) {
    return null;
  }
  const key = SKILL_KEYS[SKILL_MOVES[code]?.indexOf(moveId) ?? -1];
  return key && ER_SKILL_SFX[code]?.includes(key) ? `er/sfx/${code}_${key}.m4a` : null;
}

/** Phaser 소리 열쇠 */
export function bseoSkillSfxKey(file: string): string {
  return `battle_anims/bseo_sfx_${file.replace(/^er\/sfx\//, "").replace(/\.m4a$/, "")}`;
}

/** 그 실험체 스킬 효과음을 미리 받아 두기 (그림 · 음성을 받을 때 같이). 받기 시작은 부르는 쪽이 해요 */
export function loadBseoSkillSfx(speciesId: SpeciesId): void {
  const code = erCodeOfSpecies(speciesId);
  if (code == null || !audioManager?.isAudioEnabled || typeof globalScene?.load?.audio !== "function") {
    return;
  }
  for (const key of ER_SKILL_SFX[code] ?? "") {
    const file = `er/sfx/${code}_${key}.m4a`;
    const soundKey = bseoSkillSfxKey(file);
    if (!globalScene.cache.audio.exists(soundKey)) {
      globalScene.load.audio(soundKey, getCachedUrl(file));
    }
  }
}

/** 받아 둔 스킬 효과음 열쇠 (연출 소리 대신 틀 것). 없거나 아직 안 받았으면 null */
export function loadedBseoSkillSfx(speciesId: SpeciesId, moveId: MoveId): string | null {
  const file = bseoSkillSfxFile(speciesId, moveId);
  if (!file) {
    return null;
  }
  const soundKey = bseoSkillSfxKey(file);
  return globalScene?.cache?.audio?.exists(soundKey) ? soundKey : null;
}
