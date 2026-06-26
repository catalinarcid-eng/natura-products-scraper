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

def aceptar_cookies(driver):
    try:
        driver.execute_script("let b=document.querySelector('#onetrust-accept-btn-handler'); if(b)b.click();")
        time.sleep(0.5)
    except: pass

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

# PRIMERO: obtener algunas URLs reales rápido
driver = crear_driver()
driver.get(URL_BASE)
time.sleep(5)
aceptar_cookies(driver)
time.sleep(2)
urls = driver.execute_script("""
    let links = document.querySelectorAll('a[href*="/p/"]');
    let r = []; links.forEach(a => r.push(a.href));
    return [...new Set(r)].slice(0, 15);
""")
driver.quit()

print("=" * 70)
print("DIAGNÓSTICO 9 - ¿Reiniciar Chrome arregla el problema de memoria?")
print("=" * 70)

# TEORÍA: si proceso productos SIN escanear 1101 URLs antes,
# y reinicio Chrome cada 5 productos, NO debería fallar.

print("\nProcesando 15 productos, REINICIANDO Chrome cada 5:\n")

driver = crear_driver()
contador = 0

try:
    for i, url in enumerate(urls, 1):
        # Reiniciar cada 5 productos
        if contador >= 5:
            print("   🔄 Reiniciando Chrome (liberar memoria)...")
            driver.quit()
            driver = crear_driver()
            contador = 0

        driver.get(url)
        try:
            WebDriverWait(driver, 8).until(EC.presence_of_element_located((By.TAG_NAME, "h1")))
        except: pass
        aceptar_cookies(driver)
        time.sleep(1)

        desc = driver.execute_script(SCRIPT_DESC)
        print(f"   [{i:2d}] {desc}")
        contador += 1

finally:
    driver.quit()
    print("\n" + "=" * 70)
    print("Si TODOS van OK = el problema era MEMORIA y reiniciar lo arregla")
    print("=" * 70)
