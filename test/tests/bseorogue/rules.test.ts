/*
 * SPDX-FileCopyrightText: 2026 SG
 * SPDX-License-Identifier: AGPL-3.0-only
 */

// 블서로그 규칙: 파티 3명 · 클래식 50웨이브 · 1:1 싱글만 · 판 중 영입 없음 · 미스터리 인카운터 없음
import { BSEO } from "#app/bseorogue";
import { defaultStarterSpecies, PLAYER_PARTY_MAX_SIZE } from "#app/constants";
import { getGameMode } from "#app/game-mode";
import { speciesDataRegistry } from "#app/global-species-data-registry";
import { speciesEggMoves } from "#balance/moves/egg-moves";
import { ER_CHARACTERS } from "#data/bseorogue/er-data";
import { bseoBossSpecies } from "#data/bseorogue/hooks";
import { leagueForWave, promotionMessage, teamLeagueForWave } from "#data/bseorogue/league";
import { bseoTypeMultiplier, Role } from "#data/bseorogue/roles";
import {
  BSEO_BOSSES,
  BSEO_CHARACTERS,
  BSEO_STARTER_IDS,
  BSEO_STARTERS,
  BSEO_WILD,
  bseoCharacter,
} from "#data/bseorogue/roster";
import { COST_TOTALS } from "#data/bseorogue/stats";
import { setRunTier, TIERS, tierLevelMultiplier, tierName, unlockedTier, unlockNextTier } from "#data/bseorogue/tiers";
import { GameModes } from "#enums/game-modes";
import { MoveId } from "#enums/move-id";
import { SpeciesId } from "#enums/species-id";
import { GameManager } from "#test/framework/game-manager";
import Phaser from "phaser";
import { beforeAll, beforeEach, describe, expect, it } from "vitest";

describe("블서로그 규칙", () => {
  it("파티는 최대 3명", () => {
    expect(BSEO.partyMax).toBe(3);
    expect(PLAYER_PARTY_MAX_SIZE).toBe(3);
  });

  it("클래식은 50웨이브가 마지막 (10웨이브마다 보스)", () => {
    const classic = getGameMode(GameModes.CLASSIC);
    expect(classic.isWaveFinal(50)).toBe(true);
    expect(classic.isWaveFinal(200)).toBe(false);
    expect(classic.isBattleClassicFinalBoss(50)).toBe(true);
    for (const wave of [10, 20, 30, 40, 50]) {
      expect(classic.isBoss(wave)).toBe(true);
    }
  });

  it("판 중 영입 · 미스터리 인카운터는 꺼져 있어요", () => {
    expect(BSEO.allowCatch).toBe(false);
    expect(BSEO.mysteryEncounters).toBe(false);
    expect(BSEO.singleBattlesOnly).toBe(true);
  });
});

