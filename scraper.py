from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import pandas as pd
import time
import re
import os
from datetime import datetime

# ══════════════════════════════════════════════════════════════════
#  CONFIGURACIÓN DE LOTES
#  Cambia LOTE para procesar diferentes rangos:
#    LOTE = 1  →  productos    1 a  250
#    LOTE = 2  →  productos  251 a  500
#    LOTE = 3  →  productos  501 a  750
#    LOTE = 4  →  productos  751 a 1000
#    LOTE = 5  →  productos 1001 a 1250
#  Puedes cambiarlo aquí o con la variable de entorno LOTE en GitHub.
# ══════════════════════════════════════════════════════════════════
LOTE = int(os.environ.get("LOTE", "1"))
TAMANO_LOTE = 250

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

def obtener_codigo_de_url(url: str) -> str:
    match = re.search(r'(NATCHL-\d+)', url, re.IGNORECASE)
    return match.group(1).upper() if match else "No detectado"

# Script validado en diagnóstico 5: funciona en ambos formatos (A y B)
SCRIPT_DESC = """
let resultado = null;

// MÉTODO A: span.text-sm con <li> (formato perfumes/shampoo)
let spans = document.querySelectorAll('span.text-sm');
for (let s of spans) {
    let lis = s.querySelectorAll('li');
    if (lis.length > 0) {
        let items = Array.from(lis).map(li => li.textContent.trim()).filter(t => t.length > 2);
        if (items.length > 0) return items.join(' | ');
    }
}

// MÉTODO B: región del acordeón (role=region) con texto plano
let regiones = document.querySelectorAll('[role="region"]');
for (let r of regiones) {
    let texto = r.textContent.trim();
    if (texto.length > 30 && !texto.toLowerCase().includes('cookie')) {
        return texto;
    }
}

return resultado;
"""

def obtener_descripcion(driver) -> str:
    """El acordeón ya está abierto. NO hacer click. Solo leer."""
    try:
        resultado = driver.execute_script(SCRIPT_DESC)
        if resultado and resultado.strip():
            # Limpiar saltos de línea múltiples
            limpio = re.sub(r'\s*\n\s*', ' ', resultado)
            limpio = re.sub(r'\s{2,}', ' ', limpio)
            return limpio.strip()[:600]
    except:
        pass
    return "No disponible"

def obtener_todas_las_urls(driver) -> list:
    """Escanea el listado completo y junta todas las URLs"""
    print("🌐 Escaneando listado completo de productos...")
    todos_urls = []
    pagina = 1

    while pagina <= 100:
        url = URL_BASE if pagina == 1 else f"{URL_BASE}?page={pagina}"
        driver.get(url)
        try:
            WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, 'a[href*="/p/"]'))
            )
        except:
            pass
        if pagina == 1:
            aceptar_cookies(driver)
        time.sleep(1.5)

        hrefs = driver.execute_script("""
            let links = document.querySelectorAll('a[href*="/p/"]');
            let r = [];
            links.forEach(a => r.push(a.href));
            return [...new Set(r)];
        """)

        nuevos = [u for u in hrefs if u not in todos_urls]
        if not nuevos:
            break
        todos_urls.extend(nuevos)
        if pagina % 10 == 0:
            print(f"   Página {pagina}: {len(todos_urls)} URLs acumuladas...")
        pagina += 1
        time.sleep(0.5)

    todos_urls = list(dict.fromkeys(todos_urls))
    print(f"📦 {len(todos_urls)} productos totales en el sitio\n")
    return todos_urls

def extraer_producto(driver, url: str, numero: int, total: int) -> dict:
    try:
        print(f"[{numero}/{total}] ", end="", flush=True)
        driver.get(url)
        try:
            WebDriverWait(driver, 8).until(
                EC.presence_of_element_located((By.TAG_NAME, "h1"))
            )
        except:
            pass
        time.sleep(1)

        nombre = driver.execute_script("let h=document.querySelector('h1');return h?h.textContent.trim():'N/A';")
        codigo = obtener_codigo_de_url(url)
        descripcion = obtener_descripcion(driver)
        url_limpia = url.split("?")[0]

        print("✅" if descripcion != "No disponible" else "⚠️", flush=True)

        return {"nombre": nombre, "codigo": codigo, "descripcion": descripcion, "url": url_limpia}
    except Exception as e:
        print("❌", flush=True)
        return None

def main():
    print("=" * 60)
    print(f"🚀 NATURA SCRAPER - LOTE {LOTE}")
    print(f"⏰ {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 60 + "\n")

    driver = crear_driver()

    try:
        # Paso 1: obtener TODAS las URLs (rápido, ~3 min)
        todas = obtener_todas_las_urls(driver)
        if not todas:
            print("❌ No se encontraron productos")
            return False

        # Paso 2: seleccionar solo el rango de este lote
        inicio = (LOTE - 1) * TAMANO_LOTE
        fin = inicio + TAMANO_LOTE
        urls_lote = todas[inicio:fin]

        if not urls_lote:
            print(f"⚠️ El lote {LOTE} no tiene productos (solo hay {len(todas)} en total)")
            print(f"   Lotes válidos: 1 a {(len(todas) // TAMANO_LOTE) + 1}")
            return False

        print(f"📥 LOTE {LOTE}: procesando productos {inicio+1} a {min(fin, len(todas))}")
        print(f"   ({len(urls_lote)} productos en este lote)")
        print("=" * 60 + "\n")

        productos = []
        for i, url in enumerate(urls_lote, 1):
            datos = extraer_producto(driver, url, i, len(urls_lote))
            if datos:
                productos.append(datos)

        # Paso 3: guardar CSV de este lote
        print("\n" + "=" * 60)
        if productos:
            nombre_archivo = f"productos_lote_{LOTE}.csv"
            df = pd.DataFrame(productos)
            df.to_csv(nombre_archivo, index=False, encoding="utf-8")
            con_desc = sum(1 for p in productos if p["descripcion"] != "No disponible")
            print(f"✅ LOTE {LOTE} COMPLETADO: {len(productos)} productos")
            print(f"   📝 Con descripción: {con_desc}")
            print(f"   ⚠️  Sin descripción: {len(productos) - con_desc}")
            print(f"💾 Guardado en: {nombre_archivo}")
            print("=" * 60)
            return True
        else:
            print("❌ No se extrajeron productos")
            return False
    except Exception as e:
        print(f"❌ ERROR: {e}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        driver.quit()
        print("🔌 Chrome cerrado")

if __name__ == "__main__":
    exito = main()
    exit(0 if exito else 1)
