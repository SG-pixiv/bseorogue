# SPDX-FileCopyrightText: 2026 SG
# SPDX-License-Identifier: AGPL-3.0-only
"""기술 연출 확인 (브라우저 자동 진행): 스킬을 쓰고 연출 중간을 연달아 찍어요

준비: mouse_check.py 와 같아요 (개발 모드 빌드를 8010 에 띄우기, docs/이어서-할-일.md 4-2)
실행: python3 -B scripts/browser-check/fx_check.py [스킬 칸 번호 0~3 …]   (기본 0 1)
결과: /tmp/pwcheck/fx-<칸>-<순서>.png, 한 장에 모은 것 /tmp/pwcheck/fx-sheet.png
"""
import asyncio
import os
import sys

from PIL import Image
from playwright.async_api import async_playwright

sys.path.insert(0, os.path.dirname(__file__))
from mouse_check import canvas_box, click, say, state, targets, to_battle  # noqa: E402

OUT = "/tmp/pwcheck/fx"


async def wait_mode(pg, mode, tries=40):
    for _ in range(tries):
        if (await state(pg))["mode"] == mode:
            return True
        await pg.wait_for_timeout(500)
    return False


async def burst(pg, tag, n=14, gap=90):
    x, y, w, h = await canvas_box(pg)
    paths = []
    for i in range(n):
        path = f"{OUT}-{tag}-{i:02d}.png"
        await pg.screenshot(path=path, clip={"x": x, "y": y, "width": w, "height": h})
        paths.append(path)
        await pg.wait_for_timeout(gap)
    return paths


async def main():
    slots = [int(a) for a in sys.argv[1:]] or [0, 1]
    shots = []
    async with async_playwright() as p:
        b = await p.chromium.launch()
        pg = await b.new_page(viewport={"width": 1280, "height": 720})
        errs = []
        pg.on("pageerror", lambda e: errs.append(str(e)))
        say("battle ready", await to_battle(pg))
        for slot in slots:
            await wait_mode(pg, "COMMAND")
            await click(pg, "command:0", 1200)
            labels = [t["label"] for t in await targets(pg)]
            move = next((l for l in labels if l.startswith("move:") and l.endswith(str(slot))), None)
            say("slot", slot, move, labels[:8])
            if not move:
                continue
            await click(pg, move, 300)
            shots.append(await burst(pg, str(slot)))
        say("errors", errs[:5])
        await b.close()
    # 한 장에: 칸마다 한 줄, 찍은 순서대로 (반 크기)
    if shots:
        ims = [[Image.open(pth).convert("RGB") for pth in row] for row in shots]
        w, h = ims[0][0].width // 2, ims[0][0].height // 2
        cols = max(len(r) for r in ims)
        sheet = Image.new("RGB", (w * cols, h * len(ims)), (0, 0, 0))
        for r, row in enumerate(ims):
            for c, im in enumerate(row):
                sheet.paste(im.resize((w, h)), (c * w, r * h))
        sheet.save(f"{OUT}-sheet.png")


if __name__ == "__main__":
    asyncio.run(main())
