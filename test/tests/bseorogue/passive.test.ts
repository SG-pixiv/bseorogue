/*
 * SPDX-FileCopyrightText: 2026 SG
 * SPDX-License-Identifier: AGPL-3.0-only
 */

// 고유 패시브: 실험체마다 포켓로그 특성 하나를 빌려 쓰고 이름 · 설명은 시트 것
import { speciesDataRegistry } from "#app/global-species-data-registry";
import { bseoPassiveAbility } from "#data/bseorogue/passive";
import { BSEO_BOSSES, BSEO_CHARACTERS, BSEO_WILD, bseoSpeciesId } from "#data/bseorogue/roster";
import { SHEET_PASSIVES } from "#data/bseorogue/sheet-data";
import { allAbilities } from "#data/data-lists";
import { AbilityId } from "#enums/ability-id";
import { MoveId } from "#enums/move-id";
import { SpeciesId } from "#enums/species-id";
import { Stat } from "#enums/stat";
import { GameManager } from "#test/framework/game-manager";
import Phaser from "phaser";
import { beforeAll, beforeEach, describe, expect, it } from "vitest";

describe("블서로그 고유 패시브", () => {
  let phaserGame: Phaser.Game;
  let game: GameManager;

  beforeAll(() => {
    phaserGame = new Phaser.Game({ type: Phaser.HEADLESS });
  });

  beforeEach(() => {
    game = new GameManager(phaserGame);
    game.override.enemyMoveset(MoveId.SPLASH);
  });

  it("실험체마다 다른 특성, 세 모습 모두 같은 패시브", () => {
    const seen = new Map<AbilityId, string>();
    for (const c of BSEO_CHARACTERS) {
      const id = bseoPassiveAbility(c.erCode);
      expect(id, c.name).not.toBe(AbilityId.NONE);
      expect(seen.get(id), `${c.name} ↔ ${seen.get(id)}`).toBeUndefined();
      seen.set(id, c.name);
      for (const f of c.forms) {
        const s = speciesDataRegistry.getSpecies(f.id);
        expect([s.ability1, s.ability2, s.abilityHidden], f.name).toEqual([id, id, id]);
      }
      const a = allAbilities[id];
      expect(a.unimplemented || a.partial, `${c.name} ${AbilityId[id]}`).toBe(false);
    }
    expect(seen.size).toBe(Object.keys(SHEET_PASSIVES).length);
  });

  it("빌려 쓴 특성 이름 · 설명은 시트 패시브 것", () => {
    for (const c of BSEO_CHARACTERS) {
      const p = SHEET_PASSIVES[c.erCode];
      const a = allAbilities[bseoPassiveAbility(c.erCode)];
      expect(a.name, c.name).toBe(p.name);
      expect(a.description, c.name).toBe(p.desc);
      expect(c.passive).toBe(p.name);
    }
  });

  it("야생동물 · 보스는 패시브 없음", () => {
    for (const w of [...BSEO_WILD, ...BSEO_BOSSES]) {
      expect(speciesDataRegistry.getSpecies(w.id).ability1, w.name).toBe(AbilityId.NONE);
    }
  });

  it("전투에서: 레녹스(위풍당당 = 위협)가 나오면 내 공격력이 1단계 떨어져요", async () => {
    expect(bseoPassiveAbility(20)).toBe(AbilityId.INTIMIDATE);
    game.override.enemySpecies(bseoSpeciesId(20)).startingWave(3).startingLevel(10).enemyLevel(5);
    await game.classicMode.startBattle(SpeciesId.BSEO_ELEVEN);
    expect(game.field.getEnemyPokemon().getAbility().name).toBe(SHEET_PASSIVES[20].name);
    expect(game.field.getPlayerPokemon().getStatStage(Stat.ATK)).toBe(-1);
  });
});
