/*
 * SPDX-FileCopyrightText: 2026 SG
 * SPDX-License-Identifier: AGPL-3.0-only
 */

/**
 * 실험체 스킬 아이콘 (팬키트 Skill Icon · scripts/fankit/build_skill_icons.py 가 assets/er/skill/ 에 만들어요)
 *
 * - 스킬(Q W E R = skill-moves.ts 의 기술)마다 그 실험체의 아이콘. 한 기술은 한 실험체만 쓰니까 기술만 보고 찾아요
 * - 전투 스킬 고르기 · 실험체 정보(스킬 쪽) · 새 스킬 배우기 줄에서 스킬 이름 왼쪽에 작게 그려요
 * - 그림을 받을 때(실험체 loadAssets) 같이 받아 두고, 아직 없으면 화면에서 받고 나서 보여 줘요
 * - 아이콘이 없는 기술(동물 · 보스 · 포켓로그 기술)은 아무것도 안 그려요 (null)
 */
import { globalScene } from "#app/global-scene";
import { erCodeOfSpecies } from "#data/bseorogue/roster";
import { BSEO_SKILL_ICONS } from "#data/bseorogue/skill-icon-manifest";
import { SKILL_MOVES } from "#data/bseorogue/skill-moves";
import type { MoveId } from "#enums/move-id";
import type { SpeciesId } from "#enums/species-id";
import { getCachedUrl } from "#utils/fetch-utils";
import Phaser from "phaser";

export type BseoSkillIconKey = "p" | "q" | "w" | "e" | "r";

const SKILL_KEYS: readonly BseoSkillIconKey[] = ["q", "w", "e", "r"];

/** 아이콘 원본 크기 (72px = 화면 12칸 × 6배) */
export const BSEO_SKILL_ICON_PX = 72;

let byMove: Map<MoveId, string> | null = null;

/** 기술 → "ER번호_키" (아이콘이 있을 때만) */
function iconsByMove(): Map<MoveId, string> {
  if (!byMove) {
    byMove = new Map();
    for (const [code, moves] of Object.entries(SKILL_MOVES)) {
      const have = BSEO_SKILL_ICONS[Number(code)] ?? "";
      moves.forEach((moveId, i) => {
        if (have.includes(SKILL_KEYS[i])) {
          byMove!.set(moveId, `${code}_${SKILL_KEYS[i]}`);
        }
      });
    }
  }
  return byMove;
}

/** 기술의 아이콘 이름 "ER번호_키" (없으면 null) */
export function bseoSkillIconName(moveId: MoveId): string | null {
  return iconsByMove().get(moveId) ?? null;
}

/** 아이콘 파일 (assets 기준 경로) */
export function bseoSkillIconFile(name: string): string {
  return `er/skill/${name}.png`;
}

/** Phaser 그림 열쇠 */
export function bseoSkillIconTexture(name: string): string {
  return `bseo_skill_${name}`;
}

/** 그 실험체의 아이콘 이름들 (패시브 포함). 없으면 빈 배열 */
export function bseoSkillIconNames(code: number): string[] {
  return [...(BSEO_SKILL_ICONS[code] ?? "")].map(k => `${code}_${k}`);
}

function canLoad(): boolean {
  return typeof globalScene?.load?.image === "function" && !!globalScene.textures;
}

function queue(name: string): boolean {
  const tex = bseoSkillIconTexture(name);
  if (globalScene.textures.exists(tex)) {
    return false;
  }
  globalScene.load.image(tex, getCachedUrl(bseoSkillIconFile(name)));
  return true;
}

/** 그 실험체의 스킬 아이콘을 미리 받아 두기 (그림을 받을 때 같이). 받기 시작은 부르는 쪽이 해요 */
export function loadBseoSkillIcons(speciesId: SpeciesId): void {
  const code = erCodeOfSpecies(speciesId);
  if (code == null || !canLoad()) {
    return;
  }
  for (const name of bseoSkillIconNames(code)) {
    queue(name);
  }
}

/** 크기 맞추기 (원본이 72px 이라 12칸이면 1:1, 다른 크기면 부드럽게 줄여요) */
function fitIcon(icon: Phaser.GameObjects.Image, size: number): void {
  const tex = icon.texture;
  if (size * 6 !== BSEO_SKILL_ICON_PX && tex.key.startsWith("bseo_skill_")) {
    tex.setFilter(Phaser.Textures.FilterMode.LINEAR);
  }
  icon.setDisplaySize(size, size);
}

/**
 * 스킬 아이콘 그림 만들기 (화면 단위 size 칸 네모, 기준점 왼쪽 위). 그 기술에 아이콘이 없으면 null.
 * 아직 안 받은 아이콘이면 빈 그림을 먼저 두고, 받으면 바로 바꿔요.
 */
export function addBseoSkillIcon(x: number, y: number, moveId: MoveId, size = 12): Phaser.GameObjects.Image | null {
  const name = bseoSkillIconName(moveId);
  if (!name || !canLoad()) {
    return null;
  }
  const tex = bseoSkillIconTexture(name);
  const ready = globalScene.textures.exists(tex);
  const icon = globalScene.add
    .image(x, y, ready ? tex : "__DEFAULT")
    .setOrigin(0, 0)
    .setName(`skill-icon-${name}`);
  if (ready) {
    fitIcon(icon, size);
    return icon;
  }
  icon.setVisible(false);
  globalScene.load.once(`filecomplete-image-${tex}`, () => {
    if (icon.active) {
      icon.setTexture(tex).setVisible(true);
      fitIcon(icon, size);
    }
  });
  if (queue(name) && !globalScene.load.isLoading()) {
    globalScene.load.start();
  }
  return icon;
}
