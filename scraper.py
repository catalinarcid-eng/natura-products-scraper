from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from bs4 import BeautifulSoup
import pandas as pd
import time
import re
from datetime import datetime

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
    """Acepta el banner de cookies de OneTrust si aparece"""
    try:
        driver.execute_script("""
            let btn = document.querySelector('#onetrust-accept-btn-handler');
            if (btn) { btn.click(); }
        """)
        time.sleep(1)
    except:
        pass

def obtener_codigo_de_url(url: str) -> str:
    """Extrae el código NATCHL directamente de la URL"""
    match = re.search(r'(NATCHL-\d+)', url, re.IGNORECASE)
    return match.group(1).upper() if match else "No detectado"

def obtener_descripcion(driver) -> str:
    """
    Abre el acordeón de descripción y extrae el contenido del span.text-sm
    """
    try:
        # Hacer click en el botón/acordeón de descripción
        driver.execute_script("""
            let botones = document.querySelectorAll('button');
            for (let btn of botones) {
                if (btn.textContent.toLowerCase().includes('descripción')) {
                    btn.click();
                    return;
                }
            }
        """)
        time.sleep(1.5)

        # Extraer el contenido del span.text-sm (los <li>)
        resultado = driver.execute_script("""
            let spans = document.querySelectorAll('span.text-sm');
            for (let span of spans) {
                let lis = span.querySelectorAll('li');
                if (lis.length > 0) {
                    let items = [];
                    for (let li of lis) {
                        let t = li.textContent.trim();
                        if (t) items.push(t);
                    }
                    if (items.length > 0) return items.join(' | ');
                }
            }
            return null;
        """)

        if resultado and resultado.strip():
            return resultado[:600]
    except:
        pass

    return "No disponible"

def obtener_productos_pagina(driver, pagina: int) -> list:
    """Obtiene las URLs reales (.href completo) de los productos de una página"""
    url = URL_BASE if pagina == 1 else f"{URL_BASE}?page={pagina}"
    print(f"📄 Página {pagina}")
    driver.get(url)

    # Esperar a que carguen los productos
    try:
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, 'a[href*="/p/"]'))
        )
    except:
        pass

    aceptar_cookies(driver)
    time.sleep(2)

    # Usar .href completo (ya trae https + nombre + NATCHL + parámetros)
    hrefs = driver.execute_script("""
        let links = document.querySelectorAll('a[href*="/p/"]');
        let resultado = [];
        links.forEach(a => resultado.push(a.href));
        return [...new Set(resultado)];
    """)

    print(f"   ✅ {len(hrefs)} URLs encontradas")
    return hrefs

def escanear_todos_productos(driver) -> list:
    print(f"🌐 INICIANDO SCRAPING\n" + "=" * 60)
    todos_urls = []
    pagina = 1
    paginas_sin_productos = 0

    while pagina <= 200:
        try:
            urls = obtener_productos_pagina(driver, pagina)
            if not urls:
                paginas_sin_productos += 1
                if paginas_sin_productos >= 2:
                    break
            else:
                # ¿Trae productos nuevos respecto a lo que ya tenemos?
                nuevos = [u for u in urls if u not in todos_urls]
                if not nuevos:
                    print("   ℹ️ Sin productos nuevos, fin del paginado")
                    break
                todos_urls.extend(nuevos)
                paginas_sin_productos = 0
            pagina += 1
            time.sleep(1)
        except Exception as e:
            print(f"   ❌ Error: {e}")
            pagina += 1
            continue

    todos_urls = list(dict.fromkeys(todos_urls))
    print(f"\n📦 {len(todos_urls)} URLs TOTALES")
    return todos_urls

def extraer_datos_producto(driver, url: str, numero: int) -> dict:
    try:
        print(f"[{numero}] ", end="", flush=True)
        driver.get(url)

        # Esperar a que cargue el h1
        try:
            WebDriverWait(driver, 8).until(
                EC.presence_of_element_located((By.TAG_NAME, "h1"))
            )
        except:
            pass

        aceptar_cookies(driver)
        time.sleep(1.5)

        soup = BeautifulSoup(driver.page_source, "html.parser")

        # Nombre (del h1)
        nombre = "N/A"
        h1 = soup.find("h1")
        if h1:
            nombre = h1.get_text(strip=True)

        # Código (de la URL, que es lo más confiable)
        codigo = obtener_codigo_de_url(url)

        # Descripción (abrir acordeón + leer)
        descripcion = obtener_descripcion(driver)

        # URL limpia (sin parámetros de tracking)
        url_limpia = url.split("?")[0]

        estado = "✅" if descripcion != "No disponible" else "⚠️"
        print(estado, flush=True)

        return {
            "nombre": nombre,
            "codigo": codigo,
            "descripcion": descripcion,
            "url": url_limpia
        }
    except Exception as e:
        print("❌", flush=True)
        return None

def main():
    print("=" * 60)
    print(f"🚀 NATURA PRODUCTOS SCRAPER CHILE")
    print(f"⏰ {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 60 + "\n")

    driver = crear_driver()

    try:
        urls = escanear_todos_productos(driver)
        if not urls:
            print("❌ No se encontraron productos")
            return False

        print(f"\n📥 EXTRAYENDO DATOS DE {len(urls)} PRODUCTOS")
        print("(✅=con descripción  ⚠️=sin descripción  ❌=error)")
        print("=" * 60 + "\n")

        productos = []
        for i, url in enumerate(urls, 1):
            datos = extraer_datos_producto(driver, url, i)
            if datos:
                productos.append(datos)

        print("\n" + "=" * 60)

        if productos:
            df = pd.DataFrame(productos)
            df.to_csv("productos.csv", index=False, encoding="utf-8")
            con_desc = sum(1 for p in productos if p["descripcion"] != "No disponible")
            print(f"✅ COMPLETADO: {len(productos)} productos")
            print(f"   📝 Con descripción: {con_desc}")
            print(f"   ⚠️  Sin descripción: {len(productos) - con_desc}")
            print(f"💾 Guardado en: productos.csv")
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
