from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from bs4 import BeautifulSoup
import pandas as pd
import time
import re
from datetime import datetime

URL_BASE = "https://www.natura.cl/c/nuestros-productos"

def crear_driver():
    """Crea un driver de Chrome con las opciones correctas"""
    opts = Options()
    opts.add_argument("--headless")
    opts.add_argument("--no-sandbox")
    opts.add_argument("--disable-dev-shm-usage")
    opts.add_argument("--window-size=1920,1080")
    opts.add_argument("--disable-blink-features=AutomationControlled")
    opts.add_argument(
        "user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/149.0.0.0 Safari/537.36"
    )
    return webdriver.Chrome(options=opts)

def obtener_codigo_desde_pagina(driver, texto_pagina: str) -> str:
    """Obtiene código del texto de la página"""
    match = re.search(r'(NATCHL-\d+)', texto_pagina, re.IGNORECASE)
    if match:
        return match.group(1).upper()
    return "No detectado"

def obtener_descripcion_desde_pagina(soup) -> str:
    """Obtiene descripción del soup"""
    # Buscar descripción
    for p in soup.find_all("p"):
        texto = p.get_text(strip=True)
        if len(texto) > 50 and "NATCHL" not in texto:
            return texto[:300]
    return "No disponible"

def obtener_productos_pagina(driver, pagina: int) -> list:
    """Obtiene URLs de productos de una página"""
    if pagina == 1:
        url = URL_BASE
    else:
        url = f"{URL_BASE}?page={pagina}"
    
    print(f"📄 Página {pagina}")
    driver.get(url)
    time.sleep(3)
    
    soup = BeautifulSoup(driver.page_source, "html.parser")
    productos_urls = []
    
    # Buscar todos los enlaces de productos
    for a in soup.find_all("a", href=re.compile(r"/p/", re.I)):
        href = a.get("href", "")
        if href and "/p/" in href:
            if not href.startswith("http"):
                href = "https://www.natura.cl" + href
            productos_urls.append(href)
    
    # Eliminar duplicados
    productos_urls = list(dict.fromkeys(productos_urls))
    print(f"   ✅ {len(productos_urls)} URLs encontradas")
    
    return productos_urls

def escanear_todos_productos(driver) -> list:
    """Escanea todas las páginas y obtiene URLs"""
    print(f"🌐 INICIANDO SCRAPING")
    print("=" * 60)
    
    todos_urls = []
    pagina = 1
    max_paginas = 50
    paginas_sin_productos = 0
    
    while pagina <= max_paginas:
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
    
    # Eliminar duplicados globales
    todos_urls = list(dict.fromkeys(todos_urls))
    print(f"📦 {len(todos_urls)} URLs TOTALES encontradas")
    
    return todos_urls

def extraer_datos_producto(driver, url: str, numero: int) -> dict:
    """Extrae nombre, código y descripción visitando la URL"""
    try:
        print(f"[{numero}] ", end="", flush=True)
        driver.get(url)
        time.sleep(0.8)  # MENOS TIEMPO
        
        soup = BeautifulSoup(driver.page_source, "html.parser")
        
        # Nombre
        nombre = "N/A"
        for h in soup.find_all(["h1", "h2"]):
            texto = h.get_text(strip=True)
            if texto and "producto agotado" not in texto.lower():
                nombre = texto
                break
        
        # Código y Descripción
        texto_pagina = soup.get_text(separator=" ")
        codigo = obtener_codigo_desde_pagina(driver, texto_pagina)
        descripcion = obtener_descripcion_desde_pagina(soup)
        
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
    """Función principal"""
    print("=" * 60)
    print(f"🚀 NATURA PRODUCTOS SCRAPER CHILE")
    print(f"⏰ {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 60 + "\n")
    
    driver = crear_driver()
    
    try:
        # Paso 1: Escanear todas las páginas para obtener URLs
        urls = escanear_todos_productos(driver)
        
        if not urls:
            print("❌ No se encontraron productos")
            return False
        
        # Paso 2: Extraer datos de cada URL
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
        
        # Paso 3: Guardar en CSV
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
        return False
    
    finally:
        driver.quit()
        print("🔌 Chrome cerrado")

if __name__ == "__main__":
    exito = main()
    exit(0 if exito else 1)
