"""판 중 영입 · 잠재력 확인 (브라우저 자동 진행)

준비 · 실행은 mouse_check.py 와 같아요 (개발 빌드를 8010 에 띄운 뒤): python3 -B scripts/browser-check/catch_check.py
결과: /tmp/pwcheck/ct-*.png
  ct-00-starter        시작 고르기 (처음 열린 6명만 밝게)
  ct-01-potential      '잠재력 보기' 를 켠 모습
  ct-02-command        전투 명령 ('영입×3')
  ct-03-result         영입을 누른 뒤 결과 메시지 (야생동물이면 '실험체만 영입', 실패면 '확정 영입까지 N번')
인자 potential 을 주면 잠재력 화면까지만
"""
import asyncio
import sys

from playwright.async_api import async_playwright

sys.path.insert(0, __file__.rsplit("/", 1)[0])
import mouse_check as mc  # noqa: E402

mc.OUT = "/tmp/pwcheck/ct"


async def snap(pg, name):
    await pg.screenshot(path=f"{mc.OUT}-{name}.png")
    mc.say("snap", name, await mc.state(pg))


async def main():
    async with async_playwright() as p:
        b = await p.chromium.launch(args=["--use-gl=swiftshader", "--enable-unsafe-swiftshader"])
        pg = await b.new_page(viewport={"width": 1280, "height": 720})
        errors = []
        pg.on("pageerror", lambda e: errors.append(str(e)))
        # 시작 고르기까지 (mouse_check.to_battle 앞부분과 같아요)
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
        await snap(pg, "00-starter")
        # 일레븐을 고르고 잠재력 보기
        await mc.click(pg, "starter:4")
        await mc.skip_tutorial(pg)
        await mc.back_to_starters(pg)
        # '잠재력 보기' 는 실험체 고르기 창 안의 줄인데 창이 뜨는 때가 들쭉날쭉해서, 확인용으로는 바로 켜요
        await pg.evaluate("() => window.__bseoScene.ui.getHandler().toggleShowIvsMode()")
        await pg.wait_for_timeout(2500)
        await snap(pg, "01-potential")
        if "potential" in sys.argv:
            await b.close()
            return
        # 전투로 → '영입' (화면 그리기가 느려서 던지기 한 번에 30초쯤 걸려요)
        if await mc.to_battle(pg):
            await snap(pg, "02-command")
            await mc.click(pg, "command:1", 1800)
            for i in range(24):
                await pg.wait_for_timeout(2500)
                text = await pg.evaluate("() => window.__bseoScene.ui.getMessageHandler().message.text")
                if text and i > 1:
                    break
            await pg.wait_for_timeout(2500)
            await snap(pg, "03-result")
        else:
            mc.say("전투까지 못 감")
        mc.say("errors", errors[:5])
        await b.close()


asyncio.run(main())
