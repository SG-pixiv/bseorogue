/*
 * SPDX-FileCopyrightText: 2026 SG
 * SPDX-License-Identifier: AGPL-3.0-only
 */

import { FixedBattleConfig } from "#app/battle";
/**
 * 관장 전투 (포켓로그 관장 자리) = 마스터즈 팀 (11-19 SG)
 *
 * 정해진 웨이브(BSEO.leaderWaves)마다 마스터즈 팀 하나가 나와요. 판마다 순서가 다르고, 한 판에 같은 팀은 안 나와요.
 * 팀 · 실험체 · 대사는 난이도 시트 '마스터즈 팀' (docs/sheets/난이도.xlsx → difficulty-sheet.ts 의 MASTERS_TEAMS).
 * SG가 줄을 더하면 팀이 늘어나요. 실험체 3이 에이스(관장 자리, 레벨이 더 높음). 역할군 관장은 11-19 에 없앴어요.
 * 첫 관장 웨이브는 2명(실험체 2 · 3), 그다음부터 3명.
 */
import { BSEO } from "#app/bseorogue";
import { globalScene } from "#app/global-scene";
import { MASTERS_TEAMS, type MastersTeam } from "#data/bseorogue/difficulty-sheet";
import { ensureTeamSprite } from "#data/bseorogue/placeholder-art";
import { bseoCharacter } from "#data/bseorogue/roster";
import { BattleType } from "#enums/battle-type";
import { ModifierTier } from "#enums/modifier-tier";
import { PartyMemberStrength } from "#enums/party-member-strength";
import { TrainerType } from "#enums/trainer-type";
import { TrainerVariant } from "#enums/trainer-variant";
import { Trainer } from "#field/trainer";
import { getRandomPartyMemberFunc, TrainerConfig } from "#trainers/trainer-config";
import { TrainerPartyCompoundTemplate, TrainerPartyTemplate } from "#trainers/trainer-party-template";
import { randSeedShuffle } from "#utils/common";

/** 시트에 대사가 빈칸일 때 */
const DEFAULT_LINES = {
  encounter: "마스터즈 팀이다. 여기서부턴 쉽지 않을걸?",
  defeated: "좋은 경기였어. 다음엔 지지 않아.",
  won: "아직은 마스터즈의 벽이 높지?",
};

export function isLeaderWave(waveIndex: number): boolean {
  return (BSEO.leaderWaves as readonly number[]).includes(waveIndex);
}

/** 이 판 · 이 웨이브의 마스터즈 팀과 나오는 실험체 (마지막이 에이스) */
export function leaderLineupForWave(waveIndex: number): { team: MastersTeam; members: number[] } {
  const slot = Math.max(0, BSEO.leaderWaves.indexOf(waveIndex as never));
  // 첫 관장 웨이브는 2명, 그다음부터 3명 (에이스는 늘 나와요)
  const size = slot === 0 ? 2 : 3;
  let out: { team: MastersTeam; members: number[] } | null = null;
  globalScene.executeWithSeedOffset(() => {
    const order = randSeedShuffle(MASTERS_TEAMS.map((_, i) => i));
    const team = MASTERS_TEAMS[order[slot % order.length]];
    out = { team, members: team.members.slice(-size) };
  }, 7001);
  return out as unknown as { team: MastersTeam; members: number[] };
}

class LeaderTrainerConfig extends TrainerConfig {
  constructor(
    private readonly team: MastersTeam,
    members: readonly number[],
    private readonly spriteKey: string,
  ) {
    super(TrainerType.BSEO_LEADER);
    this.setName(`마스터즈 ${team.name}`);
    this.setMoneyMultiplier(2);
    // 관장 전투 곡 (이터널 리턴 마지막 금지구역 곡, er-sound-manifest.ts)
    this.setBattleBgm("bseo_leader");
    this.setMixedBattleBgm("bseo_leader");
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
    this.encounterMessages = [team.encounter || DEFAULT_LINES.encounter];
    this.victoryMessages = [team.defeated || DEFAULT_LINES.defeated];
    this.defeatMessages = [team.won || DEFAULT_LINES.won];
  }

  override getSpriteKey(): string {
    return this.spriteKey;
  }

  override loadAssets(): Promise<void> {
    ensureTeamSprite(this.spriteKey, `마스터즈\n${this.team.name}`, undefined, "#8fd18f");
    return Promise.resolve();
  }
}

export function createLeaderTrainer(waveIndex: number): Trainer {
  const { team, members } = leaderLineupForWave(waveIndex);
  const config = new LeaderTrainerConfig(team, members, `bseo_leader_${waveIndex}`);
  return new Trainer(TrainerType.BSEO_LEADER, TrainerVariant.DEFAULT, 0, undefined, undefined, config);
}

/** game-mode.ts 의 고정 전투 자리에 넣는 관장 전투 = 마스터즈 팀 (보상이 더 좋아요) */
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
