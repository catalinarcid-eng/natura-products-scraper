from selenium import webdriver
from selenium.webdriver.chrome.options import Options
import time

URL_LISTADO = "https://www.natura.cl/c/nuestros-productos"

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

driver = crear_driver()

def aceptar_cookies(driver):
    try:
        r = driver.execute_script("""
            let btn = document.querySelector('#onetrust-accept-btn-handler');
            if (btn) { btn.click(); return 'Cookies aceptadas'; }
            return 'No habia banner';
        """)
        print(f"   {r}")
        time.sleep(2)
    except Exception as e:
        print(f"   Error: {e}")

try:
    print("=" * 70)
    print("DIAGNÓSTICO 3 - URLs REALES DE PRODUCTOS")
    print("=" * 70)

    driver.get(URL_LISTADO)
    print("Cargando listado, esperando 8s...")
    time.sleep(8)

    print("\nAceptando cookies:")
    aceptar_cookies(driver)
    time.sleep(3)

    # Extraer TODOS los href que contengan /p/ tal como vienen
    print("\n" + "─" * 70)
    print("HREF EXACTOS DE PRODUCTOS (tal como vienen en el HTML):")
    print("─" * 70)
    hrefs = driver.execute_script("""
        let links = document.querySelectorAll('a[href*="/p/"]');
        let resultado = [];
        links.forEach(a => {
            resultado.push(a.getAttribute('href'));
        });
        return resultado;
    """)
    print(f"Total enlaces con /p/: {len(hrefs)}\n")
    # Mostrar únicos
    unicos = list(dict.fromkeys(hrefs))
    print(f"Enlaces únicos: {len(unicos)}\n")
    for i, h in enumerate(unicos[:15]):
        print(f"   {i+1}. {h}")

    # También probar con el href completo (.href en vez de getAttribute)
    print("\n" + "─" * 70)
    print("MISMOS ENLACES PERO CON .href COMPLETO:")
    print("─" * 70)
    hrefs_full = driver.execute_script("""
        let links = document.querySelectorAll('a[href*="/p/"]');
        let resultado = [];
        links.forEach(a => {
            resultado.push(a.href);
        });
        return [...new Set(resultado)];
    """)
    for i, h in enumerate(hrefs_full[:15]):
        print(f"   {i+1}. {h}")

    # Tomar la primera URL y PROBARLA
    if hrefs_full:
        print("\n" + "─" * 70)
        print("PROBANDO LA PRIMERA URL REAL:")
        print("─" * 70)
        primera = hrefs_full[0]
        print(f"   Navegando a: {primera}")
        driver.get(primera)
        time.sleep(6)
        aceptar_cookies(driver)
        time.sleep(4)

        info = driver.execute_script("""
            let h1 = document.querySelector('h1');
            let body = document.body.innerText.substring(0, 200);
            return {
                h1: h1 ? h1.textContent.trim() : 'NO HAY H1',
                body: body
            };
        """)
        print(f"\n   h1: {info['h1']}")
        print(f"   body: {info['body']}")

finally:
    driver.quit()
    print("\n" + "=" * 70)
    print("FIN")
    print("=" * 70)
