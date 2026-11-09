# SPDX-FileCopyrightText: 2026 SG
# SPDX-License-Identifier: AGPL-3.0-only
"""스킬 아이콘 화면 확인 (브라우저 자동 진행): 전투 스킬 고르기 · 실험체 정보 스킬 쪽 스크린샷

준비: mouse_check.py 와 같아요 (개발 모드 빌드를 8010 에 띄우기, docs/이어서-할-일.md 4-2)
실행: python3 -B scripts/browser-check/skill_icon_check.py
결과: /tmp/pwcheck/si-*.png (칸 없는 스크린샷), si-*-zoom.png (아래쪽 확대)
"""
import asyncio
import os
import sys

from PIL import Image
from playwright.async_api import async_playwright

sys.path.insert(0, os.path.dirname(__file__))
from mouse_check import canvas_box, click, press, say, state, targets, to_battle  # noqa: E402

OUT = "/tmp/pwcheck/si"


async def snap(pg, name):
    path = f"{OUT}-{name}.png"
    await pg.screenshot(path=path)
    x, y, w, h = await canvas_box(pg)
    im = Image.open(path).convert("RGB").crop((round(x), round(y), round(x + w), round(y + h)))
    im.save(path)
    # 아래쪽(스킬 칸) 2배 확대
    zoom = im.crop((0, round(im.height * 0.62), im.width, im.height))
    zoom.resize((zoom.width * 2, zoom.height * 2), Image.NEAREST).save(path.replace(".png", "-zoom.png"))
    say("snap", name, await state(pg))


async def wait_target(pg, label, tries=20):
    for _ in range(tries):
        if any(t["label"] == label for t in await targets(pg)):
            return True
        await pg.wait_for_timeout(400)
    return False


async def main():
    async with async_playwright() as p:
        b = await p.chromium.launch()
        pg = await b.new_page(viewport={"width": 1280, "height": 720})
        errs = []
        pg.on("pageerror", lambda e: errs.append(str(e)))
        ok = await to_battle(pg)
        say("battle ready", ok)
        await snap(pg, "01-command")
        # 싸우기 → 스킬 고르기
        await click(pg, "command:0", 1500)
        await snap(pg, "02-fight")
        await pg.mouse.click(1270, 710, button="right")
        await pg.wait_for_timeout(900)
        # 실험체 → 첫 칸 → 정보 → 스킬 쪽
        for _ in range(10):
            if (await state(pg))["mode"] == "COMMAND":
                break
            await pg.wait_for_timeout(500)
        await click(pg, "command:2", 1500)
        await wait_target(pg, "party:0")
        await click(pg, "party:0", 1200)
        await wait_target(pg, "party-option:0")
        await click(pg, "party-option:0", 1500)
        await wait_target(pg, "summary-page:1")
        await pg.wait_for_timeout(1000)
        # 스킬 쪽 탭 한 번에 (정보 → 스킬, 두 쪽 건너뛰기)
        await click(pg, "summary-page:2", 2000)
        page = await pg.evaluate("() => window.__bseoScene?.ui?.getHandler?.()?.cursor")
        say("summary page after one click", page)
        await snap(pg, "03-summary-moves")
        # 스킬 하나 고르면 설명 · 위력 칸
        await press(pg, "Space", 1000)
        await snap(pg, "04-summary-move-selected")
        say("errors", errs[:5])
        await b.close()


if __name__ == "__main__":
    asyncio.run(main())
