from playwright.sync_api import sync_playwright
import time

with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    page = browser.new_page(viewport={"width": 1400, "height": 900})
    
    errors = []
    page.on("console", lambda msg: errors.append(f"[{msg.type}] {msg.text}") if msg.type == "error" else None)
    page.on("pageerror", lambda err: errors.append(f"[PAGE_ERROR] {err}"))
    
    # Check stock page
    page.goto("http://localhost:3000/stock?code=002115", wait_until="networkidle", timeout=60000)
    time.sleep(5)
    page.screenshot(path=r"d:\c盘文件\市场认知引擎\bug_stock.png", full_page=True)
    
    # Check backtest page
    page.goto("http://localhost:3000/backtest", wait_until="networkidle", timeout=30000)
    time.sleep(2)
    page.screenshot(path=r"d:\c盘文件\市场认知引擎\bug_backtest.png", full_page=True)
    
    # Check market page
    page.goto("http://localhost:3000/market", wait_until="networkidle", timeout=30000)
    time.sleep(3)
    page.screenshot(path=r"d:\c盘文件\市场认知引擎\bug_market.png", full_page=True)
    
    # Check home page
    page.goto("http://localhost:3000", wait_until="networkidle", timeout=30000)
    time.sleep(2)
    page.screenshot(path=r"d:\c盘文件\市场认知引擎\bug_home.png", full_page=True)
    
    browser.close()
    
    if errors:
        print("ERRORS FOUND:")
        for e in errors:
            print(f"  {e}")
    else:
        print("No console errors")
    print("Screenshots saved")
