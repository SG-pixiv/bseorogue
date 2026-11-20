import { audioManager } from "#app/global-audio-manager";
import { globalScene } from "#app/global-scene";
import { settings } from "#app/global-settings-manager";
import type { BattlerIndex } from "#enums/battler-index";
import { HitResult } from "#enums/hit-result";
import { PokemonPhase } from "#phases/pokemon-phase";
import type { DamageResult } from "#types/damage-result";
import { fixedInt } from "#utils/common";

export class DamageAnimPhase extends PokemonPhase {
  public readonly phaseName = "DamageAnimPhase";

  private amount: number;
  private readonly damageResult: DamageResult;
  private readonly critical: boolean;

  constructor(
    battlerIndex: BattlerIndex,
    amount: number,
    damageResult: DamageResult = HitResult.EFFECTIVE,
    critical = false,
  ) {
    super(battlerIndex);

    this.amount = amount;
    this.damageResult = damageResult;
    this.critical = critical;
  }

  start() {
    super.start();

    if (this.damageResult === HitResult.ONE_HIT_KO || this.damageResult === HitResult.INDIRECT_KO) {
      if (settings.display.enableMoveAnimations) {
        globalScene.toggleInvert(true);
      }
      globalScene.time.delayedCall(fixedInt(1000), () => {
        globalScene.toggleInvert(false);
        this.applyDamage();
      });
      return;
    }

    this.applyDamage();
  }

  // TODO: this is silly, just make `amount` `public`
  public updateAmount(amount: number): void {
    this.amount = amount;
  }

  private applyDamage() {
    switch (this.damageResult) {
      case HitResult.EFFECTIVE:
      case HitResult.CONFUSION:
        audioManager.playSound("se/hit");
        break;
      case HitResult.EXTREMELY_EFFECTIVE:
      case HitResult.SUPER_EFFECTIVE:
      case HitResult.INDIRECT_KO:
      case HitResult.ONE_HIT_KO:
        audioManager.playSound("se/hit_strong");
        break;
      case HitResult.NOT_VERY_EFFECTIVE:
      case HitResult.MOSTLY_INEFFECTIVE:
        audioManager.playSound("se/hit_weak");
        break;
    }

    if (this.amount) {
      globalScene.damageNumberHandler.add(this.getPokemon(), this.amount, this.damageResult, this.critical);
    }

    if (this.damageResult !== HitResult.INDIRECT && this.amount > 0) {
      // 블서로그 (11-20): 맞으면 옆으로 짧게 흔들려요 ('기술 연출' 설정이 켜져 있을 때)
      if (settings.display.enableMoveAnimations) {
        const sprites = [this.getPokemon().getSprite(), this.getPokemon().getTintSprite()].filter(s => !!s);
        globalScene.tweens.add({
          targets: sprites,
          x: { from: -2, to: 2 },
          duration: 50,
          yoyo: true,
          repeat: 2,
          onComplete: () => sprites.forEach(s => s.setX(0)),
        });
      }
      const flashTimer = globalScene.time.addEvent({
        delay: 100,
        repeat: 5,
        startAt: 200,
        callback: () => {
          this.getPokemon()
            .getSprite()
            .setVisible(flashTimer.repeatCount % 2 === 0);
          if (!flashTimer.repeatCount) {
            this.getPokemon()
              .updateInfo()
              .then(() => this.end());
          }
        },
      });
    } else {
      this.getPokemon()
        .updateInfo()
        .then(() => this.end());
    }
  }

  public override end() {
    if (globalScene.currentBattle.isClassicFinalBoss) {
      globalScene.initFinalBossPhaseTwo(this.getPokemon());
    } else {
      super.end();
    }
  }
}
