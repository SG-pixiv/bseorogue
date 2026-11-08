# SPDX-FileCopyrightText: 2026 SG
# SPDX-License-Identifier: AGPL-3.0-only
"""마우스 칸 확인 (브라우저 자동 진행): 정보 화면 · 보상 고르기 화면에서 칸을 스크린샷 위에 그려요

준비: 개발 모드로 따로 빌드해서 띄우기 (docs/이어서-할-일.md 4-2)
  NODE_ENV=development pnpm exec vite build --mode development --outDir /tmp/bseo-check/dist
  cd /tmp/bseo-check/dist && python3 -m http.server 8010
실행: python3 scripts/browser-check/mouse_check.py [all|summary|reward]
결과: /tmp/pwcheck/mc-*.png (빨강 = 칸, 초록 = 올린 칸), mc-log.txt
"""
import asyncio
import json
import os
import sys
from PIL import Image, ImageDraw
from playwright.async_api import async_playwright

OUT = "/tmp/pwcheck/mc"
os.makedirs("/tmp/pwcheck", exist_ok=True)
log = []


def say(*a):
    s = " ".join(str(x) for x in a)
    log.append(s)
    print(s, flush=True)


async def state(pg):
    return json.loads(await pg.evaluate("() => JSON.stringify(window.__bseoMouse.debugState())"))


async def targets(pg):
    return json.loads(await pg.evaluate("() => JSON.stringify(window.__bseoMouse.debugTargets())"))


async def press(pg, key, wait=400):
    await pg.keyboard.press(key)
    await pg.wait_for_timeout(wait)


async def canvas_box(pg):
    return await pg.evaluate("() => { const r = document.querySelector('canvas').getBoundingClientRect(); return [r.x, r.y, r.width, r.height]; }")


async def center(pg, t):
    box = await canvas_box(pg)
    s = box[2] / 1920
    return box[0] + (t["x"] + t["w"] / 2) * s, box[1] + (t["y"] + t["h"] / 2) * s


async def click(pg, label, wait=900):
    t = next((x for x in await targets(pg) if x["label"] == label), None)
    if not t:
        say("no target", label, [x["label"] for x in await targets(pg)][:30])
        return False
    cx, cy = await center(pg, t)
    await pg.mouse.move(cx, cy)
    await pg.wait_for_timeout(250)
    await pg.mouse.click(cx, cy)
    await pg.wait_for_timeout(wait)
    return True


async def shot(pg, name, hover=None):
    """스크린샷 + 칸 그리기 (빨강: 칸, 초록: 지금 올린 칸)"""
    path = f"{OUT}-{name}.png"
    await pg.screenshot(path=path)
    ts = await targets(pg)
    box = await canvas_box(pg)
    s = box[2] / 1920
    im = Image.open(path).convert("RGB")
    im.save(path.replace(".png", "-raw.png"))  # 칸 없는 그림 (UI 스타일 보기용)
    d = ImageDraw.Draw(im)
    for t in ts:
        x0, y0 = box[0] + t["x"] * s, box[1] + t["y"] * s
        x1, y1 = x0 + t["w"] * s, y0 + t["h"] * s
        col = (0, 255, 0) if hover and t["label"] == hover else (255, 40, 40)
        d.rectangle([x0, y0, x1, y1], outline=col, width=2)
        d.text((x0 + 2, y0 + 1), t["label"], fill=col)
    im.save(path)
    say("shot", name, json.dumps(await state(pg), ensure_ascii=False))
    say("  targets", [(t["label"], round(t["x"]), round(t["y"]), round(t["w"]), round(t["h"])) for t in ts])
    return ts


async def to_battle(pg):
    await pg.goto("http://localhost:8010/index.html")
    await pg.wait_for_timeout(12000)
    await pg.mouse.click(640, 300)
    for _ in range(40):
        if (await state(pg))["mode"] == "TITLE":
            break
        await press(pg, "Space", 500)
    await pg.wait_for_timeout(800)
    await press(pg, "Space", 2500)
    for _ in range(8):
        s = await state(pg)
        if not s.get("tutorial") and not s.get("awaiting"):
            break
        await press(pg, "Space", 700)
    await pg.wait_for_timeout(800)
    for idx in (0, 71):
        await click(pg, f"starter:{idx}")
        await press(pg, "Space", 1200)
    await shot(pg, "00-starter")
    await click(pg, "start", 1200)
    # "이 실험체들로 시작하시겠습니까?" → 예 (Space 만 누르면 느릴 때 아니오 쪽으로 넘어가 같은 화면을 맴돌아요)
    for _ in range(10):
        if (await state(pg))["mode"] == "CONFIRM":
            await click(pg, "option:0", 2500)
            break
        await pg.wait_for_timeout(300)
    else:
        await press(pg, "Space", 2500)
    for _ in range(40):
        s = await state(pg)
        if s["mode"] == "COMMAND":
            return True
        if s["mode"] == "CONFIRM":
            await pg.wait_for_timeout(600)
            await shot(pg, "00-confirm")
            await click(pg, "option:1", 1200)
            say("after confirm click", await state(pg))
            continue
        if s["mode"] == "PARTY":
            await shot(pg, "00-party-at-start")
            await click(pg, "party-cancel", 900)
            continue
        await press(pg, "Space", 900)
    return False


