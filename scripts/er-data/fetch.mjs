#!/usr/bin/env node

// SPDX-FileCopyrightText: 2026 SG
// SPDX-License-Identifier: AGPL-3.0-only
//
// 이터널 리턴 공식 API 에서 블서로그에 쓸 게임 데이터를 받아요.
// (실험체 기본 스탯 · 스킨 · 아이템 · 야생동물 · 지역 · 한국어 이름)
//
// 쓰는 법 (Windows CMD):
//   1) 이 파일이 있는 폴더에 er-key.txt 를 만들고 ER API 키 한 줄만 적어 저장해요.
//      (또는 set ER_API_KEY=키 를 먼저 입력해도 돼요)
//   2) node fetch.mjs
//   3) 같은 폴더에 er-data 폴더가 생겨요. 폴더를 압축해서 채팅에 첨부해 주세요.
//
// 키는 er-data 폴더 안에 저장되지 않아요. er-key.txt 는 절대 깃허브에 올리지 마세요.

import { existsSync } from "node:fs";
import { mkdir, readFile, writeFile } from "node:fs/promises";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";

const HERE = dirname(fileURLToPath(import.meta.url));
const BASE = process.env.ER_BASE || "https://open-api.bser.io";
const OUT = join(process.cwd(), "er-data");
const WAIT_MS = 1100; // 무료 키는 1초에 1번 정도만 허용돼요
// 블서로그에 필요한 종류만 받아요. 나머지는 manifest.json 에 이름만 남겨요.
const WANT =
  /^(Character|Item|Monster|Area|Weapon|Trait|Skill|Tactical|Infusion|Season|Mastery|Emotion|Booster|Collectible|Npc|Natural|Recommended)/i;

const sleep = ms => new Promise(r => setTimeout(r, ms));

async function readKey() {
  if (process.env.ER_API_KEY?.trim()) {
    return process.env.ER_API_KEY.trim();
  }
  for (const dir of [process.cwd(), HERE]) {
    const f = join(dir, "er-key.txt");
    if (existsSync(f)) {
      const k = (await readFile(f, "utf8")).replace(/^﻿/, "").trim();
      if (k) {
        return k;
      }
    }
  }
  return "";
}

async function call(key, path, tries = 4) {
  for (let i = 0; i < tries; i++) {
    let res;
    try {
      res = await fetch(BASE + path, { headers: { "x-api-key": key, accept: "application/json" } });
    } catch (e) {
      if (i === tries - 1) {
        throw new Error(`인터넷 연결을 확인해 주세요 (${e.message})`);
      }
      await sleep(2000);
      continue;
    }
    if (res.status === 429) {
      await sleep(3000 * (i + 1));
      continue;
    }
    if (res.status === 401 || res.status === 403) {
      throw new Error("API 키가 맞지 않아요. er-key.txt 를 확인해 주세요");
    }
    const body = await res.json().catch(() => null);
    if (!res.ok || !body) {
      throw new Error(`${path} 응답 ${res.status}`);
    }
    if (body.code && body.code !== 200) {
      throw new Error(`${path} 응답 코드 ${body.code} ${body.message || ""}`);
    }
    return body;
  }
  throw new Error(`${path} 요청이 너무 많다고 해요. 1분 뒤 다시 실행해 주세요`);
}

// v2 를 먼저 쓰고, 없으면 v1 으로 받아요
async function data(key, name) {
  try {
    return { ver: "v2", body: await call(key, `/v2/data/${name}`) };
  } catch (e) {
    if (/키가 맞지/.test(e.message)) {
      throw e;
    }
    await sleep(WAIT_MS);
    return { ver: "v1", body: await call(key, `/v1/data/${name}`) };
  }
}

async function main() {
  const key = await readKey();
  if (!key) {
    console.log("ER API 키가 없어요. 이 파일 옆에 er-key.txt 를 만들고 키 한 줄을 적어 주세요.");
    process.exit(1);
  }
  if (Number(process.versions.node.split(".")[0]) < 18) {
    console.log("Node.js 18 이상이 필요해요. https://nodejs.org 에서 LTS 를 설치해 주세요.");
    process.exit(1);
  }
  await mkdir(join(OUT, "raw"), { recursive: true });

  console.log("데이터 종류 목록을 받는 중…");
  const hash = (await data(key, "hash")).body?.data || {};
  const all = Object.keys(hash).sort();
  const picked = all.filter(n => WANT.test(n));
  console.log(`전체 ${all.length}종 중 ${picked.length}종을 받아요. 1~2분 걸려요.`);

  const manifest = {
    fetchedAt: new Date().toISOString(),
    base: BASE,
    all,
    picked: {},
    skipped: all.filter(n => !WANT.test(n)),
    failed: {},
  };
  let n = 0;
  for (const name of picked) {
    n += 1;
    await sleep(WAIT_MS);
    try {
      const { ver, body } = await data(key, name);
      const rows = body.data ?? body;
      await writeFile(join(OUT, "raw", `${name}.json`), JSON.stringify(rows, null, 1));
      manifest.picked[name] = { ver, rows: Array.isArray(rows) ? rows.length : null, hash: hash[name] };
      console.log(`  [${n}/${picked.length}] ${name} ${Array.isArray(rows) ? rows.length + "줄" : ""}`);
    } catch (e) {
      manifest.failed[name] = e.message;
      console.log(`  [${n}/${picked.length}] ${name} 실패: ${e.message}`);
      if (/키가 맞지/.test(e.message)) {
        break;
      }
    }
  }

  for (const lang of ["Korean", "English"]) {
    await sleep(WAIT_MS);
    try {
      const body = await call(key, `/v1/l10n/${lang}`);
      const url = body?.data?.l10Path;
      if (!url) {
        throw new Error("주소가 없어요");
      }
      const text = await (await fetch(url)).text();
      await writeFile(join(OUT, `l10n-${lang}.txt`), text);
      manifest[`l10n${lang}`] = { lines: text.split("\n").length };
      console.log(`  ${lang} 이름표 ${text.split("\n").length}줄`);
    } catch (e) {
      manifest.failed[`l10n-${lang}`] = e.message;
      console.log(`  ${lang} 이름표 실패: ${e.message}`);
    }
  }

  await writeFile(join(OUT, "manifest.json"), JSON.stringify(manifest, null, 2));
  const failed = Object.keys(manifest.failed).length;
  console.log("");
  console.log(failed ? `끝났어요. ${failed}개는 실패했어요 (manifest.json 에 이유가 있어요).` : "끝났어요!");
  console.log(`${OUT} 폴더를 압축해서 채팅에 첨부해 주세요.`);
}

main().catch(e => {
  console.log("멈췄어요: " + e.message);
  process.exit(1);
});