describe("블서로그 데이터", () => {
  beforeAll(() => {
    new Phaser.Game({ type: Phaser.HEADLESS }); // 종 데이터 준비
  });

  it("시작 실험체는 블서로그 6명만", () => {
    expect([...speciesDataRegistry.getAllStarters()].sort()).toEqual([...BSEO_STARTER_IDS].sort());
  });

  it("ER 데이터: 실험체 이름 · 스킬 이름 · 스킨", () => {
    const eleven = BSEO_STARTERS.find(c => c.erCode === 30)!;
    expect(eleven.name).toBe("일레븐");
    expect(eleven.skills.map(s => s.name)).toEqual(["방해하지마!", "자~ 집중!", "나 불렀어?", "다 덤벼보라구!"]);
    expect(eleven.skins[0]).toBe("일레븐");
  });

  it("종족값: 같은 코스트면 합이 같고, 기본 → 스킨 진화 1 → 2 로 커져요", () => {
    const sum = (s: readonly number[]) => s.reduce((a, b) => a + b, 0);
    for (const c of BSEO_STARTERS) {
      expect(c.stages.map(sum)).toEqual([...COST_TOTALS[c.cost]]);
      expect(c.stats).toEqual(c.stages[0]);
      expect(c.stats.every(v => v >= 10 && v <= 255)).toBe(true);
    }
    expect(BSEO_STARTERS[0].stages.map(sum)).toEqual([320, 410, 500]);
    // 동물은 뒤에 나올수록, 보스는 알파 → 루미 순서로 세져요
    const wild = BSEO_WILD.map(w => sum(w.stats));
    expect(wild).toEqual([...wild].sort((a, b) => a - b));
    const boss = BSEO_BOSSES.map(b => sum(b.stats));
    expect(boss).toEqual([420, 480, 540, 600, 680]);
    console.log(
      BSEO_STARTERS.map(c => `${c.name}(${c.focus}) ${c.stages.map(s => s.join("/")).join(" → ")}`).join("\n"),
    );
    console.log(BSEO_WILD.map(w => `${w.name} ${w.stats.join("/")} 합 ${sum(w.stats)}`).join("\n"));
  });

  it("ER 실험체 전부가 적으로 나올 수 있고, 역할군은 ER 분류를 따라요", () => {
    expect(BSEO_CHARACTERS.length).toBe(Object.keys(ER_CHARACTERS).length);
    // 직접 정한 6명
    const roles = [30, 11, 18, 6, 12, 69].map(code => {
      const c = bseoCharacter(code)!;
      return [c.name, c.role];
    });
    expect(roles).toEqual([
      ["일레븐", Role.TANK],
      ["유키", Role.BRUISER],
      ["쇼이치", Role.ASSASSIN],
      ["나딘", Role.MARKSMAN],
      ["혜진", Role.MAGE],
      ["레니", Role.SUPPORT],
    ]);
    expect(BSEO_CHARACTERS.filter(c => c.playable).length).toBe(BSEO_STARTERS.length);
  });

  it("지금은 실험체 전부를 고를 수 있고 (도감처럼 ER 번호 순서), 처음부터 열려 있어요", () => {
    expect(BSEO_STARTERS.length).toBe(BSEO_CHARACTERS.length);
    const codes = BSEO_STARTERS.map(c => c.erCode);
    expect(codes).toEqual([...codes].sort((a, b) => a - b));
    expect([...defaultStarterSpecies].sort()).toEqual([...BSEO_STARTER_IDS].sort());
  });

  it("스킨 진화: 기본 → 스킨 진화 1 (Lv12) → 스킨 진화 2 (Lv24)", () => {
    const eleven = bseoCharacter(30)!;
    expect(eleven.forms.map(f => f.name)).toEqual(["일레븐", "스위트 일레븐", "티타임 래빗 일레븐"]);
    expect(eleven.forms.map(f => f.id)).toEqual([
      SpeciesId.BSEO_ELEVEN,
      SpeciesId.BSEO_ELEVEN_S1,
      SpeciesId.BSEO_ELEVEN_S2,
    ]);
    const base = speciesDataRegistry.getSpecies(SpeciesId.BSEO_ELEVEN);
    expect(base.getEvolutionLevels()).toEqual([
      [SpeciesId.BSEO_ELEVEN_S1, 12],
      [SpeciesId.BSEO_ELEVEN_S2, 24],
    ]);
    expect(speciesDataRegistry.getSpecies(SpeciesId.BSEO_ELEVEN_S2).getRootSpeciesId()).toBe(SpeciesId.BSEO_ELEVEN);
    expect(speciesDataRegistry.getSpecies(SpeciesId.BSEO_ELEVEN_S2).baseTotal).toBe(500);
  });

  it("실험체 스킬은 다른 실험체 · 동물 · 보스 · 추가 스킬과 겹치지 않아요 (이름이 바뀌니까)", () => {
    const owner = new Map<MoveId, string>();
    for (const c of BSEO_CHARACTERS) {
      for (const s of c.skills) {
        expect(owner.get(s.move), `${c.name} ${s.name}`).toBeUndefined();
        owner.set(s.move, c.name);
      }
    }
    for (const x of [...BSEO_WILD, ...BSEO_BOSSES]) {
      for (const m of x.moves) {
        expect(owner.get(m), `${x.name} ${MoveId[m]}`).toBeUndefined();
      }
    }
    for (const c of BSEO_STARTERS) {
      for (const m of speciesEggMoves[c.id] ?? []) {
        expect(owner.get(m), `${c.name} 추가 스킬 ${MoveId[m]}`).toBeUndefined();
      }
    }
  });

  it("10웨이브마다 보스", () => {
    expect(bseoBossSpecies(10)?.speciesId).toBe(1701); // 알파
    expect(bseoBossSpecies(50)?.speciesId).toBe(1705); // 루미
    expect(bseoBossSpecies(15)).toBeNull();
  });

  it("역할군 상성: 암살자 → 평원딜 2배, 탱커 → 브루저 0.5배, 그 밖 1배", () => {
    expect(bseoTypeMultiplier(Role.ASSASSIN, Role.MARKSMAN)).toBe(2);
    expect(bseoTypeMultiplier(Role.TANK, Role.BRUISER)).toBe(0.5);
    expect(bseoTypeMultiplier(Role.SUPPORT, Role.TANK)).toBe(1);
  });
});

describe("블서로그 규칙 - 전투", () => {
  let phaserGame: Phaser.Game;
  let game: GameManager;

  beforeAll(() => {
    phaserGame = new Phaser.Game({ type: Phaser.HEADLESS });
  });

  beforeEach(() => {
    game = new GameManager(phaserGame);
    game.override.startingWave(5).enemyMoveset(MoveId.SPLASH).moveset([MoveId.TACKLE]);
  });

  it("야생 전투는 늘 1:1 이에요", async () => {
    game.override.enemySpecies(SpeciesId.BSEO_CHICKEN);
    await game.classicMode.startBattle(SpeciesId.BSEO_ELEVEN);
    expect(game.scene.currentBattle.double).toBe(false);
    expect(game.scene.getEnemyField().length).toBe(1);
  });

  it("판 안 승단: 마스터즈 → KEL → KEL 결승, 바뀌는 웨이브에 안내", () => {
    expect(leagueForWave(1).key).toBe("masters");
    expect(leagueForWave(20).key).toBe("masters");
    expect(leagueForWave(21).key).toBe("kel");
    expect(leagueForWave(41).key).toBe("final");
    expect(teamLeagueForWave(15)).toBe("masters");
    expect(teamLeagueForWave(45)).toBe("kel");
    expect(promotionMessage(21)).toContain("KEL");
    expect(promotionMessage(22)).toBeNull();
  });

  it("판 밖 티어: 아이언부터, 깨면 다음 티어가 열려요 (승급만)", () => {
    expect(TIERS.length).toBe(10);
    expect(tierName(0)).toBe("아이언");
    expect(tierName(9)).toBe("이터니티");
    expect(tierLevelMultiplier(9)).toBeCloseTo(1.27);
    localStorage.removeItem("bseo.tier.unlocked");
    expect(unlockedTier()).toBe(0);
    setRunTier(0);
    expect(unlockNextTier()).toBe(1);
    expect(unlockedTier()).toBe(1);
    // 낮은 티어를 다시 깨도 그대로
    expect(unlockNextTier()).toBeNull();
    setRunTier(9);
    expect(unlockNextTier()).toBeNull();
    setRunTier(0);
    localStorage.removeItem("bseo.tier.unlocked");
  });
});
