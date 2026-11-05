/*
 * SPDX-FileCopyrightText: 2026 SG
 * SPDX-License-Identifier: AGPL-3.0-only
 */

import { FixedBattleConfig } from "#app/battle";
/**
 * 관장 전투 (포켓로그 관장 자리)
 *
 * 역할군마다 관장이 1명씩 있어요. 관장은 실험체이고, 같은 역할군 실험체로 팀을 꾸려요.
 * 정해진 웨이브(BSEO.leaderWaves)마다 한 명씩 나와요. 판마다 순서가 다르고, 한 판에 같은 관장은 안 나와요.
 * 관장 · 대사는 초안이에요. SG가 정하면 LEADERS 표만 고치면 돼요.
 */
import { BSEO } from "#app/bseorogue";
import { globalScene } from "#app/global-scene";
import type { ErRoleKey } from "#data/bseorogue/er-data";
import { ensureTeamSprite, roleColor } from "#data/bseorogue/placeholder-art";
import { Role } from "#data/bseorogue/roles";
import { BSEO_CHARACTERS, bseoCharacter } from "#data/bseorogue/roster";
import { BattleType } from "#enums/battle-type";
import { ModifierTier } from "#enums/modifier-tier";
import { PartyMemberStrength } from "#enums/party-member-strength";
import { PokemonType } from "#enums/pokemon-type";
import { TrainerType } from "#enums/trainer-type";
import { TrainerVariant } from "#enums/trainer-variant";
import { Trainer } from "#field/trainer";
import { getRandomPartyMemberFunc, TrainerConfig } from "#trainers/trainer-config";
import { TrainerPartyCompoundTemplate, TrainerPartyTemplate } from "#trainers/trainer-party-template";
import { randSeedShuffle } from "#utils/common";
import { toCamelCase } from "#utils/strings";
import i18next from "i18next";

export interface Leader {
  role: ErRoleKey;
  /** 관장 실험체 (ER 번호). 팀의 마지막(에이스)으로 직접 나와요 */
  erCode: number;
  /** 나올 때 · 졌을 때 대사 ($ 로 나누면 여러 장) */
  encounter: string;
  defeated: string;
  /** 플레이어가 졌을 때 */
  won: string;
}

/** 역할군 관장 (초안) */
export const LEADERS: readonly Leader[] = [
  {
    role: "TANK",
    erCode: 4, // 매그너스
    encounter: "여기서부턴 못 지나가.$탱커가 얼마나 단단한지 보여 주지!",
    defeated: "…이걸 버텨 내다니. 지나가도 좋아.",
    won: "벽은 부수는 게 아니라 넘는 거야. 다시 와.",
  },
  {
    role: "BRUISER",
    erCode: 1, // 재키
    encounter: "정면으로 붙자!$브루저는 도망치지 않아!",
    defeated: "좋은 싸움이었어. 더 세져서 또 만나!",
    won: "아직 멀었네. 몸부터 다시 만들어 와!",
  },
  {
    role: "ASSASSIN",
    erCode: 23, // 캐시
    encounter: "눈치챘을 땐 이미 늦었어.",
    defeated: "내 움직임을 다 읽다니… 인정할게.",
    won: "뒤를 조심했어야지.",
  },
  {
    role: "MARKSMAN",
    erCode: 31, // 리오
    encounter: "사거리 안에 들어온 순간 끝이야.",
    defeated: "조준이 빗나갔네. 네가 이겼어.",
    won: "거리를 못 좁히면 이길 수 없어.",
  },
  {
    role: "MAGE",
    erCode: 5, // 자히르
    encounter: "스킬 한 방이면 충분하다.",
    defeated: "계산이 틀렸군… 다음엔 지지 않는다.",
    won: "스킬 저항을 더 챙기는 게 좋을 거다.",
  },
  {
    role: "SUPPORT",
    erCode: 41, // 요한
    encounter: "우리 팀은 쉽게 쓰러지지 않아요!",
    defeated: "끝까지 지켜 내지 못했네요… 축하해요!",
    won: "혼자 싸우면 오래 못 버텨요.",
  },
];

