/*
 * SPDX-FileCopyrightText: 2026 SG
 * SPDX-License-Identifier: AGPL-3.0-only
 */

// 판이 끝나면 무명섬 랭킹에 올릴지 물어봐요 (닉네임만, 로그인 없음)
import { BSEO } from "#app/bseorogue";
import { mumeiConnected, submitScore } from "#app/bseorogue-api";
import { globalScene } from "#app/global-scene";
import { BSEO_STARTERS } from "#data/bseorogue/roster";
import { UiMode } from "#enums/ui-mode";

const NICK_KEY = "bseo.nickname";
const NICK_RULE = /^[가-힣A-Za-z0-9_]{2,12}$/;
const erCodeOf = new Map<number, number>(
  BSEO_STARTERS.filter(c => c.erCode != null).map(c => [c.id, c.erCode as number]),
);

function readNick(): string {
  try {
    return localStorage.getItem(NICK_KEY) ?? "";
  } catch {
    return "";
  }
}
function saveNick(v: string): void {
  try {
    localStorage.setItem(NICK_KEY, v);
  } catch {
    // 저장 못 해도 괜찮아요
  }
}

function say(text: string): Promise<void> {
  return new Promise(resolve => {
    globalScene.ui.setMode(UiMode.MESSAGE);
    globalScene.ui.showText(text, null, () => resolve(), null, true);
  });
}

/** 클래식 판이 끝났을 때 한 번 불러요. 무명섬과 연결 안 돼 있거나 건너뛰면 바로 끝나요 */
export async function offerRanking(isVictory: boolean): Promise<void> {
  if (!mumeiConnected || !globalScene.gameMode.isClassic) {
    return;
  }
  const wave = Math.min(globalScene.currentBattle?.waveIndex ?? 1, BSEO.classicFinalWave);
  const party = globalScene
    .getPlayerParty()
    .map(p => erCodeOf.get(p.species.getRootSpeciesId()))
    .filter((c): c is number => typeof c === "number");
  if (party.length === 0) {
    return;
  }
  // 닉네임 묻기 (PC 전용이라 브라우저 입력창을 써요)
  let nickname = window.prompt(
    `${wave}웨이브 기록을 무명섬 랭킹에 올릴까요?\n닉네임 (2~12자, 한글 · 영문 · 숫자 · _) · 취소하면 안 올려요`,
    readNick(),
  );
  while (nickname !== null && !NICK_RULE.test(nickname.trim())) {
    nickname = window.prompt("닉네임은 2~12자 한글 · 영문 · 숫자 · _ 만 쓸 수 있어요", nickname);
  }
  if (nickname === null) {
    return;
  }
  nickname = nickname.trim();
  saveNick(nickname);
  try {
    const res = await submitScore({
      nickname,
      wave,
      seconds: Math.round(globalScene.sessionPlayTime ?? 0),
      cleared: isVictory && wave >= BSEO.classicFinalWave,
      party,
      version: BSEO.version,
      runId: `bseo-${globalScene.seed}`,
    });
    await say(
      res.duplicate
        ? "이 판 기록은 이미 올라가 있어요!"
        : `삐빅-! 무명섬 랭킹에 올렸어요.${res.week_rank ? `\n이번 주 ${res.week_rank}위예요!` : ""}`,
    );
  } catch (e) {
    await say(`랭킹에 올리지 못했어요.\n${(e as Error).message}`);
  }
}
