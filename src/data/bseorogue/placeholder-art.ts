/*
 * SPDX-FileCopyrightText: 2026 SG
 * SPDX-License-Identifier: AGPL-3.0-only
 */

/**
 * 임시 그림 (진짜 일러스트가 오기 전까지)
 *
 * 블서로그 실험체 · 동물 · 보스와 KEL 팀은 그림 파일이 아직 없어서, 게임 안에서 역할군 색 카드에 이름을 적어 그려요.
 * 진짜 그림을 넣으면 REAL_ART 에 종 번호를 적고 assets/images/pokemon/<번호>.png(.json) 에 두면 그 그림을 써요.
 */
import { globalScene } from "#app/global-scene";
import { speciesDataRegistry } from "#app/global-species-data-registry";
import { BOSS_TYPE, Role, WILD_TYPE } from "#data/bseorogue/roles";
import { BSEO_ALL_IDS } from "#data/bseorogue/roster";
import type { PokemonType } from "#enums/pokemon-type";
import type { SpeciesId } from "#enums/species-id";

/** 진짜 그림이 있는 종 번호 (지금은 없음) */
export const REAL_ART: ReadonlySet<number> = new Set<number>([]);

const COLORS: Partial<Record<PokemonType, string>> = {
  [Role.TANK]: "#5b7fa6",
  [Role.BRUISER]: "#b5543c",
  [Role.ASSASSIN]: "#6b4a94",
  [Role.MARKSMAN]: "#c99a2e",
  [Role.MAGE]: "#2f97b3",
  [Role.SUPPORT]: "#4f9e5c",
  [WILD_TYPE]: "#7d6f5c",
  [BOSS_TYPE]: "#a3283c",
};

const FONT = "emerald, sans-serif";

/** 검사 환경(가짜 화면)에는 캔버스 그림을 만드는 기능이 없어요 */
function canDraw(): boolean {
  return typeof globalScene?.textures?.createCanvas === "function";
}
export const ICON_ATLAS_KEY = "bseo_icons";
const ICON_W = 40;
const ICON_H = 30;

/** 역할군 색 (관장 그림 테두리 등) */
export function roleColor(type: PokemonType): string {
  return COLORS[type] ?? "#9fb4d8";
}

function colorOf(speciesId: SpeciesId): string {
  const species = speciesDataRegistry.getSpecies(speciesId);
  return COLORS[species.type1] ?? "#666666";
}

function shade(hex: string, amount: number): string {
  const n = Number.parseInt(hex.slice(1), 16);
  const f = (c: number) => Math.max(0, Math.min(255, Math.round(c + amount)));
  return `rgb(${f((n >> 16) & 255)}, ${f((n >> 8) & 255)}, ${f(n & 255)})`;
}

/** 이름을 폭에 맞게 줄바꿈 (한국어는 글자 단위) */
function wrap(ctx: CanvasRenderingContext2D, text: string, width: number): string[] {
  const lines: string[] = [];
  let line = "";
  for (const word of text.split(" ")) {
    const next = line ? `${line} ${word}` : word;
    if (ctx.measureText(next).width <= width) {
      line = next;
      continue;
    }
    if (line) {
      lines.push(line);
    }
    line = "";
    for (const ch of word) {
      if (ctx.measureText(line + ch).width > width && line) {
        lines.push(line);
        line = "";
      }
      line += ch;
    }
  }
  if (line) {
    lines.push(line);
  }
  return lines.slice(0, 3);
}

function drawCard(
  ctx: CanvasRenderingContext2D,
  w: number,
  h: number,
  name: string,
  color: string,
  back: boolean,
): void {
  ctx.clearRect(0, 0, w, h);
  // 몸통 (사람 모양 실루엣)
  ctx.fillStyle = shade(color, -40);
  ctx.beginPath();
  ctx.ellipse(w / 2, h - 3, w * 0.34, 3, 0, 0, Math.PI * 2);
  ctx.fill();
  ctx.fillStyle = color;
  ctx.beginPath();
  ctx.arc(w / 2, h * 0.3, h * 0.16, 0, Math.PI * 2);
  ctx.fill();
  ctx.beginPath();
  ctx.roundRect(w * 0.22, h * 0.46, w * 0.56, h * 0.5, 6);
  ctx.fill();
  ctx.strokeStyle = shade(color, -60);
  ctx.lineWidth = 1;
  ctx.stroke();
  if (back) {
    return;
  }
  // 이름
  ctx.font = `12px ${FONT}`;
  ctx.textAlign = "center";
  ctx.textBaseline = "middle";
  const lines = wrap(ctx, name, w * 0.54);
  const lh = 8;
  const top = h * 0.71 - ((lines.length - 1) * lh) / 2;
  ctx.fillStyle = "#ffffff";
  lines.forEach((l, i) => ctx.fillText(l, w / 2, top + i * lh));
}