export function isLeaderWave(waveIndex: number): boolean {
  return (BSEO.leaderWaves as readonly number[]).includes(waveIndex);
}

/** 이 판 · 이 웨이브의 관장과 팀 (마지막이 관장 본인) */
export function leaderLineupForWave(waveIndex: number): { leader: Leader; members: number[] } {
  const slot = Math.max(0, BSEO.leaderWaves.indexOf(waveIndex as never));
  // 첫 관장은 2명, 그다음부터 3명
  const size = slot === 0 ? 2 : 3;
  let out: { leader: Leader; members: number[] } | null = null;
  globalScene.executeWithSeedOffset(() => {
    const order = randSeedShuffle(LEADERS.map((_, i) => i));
    const leader = LEADERS[order[slot % order.length]];
    const sameRole = randSeedShuffle(
      BSEO_CHARACTERS.filter(c => c.erCode !== leader.erCode && c.role === Role[leader.role]).map(c => c.erCode),
    );
    const members = [...sameRole.slice(0, size - 1), leader.erCode];
    out = { leader, members };
  }, 7001);
  return out as unknown as { leader: Leader; members: number[] };
}

const roleName = (role: ErRoleKey) => i18next.t(`pokemonInfo:type.${toCamelCase(PokemonType[Role[role]])}`);

class LeaderTrainerConfig extends TrainerConfig {
  constructor(
    private readonly leader: Leader,
    members: readonly number[],
    private readonly spriteKey: string,
  ) {
    super(TrainerType.BSEO_LEADER);
    const name = bseoCharacter(leader.erCode)?.name ?? "";
    this.setName(`${roleName(leader.role)} 관장 ${name}`);
    this.setMoneyMultiplier(2);
    this.setPartyTemplates(
      new TrainerPartyCompoundTemplate(
        new TrainerPartyTemplate(members.length - 1, PartyMemberStrength.AVERAGE),
        new TrainerPartyTemplate(1, PartyMemberStrength.STRONG),
      ),
    );
    members.forEach((code, i) => {
      const c = bseoCharacter(code);
      if (c) {
        this.setPartyMemberFunc(i, getRandomPartyMemberFunc([c.id]));
      }
    });
    this.encounterMessages = [leader.encounter];
    this.victoryMessages = [leader.defeated];
    this.defeatMessages = [leader.won];
  }

  override getSpriteKey(): string {
    return this.spriteKey;
  }

  override loadAssets(): Promise<void> {
    const name = bseoCharacter(this.leader.erCode)?.name ?? "";
    ensureTeamSprite(
      this.spriteKey,
      `${roleName(this.leader.role)} 관장\n${name}`,
      undefined,
      roleColor(Role[this.leader.role]),
    );
    return Promise.resolve();
  }
}

export function createLeaderTrainer(waveIndex: number): Trainer {
  const { leader, members } = leaderLineupForWave(waveIndex);
  const config = new LeaderTrainerConfig(leader, members, `bseo_leader_${waveIndex}`);
  return new Trainer(TrainerType.BSEO_LEADER, TrainerVariant.DEFAULT, 0, undefined, undefined, config);
}

/** game-mode.ts 의 고정 전투 자리에 넣는 관장 전투 (보상이 더 좋아요) */
export function leaderFixedBattle(waveIndex: number): FixedBattleConfig {
  const first = BSEO.leaderWaves.indexOf(waveIndex as never) === 0;
  return new FixedBattleConfig()
    .setBattleType(BattleType.TRAINER)
    .setGetTrainerFunc(() => createLeaderTrainer(waveIndex))
    .setCustomModifierRewards({
      guaranteedModifierTiers: first
        ? [ModifierTier.GREAT, ModifierTier.GREAT]
        : [ModifierTier.ULTRA, ModifierTier.GREAT, ModifierTier.GREAT],
    });
}
