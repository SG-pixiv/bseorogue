/*
 * SPDX-FileCopyrightText: 2026 SG
 * SPDX-License-Identifier: AGPL-3.0-only
 */

// 이 파일은 scripts/er-dot/import_dot.py 가 만들어요. 직접 고치지 마세요.

/** 전투 도트가 있는 스킨 (ER 번호 → 스킨 번호들). 그림: er/dot/<ER번호>_<스킨>.png (80×80, 1배) */
export const BSEO_DOT_SKINS: Readonly<Record<number, readonly number[]>> = {};

/** 아이콘 도트 자리 (er/dot-icons.png 안, ER 번호 → 스킨 → [x, y], 40×30) */
export const BSEO_DOT_ICON_FRAMES: Readonly<Record<number, Readonly<Record<number, readonly [number, number]>>>> = {};
