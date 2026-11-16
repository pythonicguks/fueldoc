import os
import asyncio, subprocess, sys, time
from playwright.async_api import async_playwright
srv = subprocess.Popen([sys.executable, "-m", "http.server", "8765", "-d", "site"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
time.sleep(1)
async def main():
    async with async_playwright() as p:
        b = await p.chromium.launch(executable_path=os.environ.get("CHROME_PATH") or None, args=["--no-sandbox","--use-gl=swiftshader","--enable-unsafe-swiftshader","--ignore-gpu-blocklist"])
        pg = await b.new_page(viewport={"width":1400,"height":1000})
        ext=[]; errs=[]
        pg.on("request", lambda r: ext.append(r.url) if not r.url.startswith("http://localhost:8765") and not r.url.startswith("data:") else None)
        pg.on("pageerror", lambda e: errs.append(str(e)))
        pg.on("console", lambda m: errs.append("console:"+m.text) if m.type=="error" else None)
        for name in ["index.html","modele.html","etude-parametrique.html","resultats.html","reproductibilite.html"]:
            await pg.goto(f"http://localhost:8765/{name}", wait_until="networkidle")
            await pg.wait_for_timeout(2500)
            n_mm = await pg.locator("svg[id^=mermaid]").count()
            n_pl = await pg.locator(".js-plotly-plot").count()
            print(name or "index", "mermaid svg:", n_mm, "plotly:", n_pl)
            await pg.screenshot(path=f"/tmp/shot_{name.replace(".html","")}.png", full_page=False)
        # interaction on study page
        await pg.goto("http://localhost:8765/etude-parametrique.html", wait_until="networkidle")
        await pg.fill("#sl-q", "7") if False else await pg.evaluate("()=>{const s=document.getElementById('sl-q');s.value=8;s.dispatchEvent(new Event('input'))}")
        await pg.wait_for_timeout(3500)
        print("kpis:", (await pg.inner_text("#kpis")).replace("\n"," | "))
        print("iframe src:", await pg.get_attribute("#vtk-view","src"))
        await pg.screenshot(path="/tmp/shot_study_q50.png")
        print("EXTERNAL:", sorted(set(ext))[:10]); print("ERRORS:", errs[:8])
        await b.close()
asyncio.run(main()); srv.kill()
