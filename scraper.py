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
    opts.add_argument("--headless")
    opts.add_argument("--no-sandbox")
    opts.add_argument("--disable-dev-shm-usage")
    opts.add_argument("--window-size=1920,1080")
    opts.add_argument("--disable-blink-features=AutomationControlled")
    opts.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36")
    return webdriver.Chrome(options=opts)

def obtener_codigo(texto_pagina: str) -> str:
    match = re.search(r'(NATCHL-\d+)', texto_pagina, re.IGNORECASE)
    return match.group(1).upper() if match else "No detectado"

def obtener_descripcion(driver) -> str:
    """Abre el acordeón y extrae la descripción"""
    
    try:
        # PASO 1: Abrir el acordeón con JavaScript
        script_abrir = """
        let botones = document.querySelectorAll('button');
        for (let btn of botones) {
            if (btn.textContent.toLowerCase().includes('descripción')) {
                btn.click();
                return true;
            }
        }
        return false;
        """
        
        driver.execute_script(script_abrir)
        time.sleep(1)
        
        # PASO 2: Extraer el contenido
        script_extraer = """
        let span = document.querySelector('span.text-sm');
        if (span) {
            let lis = span.querySelectorAll('li');
            if (lis.length > 0) {
                return Array.from(lis).map(li => li.textContent.trim()).join(' | ');
            }
        }
        return null;
        """
        
        resultado = driver.execute_script(script_extraer)
        if resultado:
            return resultado[:500]
    
    except Exception as e:
        pass
    
    return "No disponible"

def obtener_productos_pagina(driver, pagina: int) -> list:
    url = URL_BASE if pagina == 1 else f"{URL_BASE}?page={pagina}"
    
    print(f"📄 Página {pagina}")
    driver.get(url)
    
    # ESPERAR A QUE LOS PRODUCTOS CARGUEN
    try:
        WebDriverWait(driver, 8).until(
            EC.presence_of_all_elements_located((By.XPATH, "//a[contains(@href, '/p/')]"))
        )
    except:
        print("   ⚠️  Timeout esperando productos, continuando...")
    
    time.sleep(2)
    
    soup = BeautifulSoup(driver.page_source, "html.parser")
    productos_urls = []
    
    for a in soup.find_all("a", href=re.compile(r"/p/", re.I)):
        href = a.get("href", "")
        if href and "/p/" in href:
            if not href.startswith("http"):
                href = "https://www.natura.cl" + href
            productos_urls.append(href)
    
    productos_urls = list(dict.fromkeys(productos_urls))
    print(f"   ✅ {len(productos_urls)} URLs encontradas")
    return productos_urls

def escanear_todos_productos(driver) -> list:
    print(f"🌐 INICIANDO SCRAPING\n" + "=" * 60)
    
    todos_urls = []
    pagina = 1
    paginas_sin_productos = 0
    
    while pagina <= 1:
        try:
            urls = obtener_productos_pagina(driver, pagina)
            
            if not urls:
                paginas_sin_productos += 1
                if paginas_sin_productos >= 2:
                    print(f"\n✅ Todas las páginas escaneadas")
                    break
            else:
                paginas_sin_productos = 0
                todos_urls.extend(urls)
            
            pagina += 1
            time.sleep(1)
        except Exception as e:
            print(f"   ❌ Error: {e}")
            pagina += 1
            continue
    
    todos_urls = list(dict.fromkeys(todos_urls))
    print(f"📦 {len(todos_urls)} URLs TOTALES")
    return todos_urls

def extraer_datos_producto(driver, url: str, numero: int) -> dict:
    try:
        print(f"[{numero}] ", end="", flush=True)
        driver.get(url)
        
        # Esperar a que cargue
        try:
            WebDriverWait(driver, 5).until(
                EC.presence_of_element_located((By.TAG_NAME, "h1"))
            )
        except:
            pass
        
        time.sleep(2)
        
        soup = BeautifulSoup(driver.page_source, "html.parser")
        
        # Nombre
        nombre = "N/A"
        for h in soup.find_all(["h1", "h2"]):
            texto = h.get_text(strip=True)
            if texto and "producto agotado" not in texto.lower():
                nombre = texto
                break
        
        # Código
        texto_pagina = soup.get_text(separator=" ")
        codigo = obtener_codigo(texto_pagina)
        
        # Descripción (abre acordeón)
        descripcion = obtener_descripcion(driver)
        
        return {
            "nombre": nombre,
            "codigo": codigo,
            "descripcion": descripcion,
            "url": url
        }
    
    except Exception as e:
        print(f"❌", flush=True)
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
        print("=" * 60 + "\n")
        
        productos = []
        for i, url in enumerate(urls, 1):
            try:
                datos = extraer_datos_producto(driver, url, i)
                if datos:
                    productos.append(datos)
                    print("✅", flush=True)
            except Exception as e:
                print(f"❌", flush=True)
                continue
        
        print("\n" + "=" * 60)
        
        if productos:
            df = pd.DataFrame(productos)
            df.to_csv("productos.csv", index=False, encoding="utf-8")
            print(f"✅ COMPLETADO: {len(productos)} PRODUCTOS EXTRAÍDOS")
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
