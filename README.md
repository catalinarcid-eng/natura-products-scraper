# 🌿 Natura Products Scraper

Bot automatizado para extraer productos, códigos y descripciones de [Natura Chile](https://www.natura.cl/c/nuestros-productos) ejecutándose en **GitHub Actions** ☁️

## ✨ Funcionalidades

✅ Carga automáticamente **todos los productos** (presionando "explorar más resultados")  
✅ Extrae **nombre del producto**  
✅ Extrae **código NATCHL-xxx**  
✅ Extrae **descripción completa** (expandiendo acordeones automáticamente)  
✅ Guarda datos en **CSV**  
✅ Ejecuta **diariamente en la nube** sin necesidad de tu PC  
✅ **Historial de ejecuciones** en GitHub Actions  

## 🚀 Cómo Usar

### 1️⃣ En GitHub (Crear Repositorio)

1. Ve a [github.com](https://github.com)
2. Click en **"New"** → Crea un repositorio llamado `natura-products-scraper`
3. Clona el repositorio localmente:
```bash
git clone https://github.com/TU_USUARIO/natura-products-scraper.git
cd natura-products-scraper
```

### 2️⃣ Copiar Archivos

Copia estos archivos al repositorio:
- `scraper.py` (en raíz)
- `requirements.txt` (en raíz)
- `.gitignore` (en raíz)
- `.github/workflows/scraper.yml` (crea la carpeta `.github/workflows/`)

### 3️⃣ Subir a GitHub

```bash
git add .
git commit -m "Initial commit: Natura scraper setup"
git push origin main
```

### 4️⃣ Ejecutar el Bot

**Opción A - Automático (diariamente a las 2 AM UTC):**
- No hagas nada, se ejecuta automáticamente cada día

**Opción B - Manual (ahora mismo):**
1. Ve a tu repo → **Actions**
2. Selecciona **"Natura Scraper"**
3. Click en **"Run workflow"**

### 5️⃣ Ver Resultados

1. Espera a que termine la ejecución (2-10 minutos)
2. Abre el archivo `productos.csv` en tu repositorio
3. O descárgalo:
```bash
git pull origin main
```

## 📊 Estructura del CSV

| nombre | codigo | descripcion | url |
|--------|--------|-------------|-----|
| Eau de Toilette Masculino Kaiak Aero 100 ml | NATCHL-111174 | Descripción del producto... | https://www.natura.cl/p/... |

## 🔧 Personalización

### Cambiar horario de ejecución

Edita `.github/workflows/scraper.yml` y cambia esta línea:
```yaml
- cron: '0 2 * * *'  # Formato: minuto hora día mes día_semana
```

Ejemplos:
- `'0 0 * * *'` → Medianoche UTC
- `'0 12 * * *'` → Mediodía UTC  
- `'0 18 * * MON'` → Lunes a las 6 PM UTC

### Ejecutar cada hora
```yaml
- cron: '0 * * * *'  # Cada hora
```

### Ejecutar cada 30 minutos
```yaml
- cron: '*/30 * * * *'  # Cada 30 minutos
```

## 📝 Monitorear Ejecuciones

1. Ve a tu repositorio → **Actions**
2. Verás un historial de todas las ejecuciones
3. Click en una ejecución para ver logs detallados:
   - ✅ Verde = Éxito
   - ❌ Rojo = Error
   - ⏳ Amarillo = En progreso

## 🐛 Troubleshooting

### "No se encuentra el elemento"
La estructura HTML de Natura puede cambiar. Abre un Issue con los detalles.

### "Timeout"
El servidor está lento. Aumenta los tiempos de espera en `scraper.py` (líneas con `time.sleep()`)

### "0 productos extraídos"
Verifica en GitHub Actions el log completo para ver dónde falla.

Pide ayuda si quieres configurar esto.

⭐ Si te sirve, dale una estrella en GitHub
