from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from bs4 import BeautifulSoup
import pandas as pd
import time
import re
from datetime import datetime

# Configuración
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

def obtener_codigo_desde_pagina(driver, url: str) -> str:
    """Obtiene el código NATCHL de la página del producto"""
    try:
        driver.get(url)
        time.sleep(2)
        soup = BeautifulSoup(driver.page_source, "html.parser")
        
        texto_pagina = soup.get_text(separator=" ")
        match = re.search(r'(NATCHL-\d+)', texto_pagina, re.IGNORECASE)
        if match:
            return match.group(1).upper()
    except Exception as e:
        pass
    
    return "No detectado"

def obtener_descripcion_desde_pagina(driver, url: str) -> str:
    """Obtiene la descripción de la página del producto"""
    try:
        driver.get(url)
        time.sleep(2)
        soup = BeautifulSoup(driver.page_source, "html.parser")
        
        # Buscar descripción
        descripcion = soup.find("div", {"class": re.compile(r"description|product-description", re.I)})
        if descripcion:
            return descripcion.get_text(strip=True)[:500]
        
        for p in soup.find_all("p"):
            texto = p.get_text(strip=True)
            if len(texto) > 50:
                return texto[:500]
    except Exception as e:
        pass
    
    return "No disponible"

def obtener_productos_pagina(driver, pagina: int) -> list:
    """
    Obtiene productos de una página específica
    Navega directamente sin hacer click en el botón
    """
    if pagina == 1:
        url = URL_BASE
    else:
        url = f"{URL_BASE}?page={pagina}"
    
    print(f"📄 Cargando página {pagina}: {url}")
    driver.get(url)
    time.sleep(4)  # Esperar a que cargue
    
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
    print(f"   ✅ {len(productos_urls)} productos encontrados en página {pagina}")
    
    return productos_urls

def detectar_paginas_totales(driver) -> int:
    """
    Detecta cuántas páginas hay
    Busca el botón "explorar más resultados" y obtiene el href
    """
    print("🔍 Detectando páginas totales...")
    driver.get(URL_BASE)
    time.sleep(5)
    
    soup = BeautifulSoup(driver.page_source, "html.parser")
    
    # Buscar el botón de "explorar más resultados"
    for a in soup.find_all("a"):
        href = a.get("href", "")
        aria_label = a.get("aria-label", "").lower()
        
        if "?page=" in href and ("cargar" in aria_label or "explorar" in aria_label):
            # Encontró el botón, extrae el número de página
            match = re.search(r'\?page=(\d+)', href)
            if match:
                max_page = int(match.group(1))
                print(f"   ℹ️ Detectadas al menos {max_page} páginas")
                # En realidad podría haber más, así que vamos a probar más
                return max_page + 50  # Probar muchas más páginas
    
    # Si no encuentra botón, intenta muchas páginas
    print("   ℹ️ No se detectó botón, probando múltiples páginas...")
    return 100

def escanear_todos_productos(driver) -> list:
    """Escanea todos los productos navegando por cada página"""
    print(f"🌐 INICIANDO SCRAPING DE {URL_BASE}")
    print("=" * 60)
    
    todos_productos = []
    pagina = 1
    max_paginas = detectar_paginas_totales(driver)
    paginas_sin_productos = 0
    
    while pagina <= max_paginas:
        try:
            productos = obtener_productos_pagina(driver, pagina)
            
            if not productos:
                paginas_sin_productos += 1
                print(f"   ⚠️  Página {pagina}: Sin productos (intento {paginas_sin_productos})")
                
                # Si llevamos 3 páginas sin productos, paramos
                if paginas_sin_productos >= 3:
                    print(f"✅ Todas las páginas escaneadas. Total: {pagina - paginas_sin_productos} páginas con contenido")
                    break
            else:
                paginas_sin_productos = 0
                todos_productos.extend(productos)
            
            pagina += 1
            time.sleep(2)  # Esperar entre páginas
            
        except Exception as e:
            print(f"   ❌ Error en página {pagina}: {e}")
            pagina += 1
            continue
    
    # Eliminar duplicados globales
    todos_productos = list(dict.fromkeys(todos_productos))
    print(f"📦 TOTAL PRODUCTOS ENCONTRADOS: {len(todos_productos)}")
    
    return todos_productos

def extraer_datos_producto(driver, url: str, numero: int) -> dict:
    """Extrae nombre, código y descripción de un producto"""
    try:
        print(f"[{numero}] Extrayendo datos...")
        driver.get(url)
        time.sleep(1.5)
        
        soup = BeautifulSoup(driver.page_source, "html.parser")
        
        # Nombre
        nombre = "N/A"
        for h in soup.find_all(["h1", "h2"]):
            texto = h.get_text(strip=True)
            if texto and "producto agotado" not in texto.lower():
                nombre = texto
                break
        
        # Código
        codigo = obtener_codigo_desde_pagina(driver, url)
        
        # Descripción
        descripcion = obtener_descripcion_desde_pagina(driver, url)
        
        return {
            "nombre": nombre,
            "codigo": codigo,
            "descripcion": descripcion,
            "url": url
        }
    
    except Exception as e:
        print(f"❌ Error en producto {numero}: {e}")
        return None

def main():
    """Función principal"""
    print("=" * 60)
    print(f"🚀 NATURA PRODUCTOS SCRAPER CHILE")
    print(f"⏰ {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 60)
    
    driver = crear_driver()
    productos = []
    
    try:
        # Escanear todos los productos (por páginas)
        urls = escanear_todos_productos(driver)
        
        if not urls:
            print("❌ No se encontraron productos")
            return False
        
        print("\n" + "=" * 60)
        print(f"📥 EXTRAYENDO DATOS DE {len(urls)} PRODUCTOS")
        print("=" * 60 + "\n")
        
        # Extraer datos de cada producto
        for i, url in enumerate(urls, 1):
            try:
                datos = extraer_datos_producto(driver, url, i)
                if datos:
                    productos.append(datos)
                time.sleep(0.3)
            except Exception as e:
                print(f"❌ Error producto {i}: {e}")
                continue
        
        # Guardar en CSV
        if productos:
            df = pd.DataFrame(productos)
            df.to_csv("productos.csv", index=False, encoding="utf-8")
            print("\n" + "=" * 60)
            print(f"✅ COMPLETADO: {len(productos)} PRODUCTOS EXTRAÍDOS")
            print(f"💾 Guardado en: productos.csv")
            print("=" * 60)
            return True
        else:
            print("❌ No se extrajeron productos")
            return False
    
    except Exception as e:
        print(f"❌ ERROR FATAL: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    finally:
        driver.quit()
        print("🔌 Chrome cerrado")

if __name__ == "__main__":
    exito = main()
    exit(0 if exito else 1)
