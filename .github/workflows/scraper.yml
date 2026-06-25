from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
import pandas as pd
import time
import logging
import os
from datetime import datetime

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('scraper.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger()

class NaturaScraper:
    def __init__(self):
        options = webdriver.ChromeOptions()
        
        # Configuración para GitHub Actions
        options.add_argument('--headless')
        options.add_argument('--no-sandbox')
        options.add_argument('--disable-dev-shm-usage')
        options.add_argument('--disable-gpu')
        options.add_argument('--disable-web-resources')
        options.add_argument('--single-process')
        options.add_argument('user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36')
        
        try:
            self.driver = webdriver.Chrome(
                service=Service(ChromeDriverManager().install()),
                options=options
            )
        except:
            self.driver = webdriver.Chrome(options=options)
        
        self.productos = []
        self.wait = WebDriverWait(self.driver, 15)

    def cargar_todos_productos(self):
        """Carga todos los productos haciendo click en 'explorar más resultados'"""
        url = "https://www.natura.cl/c/nuestros-productos"
        logger.info(f"🌐 Accediendo a {url}")
        self.driver.get(url)
        time.sleep(4)
        
        logger.info("⏳ Iniciando carga de productos...")
        contador_clicks = 0
        
        while True:
            try:
                # Buscar botones que contienen "explorar más resultados" o similar
                botones = self.driver.find_elements(
                    By.XPATH, 
                    "//button[contains(translate(text(), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'explorar')]"
                )
                
                if not botones:
                    logger.info("✅ No hay más botones para cargar. Todos los productos cargados.")
                    break
                
                boton = botones[0]
                
                # Hacer scroll hacia el botón
                self.driver.execute_script("arguments[0].scrollIntoView(true);", boton)
                time.sleep(1)
                
                # Click en el botón
                self.driver.execute_script("arguments[0].click();", boton)
                contador_clicks += 1
                logger.info(f"✅ Click #{contador_clicks} realizado")
                
                # Esperar a que carguen nuevos productos
                time.sleep(3)
                
            except Exception as e:
                logger.info("✅ Todos los productos cargados correctamente")
                break
        
        logger.info(f"📦 Total de clicks realizados: {contador_clicks}")

    def obtener_enlaces_productos(self):
        """Extrae los enlaces de todos los productos en la página"""
        try:
            logger.info("🔍 Extrayendo enlaces de productos...")
            time.sleep(2)
            
            # Obtener todos los enlaces de productos
            elementos = self.driver.find_elements(
                By.XPATH, 
                "//a[contains(@href, '/p/') and .//div]"
            )
            
            enlaces = []
            visto = set()
            
            for elemento in elementos:
                try:
                    href = elemento.get_attribute('href')
                    if href and '/p/' in href and href not in visto:
                        enlaces.append(href)
                        visto.add(href)
                except:
                    continue
            
            # Eliminar duplicados manteniendo orden
            enlaces = list(dict.fromkeys(enlaces))
            
            logger.info(f"📦 Se encontraron {len(enlaces)} productos únicos")
            return enlaces
            
        except Exception as e:
            logger.error(f"❌ Error obteniendo enlaces: {e}")
            return []

    def extraer_datos_producto(self, url_producto, numero):
        """Extrae nombre, código y descripción de un producto"""
        try:
            logger.info(f"\n⏳ [{numero}] Accediendo a: {url_producto}")
            self.driver.get(url_producto)
            time.sleep(3)
            
            datos = {'url': url_producto}
            
            # ========== EXTRAER NOMBRE ==========
            try:
                nombre_elem = self.driver.find_element(
                    By.XPATH, 
                    "//h1 | //h2[@role='heading'] | //*[contains(@class, 'product-title')]"
                )
                datos['nombre'] = nombre_elem.text.strip()
                logger.info(f"✅ Nombre: {datos['nombre']}")
            except:
                datos['nombre'] = "N/A"
                logger.warning("⚠️ No se encontró nombre")
            
            # ========== EXTRAER CÓDIGO NATCHL ==========
            try:
                codigo_elementos = self.driver.find_elements(
                    By.XPATH, 
                    "//*[contains(text(), 'NATCHL-')] | //span[contains(text(), 'NATCHL-')]"
                )
                
                if codigo_elementos:
                    # Obtener el primer elemento que contenga el código
                    for elem in codigo_elementos:
                        texto = elem.text.strip()
                        if 'NATCHL-' in texto:
                            # Extraer solo el código (NATCHL-XXXXX)
                            codigo = texto.split()[0] if ' ' in texto else texto
                            datos['codigo'] = codigo
                            logger.info(f"✅ Código: {datos['codigo']}")
                            break
                else:
                    datos['codigo'] = "N/A"
                    logger.warning("⚠️ No se encontró código NATCHL")
            except Exception as e:
                datos['codigo'] = "N/A"
                logger.warning(f"⚠️ Error extrayendo código: {e}")
            
            # ========== EXTRAER DESCRIPCIÓN ==========
            datos['descripcion'] = self.extraer_descripcion()
            
            return datos
            
        except Exception as e:
            logger.error(f"❌ Error extrayendo datos del producto: {e}")
            return None

    def extraer_descripcion(self):
        """Extrae la descripción expandiendo el acordeón si es necesario"""
        try:
            # Buscar y hacer click en la sección de descripción
            try:
                # Buscar botón que contenga "descripción"
                botones_desc = self.driver.find_elements(
                    By.XPATH,
                    "//button[contains(translate(text(), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'descripción')]"
                )
                
                if botones_desc:
                    boton = botones_desc[0]
                    
                    # Verificar si está cerrado
                    aria_expanded = boton.get_attribute('aria-expanded')
                    if aria_expanded == 'false':
                        self.driver.execute_script("arguments[0].click();", boton)
                        logger.info("📖 Expandiendo descripción...")
                        time.sleep(2)
            except:
                pass
            
            # Extraer el texto de descripción
            try:
                # Buscar div con contenido de descripción
                descripciones = self.driver.find_elements(
                    By.XPATH,
                    "//*[contains(@class, 'description') or contains(@class, 'producto-descripcion') or contains(@class, 'product-description')]//p | //*[contains(@id, 'description')]"
                )
                
                if descripciones:
                    texto_desc = " ".join([desc.text.strip() for desc in descripciones if desc.text.strip()])
                    if texto_desc:
                        logger.info(f"✅ Descripción extraída ({len(texto_desc)} caracteres)")
                        return texto_desc
                
                # Alternativa: buscar cualquier div con texto después de describción
                todos_los_divs = self.driver.find_elements(By.TAG_NAME, "div")
                for i, div in enumerate(todos_los_divs):
                    texto = div.text.strip()
                    if len(texto) > 50 and ("explosión" in texto or "aroma" in texto or "familia" in texto or "uso" in texto):
                        logger.info(f"✅ Descripción extraída (alternativa)")
                        return texto
                
                logger.warning("⚠️ Descripción no disponible")
                return "Descripción no disponible"
                
            except Exception as e:
                logger.warning(f"⚠️ Error extrayendo texto: {e}")
                return "Descripción no disponible"
                
        except Exception as e:
            logger.warning(f"⚠️ Error en extraer_descripcion: {e}")
            return "Descripción no disponible"

    def ejecutar(self):
        """Ejecuta el scraper completo"""
        try:
            logger.info("=" * 60)
            logger.info("🚀 INICIANDO SCRAPER DE NATURA CHILE")
            logger.info(f"⏰ Fecha: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
            logger.info("=" * 60)
            
            # Paso 1: Cargar todos los productos
            self.cargar_todos_productos()
            
            # Paso 2: Obtener enlaces
            enlaces = self.obtener_enlaces_productos()
            
            if not enlaces:
                logger.error("❌ No se encontraron enlaces de productos")
                return False
            
            # Paso 3: Extraer datos de cada producto
            for i, enlace in enumerate(enlaces, 1):
                try:
                    datos = self.extraer_datos_producto(enlace, i)
                    if datos:
                        self.productos.append(datos)
                    time.sleep(2)
                except Exception as e:
                    logger.error(f"❌ Error procesando producto {i}: {e}")
                    continue
            
            # Paso 4: Guardar en CSV
            if self.productos:
                self.guardar_csv()
                logger.info("=" * 60)
                logger.info(f"✅ SCRAPING COMPLETADO")
                logger.info(f"📊 Total de productos extraídos: {len(self.productos)}")
                logger.info(f"💾 Archivo: productos.csv")
                logger.info("=" * 60)
                return True
            else:
                logger.error("❌ No se extrajeron productos")
                return False
            
        except Exception as e:
            logger.error(f"❌ Error en la ejecución: {e}")
            return False
        finally:
            try:
                self.driver.quit()
                logger.info("🔌 Navegador cerrado")
            except:
                pass

    def guardar_csv(self):
        """Guarda los datos en un archivo CSV"""
        try:
            df = pd.DataFrame(self.productos)
            
            # Reordenar columnas
            columnas = ['nombre', 'codigo', 'descripcion', 'url']
            df = df[[col for col in columnas if col in df.columns]]
            
            # Guardar
            df.to_csv('productos.csv', index=False, encoding='utf-8')
            logger.info(f"💾 CSV guardado: productos.csv")
            logger.info(f"📈 Filas: {len(df)}, Columnas: {len(df.columns)}")
        except Exception as e:
            logger.error(f"❌ Error guardando CSV: {e}")

if __name__ == "__main__":
    scraper = NaturaScraper()
    exito = scraper.ejecutar()
    exit(0 if exito else 1)
