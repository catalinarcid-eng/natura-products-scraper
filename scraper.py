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
        options.add_argument('--headless')
        options.add_argument('--no-sandbox')
        options.add_argument('--disable-dev-shm-usage')
        options.add_argument('--disable-gpu')
        options.add_argument('--disable-web-resources')
        options.add_argument('--single-process')
        options.add_argument('--disable-blink-features=AutomationControlled')
        options.add_argument('user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64)')
        
        logger.info("🔧 Inicializando ChromeDriver...")
        
        try:
            logger.info("Descargando ChromeDriver...")
            self.driver = webdriver.Chrome(
                service=Service(ChromeDriverManager().install()),
                options=options
            )
            logger.info("✅ ChromeDriver instalado")
        except Exception as e:
            logger.warning(f"⚠️ ChromeDriver falló: {e}")
            logger.info("🔄 Usando Chrome del sistema...")
            try:
                self.driver = webdriver.Chrome(options=options)
                logger.info("✅ Chrome encontrado")
            except Exception as e2:
                logger.error(f"❌ FATAL: {e2}")
                raise RuntimeError("Chrome no disponible")
        
        self.productos = []
        self.wait = WebDriverWait(self.driver, 15)

    def cargar_todos_productos(self):
        url = "https://www.natura.cl/c/nuestros-productos"
        logger.info(f"🌐 Accediendo a {url}")
        
        try:
            self.driver.get(url)
            time.sleep(5)
        except Exception as e:
            logger.error(f"❌ Error accediendo: {e}")
            raise
        
        logger.info("⏳ Cargando productos...")
        contador_clicks = 0
        
        while contador_clicks < 50:
            try:
                botones = self.driver.find_elements(
                    By.XPATH, 
                    "//button[contains(translate(text(), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'explorar')]"
                )
                
                if not botones:
                    logger.info("✅ Todos los productos cargados")
                    break
                
                boton = botones[0]
                self.driver.execute_script("arguments[0].scrollIntoView(true);", boton)
                time.sleep(1)
                
                try:
                    self.driver.execute_script("arguments[0].click();", boton)
                except:
                    boton.click()
                
                contador_clicks += 1
                logger.info(f"✅ Click {contador_clicks}")
                time.sleep(3)
                
            except Exception as e:
                logger.info(f"✅ Completado: {contador_clicks} clicks")
                break

    def obtener_enlaces_productos(self):
        try:
            logger.info("🔍 Extrayendo enlaces...")
            time.sleep(2)
            
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
            
            enlaces = list(dict.fromkeys(enlaces))
            logger.info(f"📦 Encontrados: {len(enlaces)} productos")
            return enlaces
            
        except Exception as e:
            logger.error(f"❌ Error: {e}")
            return []

    def extraer_datos_producto(self, url_producto, numero):
        try:
            logger.info(f"[{numero}] Producto...")
            self.driver.get(url_producto)
            time.sleep(3)
            
            datos = {'url': url_producto}
            
            try:
                nombre_elem = self.driver.find_element(
                    By.XPATH, 
                    "//h1 | //h2[@role='heading']"
                )
                datos['nombre'] = nombre_elem.text.strip()
                logger.info(f"✅ Nombre: {datos['nombre'][:40]}")
            except:
                datos['nombre'] = "N/A"
            
            try:
                codigo_elementos = self.driver.find_elements(
                    By.XPATH, 
                    "//*[contains(text(), 'NATCHL-')]"
                )
                
                if codigo_elementos:
                    for elem in codigo_elementos:
                        texto = elem.text.strip()
                        if 'NATCHL-' in texto:
                            datos['codigo'] = texto.split()[0]
                            logger.info(f"✅ Código: {datos['codigo']}")
                            break
                else:
                    datos['codigo'] = "N/A"
            except:
                datos['codigo'] = "N/A"
            
            datos['descripcion'] = self.extraer_descripcion()
            return datos
            
        except Exception as e:
            logger.error(f"❌ Producto {numero}: {e}")
            return None

    def extraer_descripcion(self):
        try:
            try:
                botones = self.driver.find_elements(
                    By.XPATH,
                    "//button[contains(translate(text(), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'descripción')]"
                )
                
                if botones:
                    boton = botones[0]
                    if boton.get_attribute('aria-expanded') == 'false':
                        self.driver.execute_script("arguments[0].click();", boton)
                        time.sleep(2)
            except:
                pass
            
            try:
                descripciones = self.driver.find_elements(
                    By.XPATH,
                    "//*[contains(@class, 'description')]//p"
                )
                
                if descripciones:
                    texto = " ".join([d.text.strip() for d in descripciones if d.text.strip()])
                    if texto:
                        logger.info(f"✅ Descripción: {len(texto)} caracteres")
                        return texto
                
                return "No disponible"
                
            except:
                return "No disponible"
                
        except:
            return "No disponible"

    def ejecutar(self):
        try:
            logger.info("=" * 60)
            logger.info("🚀 INICIANDO SCRAPER")
            logger.info(f"⏰ {datetime.now()}")
            logger.info("=" * 60)
            
            self.cargar_todos_productos()
            enlaces = self.obtener_enlaces_productos()
            
            if not enlaces:
                logger.error("❌ Sin productos")
                return False
            
            for i, enlace in enumerate(enlaces, 1):
                try:
                    datos = self.extraer_datos_producto(enlace, i)
                    if datos:
                        self.productos.append(datos)
                    time.sleep(1)
                except Exception as e:
                    logger.error(f"❌ Producto {i}: {e}")
                    continue
            
            if self.productos:
                self.guardar_csv()
                logger.info("=" * 60)
                logger.info(f"✅ COMPLETADO: {len(self.productos)} productos")
                logger.info("=" * 60)
                return True
            else:
                logger.error("❌ Sin datos")
                return False
            
        except Exception as e:
            logger.error(f"❌ FATAL: {e}")
            return False
        finally:
            try:
                self.driver.quit()
                logger.info("🔌 Chrome cerrado")
            except:
                pass

    def guardar_csv(self):
        try:
            df = pd.DataFrame(self.productos)
            columnas = ['nombre', 'codigo', 'descripcion', 'url']
            df = df[[col for col in columnas if col in df.columns]]
            df.to_csv('productos.csv', index=False, encoding='utf-8')
            logger.info(f"💾 {len(df)} filas en CSV")
        except Exception as e:
            logger.error(f"❌ Error CSV: {e}")

if __name__ == "__main__":
    try:
        scraper = NaturaScraper()
        exito = scraper.ejecutar()
        exit(0 if exito else 1)
    except Exception as e:
        logger.error(f"❌ FATAL: {e}")
        exit(1)
