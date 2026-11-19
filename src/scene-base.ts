import { audioManager } from "#app/global-audio-manager";
import { timedEventManager } from "#app/global-event-manager";
import { ER_ARENA_FILES } from "#data/bseorogue/er-arena-manifest";
import { ER_BGM_FILES, ER_SOUND_FILES } from "#data/bseorogue/er-sound-manifest";
import { coerceArray } from "#utils/array";
import { getCachedUrl } from "#utils/fetch-utils";
import Phaser from "phaser";

export const legacyCompatibleImages: string[] = [];

export class SceneBase extends Phaser.Scene {
  /**
   * Since everything is scaled up by 6 by default using the game.canvas is annoying
   * Until such point that we use the canvas normally, this will be easier than
   * having to divide every width and heigh by 6 to position and scale the ui
   * @readonly
   * @defaultValue
   * width: `320`
   * height: `180`
   */
  public readonly scaledCanvas = {
    width: 320, // (1920 / 6)
    height: 180, // (1080 / 6)
  } as const;

  public init(): void {
    this.load.on(Phaser.Loader.Events.FILE_LOAD, (file: Phaser.Loader.File) => {
      if (file.key.endsWith("_legacy")) {
        const fileKey = file.key.slice(0, -7);
        legacyCompatibleImages.push(fileKey);
      }
    });
  }

  public loadImage(key: string, folder: string, filename = `${key}.png`): this {
    const eventReplacment = timedEventManager.getEventImageReplacement(key);
    if (eventReplacment) {
      folder = "events";
      filename = `${eventReplacment}.png`;
    }
    // 블서로그: 이터널 리턴 스토리 모드 배경 그림이 있는 지역은 그 도트 배경 (assets/er/arena, make_arenas.py)
    const erArena = folder === "arenas" ? ER_ARENA_FILES[key] : undefined;
    this.load.image(key, getCachedUrl(erArena ?? `images/${folder}/${filename}`));
    if (folder.startsWith("ui")) {
      folder = folder.replace("ui", "ui/legacy");
      this.load.image(`${key}_legacy`, getCachedUrl(`images/${folder}/${filename}`));
    }
    return this;
  }

  public loadSpritesheet(key: string, folder: string, size: number, filename = `${key}.png`): this {
    this.load.spritesheet(key, getCachedUrl(`images/${folder}/${filename}`), {
      frameWidth: size,
      frameHeight: size,
    });
    if (folder.startsWith("ui")) {
      folder = folder.replace("ui", "ui/legacy");
      this.load.spritesheet(`${key}_legacy`, getCachedUrl(`images/${folder}/${filename}`), {
        frameWidth: size,
        frameHeight: size,
      });
    }
    return this;
  }

  public loadAtlas(key: string, folder: string, filenameRoot = key): this {
    if (folder) {
      folder += "/";
    }
    const eventReplacment = timedEventManager.getEventImageReplacement(key);
    if (eventReplacment) {
      folder = "events/";
      filenameRoot = `${eventReplacment}`;
    }
    this.load.atlas(
      key,
      getCachedUrl(`images/${folder}${filenameRoot}.png`),
      getCachedUrl(`images/${folder}${filenameRoot}.json`),
    );
    if (folder.startsWith("ui")) {
      folder = folder.replace("ui", "ui/legacy");
      this.load.atlas(
        `${key}_legacy`,
        getCachedUrl(`images/${folder}${filenameRoot}.png`),
        getCachedUrl(`images/${folder}${filenameRoot}.json`),
      );
    }
    return this;
  }

  public loadSe(key: string, folder = "se", filenames: string | string[] = `${key}.wav`): this {
    if (!audioManager.isAudioEnabled) {
      return this;
    }

    folder += "/";

    filenames = coerceArray(filenames);
    for (const f of filenames as string[]) {
      // TODO: Use actual path joining logic
      // 블서로그: 이터널 리턴 게임 소리가 있는 자리는 그 파일로 (er-sound-manifest.ts)
      this.load.audio(folder + key, getCachedUrl(ER_SOUND_FILES[`${folder}${f}`] ?? `audio/${folder}${f}`));
    }
    return this;
  }

  public async loadBgm(key: string): Promise<void> {
    if (!audioManager.isAudioEnabled || this.cache.audio.exists(key)) {
      return;
    }

    this.load.audio(key, getCachedUrl(ER_BGM_FILES[key] ?? `audio/bgm/${key}.mp3`));
    await new Promise<void>((resolve, reject) => {
      const onError = (file: Phaser.Loader.File) => {
        if (file.key === key) {
          this.load.off(Phaser.Loader.Events.FILE_LOAD_ERROR, onError);
          reject(new Error(`Failed to load BGM: ${key}`));
        }
      };
      this.load.once(`filecomplete-audio-${key}`, () => {
        this.load.off(Phaser.Loader.Events.FILE_LOAD_ERROR, onError);
        resolve();
      });
      this.load.on(Phaser.Loader.Events.FILE_LOAD_ERROR, onError);
      this.load.start();
    });
  }
}
