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

def obtener_productos_pagina(driver, pagina: int) -> list:
    """
    Obtiene productos de una página específica
    Extrae datos directamente del HTML de la lista (sin visitar cada producto)
    """
    if pagina == 1:
        url = URL_BASE
    else:
        url = f"{URL_BASE}?page={pagina}"
    
    print(f"📄 Página {pagina}: {url}")
    driver.get(url)
    time.sleep(3)
    
    soup = BeautifulSoup(driver.page_source, "html.parser")
    productos = []
    
    # Buscar todas las tarjetas de productos
    for card in soup.find_all("div", {"class": re.compile(r"product|card", re.I)}):
        try:
            # URL del producto
            href = None
            for a in card.find_all("a", href=re.compile(r"/p/")):
                href = a.get("href", "")
                if href:
                    if not href.startswith("http"):
                        href = "https://www.natura.cl" + href
                    break
            
            if not href:
                continue
            
            # Nombre del producto
            nombre = "N/A"
            for h in card.find_all(["h4", "h3", "h2"]):
                texto = h.get_text(strip=True)
                if texto and "producto agotado" not in texto.lower():
                    nombre = texto
                    break
            
            # Código NATCHL (buscar en todo el HTML de la tarjeta)
            codigo = "N/A"
            card_text = card.get_text(separator=" ")
            match = re.search(r'(NATCHL-\d+)', card_text, re.IGNORECASE)
            if match:
                codigo = match.group(1).upper()
            
            # Descripción (buscar en el HTML de la tarjeta)
            descripcion = "No disponible"
            for p in card.find_all("p"):
                texto = p.get_text(strip=True)
                if len(texto) > 20 and "NATCHL" not in texto:
                    descripcion = texto[:300]
                    break
            
            if nombre != "N/A" and href:
                productos.append({
                    "nombre": nombre,
                    "codigo": codigo,
                    "descripcion": descripcion,
                    "url": href
                })
        
        except Exception as e:
            continue
    
    print(f"   ✅ {len(productos)} productos encontrados")
    return productos

def escanear_todos_productos(driver) -> list:
    """Escanea todos los productos navegando por cada página"""
    print(f"🌐 INICIANDO SCRAPING")
    print("=" * 60)
    
    todos_productos = []
    pagina = 1
    max_paginas = 50  # Máximo de páginas a revisar
    paginas_sin_productos = 0
    
    while pagina <= max_paginas:
        try:
            productos = obtener_productos_pagina(driver, pagina)
            
            if not productos:
                paginas_sin_productos += 1
                
                # Si llevamos 2 páginas sin productos, paramos
                if paginas_sin_productos >= 2:
                    print(f"\n✅ Escaneadas {pagina - 1} páginas con contenido")
                    break
            else:
                paginas_sin_productos = 0
                todos_productos.extend(productos)
            
            pagina += 1
            time.sleep(1)
            
        except Exception as e:
            print(f"   ❌ Error: {e}")
            pagina += 1
            continue
    
    # Eliminar duplicados
    urls_vistas = set()
    productos_unicos = []
    for p in todos_productos:
        if p["url"] not in urls_vistas:
            urls_vistas.add(p["url"])
            productos_unicos.append(p)
    
    print(f"\n📦 TOTAL: {len(productos_unicos)} productos únicos")
    return productos_unicos

def main():
    """Función principal"""
    print("=" * 60)
    print(f"🚀 NATURA PRODUCTOS SCRAPER CHILE")
    print(f"⏰ {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 60 + "\n")
    
    driver = crear_driver()
    
    try:
        # Escanear todos los productos
        productos = escanear_todos_productos(driver)
        
        if not productos:
            print("❌ No se encontraron productos")
            return False
        
        # Guardar en CSV
        df = pd.DataFrame(productos)
        df.to_csv("productos.csv", index=False, encoding="utf-8")
        
        print("\n" + "=" * 60)
        print(f"✅ COMPLETADO: {len(productos)} PRODUCTOS EXTRAÍDOS")
        print(f"💾 Guardado en: productos.csv")
        print("=" * 60)
        
        return True
    
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
