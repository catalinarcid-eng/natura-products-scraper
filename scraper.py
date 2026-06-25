from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time

# Un producto de prueba (el del shampoo Lumina que vimos en las capturas)
URL_PRUEBA = "https://www.natura.cl/p/repuesto-shampoo-matizacion-y-restauracion-lumina-300ml"

def crear_driver():
    opts = Options()
    opts.add_argument("--headless")
    opts.add_argument("--no-sandbox")
    opts.add_argument("--disable-dev-shm-usage")
    opts.add_argument("--window-size=1920,1080")
    opts.add_argument("--disable-blink-features=AutomationControlled")
    opts.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36")
    return webdriver.Chrome(options=opts)

driver = crear_driver()

try:
    print("=" * 70)
    print("DIAGNÓSTICO DE DESCRIPCIÓN")
    print("=" * 70)
    print(f"URL: {URL_PRUEBA}\n")

    driver.get(URL_PRUEBA)

    # Esperar a que cargue el h1
    try:
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.TAG_NAME, "h1"))
        )
    except:
        print("⚠️  No cargó el h1 en 10 segundos")

    time.sleep(3)

    # ── DIAGNÓSTICO 1: ¿Cuántos span.text-sm hay ANTES de hacer click? ──
    print("─" * 70)
    print("1) ANTES DE HACER CLICK:")
    print("─" * 70)
    spans_antes = driver.execute_script("""
        let spans = document.querySelectorAll('span.text-sm');
        let resultado = [];
        spans.forEach((s, i) => {
            let lis = s.querySelectorAll('li');
            resultado.push('span #' + i + ': ' + lis.length + ' <li> | texto: ' + s.textContent.trim().substring(0,80));
        });
        return resultado;
    """)
    print(f"   Total span.text-sm encontrados: {len(spans_antes)}")
    for linea in spans_antes:
        print(f"   {linea}")

    # ── DIAGNÓSTICO 2: ¿Qué elementos dicen "descripción"? ──
    print("\n" + "─" * 70)
    print("2) ELEMENTOS QUE CONTIENEN 'descripción':")
    print("─" * 70)
    elementos_desc = driver.execute_script("""
        let resultado = [];
        let elementos = document.querySelectorAll('button, h2, h3, div, span, p');
        elementos.forEach(elem => {
            let texto = elem.textContent.trim().toLowerCase();
            if (texto === 'descripción' || texto === 'descripcion') {
                resultado.push(elem.tagName + ' | clases: ' + elem.className.substring(0,60));
            }
        });
        return resultado;
    """)
    print(f"   Elementos con texto exacto 'descripción': {len(elementos_desc)}")
    for e in elementos_desc:
        print(f"   {e}")

    # ── DIAGNÓSTICO 3: Buscar botones que CONTENGAN descripción ──
    print("\n" + "─" * 70)
    print("3) BOTONES QUE CONTIENEN 'descripción' (parcial):")
    print("─" * 70)
    botones_desc = driver.execute_script("""
        let resultado = [];
        let botones = document.querySelectorAll('button');
        botones.forEach(btn => {
            if (btn.textContent.toLowerCase().includes('descripción')) {
                resultado.push('BUTTON | aria-expanded=' + btn.getAttribute('aria-expanded') + ' | texto: ' + btn.textContent.trim().substring(0,50));
            }
        });
        return resultado;
    """)
    print(f"   Botones encontrados: {len(botones_desc)}")
    for b in botones_desc:
        print(f"   {b}")

    # ── DIAGNÓSTICO 4: Hacer click en el botón de descripción ──
    print("\n" + "─" * 70)
    print("4) HACIENDO CLICK EN EL BOTÓN DESCRIPCIÓN:")
    print("─" * 70)
    click_result = driver.execute_script("""
        let botones = document.querySelectorAll('button');
        for (let btn of botones) {
            if (btn.textContent.toLowerCase().includes('descripción')) {
                btn.click();
                return 'Click hecho en boton con aria-expanded=' + btn.getAttribute('aria-expanded');
            }
        }
        return 'NO se encontró botón con descripción';
    """)
    print(f"   {click_result}")

    time.sleep(3)

    # ── DIAGNÓSTICO 5: ¿Cuántos span.text-sm hay DESPUÉS del click? ──
    print("\n" + "─" * 70)
    print("5) DESPUÉS DE HACER CLICK:")
    print("─" * 70)
    spans_despues = driver.execute_script("""
        let spans = document.querySelectorAll('span.text-sm');
        let resultado = [];
        spans.forEach((s, i) => {
            let lis = s.querySelectorAll('li');
            resultado.push('span #' + i + ': ' + lis.length + ' <li> | texto: ' + s.textContent.trim().substring(0,80));
        });
        return resultado;
    """)
    print(f"   Total span.text-sm encontrados: {len(spans_despues)}")
    for linea in spans_despues:
        print(f"   {linea}")

    # ── DIAGNÓSTICO 6: Extraer TODOS los <li> de la página ──
    print("\n" + "─" * 70)
    print("6) TODOS LOS <li> DE LA PÁGINA (primeros 30):")
    print("─" * 70)
    todos_li = driver.execute_script("""
        let lis = document.querySelectorAll('li');
        let resultado = [];
        lis.forEach(li => {
            let t = li.textContent.trim();
            if (t.length > 3 && t.length < 100) {
                resultado.push(t);
            }
        });
        return resultado.slice(0, 30);
    """)
    print(f"   Total <li> con texto útil: {len(todos_li)}")
    for li in todos_li:
        print(f"   • {li}")

finally:
    driver.quit()
    print("\n" + "=" * 70)
    print("FIN DEL DIAGNÓSTICO")
    print("=" * 70)
