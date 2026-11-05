/*
 * SPDX-FileCopyrightText: 2026 SG
 * SPDX-License-Identifier: AGPL-3.0-only
 */

import { FixedBattleConfig } from "#app/battle";
/**
 * KEL 팀 전투
 *
 * 정해진 웨이브(BSEO.kelWaves)마다 KEL 프로리그 팀이 실험체 3명으로 싸움을 걸어요.
 * 팀 · 실험체 · 로고는 무명섬 관리 화면(블서로그 → KEL 팀)에서 정하고, 게임이 시작할 때 불러와요.
 * 무명섬과 연결이 안 되거나 팀 실험체를 아직 안 정했으면, 아래 팀 이름에 실험체를 무작위로 넣어요.
 */
import { BSEO } from "#app/bseorogue";
import { fetchKelTeams, type KelTeam, mumeiConnected } from "#app/bseorogue-api";
import { globalScene } from "#app/global-scene";
import { ensureTeamSprite } from "#data/bseorogue/placeholder-art";
import { BSEO_CHARACTERS, bseoCharacter } from "#data/bseorogue/roster";
import { BattleType } from "#enums/battle-type";
import { PartyMemberStrength } from "#enums/party-member-strength";
import { TrainerType } from "#enums/trainer-type";
import { TrainerVariant } from "#enums/trainer-variant";
import { Trainer } from "#field/trainer";
import { getRandomPartyMemberFunc, TrainerConfig } from "#trainers/trainer-config";
import { TrainerPartyTemplate } from "#trainers/trainer-party-template";
import { randSeedInt, randSeedShuffle } from "#utils/common";

/** 무명섬에 등록된 KEL 팀 이름 (연결이 안 될 때 써요) */
const FALLBACK_TEAMS: readonly KelTeam[] = [
  ["Seongnam ROX", "성남"],
  ["INCHEON WAVE", "인천"],
  ["DAEJEON AutoArms", "대전"],
  ["FN SEJONG", "세종"],
  ["Gyeonggi Innate", "경기"],
  ["Chungnam CNJ esports", "충남"],
  ["GyeongBuk Ascenders", "경북"],
  ["Daegu Guardians", "대구"],
  ["GJ Slasher", "광주"],
  ["GC Busan Stella", "부산"],
  ["New Rise Gangwon", "강원"],
  ["Gyeongnam Sparkle Esports", "경남"],
  ["YJ Whales", "양주"],
  ["Goyang Mir", "고양"],
  ["Jeju Shadow", "제주"],
  ["Jeonnam Esports", "전남"],
].map(([name, region]) => ({ name, region, logo_url: "", members: [] }));

let teams: readonly KelTeam[] = FALLBACK_TEAMS;
const logos = new Map<string, HTMLImageElement>();

/** 게임이 켜질 때 한 번: 무명섬에서 KEL 팀을 불러오고 로고를 미리 받아 둬요 */
export async function loadKelTeams(): Promise<void> {
  if (!mumeiConnected) {
    return;
  }
  try {
    const list = await fetchKelTeams();
    if (Array.isArray(list) && list.length > 0) {
      teams = list.map(t => ({ ...t, members: (t.members ?? []).filter(c => !!bseoCharacter(c)) }));
    }
  } catch (e) {
    console.warn("KEL 팀을 못 불러와서 기본 팀으로 해요", e);
    return;
  }
  for (const t of teams) {
    if (!t.logo_url) {
      continue;
    }
    const img = new Image();
    img.crossOrigin = "anonymous";
    img.onload = () => logos.set(t.name, img);
    img.src = t.logo_url;
  }
}

export function isKelWave(waveIndex: number): boolean {
  return (BSEO.kelWaves as readonly number[]).includes(waveIndex);
}

export interface KelLineup {
  name: string;
  region: string;
  /** 실험체 3명 (ER 번호) */
  members: number[];
  logo?: HTMLImageElement | undefined;
}

/** 이 판 · 이 웨이브에 나오는 팀 (판마다 순서가 달라요. 한 판에서 같은 팀은 안 나와요) */
export function kelLineupForWave(waveIndex: number): KelLineup {
  const slot = Math.max(0, BSEO.kelWaves.indexOf(waveIndex as never));
  let lineup: KelLineup | null = null;
  globalScene.executeWithSeedOffset(() => {
    const order = randSeedShuffle(teams.map((_, i) => i));
    const team = teams[order[slot % order.length]];
    const members = [...team.members].slice(0, 3);
    // 실험체를 아직 안 정한 자리는 무작위 (겹치지 않게)
    const pool = randSeedShuffle(BSEO_CHARACTERS.map(c => c.erCode).filter(c => !members.includes(c)));
    while (members.length < 3 && pool.length > 0) {
      members.push(pool.splice(randSeedInt(pool.length), 1)[0]);
    }
    lineup = { name: team.name, region: team.region, members, logo: logos.get(team.name) };
  }, 9001);
  return lineup as unknown as KelLineup;
}

/** KEL 팀 한 판용 트레이너 설정 (팀마다 이름 · 그림 · 실험체가 달라요) */
class KelTrainerConfig extends TrainerConfig {
  constructor(
    private readonly lineup: KelLineup,
    private readonly spriteKey: string,
  ) {
    super(TrainerType.BSEO_KEL);
    this.setName(lineup.name);
    this.setMoneyMultiplier(1.5);
    this.setPartyTemplates(new TrainerPartyTemplate(3, PartyMemberStrength.AVERAGE));
    lineup.members.forEach((code, i) => {
      const c = bseoCharacter(code);
      if (c) {
        this.setPartyMemberFunc(i, getRandomPartyMemberFunc([c.id]));
      }
    });
  }

  override getSpriteKey(): string {
    return this.spriteKey;
  }

  override loadAssets(): Promise<void> {
    let logoKey: string | undefined;
    if (this.lineup.logo) {
      logoKey = `${this.spriteKey}_logo`;
      if (!globalScene.textures.exists(logoKey)) {
        try {
          globalScene.textures.addImage(logoKey, this.lineup.logo);
        } catch {
          logoKey = undefined;
        }
      }
    }
    ensureTeamSprite(this.spriteKey, this.lineup.name, logoKey);
    return Promise.resolve();
  }
}

export function createKelTrainer(waveIndex: number): Trainer {
  const lineup = kelLineupForWave(waveIndex);
  const config = new KelTrainerConfig(lineup, `bseo_kel_${waveIndex}`);
  return new Trainer(TrainerType.BSEO_KEL, TrainerVariant.DEFAULT, 0, undefined, undefined, config);
}

/** game-mode.ts 의 고정 전투 자리에 넣는 KEL 팀 전투 */
export function kelFixedBattle(waveIndex: number): FixedBattleConfig {
  return new FixedBattleConfig().setBattleType(BattleType.TRAINER).setGetTrainerFunc(() => createKelTrainer(waveIndex));
}
