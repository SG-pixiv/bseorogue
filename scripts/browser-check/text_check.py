# SPDX-FileCopyrightText: 2026 SG
# SPDX-License-Identifier: AGPL-3.0-only
"""
글 바꾼 것 화면 확인 (11-18): 시작 고르기의 '성향' 줄 · 실험체 정보 첫 쪽 메모(성향 · 합류)

  개발 빌드를 8010 에 띄운 뒤  python3 -I -B scripts/browser-check/text_check.py
  → /tmp/pwcheck/tx-*.png
"""
import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import mouse_check as mc  # noqa: E402
from playwright.async_api import async_playwright  # noqa: E402

mc.OUT = "/tmp/pwcheck/tx"


async def main():
    Path("/tmp/pwcheck").mkdir(exist_ok=True)
    async with async_playwright() as p:
        b = await p.chromium.launch(args=["--autoplay-policy=no-user-gesture-required"])
        pg = await b.new_page(viewport={"width": 1280, "height": 720})
        errs = []
        pg.on("pageerror", lambda e: errs.append(str(e)))
        await pg.goto("http://localhost:8010/index.html")
        await pg.wait_for_timeout(12000)
        await pg.mouse.click(640, 300)
        for _ in range(40):
            if (await mc.state(pg))["mode"] == "TITLE":
                break
            await mc.press(pg, "Space", 500)
        await pg.wait_for_timeout(800)
        await mc.press(pg, "Space", 2500)
        for _ in range(8):
            s = await mc.state(pg)
            if not s.get("tutorial") and not s.get("awaiting"):
                break
            await mc.press(pg, "Space", 700)
        await mc.back_to_starters(pg)
        # 실험체 칸에 올리면 오른쪽에 성향 · 패시브 줄이 보여요
        for i in range(6):
            t = next((x for x in await mc.targets(pg) if x["label"] == f"starter:{i}"), None)
            if t:
                cx, cy = await mc.center(pg, t)
                await pg.mouse.move(cx, cy)
                await pg.wait_for_timeout(1500)
                await pg.screenshot(path=f"/tmp/pwcheck/tx-00-starter-{i}.png", clip={"x": 0, "y": 560, "width": 440, "height": 60})
        await pg.screenshot(path="/tmp/pwcheck/tx-00-starter.png")
        # 실험체 정보 (4-22 함정: 키보드로는 안 열려서 직접 열어요)
        await pg.evaluate(
            """async () => {
              const s = window.__bseoScene;
              const p = s.addPlayerPokemon(s.ui.getHandler().starterContainers?.[4]?.species ?? s.ui.getHandler().allSpecies?.[0], 20);
              await p.loadAssets();
              s.ui.setMode(9, p, 0);
            }"""
        )
        await pg.wait_for_timeout(3000)
        await pg.screenshot(path="/tmp/pwcheck/tx-01-summary.png")
        print("errors:", errs[:3])
        await b.close()


asyncio.run(main())
