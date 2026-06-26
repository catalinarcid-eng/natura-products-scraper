from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time

# El producto [3] que falló: desodorante erva doce
URL_PRUEBA = "https://www.natura.cl/p/desodorante-antitranspirante-roll-on-erva-doce-70-ml/NATCHL-189412"

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

try:
    print("=" * 70)
    print("DIAGNÓSTICO 4 - Producto que FALLÓ (desodorante erva doce)")
    print("=" * 70)
    print(f"URL: {URL_PRUEBA}\n")

    driver.get(URL_PRUEBA)
    try:
        WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.TAG_NAME, "h1")))
        print("✅ h1 cargó\n")
    except:
        print("⚠️ h1 NO cargó en 10s\n")

    aceptar_cookies(driver)
    time.sleep(2)

    # 1) Confirmar nombre
    nombre = driver.execute_script("let h=document.querySelector('h1'); return h?h.textContent.trim():'NO HAY';")
    print(f"1) NOMBRE (h1): {nombre}\n")

    # 2) ANTES del click: ¿hay botón descripción? ¿hay span.text-sm?
    print("2) ESTADO INICIAL (antes de click):")
    estado = driver.execute_script("""
        let botones = [];
        document.querySelectorAll('button').forEach(b => {
            if (b.textContent.toLowerCase().includes('descripción')) {
                botones.push('aria-expanded=' + b.getAttribute('aria-expanded') + ' texto=' + b.textContent.trim().substring(0,40));
            }
        });
        let spans = document.querySelectorAll('span.text-sm');
        let spanInfo = [];
        spans.forEach((s,i) => spanInfo.push('span#'+i+': '+s.querySelectorAll('li').length+' <li>'));
        return {botones: botones, numSpans: spans.length, spanInfo: spanInfo};
    """)
    print(f"   Botones 'descripción': {estado['botones']}")
    print(f"   span.text-sm: {estado['numSpans']}")
    for s in estado['spanInfo']:
        print(f"      {s}")
    print()

    # 3) Hacer click
    print("3) HACIENDO CLICK EN DESCRIPCIÓN:")
    click = driver.execute_script("""
        let botones = document.querySelectorAll('button');
        for (let b of botones) {
            if (b.textContent.toLowerCase().includes('descripción')) {
                b.click();
                return 'Click OK, aria-expanded ahora = ' + b.getAttribute('aria-expanded');
            }
        }
        return 'NO se encontró botón descripción';
    """)
    print(f"   {click}\n")

    # 4) Esperar progresivamente y ver cuándo aparece el contenido
    print("4) ESPERANDO CONTENIDO (revisando cada segundo):")
    for seg in range(1, 8):
        time.sleep(1)
        cont = driver.execute_script("""
            let spans = document.querySelectorAll('span.text-sm');
            for (let s of spans) {
                let lis = s.querySelectorAll('li');
                if (lis.length > 0) {
                    return lis.length + ' <li> | primer item: ' + lis[0].textContent.trim().substring(0,50);
                }
            }
            return 'aún vacío';
        """)
        print(f"   {seg}s: {cont}")
    print()

    # 5) Buscar la descripción en CUALQUIER parte (no solo span.text-sm)
    print("5) BÚSQUEDA AMPLIA DE LA DESCRIPCIÓN:")
    amplio = driver.execute_script("""
        // Buscar cualquier ul con varios li que parezcan características
        let uls = document.querySelectorAll('ul');
        let resultado = [];
        uls.forEach((ul, i) => {
            let lis = ul.querySelectorAll('li');
            if (lis.length >= 2) {
                let textos = Array.from(lis).map(li => li.textContent.trim()).filter(t => t.length > 3);
                // Filtrar las de cookies
                let esCookie = textos.some(t => t.toLowerCase().includes('cookie') || t.toLowerCase().includes('privacidad'));
                if (!esCookie && textos.length >= 2) {
                    resultado.push('ul#' + i + ' (' + textos.length + ' items): ' + textos.slice(0,3).join(' / '));
                }
            }
        });
        return resultado;
    """)
    print(f"   Listas <ul> con características (sin cookies): {len(amplio)}")
    for a in amplio:
        print(f"      {a}")

finally:
    driver.quit()
    print("\n" + "=" * 70)
    print("FIN")
    print("=" * 70)
