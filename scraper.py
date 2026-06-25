from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
import time

URL_PRUEBA = "https://www.natura.cl/p/repuesto-shampoo-matizacion-y-restauracion-lumina-300ml"

def crear_driver():
    opts = Options()
    opts.add_argument("--headless=new")  # Probar headless nuevo
    opts.add_argument("--no-sandbox")
    opts.add_argument("--disable-dev-shm-usage")
    opts.add_argument("--window-size=1920,1080")
    opts.add_argument("--disable-blink-features=AutomationControlled")
    opts.add_argument("--lang=es-CL")
    opts.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36")
    return webdriver.Chrome(options=opts)

driver = crear_driver()

try:
    print("=" * 70)
    print("DIAGNÓSTICO 2 - ¿Por qué no carga la página de producto?")
    print("=" * 70)

    driver.get(URL_PRUEBA)
    print("Esperando 15 segundos completos...\n")
    time.sleep(15)

    # 1) Título de la página
    print("1) TÍTULO DE LA PÁGINA:")
    print(f"   {driver.title}\n")

    # 2) URL actual (¿hubo redirección?)
    print("2) URL ACTUAL:")
    print(f"   {driver.current_url}\n")

    # 3) ¿Cuántos elementos en total hay?
    total = driver.execute_script("return document.querySelectorAll('*').length;")
    print(f"3) TOTAL DE ELEMENTOS EN EL DOM: {total}\n")

    # 4) ¿Hay banner de cookies? Buscar botones de aceptar
    print("4) BOTONES DE COOKIES / ACEPTAR:")
    botones = driver.execute_script("""
        let resultado = [];
        let btns = document.querySelectorAll('button, a');
        btns.forEach(b => {
            let t = b.textContent.trim().toLowerCase();
            if (t.includes('acept') || t.includes('cookie') || t.includes('continuar') || t.includes('permitir') || t.includes('entendido')) {
                resultado.push(b.tagName + ': "' + b.textContent.trim().substring(0,40) + '" id=' + b.id);
            }
        });
        return resultado;
    """)
    print(f"   Encontrados: {len(botones)}")
    for b in botones:
        print(f"   {b}")
    print()

    # 5) Intentar aceptar cookies
    print("5) INTENTANDO ACEPTAR COOKIES:")
    resultado = driver.execute_script("""
        let btns = document.querySelectorAll('button, a');
        for (let b of btns) {
            let t = b.textContent.trim().toLowerCase();
            if (t.includes('acept') || t.includes('permitir todas') || t.includes('entendido')) {
                b.click();
                return 'Click en: ' + b.textContent.trim().substring(0,40);
            }
        }
        return 'No se encontró botón de aceptar';
    """)
    print(f"   {resultado}\n")

    time.sleep(5)

    # 6) Después de aceptar cookies, ¿aparece el h1?
    print("6) DESPUÉS DE ACEPTAR COOKIES:")
    info = driver.execute_script("""
        let h1 = document.querySelector('h1');
        let spans = document.querySelectorAll('span.text-sm');
        let total = document.querySelectorAll('*').length;
        return {
            h1: h1 ? h1.textContent.trim().substring(0,60) : 'NO HAY H1',
            spans_text_sm: spans.length,
            total_elementos: total
        };
    """)
    print(f"   h1: {info['h1']}")
    print(f"   span.text-sm: {info['spans_text_sm']}")
    print(f"   total elementos: {info['total_elementos']}\n")

    # 7) Primeros 1000 caracteres del body visible
    print("7) TEXTO VISIBLE DEL BODY (primeros 600 chars):")
    texto = driver.execute_script("return document.body.innerText.substring(0, 600);")
    print(f"   {texto}\n")

finally:
    driver.quit()
    print("=" * 70)
    print("FIN")
    print("=" * 70)
