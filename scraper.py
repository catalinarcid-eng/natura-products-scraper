from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
import pandas as pd
import time
import logging
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
        logger.info("🔧 Configurando Chrome...")
        
        # OPCIONES CRÍTICAS PARA HEADLESS
        options = Options()
        
        # Modo headless (sin interfaz visual)
        options.add_argument('--headless=new')
        options.add_argument('--no-sandbox')
        options.add_argument('--disable-dev-shm-usage')
        options.add_argument('--disable-gpu')
        options.add_argument('--disable-blink-features=AutomationControlled')
        options.add_argument('--disable-extensions')
        options.add_argument('--disable-plugins')
        options.add_argument('--disable-images')
        options.add_argument('--disable-popup-blocking')
        options.add_argument('--start-maximized')
        options.add_argument('--window-size=1920,1080')
        options.add_argument('user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36')
        options.add_argument('--disable-web-resources')
        options.add_argument('--remote-debugging-port=9222')
        
        # IMPORTANTE: Sin estas opciones, Chrome se cierra inmediatamente en headless
        options.add_argument('--single-process')
        options.add_argument('--disable-background-networking')
        options.add_argument('--disable-default-apps')
        options.add_argument('--disable-hang-monitor')
        options.add_argument('--disable-popup-blocking')
        options.add_argument('--disable-prompt-on-repost')
        options.add_argument('--disable-sync')
        
        logger.info("🔧 Iniciando Chrome...")
        
        try:
            # Intentar con ChromeDriver descargado
            logger.info("Intentando usar ChromeDriver descargado...")
            self.driver = webdriver.Chrome(
                service=Service(ChromeDriverManager().install()),
                options=options
            )
            logger.info("✅ Chrome iniciado (descargado)")
        except Exception as e1:
            logger.warning(f"⚠️ ChromeDriver descargado falló: {e1}")
            logger.info("🔄 Intentando usar Chrome del sistema...")
            
            try:
                # Intentar con Chrome del sistema
                self.driver = webdriver.Chrome(options=options)
                logger.info("✅ Chrome iniciado (sistema)")
            except Exception as e2:
                logger.error(f"❌ Error crítico: {e2}")
                raise RuntimeError(f"No se pudo iniciar Chrome: {e2}")
        
        self.productos = []
        self.wait = WebDriverWait(self.driver, 15)
        logger.info("✅ ChromeDriver listo")

    def cargar_todos_productos(self):
        """Carga todos los productos"""
        url = "https://www.natura.cl/c/nuestros-productos"
        logger.info(f"🌐 Accediendo a {url}")
        
        try:
            self.driver.get(url)
            time.sleep(6)
        except Exception as e:
            logger.error(f"❌ Error accediendo: {e}")
            raise
        
        logger.info("⏳ Cargando productos...")
        contador_clicks = 0
        max_clicks = 50
        
        while contador_clicks < max_clicks:
            try:
                # Buscar botón "explorar más resultados"
                botones = self.driver.find_elements(
                    By.XPATH, 
                    "//button[contains(translate(text(), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'explorar')]"
                )
                
                if not botones:
                    logger.info(f"✅ Productos cargados después de {contador_clicks} clicks")
                    break
                
                boton = botones[0]
                
                # Scroll al botón
                self.driver.execute_script("arguments[0].scrollIntoView(true);", boton)
                time.sleep(1)
                
                # Click
                try:
                    self.driver.execute_script("arguments[0].click();", boton)
                except:
                    boton.click()
                
                contador_clicks += 1
                logger.info(f"✅ Click {contador_clicks}")
                time.sleep(3)
                
            except Exception as e:
                logger.info(f"ℹ️ Carga completada")
                break
        
        logger.info(f"📦 Total clicks: {contador_clicks}")

    def obtener_enlaces_productos(self):
        """Obtiene enlaces de productos"""
        try:
            logger.info("🔍 Buscando productos...")
            time.sleep(2)
            
            # Obtener todos los enlaces
            elementos = self.driver.find_elements(
                By.XPATH, 
                "//a[contains(@href, '/p/')]"
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
                    pass
            
            # Eliminar duplicados
            enlaces = list(dict.fromkeys(enlaces))
            logger.info(f"📦 {len(enlaces)} productos encontrados")
            return enlaces
            
        except Exception as e:
            logger.error(f"❌ Error obteniendo enlaces: {e}")
            return []

    def extraer_datos_producto(self, url_producto, numero):
        """Extrae datos de un producto"""
        try:
            logger.info(f"[{numero}] Cargando producto...")
            self.driver.get(url_producto)
            time.sleep(3)
            
            datos = {'url': url_producto}
            
            # NOMBRE
            try:
                nombre = self.driver.find_element(By.XPATH, "//h1 | //h2")
                datos['nombre'] = nombre.text.strip()
                logger.info(f"✅ {datos['nombre'][:40]}")
            except:
                datos['nombre'] = "N/A"
            
            # CÓDIGO
            try:
                codigos = self.driver.find_elements(
                    By.XPATH, 
                    "//*[contains(text(), 'NATCHL-')]"
                )
                
                if codigos:
                    texto = codigos[0].text.strip()
                    datos['codigo'] = texto.split()[0]
                    logger.info(f"Código: {datos['codigo']}")
                else:
                    datos['codigo'] = "N/A"
            except:
                datos['codigo'] = "N/A"
            
            # DESCRIPCIÓN
            datos['descripcion'] = self.extraer_descripcion()
            
            return datos
            
        except Exception as e:
            logger.error(f"❌ Producto {numero}: {e}")
            return None

    def extraer_descripcion(self):
        """Extrae descripción"""
        try:
            # Intentar expandir descripción
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
            
            # Extraer texto
            try:
                descripciones = self.driver.find_elements(
                    By.XPATH,
                    "//*[contains(@class, 'description')]//p | //div[contains(text(), 'aroma')] | //div[contains(text(), 'Descripción')]"
                )
                
                if descripciones:
                    texto = " ".join([d.text.strip() for d in descripciones if d.text.strip()])
                    if texto:
                        return texto[:500]  # Limitar a 500 caracteres
                
                return "No disponible"
            except:
                return "No disponible"
                
        except Exception as e:
            logger.warning(f"⚠️ Descripción: {e}")
            return "No disponible"

    def ejecutar(self):
        """Ejecuta el scraper"""
        try:
            logger.info("=" * 60)
            logger.info("🚀 SCRAPER DE NATURA CHILE")
            logger.info(f"⏰ {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
            logger.info("=" * 60)
            
            # Cargar productos
            self.cargar_todos_productos()
            
            # Obtener enlaces
            enlaces = self.obtener_enlaces_productos()
            
            if not enlaces:
                logger.error("❌ Sin productos")
                return False
            
            # Procesar cada producto
            for i, enlace in enumerate(enlaces, 1):
                try:
                    datos = self.extraer_datos_producto(enlace, i)
                    if datos:
                        self.productos.append(datos)
                    time.sleep(1)
                except Exception as e:
                    logger.error(f"Error producto {i}: {e}")
                    continue
            
            # Guardar
            if self.productos:
                self.guardar_csv()
                logger.info("=" * 60)
                logger.info(f"✅ {len(self.productos)} PRODUCTOS EXTRAÍDOS")
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
        """Guarda en CSV"""
        try:
            df = pd.DataFrame(self.productos)
            columnas = ['nombre', 'codigo', 'descripcion', 'url']
            df = df[[col for col in columnas if col in df.columns]]
            df.to_csv('productos.csv', index=False, encoding='utf-8')
            logger.info(f"💾 {len(df)} filas guardadas")
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
