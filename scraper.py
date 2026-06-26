from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time

def crear_driver():
    opts = Options()
    opts.add_argument("--headless=new")
    opts.add_argument("--no-sandbox")
    opts.add_argument("--disable-dev-shm-usage")
    opts.add_argument("--window-size=1920,1080")
    opts.add_argument("--disable-blink-features=AutomationControlled")
    opts.add_argument("--lang=es-CL")
    opts.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36")
    return webdriver.Chrome(options=opts)

SCRIPT_DESC = """
let spans = document.querySelectorAll('span.text-sm');
for (let s of spans) {
    let lis = s.querySelectorAll('li');
    if (lis.length > 0) {
        let items = Array.from(lis).map(li => li.textContent.trim()).filter(t => t.length > 2);
        if (items.length > 0) return 'OK';
    }
}
let regiones = document.querySelectorAll('[role="region"]');
for (let r of regiones) {
    let texto = r.textContent.trim();
    if (texto.length > 30 && !texto.toLowerCase().includes('cookie')) return 'OK';
}
return 'FALLA';
"""

driver = crear_driver()

try:
    print("=" * 70)
    print("DIAGNÓSTICO 7 - Reproducir el fallo con 15 productos seguidos")
    print("=" * 70)

    # Primero obtener 15 URLs reales del listado
    driver.get("https://www.natura.cl/c/nuestros-productos")
    time.sleep(5)
    driver.execute_script("let b=document.querySelector('#onetrust-accept-btn-handler'); if(b)b.click();")
    time.sleep(2)
    urls = driver.execute_script("""
        let links = document.querySelectorAll('a[href*="/p/"]');
        let r = [];
        links.forEach(a => r.push(a.href));
        return [...new Set(r)].slice(0, 15);
    """)
    print(f"\nProbando {len(urls)} productos seguidos (rápido, como el lote real):\n")

    for i, url in enumerate(urls, 1):
        t0 = time.time()
        driver.get(url)
        try:
            WebDriverWait(driver, 8).until(EC.presence_of_element_located((By.TAG_NAME, "h1")))
            h1_ok = "h1 OK"
        except:
            h1_ok = "h1 TIMEOUT"
        time.sleep(1)  # mismo sleep que el scraper real

        desc = driver.execute_script(SCRIPT_DESC)

        # Si falla, esperar más y reintentar para confirmar que es timing
        reintento = ""
        if desc == "FALLA":
            time.sleep(3)
            desc2 = driver.execute_script(SCRIPT_DESC)
            reintento = f" → tras +3s: {desc2}"

        t = time.time() - t0
        print(f"   [{i:2d}] {h1_ok:12s} | desc={desc:6s}{reintento} | {t:.1f}s")

finally:
    driver.quit()
    print("\n" + "=" * 70)
    print("FIN - Si los primeros van OK y luego empiezan a FALLAR,")
    print("      y el reintento +3s los arregla, es problema de TIMING/velocidad")
    print("=" * 70)
