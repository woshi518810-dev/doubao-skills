"""
Ozon商品图片批量下载脚本
用法: python ozon_download.py <商品URL> [输出目录]
默认输出目录: D:\\ozon下图
"""
import os
import re
import sys
import time
import requests
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By

DEFAULT_OUTPUT_DIR = r"D:\ozon下图"
CHROMEDRIVER_CANDIDATES = [
    os.path.join(os.path.dirname(os.path.abspath(__file__)), "chromedriver.exe"),
    r"C:\Users\Administrator\Doubao\chats\2026-08-20\new-chat-1\chromedriver-win64\chromedriver.exe",
    "chromedriver.exe",
]

def find_chromedriver():
    for p in CHROMEDRIVER_CANDIDATES:
        if os.path.exists(p):
            return p
    return "chromedriver"

def get_high_res_url(url):
    if not url:
        return url
    return re.sub(r'/wc\d+/', '/wc1500/', url)

def is_product_image(url):
    if not url:
        return False
    ul = url.lower()
    if any(x in ul for x in ['/video-', 'qr-code', 'qrcode', 'logo', '/cms/']):
        return False
    return 'multimedia' in ul

def download_image(url, filepath):
    try:
        r = requests.get(url, headers={
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            'Referer': 'https://www.ozon.ru/',
        }, timeout=30)
        if r.status_code == 200:
            with open(filepath, 'wb') as f:
                f.write(r.content)
            return True
    except Exception as e:
        print(f"    下载失败: {e}")
    return False

def detect_captcha(driver):
    try:
        body = driver.find_element(By.TAG_NAME, "body").text
        if any(x in body for x in ['拖动滑块', '拼图', '不是机器人', '验证']):
            return True
    except:
        pass
    try:
        if 'captcha' in driver.current_url.lower() or 'verify' in driver.current_url.lower():
            return True
    except:
        pass
    return False

def wait_for_captcha_solve(driver, timeout=600):
    if not detect_captcha(driver):
        return True
    print("\n" + "=" * 60)
    print("  检测到滑块验证码！")
    print("  请在浏览器中手动拖动滑块完成验证")
    print("  验证通过后脚本将自动继续...")
    print("=" * 60 + "\n")
    start = time.time()
    while time.time() - start < timeout:
        time.sleep(2)
        if not detect_captcha(driver):
            print("✓ 验证码已通过，继续执行...\n")
            time.sleep(2)
            return True
        elapsed = int(time.time() - start)
        if elapsed % 10 == 0:
            print(f"  等待手动验证中... ({elapsed}s)")
    print(f"  等待超时（{timeout}秒）")
    return False

def collect_variants(driver):
    return driver.execute_script("""
        var variants = [], seen = {};
        var imgs = document.querySelectorAll('img');
        var vw = window.innerWidth;
        for (var i = 0; i < imgs.length; i++) {
            var src = imgs[i].src || imgs[i].getAttribute('src') || '';
            if (!src || src.indexOf('multimedia') === -1) continue;
            var rect = imgs[i].getBoundingClientRect();
            if (rect.x > vw * 0.3 && rect.width > 25 && rect.width < 100 && rect.height > 25 && rect.height < 100) {
                var m = src.match(/\\/(\\d+)\\./);
                if (m && !seen[m[1]]) { seen[m[1]] = true; variants.push(m[1]); }
            }
        }
        return variants;
    """)

def click_variant(driver, vid):
    return driver.execute_script(f"""
        var target = '{vid}';
        var imgs = document.querySelectorAll('img');
        var vw = window.innerWidth;
        for (var j = 0; j < imgs.length; j++) {{
            var src = imgs[j].src || imgs[j].getAttribute('src') || '';
            if (src.indexOf('multimedia') !== -1 && src.indexOf(target) !== -1) {{
                var rect = imgs[j].getBoundingClientRect();
                if (rect.x > vw * 0.25 && rect.width > 20 && rect.width < 120) {{
                    var p = imgs[j].closest('button, [role="button"], a, div');
                    if (p) {{
                        p.scrollIntoView({{block: 'center'}});
                        try {{ p.click(); }} catch(e) {{ imgs[j].click(); }}
                        return true;
                    }}
                }}
            }}
        }}
        return false;
    """)

def extract_left_thumbs(driver):
    return driver.execute_script("""
        var thumbs = [], seen = {};
        var imgs = document.querySelectorAll('img');
        var vw = window.innerWidth;
        for (var i = 0; i < imgs.length; i++) {
            var src = imgs[i].src || imgs[i].getAttribute('src') || '';
            if (!src) continue;
            var rect = imgs[i].getBoundingClientRect();
            if (rect.x < vw * 0.25 && rect.width > 30 && rect.width < 150 && rect.height > 40 && rect.height < 200) {
                var m = src.match(/\\/(\\d+)\\./);
                var key = m ? m[1] : src;
                if (!seen[key]) { seen[key] = true; thumbs.push({src: src, y: Math.round(rect.y)}); }
            }
        }
        thumbs.sort(function(a, b) { return a.y - b.y; });
        return thumbs;
    """)

