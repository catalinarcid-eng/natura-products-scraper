from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from bs4 import BeautifulSoup
import pandas as pd
import time
import re
from datetime import datetime

# Configuración
URL_CHILE = "https://www.natura.cl/c/nuestros-productos"

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
        
        # Buscar código NATCHL
        texto_pagina = soup.get_text(separator=" ")
        match = re.search(r'(NATCHL-\d+)', texto_pagina, re.IGNORECASE)
        if match:
            return match.group(1).upper()
    except Exception as e:
        print(f"Error obteniendo código de {url}: {e}")
    
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
        
        # Alternativa: buscar cualquier párrafo con contenido
        for p in soup.find_all("p"):
            texto = p.get_text(strip=True)
            if len(texto) > 50:
                return texto[:500]
    except Exception as e:
        print(f"Error obteniendo descripción: {e}")
    
    return "No disponible"

def escanear_productos(driver) -> list:
    """Escanea todos los productos de Natura Chile"""
    print(f"🌐 Cargando {URL_CHILE}...")
    driver.get(URL_CHILE)
    time.sleep(5)
    
    # Hacer clic en "explorar más resultados" hasta que no haya más
    clics = 0
    max_clics = 100
    
    while clics < max_clics:
        try:
            # Buscar botón explorar más resultados
            boton = driver.find_element(
                By.XPATH, 
                "//button[contains(translate(text(), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'explorar')]"
            )
            driver.execute_script("arguments[0].scrollIntoView(true);", boton)
            time.sleep(1)
            driver.execute_script("arguments[0].click();", boton)
            clics += 1
            print(f"  ✅ Click {clics}...")
            time.sleep(2)
        except:
            print(f"✅ Todos los productos cargados ({clics} clicks)")
            break
    
    # Extraer URLs de productos
    soup = BeautifulSoup(driver.page_source, "html.parser")
    productos_urls = []
    
    # Buscar todos los enlaces de productos
    for a in soup.find_all("a", href=re.compile(r"/p/", re.I)):
        href = a.get("href", "")
        if href and "/p/" in href:
            if not href.startswith("http"):
                href = "https://www.natura.cl" + href
            productos_urls.append(href)
    
    # Eliminar duplicados manteniendo orden
    productos_urls = list(dict.fromkeys(productos_urls))
    print(f"📦 {len(productos_urls)} productos encontrados")
    
    return productos_urls

def extraer_datos_producto(driver, url: str, numero: int) -> dict:
    """Extrae nombre, código y descripción de un producto"""
    try:
        print(f"[{numero}] Extrayendo datos...")
        driver.get(url)
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
        # Escanear todos los productos
        urls = escanear_productos(driver)
        
        if not urls:
            print("❌ No se encontraron productos")
            return False
        
        # Extraer datos de cada producto
        for i, url in enumerate(urls, 1):
            try:
                datos = extraer_datos_producto(driver, url, i)
                if datos:
                    productos.append(datos)
                time.sleep(1)
            except Exception as e:
                print(f"❌ Error producto {i}: {e}")
                continue
        
        # Guardar en CSV
        if productos:
            df = pd.DataFrame(productos)
            df.to_csv("productos.csv", index=False, encoding="utf-8")
            print("=" * 60)
            print(f"✅ COMPLETADO: {len(productos)} PRODUCTOS EXTRAÍDOS")
            print(f"💾 Guardado en: productos.csv")
            print("=" * 60)
            return True
        else:
            print("❌ No se extrajeron productos")
            return False
    
    except Exception as e:
        print(f"❌ ERROR FATAL: {e}")
        return False
    
    finally:
        driver.quit()
        print("🔌 Chrome cerrado")

if __name__ == "__main__":
    exito = main()
    exit(0 if exito else 1)
