from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time

# Dos formatos distintos
URLS = [
    ("DESODORANTE (formato A)", "https://www.natura.cl/p/desodorante-antitranspirante-roll-on-erva-doce-70-ml/NATCHL-189412"),
    ("KAIAK PERFUME (formato ?)", "https://www.natura.cl/p/kaiak-aero-eau-de-toilette-masculino/NATCHL-111174"),
    ("CREMA EKOS (formato ?)", "https://www.natura.cl/p/crema-hidratante-para-manos-ekos-castana-75-g/NATCHL-70983"),
]

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
        time.sleep(1)
    except: pass

driver = crear_driver()

# Esta es la función candidata que quiero validar
SCRIPT_DESC = """
// La descripción está dentro de la región del acordeón "descripción" (role=region)
// Buscamos el contenedor que sigue al botón de descripción.
let resultado = {metodo: 'ninguno', texto: null};

// MÉTODO A: buscar span.text-sm con li (formato shampoo)
let spans = document.querySelectorAll('span.text-sm');
for (let s of spans) {
    let lis = s.querySelectorAll('li');
    if (lis.length > 0) {
        let items = Array.from(lis).map(li => li.textContent.trim()).filter(t => t.length > 2);
        if (items.length > 0) {
            resultado.metodo = 'A: span.text-sm con li';
            resultado.texto = items.join(' | ');
            return resultado;
        }
    }
}

// MÉTODO B: buscar la región del acordeón (role=region) que viene del botón descripción
let regiones = document.querySelectorAll('[role="region"]');
for (let r of regiones) {
    let texto = r.textContent.trim();
    // Que tenga contenido sustancial y no sea navegación
    if (texto.length > 30 && !texto.toLowerCase().includes('cookie')) {
        let lis = r.querySelectorAll('li');
        if (lis.length > 0) {
            let items = Array.from(lis).map(li => li.textContent.trim()).filter(t => t.length > 2);
            if (items.length > 0) {
                resultado.metodo = 'B: region con li';
                resultado.texto = items.join(' | ');
                return resultado;
            }
        }
        // Si no hay li pero hay texto
        resultado.metodo = 'B: region texto plano';
        resultado.texto = texto;
        return resultado;
    }
}

return resultado;
"""

try:
    for titulo, url in URLS:
        print("=" * 70)
        print(titulo)
        print(url)
        print("=" * 70)
        driver.get(url)
        try:
            WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.TAG_NAME, "h1")))
        except: pass
        aceptar_cookies(driver)
        time.sleep(2)

        nombre = driver.execute_script("let h=document.querySelector('h1');return h?h.textContent.trim():'?';")
        print(f"Nombre: {nombre}")

        # SIN hacer click (el acordeón ya está abierto)
        res = driver.execute_script(SCRIPT_DESC)
        print(f"Método usado: {res['metodo']}")
        print(f"Descripción: {res['texto'][:300] if res['texto'] else 'NADA'}")
        print()

finally:
    driver.quit()
    print("=" * 70)
    print("FIN")
    print("=" * 70)
