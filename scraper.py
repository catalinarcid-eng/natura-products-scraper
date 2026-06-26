from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time

URL_BASE = "https://www.natura.cl/c/nuestros-productos"

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
        if (items.length > 0) return 'OK-A';
    }
}
let regiones = document.querySelectorAll('[role="region"]');
for (let r of regiones) {
    let texto = r.textContent.trim();
    if (texto.length > 30 && !texto.toLowerCase().includes('cookie')) return 'OK-B';
}
return 'FALLA';
"""

driver = crear_driver()

try:
    print("=" * 70)
    print("DIAGNÓSTICO 8 - Reproducir EXACTAMENTE la condición del lote")
    print("=" * 70)

    # PASO 1: Igual que el scraper real - escanear TODO el listado primero
    print("\nPASO 1: Escaneando las 1101 URLs (como el lote, gasta ~4 min)...")
    driver.get(URL_BASE)
    time.sleep(5)
    driver.execute_script("let b=document.querySelector('#onetrust-accept-btn-handler'); if(b)b.click();")
    print("   Cookies aceptadas. Escaneando páginas...")
    time.sleep(2)

    todas = []
    pagina = 1
    while pagina <= 100:
        url = URL_BASE if pagina == 1 else f"{URL_BASE}?page={pagina}"
        driver.get(url)
        try:
            WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.CSS_SELECTOR, 'a[href*="/p/"]')))
        except: pass
        time.sleep(1.2)
        hrefs = driver.execute_script("""
            let links = document.querySelectorAll('a[href*="/p/"]');
            let r = []; links.forEach(a => r.push(a.href));
            return [...new Set(r)];
        """)
        nuevos = [u for u in hrefs if u not in todas]
        if not nuevos:
            break
        todas.extend(nuevos)
        pagina += 1
        time.sleep(0.4)

    print(f"   ✅ {len(todas)} URLs escaneadas\n")

    # PASO 2: AHORA visitar los primeros 15 productos (igual que el lote)
    print("PASO 2: Visitando los primeros 15 productos DESPUÉS del escaneo")
    print("(Si fallan del 11 en adelante = se reproduce el bug del lote)\n")

    for i, url in enumerate(todas[:15], 1):
        driver.get(url)
        try:
            WebDriverWait(driver, 8).until(EC.presence_of_element_located((By.TAG_NAME, "h1")))
            h1_ok = "h1 OK"
        except:
            h1_ok = "h1 TIMEOUT"
        time.sleep(1)

        desc = driver.execute_script(SCRIPT_DESC)

        # Si falla, reintentar con más espera
        extra = ""
        if desc == "FALLA":
            time.sleep(3)
            desc2 = driver.execute_script(SCRIPT_DESC)
            extra = f" → +3s: {desc2}"
            if desc2 == "FALLA":
                # Recargar la página completa
                driver.get(url)
                time.sleep(4)
                desc3 = driver.execute_script(SCRIPT_DESC)
                extra += f" → recarga: {desc3}"

        print(f"   [{i:2d}] {h1_ok:12s} | {desc:6s}{extra}")

finally:
    driver.quit()
    print("\n" + "=" * 70)
    print("FIN")
    print("=" * 70)