def main():
    if len(sys.argv) < 2:
        print("用法: python ozon_download.py <Ozon商品URL> [输出目录]")
        print("示例: python ozon_download.py https://www.ozon.ru/product/xxx-123456/")
        sys.exit(1)
    
    url = sys.argv[1]
    output_dir = sys.argv[2] if len(sys.argv) > 2 else DEFAULT_OUTPUT_DIR
    
    url_match = re.search(r'/(\d+)/?$', url)
    product_id = url_match.group(1) if url_match else "unknown"
    
    product_output = os.path.join(output_dir, f"ozon_{product_id}")
    os.makedirs(product_output, exist_ok=True)
    
    print("=" * 60)
    print("Ozon商品图片批量下载")
    print(f"商品URL: {url}")
    print(f"输出目录: {product_output}")
    print("=" * 60)
    
    print("\n[1/4] 启动Chrome...")
    chrome_options = Options()
    chrome_options.add_argument("--start-maximized")
    chrome_options.add_argument("--disable-blink-features=AutomationControlled")
    chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
    chrome_options.add_experimental_option('useAutomationExtension', False)
    
    chromedriver_path = find_chromedriver()
    service = Service(executable_path=chromedriver_path)
    driver = webdriver.Chrome(service=service, options=chrome_options)
    driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
    print("Chrome启动成功！")
    
    try:
        print("\n[2/4] 访问商品页面...")
        driver.get(url)
        time.sleep(6)
        
        if not wait_for_captcha_solve(driver):
            print("验证码未通过，退出")
            return
        
        time.sleep(3)
        print(f"页面标题: {driver.title[:80]}...")
        
        try:
            for btn in driver.find_elements(By.XPATH, "//button[contains(text(), 'OK')]"):
                btn.click()
                time.sleep(0.3)
        except:
            pass
        
        driver.execute_script("window.scrollTo(0, 300)")
        time.sleep(1)
        
        print("\n[3/4] 收集颜色变体...")
        variant_ids = collect_variants(driver)
        print(f"找到 {len(variant_ids)} 个颜色变体")
        
        if not variant_ids:
            print("未找到颜色变体！")
            return
        
        print("\n[4/4] 逐个下载变体套图...")
        
        total_images = 0
        success_variants = 0
        
        for i, vid in enumerate(variant_ids):
            print(f"\n--- 变体 {i+1}/{len(variant_ids)} (ID: {vid}) ---")
            
            if detect_captcha(driver):
                if not wait_for_captcha_solve(driver):
                    print("验证码未通过，停止下载")
                    break
            
            driver.execute_script("window.scrollTo(0, 280)")
            time.sleep(0.5)
            
            if not click_variant(driver, vid):
                print("  点击失败，跳过")
                continue
            
            time.sleep(2.5)
            
            if detect_captcha(driver):
                if not wait_for_captcha_solve(driver):
                    break
                time.sleep(2)
            
            left_thumbs = extract_left_thumbs(driver)
            
            urls = []
            for t in left_thumbs:
                if is_product_image(t['src']):
                    hr = get_high_res_url(t['src'])
                    if hr not in urls:
                        urls.append(hr)
            
            if not urls:
                print("  未找到套图，跳过")
                continue
            
            variant_folder = os.path.join(product_output, f"variant_{i+1:02d}_ID{vid}")
            os.makedirs(variant_folder, exist_ok=True)
            
            print(f"  下载 {len(urls)} 张套图...")
            for j, img_url in enumerate(urls):
                ext = '.png' if '.png' in img_url.lower() else '.jpg'
                filepath = os.path.join(variant_folder, f"{j+1:02d}{ext}")
                if download_image(img_url, filepath):
                    print(f"    ✓ {j+1}/{len(urls)}")
                    total_images += 1
            
            success_variants += 1
        
        print("\n" + "=" * 60)
        print("下载完成！")
        print(f"  成功变体: {success_variants}/{len(variant_ids)}")
        print(f"  图片总数: {total_images}")
        print(f"  保存目录: {product_output}")
        print("=" * 60)
        
        print("\n下载的变体:")
        for d in sorted(os.listdir(product_output)):
            dp = os.path.join(product_output, d)
            if os.path.isdir(dp):
                files = os.listdir(dp)
                print(f"  {d}/ ({len(files)} 张)")
        
        time.sleep(10)
        
    except Exception as e:
        print(f"\n错误: {e}")
        import traceback
        traceback.print_exc()
        print("\n浏览器保持打开60秒...")
        time.sleep(60)
    finally:
        driver.quit()

if __name__ == "__main__":
    main()