async def main():
    which = sys.argv[1] if len(sys.argv) > 1 else "all"
    async with async_playwright() as p:
        b = await p.chromium.launch()
        pg = await b.new_page(viewport={"width": 1280, "height": 720})
        errs = []
        pg.on("pageerror", lambda e: errs.append(str(e)))
        ok = await to_battle(pg)
        say("battle ready", ok)

        if which in ("all", "summary"):
            # 실험체 → 첫 칸 → 요약
            await shot(pg, "01-command")
            await click(pg, "command:2", 1200)
            await shot(pg, "02-party")
            await click(pg, "party:0", 1000)
            await shot(pg, "03-party-options")
            labels = [t["label"] for t in await targets(pg)]
            summary_label = next((l for l in labels if "option" in l), None)
            say("party option labels", labels)
            # 요약은 보통 두 번째 줄 (교체 · 요약 · 취소)
            await click(pg, "party-option:0", 1500)
            await shot(pg, "04-summary")
            for page in (1, 2):
                await click(pg, f"summary-page:{page}", 1200)
                ts = await shot(pg, f"05-summary-page{page}")
            # 스킬 쪽: 칸이 있으면 올려 보고, 눌러 보기
            for t in [t for t in ts if not t["label"].startswith("summary-page")][:6]:
                cx, cy = await center(pg, t)
                await pg.mouse.move(cx, cy)
                await pg.wait_for_timeout(500)
                await shot(pg, f"06-summary-hover-{t['label'].replace(':', '_')}", hover=t["label"])
            first = next((t for t in ts if not t["label"].startswith("summary-page")), None)
            if first:
                await click(pg, first["label"], 1200)
                ts2 = await shot(pg, "07-summary-clicked")
                for t in [t for t in ts2 if not t["label"].startswith("summary-page")][:6]:
                    cx, cy = await center(pg, t)
                    await pg.mouse.move(cx, cy)
                    await pg.wait_for_timeout(500)
                    await shot(pg, f"08-summary-sel-hover-{t['label'].replace(':', '_')}", hover=t["label"])
            # 나가기
            for _ in range(6):
                if (await state(pg))["mode"] == "COMMAND":
                    break
                await pg.mouse.click(1270, 710, button="right")
                await pg.wait_for_timeout(800)
            say("back", await state(pg))

        if which in ("all", "reward"):
            seen = []
            for i in range(80):
                s = await state(pg)
                if not seen or seen[-1] != s["mode"]:
                    seen.append(s["mode"])
                if s["mode"] == "MODIFIER_SELECT":
                    break
                if s["mode"] == "COMMAND":
                    await press(pg, "Space", 700)
                    await press(pg, "Space", 1500)
                    continue
                if s["mode"] == "CONFIRM":
                    await click(pg, "option:1", 1200)
                    continue
                if s["mode"] == "PARTY":
                    await click(pg, "party:0", 900)
                    await press(pg, "Space", 900)
                    continue
                await press(pg, "Space", 800)
            say("modes", seen)
            for _ in range(30):
                s = await state(pg)
                labels = [t["label"] for t in await targets(pg)]
                if s["mode"] == "MODIFIER_SELECT" and "reward:0" in labels:
                    break
                if s.get("awaiting") or s.get("tutorial") or s["mode"] == "MESSAGE":
                    await press(pg, "Space", 1000)
                else:
                    await pg.wait_for_timeout(700)
            await pg.wait_for_timeout(1500)
            ts = await shot(pg, "10-reward")
            for t in ts:
                cx, cy = await center(pg, t)
                await pg.mouse.move(cx, cy)
                await pg.wait_for_timeout(500)
                await shot(pg, f"11-reward-hover-{t['label'].replace(':', '_')}", hover=t["label"])
        if which in ("all", "reward"):
            await click(pg, "reward:1", 2500)
            await shot(pg, "12-after-click-reward1")
        say("errors", errs[:5])
        await b.close()
    open(f"{OUT}-log.txt", "w").write("\n".join(log))


if __name__ == "__main__":  # 다른 확인 스크립트에서 함수만 가져다 쓸 수 있게
    asyncio.run(main())
