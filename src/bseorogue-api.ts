/*
 * SPDX-FileCopyrightText: 2026 SG
 * SPDX-License-Identifier: AGPL-3.0-only
 */

/**
 * 무명섬 연결 (랭킹 올리기 · KEL 팀 불러오기)
 * 무명섬 Supabase 의 공개 주소 · 공개 키만 써요 (보안은 무명섬 DB 규칙 13단계가 지켜요).
 * 배포할 때 Vercel 환경 변수 VITE_SUPABASE_URL · VITE_SUPABASE_ANON_KEY 에 무명섬과 같은 값을 넣어요.
 */
const URL_ = import.meta.env.VITE_SUPABASE_URL || "";
const KEY = import.meta.env.VITE_SUPABASE_ANON_KEY || "";

/** 무명섬과 연결돼 있는지 (안 돼 있으면 랭킹 올리기를 건너뛰어요) */
export const mumeiConnected = !!(URL_ && KEY);

async function call<T>(path: string, init: RequestInit = {}): Promise<T> {
  const res = await fetch(`${URL_}/rest/v1/${path}`, {
    ...init,
    headers: { apikey: KEY, "Content-Type": "application/json", ...(init.headers || {}) },
  });
  const body = await res.json().catch(() => null);
  if (!res.ok) {
    throw new Error((body && (body.message as string)) || `무명섬 응답 ${res.status}`);
  }
  return body as T;
}

export interface SubmitResult {
  id: number;
  week_rank?: number;
  best?: boolean;
  duplicate?: boolean;
}

/** 랭킹 올리기 (무명섬 rogue_submit) */
export function submitScore(args: {
  nickname: string;
  wave: number;
  seconds: number;
  cleared: boolean;
  party: number[];
  version: string;
  runId: string;
  /** 티어 (0 아이언 ~ 9 이터니티) */
  tier: number;
}): Promise<SubmitResult> {
  const body = {
    p_nickname: args.nickname,
    p_wave: args.wave,
    p_seconds: args.seconds,
    p_cleared: args.cleared,
    p_party: args.party,
    p_version: args.version,
    p_mode: "classic",
    p_run: args.runId,
  };
  return call<SubmitResult>("rpc/rogue_submit", {
    method: "POST",
    body: JSON.stringify({ ...body, p_tier: args.tier }),
  }).catch((e: Error) => {
    // 무명섬 14단계 SQL 전이면 티어 없이 다시 올려요
    if (/p_tier|function|could not find/i.test(e.message)) {
      return call<SubmitResult>("rpc/rogue_submit", { method: "POST", body: JSON.stringify(body) });
    }
    throw e;
  });
}

export interface KelTeam {
  name: string;
  region: string;
  logo_url: string;
  members: number[];
  /** 리그 (무명섬 14단계부터. 없으면 KEL) */
  league?: "kel" | "masters";
}

/** 팀 (무명섬 관리 화면에서 정한 리그 · 실험체 3명). 14단계 SQL 전이면 리그 없이 불러와요 */
export async function fetchTeams(): Promise<KelTeam[]> {
  try {
    return await call<KelTeam[]>("rogue_teams?select=name,region,logo_url,members,league&active=eq.true&order=sort");
  } catch {
    return call<KelTeam[]>("rogue_teams?select=name,region,logo_url,members&active=eq.true&order=sort");
  }
}