/** 실험체 · 동물 · 보스 전투 그림 (앞 · 뒤). 그림 파일이 있으면 false */
export function ensureBseoSprite(spriteKey: string, speciesId: SpeciesId, back: boolean): boolean {
  if (REAL_ART.has(speciesId)) {
    return false;
  }
  if (!canDraw()) {
    return true;
  }
  const textures = globalScene.textures;
  if (!textures.exists(spriteKey)) {
    const species = speciesDataRegistry.getSpecies(speciesId);
    const isBoss = species.subLegendary;
    const size = isBoss ? 88 : 64;
    const tex = textures.createCanvas(spriteKey, size, size);
    if (!tex) {
      return true;
    }
    try {
      drawCard(tex.getContext(), size, size, species.name, colorOf(speciesId), back);
    } catch {
      // 검사 환경(가짜 캔버스)에서는 그리기를 건너뛰어요
    }
    tex.add("0001.png", 0, 0, 0, size, size);
    tex.refresh();
  }
  if (!globalScene.anims.exists(spriteKey)) {
    globalScene.anims.create({
      key: spriteKey,
      frames: [{ key: spriteKey, frame: "0001.png" }],
      frameRate: 10,
      repeat: -1,
    });
  }
  return true;
}

/** 파티 · 고르기 화면 아이콘 (블서로그 종 전부를 한 장에) */
export function ensureBseoIcons(): string {
  if (!canDraw()) {
    return ICON_ATLAS_KEY;
  }
  const textures = globalScene.textures;
  if (textures.exists(ICON_ATLAS_KEY)) {
    return ICON_ATLAS_KEY;
  }
  const cols = 32;
  const ids = BSEO_ALL_IDS;
  const rows = Math.ceil(ids.length / cols) * 2;
  const tex = textures.createCanvas(ICON_ATLAS_KEY, cols * ICON_W, rows * ICON_H);
  if (!tex) {
    return ICON_ATLAS_KEY;
  }
  const ctx = tex.getContext();
  ids.forEach((id, i) => {
    const species = speciesDataRegistry.getSpecies(id);
    const color = colorOf(id);
    for (const shiny of [false, true]) {
      const x = (i % cols) * ICON_W;
      const y = (Math.floor(i / cols) * 2 + (shiny ? 1 : 0)) * ICON_H;
      try {
        ctx.font = `12px ${FONT}`;
        ctx.textAlign = "center";
        ctx.textBaseline = "middle";
        ctx.fillStyle = shiny ? shade(color, 40) : color;
        ctx.beginPath();
        ctx.roundRect(x + 8, y + 6, ICON_W - 16, ICON_H - 10, 4);
        ctx.fill();
        ctx.fillStyle = "#ffffff";
        // 이름 앞 두 글자 (스킨 이름은 마지막 두 글자가 실험체 이름)
        const short = [...species.name.replace(/\s/g, "")];
        ctx.fillText(
          (species.name.includes(" ") ? short.slice(-2) : short.slice(0, 2)).join(""),
          x + ICON_W / 2,
          y + ICON_H / 2 + 1,
        );
      } catch {
        // 검사 환경(가짜 캔버스)
      }
      tex.add(`${id}${shiny ? "s" : ""}`, 0, x, y, ICON_W, ICON_H);
    }
  });
  tex.refresh();
  return ICON_ATLAS_KEY;
}

/** KEL 팀 그림: 팀 이름 (로고 그림이 불러와졌으면 로고도) */
/** KEL 팀 · 관장 그림. 줄바꿈(\n)으로 줄을 나눌 수 있고, color 는 테두리 색 */
export function ensureTeamSprite(spriteKey: string, teamName: string, logoKey?: string, color = "#9fb4d8"): void {
  if (!canDraw()) {
    return;
  }
  const textures = globalScene.textures;
  if (textures.exists(spriteKey)) {
    textures.remove(spriteKey);
  }
  const w = 72;
  const h = 80;
  const tex = textures.createCanvas(spriteKey, w, h);
  if (!tex) {
    return;
  }
  try {
    drawTeam(tex.getContext(), w, h, teamName, logoKey, color);
  } catch {
    // 검사 환경(가짜 캔버스)
  }
  tex.add("0001.png", 0, 0, 0, w, h);
  tex.refresh();
  if (globalScene.anims.exists(spriteKey)) {
    globalScene.anims.remove(spriteKey);
  }
  globalScene.anims.create({
    key: spriteKey,
    frames: [{ key: spriteKey, frame: "0001.png" }],
    frameRate: 24,
    repeat: -1,
  });
}

// biome-ignore lint/complexity/useMaxParams: 그림 그리기용 내부 함수
function drawTeam(
  ctx: CanvasRenderingContext2D,
  w: number,
  h: number,
  teamName: string,
  logoKey: string | undefined,
  color: string,
): void {
  const textures = globalScene.textures;
  ctx.fillStyle = "#1d2433";
  ctx.beginPath();
  ctx.roundRect(4, 8, w - 8, h - 12, 8);
  ctx.fill();
  ctx.strokeStyle = color;
  ctx.lineWidth = 2;
  ctx.stroke();
  let textTop = h * 0.5;
  if (logoKey && textures.exists(logoKey)) {
    const img = textures.get(logoKey).getSourceImage() as CanvasImageSource & { width: number; height: number };
    const s = Math.min(40 / img.width, 40 / img.height);
    ctx.drawImage(img, (w - img.width * s) / 2, 14, img.width * s, img.height * s);
    textTop = 62;
  }
  ctx.font = `12px ${FONT}`;
  ctx.textAlign = "center";
  ctx.textBaseline = "middle";
  ctx.fillStyle = "#ffffff";
  const lines = teamName.split("\n").flatMap(part => wrap(ctx, part, w - 16));
  lines.forEach((l, i) => ctx.fillText(l, w / 2, textTop + (i - (lines.length - 1) / 2) * 8));
}
