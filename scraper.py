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
        if (items.length > 0) return 'A: ' + items.join(' | ').substring(0,80);
    }
}
let regiones = document.querySelectorAll('[role="region"]');
for (let r of regiones) {
    let texto = r.textContent.trim();
    if (texto.length > 30 && !texto.toLowerCase().includes('cookie')) {
        return 'B: ' + texto.substring(0,80);
    }
}
return 'NADA';
"""

driver = crear_driver()

# Simular lo que hace el scraper: primero el listado, luego varios productos seguidos
URLS_PRODUCTOS = [
    "https://www.natura.cl/p/kaiak-aero-eau-de-toilette-masculino/NATCHL-111174",
    "https://www.natura.cl/p/protector-termico-150-ml/NATCHL-148459",
    "https://www.natura.cl/p/desodorante-antitranspirante-roll-on-erva-doce-70-ml/NATCHL-189412",
    "https://www.natura.cl/p/body-splash-tododia-cereza-negra-y-praline-200-ml/NATCHL-174618",
    "https://www.natura.cl/p/perfume-natura-homem-identidad-100-ml/NATCHL-200122",
]

try:
    print("=" * 70)
    print("DIAGNÓSTICO 6 - ¿Por qué fallan después del producto 10?")
    print("=" * 70)

    # Aceptar cookies UNA vez en el listado (como hace el scraper)
    print("\nPaso 1: Cargar listado y aceptar cookies UNA vez")
    driver.get("https://www.natura.cl/c/nuestros-productos")
    time.sleep(5)
    r = driver.execute_script("let b=document.querySelector('#onetrust-accept-btn-handler'); if(b){b.click();return 'aceptadas';} return 'no habia';")
    print(f"   Cookies: {r}")
    time.sleep(2)

    # Ahora visitar productos SIN volver a aceptar cookies
    print("\nPaso 2: Visitar productos SIN re-aceptar cookies (simula el bug)")
    for i, url in enumerate(URLS_PRODUCTOS, 1):
        driver.get(url)
        try:
            WebDriverWait(driver, 8).until(EC.presence_of_element_located((By.TAG_NAME, "h1")))
        except: pass
        time.sleep(1)

        # ¿Hay banner de cookies visible?
        hay_banner = driver.execute_script("""
            let b = document.querySelector('#onetrust-accept-btn-handler');
            if (b && b.offsetParent !== null) return 'SÍ visible';
            if (b) return 'existe pero oculto';
            return 'no existe';
        """)
        desc = driver.execute_script(SCRIPT_DESC)
        print(f"   [{i}] banner={hay_banner:20s} | desc={desc[:50]}")

    print("\nPaso 3: Probar reaceptando cookies en cada producto")
    for i, url in enumerate(URLS_PRODUCTOS, 1):
        driver.get(url)
        try:
            WebDriverWait(driver, 8).until(EC.presence_of_element_located((By.TAG_NAME, "h1")))
        except: pass
        time.sleep(1)
        driver.execute_script("let b=document.querySelector('#onetrust-accept-btn-handler'); if(b)b.click();")
        time.sleep(1)
        desc = driver.execute_script(SCRIPT_DESC)
        print(f"   [{i}] desc={desc[:55]}")

finally:
    driver.quit()
    print("\n" + "=" * 70)
    print("FIN")
    print("=" * 70)
