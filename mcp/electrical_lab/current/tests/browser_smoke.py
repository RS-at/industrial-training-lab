from pathlib import Path
import http.server, threading, functools
from playwright.sync_api import sync_playwright
p=Path(__file__).resolve().parents[1] / 'examples' / '荧光灯_自由接线_教学版.html'
handler=functools.partial(http.server.SimpleHTTPRequestHandler,directory=str(p.parent))
server=http.server.ThreadingHTTPServer(('127.0.0.1',0),handler)
threading.Thread(target=server.serve_forever,daemon=True).start()
with sync_playwright() as w:
    browser=w.chromium.launch(executable_path='/usr/bin/chromium',headless=True,args=['--no-sandbox'])
    page=browser.new_page(viewport={"width":1450,"height":950},device_scale_factor=1)
    errors=[]
    page.on('pageerror',lambda e: errors.append(str(e)))
    page.set_content(p.read_text(encoding='utf8'))
    page.locator('#check').click()
    assert '接线未通过' in page.locator('#status').inner_text()
    page.locator('#demo').click()
    page.locator('#check').click()
    assert '接线通过' in page.locator('#status').inner_text(),page.locator('#status').inner_text()
    page.locator('#power').click()
    page.wait_for_timeout(2400)
    assert '稳定点亮' in page.locator('#status').inner_text(),page.locator('#status').inner_text()
    assert 'lit' in page.locator('#lamp-v').get_attribute('class')
    page.screenshot(path='/mnt/data/电工实训仿真_自由接线_预览.png')
    page.locator('#fault').select_option('starter_stuck_closed')
    page.locator('#power').click()
    page.wait_for_timeout(1850)
    assert '不能正常启辉' in page.locator('#status').inner_text(),page.locator('#status').inner_text()
    assert not errors,errors
    print('BROWSER PASS: disconnected blocked; standard wiring passes; lit; stuck-starter fault; JS no exceptions.')
    browser.close()
