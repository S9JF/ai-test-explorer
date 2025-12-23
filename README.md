# 🤖 AI Test Explorer

> **Generación automática de tests de Playwright con exploración real de páginas usando Claude AI + MCP**

Sistema inteligente que explora páginas web automáticamente, extrae selectores reales, y genera tests de Playwright con auto-healing incorporado. Incluye exploración autenticada para páginas protegidas y modo interactivo conversacional.

[![Python](https://img.shields.io/badge/Python-3.13+-blue.svg)](https://www.python.org/)
[![Playwright](https://img.shields.io/badge/Playwright-1.49+-green.svg)](https://playwright.dev/)
[![Claude](https://img.shields.io/badge/Claude-Sonnet%204-purple.svg)](https://www.anthropic.com/)

---

## ✨ Características

### 🔍 **Exploración Real de Páginas**
- Navega páginas web con Playwright
- Extrae elementos interactivos (inputs, buttons, selects, links)
- Identifica IDs, nombres, tipos y atributos **reales**
- Sin adivinanzas - solo selectores verificados

### 🔐 **Exploración Autenticada**
- Explora páginas que requieren login
- Configuración de credenciales en `auth.yaml`
- Auto-detección de sitios
- Soporte para múltiples aplicaciones

### 🤖 **Generación Inteligente**
- Claude analiza la estructura de la página
- Genera tests con selectores **correctos desde el inicio**
- **Modo automático:** Suite completa de 2-5 tests
- **Modo interactivo:** Conversación con Claude sobre qué testear
- Código limpio con type hints y documentación

### 🔧 **Auto-Healing**
- Detecta cuando selectores cambian
- Re-explora la página automáticamente
- Actualiza tests con nuevos selectores
- Crea backups antes de modificar
- Preview de cambios con `--dry-run`

### 💻 **CLI Profesional**
- 8 comandos intuitivos
- Preview de cambios (--dry-run)
- Batch processing para múltiples URLs
- Manejo inteligente de archivos duplicados
- Validación de elementos interactivos

---

## 🚀 Instalación

### Requisitos
- Python 3.11+
- Cuenta de Anthropic (API Key)

### Setup
```bash
# Clonar repositorio
git clone https://github.com/TU_USUARIO/ai-test-explorer.git
cd ai-test-explorer

# Crear entorno virtual
python3 -m venv venv
source venv/bin/activate  # En Windows: venv\Scripts\activate

# Instalar dependencias
pip install -r requirements.txt

# Instalar navegadores de Playwright
python -m playwright install

# Configurar API Key
echo "ANTHROPIC_API_KEY=tu_api_key_aqui" > .env
```

---

## 📖 Uso

### 🎮 Comandos Disponibles
```bash
python cli.py --help

Commands:
  explore       🔍 Explora una página web
  explore-auth  🔐 Explora página con autenticación
  generate      🤖 Genera test básico
  generate-auth 🤖🔐 Genera test con autenticación
  batch         📦 Genera múltiples tests
  heal          🔧 Repara test roto (auto-healing)
  list          📋 Lista tests generados
  run           ▶️  Ejecuta tests
```

---

### 1️⃣ Explorar Páginas

#### **Exploración Básica (páginas públicas)**
```bash
# Exploración simple
python cli.py explore https://www.saucedemo.com

# Con detalles de elementos
python cli.py explore https://www.saucedemo.com --show-details
```

**Salida:**
```
📦 Elementos encontrados:
   • 2 inputs
   • 1 botones
   • 5 links

🔹 INPUTS:
   1. type=text, id=user-name, name=user-name
   2. type=password, id=password, name=password
```

---

#### **Exploración con Autenticación (páginas protegidas)** 🔐

**Para páginas que requieren login:**

**Paso 1:** Configurar credenciales en `auth.yaml`
```yaml
mi-app:
  login_url: https://mi-app.com/login
  username: testuser
  password: testpass
  username_selector: "#email"
  password_selector: "#password"
  submit_selector: "button[type='submit']"
```

**Paso 2:** Explorar página autenticada
```bash
python cli.py explore-auth https://mi-app.com/dashboard -s mi-app
```

**Qué hace:**
```
1. ✅ Navega a login
2. ✅ Ingresa credenciales automáticamente
3. ✅ Hace login
4. ✅ Navega a la página objetivo
5. ✅ Explora elementos del dashboard (NO del login)
```

---

### 2️⃣ Generar Tests

#### **Tests Básicos**
```bash
# Suite completa (2-5 tests automáticos)
python cli.py generate https://www.saucedemo.com

# Test específico con descripción
python cli.py generate https://www.saucedemo.com \
    --description "login con credenciales válidas"

# Personalizar salida
python cli.py generate https://www.saucedemo.com \
    --output tests \
    --filename test_custom.py
```

**Resultado:**
```python
import pytest
from playwright.async_api import Page


@pytest.mark.asyncio
async def test_login(page: Page):
    '''Test de login con credenciales válidas'''
    
    await page.goto("https://www.saucedemo.com")
    
    # Selectores REALES extraídos de la página
    await page.fill("#user-name", "standard_user")
    await page.fill("#password", "secret_sauce")
    await page.click("#login-button")
    
    await page.wait_for_url("**/inventory.html")
    assert "inventory.html" in page.url
```

---

#### **Tests con Autenticación** 🔐

**Para páginas que requieren login (dashboard, perfil, etc):**

**Modo Automático:**
```bash
python cli.py generate-auth https://mi-app.com/dashboard -s mi-app
```

**Claude:**
- Hace login automáticamente
- Explora el dashboard
- Identifica acciones principales
- Genera 2-4 tests de flows comunes

---

**Modo Interactivo (conversación con Claude):**
```bash
python cli.py generate-auth https://mi-app.com/dashboard -s mi-app --interactive
```

**Conversación:**
```
💬 MODO INTERACTIVO

Elementos encontrados en la página:
  • 3 inputs
  • 5 botones

Botones principales:
  1. Exportar Reporte
  2. Crear Nuevo
  3. Filtrar Datos

💡 ¿Qué quieres testear? (describe en una frase)
Tú: exportar reporte con fechas personalizadas

🤖 Generando test específico...
✅ Test generado
```

**Test generado incluye:**
```python
@pytest.mark.asyncio
async def test_exportar_reporte_fechas_personalizadas(page: Page):
    # PASO 1: Login
    await page.goto("https://mi-app.com/login")
    await page.fill("#email", "testuser")
    await page.fill("#password", "testpass")
    await page.click("button[type='submit']")
    
    # PASO 2: Navegar a dashboard
    await page.goto("https://mi-app.com/dashboard")
    
    # PASO 3: Exportar reporte
    await page.fill("#fecha-inicio", "2024-01-01")
    await page.fill("#fecha-fin", "2024-12-31")
    await page.click("#exportar-btn")
    
    # PASO 4: Verificar descarga
    # ... verificaciones ...
```

---

**Manejo Inteligente de Archivos:**

Si el archivo ya existe, el sistema pregunta:
```
⚠️  El archivo test_dashboard_auth.py ya existe

¿Qué quieres hacer?
  1. Sobrescribir (se creará backup: test_dashboard_auth.py.backup)
  2. Crear nuevo (test_dashboard_auth_2.py)
  3. Cancelar

Opción [1/2/3]:
```

---

### 3️⃣ Batch Processing

**Generar tests para múltiples URLs:**
```bash
# Crear archivo de URLs
cat > urls.txt << EOF
https://www.saucedemo.com
https://example.com
https://mi-app.com/features
EOF

# Generar tests para todas
python cli.py batch urls.txt
```

**Salida:**
```
📋 Se encontraron 3 URLs

[1/3] Procesando: https://www.saucedemo.com
   ✅ Guardado en: tests/test_saucedemo_com_generated.py

[2/3] Procesando: https://example.com
   ⚠️  Advertencia: Test muy simple
   ✅ Guardado en: tests/test_example_com_generated.py

[3/3] Procesando: https://mi-app.com/features
   ✅ Guardado en: tests/test_mi_app_com_features_generated.py

✅ Exitosos: 3/3
```

---

### 4️⃣ Auto-Healing 🔧

**Cuando los selectores cambian (después de un deploy):**

**Preview de cambios (recomendado primero):**
```bash
python cli.py heal tests/test_login.py --dry-run
```

**Salida:**
```
============================================================
   📋 ANÁLISIS DE CAMBIOS
============================================================

⚠️  SE DETECTARON CAMBIOS EN SELECTORES:

🔴 REMOVIDOS:
   • #username-field
   • #pass
   • #submit-btn

🟢 AGREGADOS:
   • #user-name
   • #password
   • #login-button

🔍 DRY RUN - No se aplicaron cambios

💾 Para aplicar cambios, ejecuta:
   python cli.py heal tests/test_login.py
```

**Aplicar reparación:**
```bash
python cli.py heal tests/test_login.py
```

**Resultado:**
```
✅ CONFIRMADO: Test necesita reparación

💾 Backup creado: tests/test_login.py.backup
✅ Test reparado: tests/test_login.py

💡 Para ejecutar:
   python -m pytest tests/test_login.py -v
```

**Cuándo usar auto-healing:**
- ✅ Después de un deploy (selectores cambiaron)
- ✅ Tests fallando por timeout de selectores
- ✅ Refactoring de frontend
- ❌ NO para bugs reales de la aplicación

---

### 5️⃣ Listar y Ejecutar Tests

**Listar todos los tests generados:**
```bash
python cli.py list
```

**Salida:**
```
============================================================
   📋 TESTS GENERADOS
============================================================

✅ Se encontraron 5 tests:

 1. test_saucedemo_com_generated.py
    Tamaño: 1247 bytes
    Ruta: tests/test_saucedemo_com_generated.py

 2. test_dashboard_auth.py
    Tamaño: 2134 bytes
    Ruta: tests/test_dashboard_auth.py

...

💡 Para ejecutar todos:
   python -m pytest tests -v
```

---

**Ejecutar todos los tests:**
```bash
# Ejecución básica
python cli.py run

# Con verbose
python cli.py run --verbose
```

---

## 🎯 Casos de Uso Reales

### **Escenario 1: Nueva Feature**
```bash
# 1. Explora la nueva página
python cli.py explore https://tu-app.com/nueva-feature

# 2. Genera tests automáticamente
python cli.py generate https://tu-app.com/nueva-feature

# 3. Ejecuta
python -m pytest tests/test_nueva_feature.py -v
```

**Tiempo:** 5 minutos vs 30-45 minutos manual

---

### **Escenario 2: Testing Post-Login**
```bash
# 1. Configura credenciales (una sola vez)
cat >> auth.yaml << EOF
mi-app:
  login_url: https://mi-app.com/login
  username: testuser
  password: testpass
  username_selector: "#email"
  password_selector: "#password"
  submit_selector: "button[type='submit']"
EOF

# 2. Explora dashboard
python cli.py explore-auth https://mi-app.com/dashboard -s mi-app

# 3. Genera tests interactivamente
python cli.py generate-auth https://mi-app.com/dashboard -s mi-app --interactive
```

**Tiempo:** 5-10 minutos vs 45-60 minutos manual

---

### **Escenario 3: Después de Deploy**
```bash
# Frontend cambió selectores
# 10 tests fallando

# 1. Preview cambios
python cli.py heal tests/test_login.py --dry-run
python cli.py heal tests/test_checkout.py --dry-run

# 2. Aplicar reparaciones
python cli.py heal tests/test_login.py
python cli.py heal tests/test_checkout.py

# 3. Re-ejecutar
python cli.py run
```

**Tiempo:** 10 minutos vs 2-3 horas manual

---

### **Escenario 4: Suite Completa para Nueva App**
```bash
# 1. Generar test de login
python cli.py generate https://nueva-app.com/login \
    --description "login exitoso"

# 2. Agregar credenciales a auth.yaml

# 3. Generar tests para resto de la app
python cli.py generate-auth https://nueva-app.com/dashboard -s nueva-app
python cli.py generate-auth https://nueva-app.com/profile -s nueva-app
python cli.py generate-auth https://nueva-app.com/settings -s nueva-app

# 4. Ejecutar suite completa
python cli.py run --verbose
```

**Tiempo:** 20-30 minutos vs 4-6 horas manual

---

## 🏗️ Arquitectura
```
┌─────────────┐
│   Usuario   │
└──────┬──────┘
       │
       ▼
┌─────────────┐
│   CLI       │ ← 8 comandos
└──────┬──────┘
       │
       ├──────────────────┬─────────────────┬──────────────┐
       ▼                  ▼                 ▼              ▼
┌─────────────┐    ┌─────────────┐  ┌─────────────┐ ┌──────────┐
│  Explorer   │    │  Generator  │  │ Auto-Healer │ │ Auth     │
│             │    │             │  │             │ │ Config   │
└──────┬──────┘    └──────┬──────┘  └──────┬──────┘ └────┬─────┘
       │                  │                 │             │
       └──────────────────┴─────────────────┴─────────────┘
                          │
                          ▼
                   ┌─────────────┐
                   │  Playwright │ ← Navegador real
                   └──────┬──────┘
                          │
                          ▼
                   ┌─────────────┐
                   │   Claude    │ ← Análisis + Generación
                   └─────────────┘
```

---

## 📊 Comparación

### **Sin AI Test Explorer:**
```
1. Abrir DevTools
2. Inspeccionar elementos manualmente
3. Copiar selectores
4. Escribir código del test
5. Ejecutar y debuggear
6. Ajustar selectores que fallan
7. Repetir para cada test

Tiempo por test: 15-30 minutos
Tasa de error: ~20% (selectores incorrectos)
Páginas con login: Requiere setup manual complejo
```

### **Con AI Test Explorer:**
```
1. python cli.py generate-auth <url> -s <sitio> --interactive
2. Conversar con Claude sobre qué testear
3. Ejecutar

Tiempo por test: 2-5 minutos
Tasa de error: ~5% (selectores verificados)
Auto-healing: Sí
Páginas con login: Manejo automático
```

**Ahorro: 80-90% de tiempo**  
**Mejora en precisión: 75%**  
**Soporte para autenticación: ✅**

---

## 🛠️ Tecnologías

- **[Playwright](https://playwright.dev/)** - Automatización de navegador
- **[Claude Sonnet 4](https://www.anthropic.com/)** - Análisis y generación de código
- **[MCP](https://modelcontextprotocol.io/)** - Model Context Protocol
- **[Click](https://click.palletsprojects.com/)** - CLI framework
- **[Pytest](https://pytest.org/)** - Testing framework
- **[PyYAML](https://pyyaml.org/)** - Configuración de autenticación

---

## 📁 Estructura del Proyecto
```
ai-test-explorer/
├── cli.py                      # CLI principal (8 comandos)
├── src/
│   ├── ai_test_generator.py   # Generador de tests
│   ├── auto_healer.py          # Sistema de auto-reparación
│   ├── auth_config.py          # Manejo de autenticación
│   └── __init__.py
├── tests/
│   ├── conftest.py            # Fixtures compartidas
│   └── test_*.py              # Tests generados
├── auth.yaml                  # Credenciales (no subir a Git)
├── screenshots/               # Screenshots de tests
├── pytest.ini                 # Configuración de Pytest
├── requirements.txt
├── LICENSE
├── EXAMPLES.md               # Ejemplos detallados
└── README.md
```

---

## ⚙️ Configuración

### `auth.yaml`

Configuración de credenciales para exploración autenticada:
```yaml
saucedemo:
  login_url: https://www.saucedemo.com
  username: standard_user
  password: secret_sauce
  username_selector: "#user-name"
  password_selector: "#password"
  submit_selector: "#login-button"

mi-app:
  login_url: https://mi-app.com/login
  username: admin
  password: admin123
  username_selector: "#email"
  password_selector: "#pwd"
  submit_selector: "button[type='submit']"
```

**⚠️ Importante:** Agregar `auth.yaml` a `.gitignore` para no subir credenciales.

---

### `pytest.ini`
```ini
[pytest]
asyncio_mode = auto
pythonpath = .
testpaths = tests
```

---

### `conftest.py`

Fixtures globales de Playwright disponibles automáticamente en todos los tests.

---

## 📄 Licencia

MIT License - ve [LICENSE](LICENSE) para más detalles

---

## 👤 Autor

**Bryan Rodriguez**

- LinkedIn: [bryan-rodriguez-32a9a8211](www.linkedin.com/in/bryan-rodriguez-32a9a8211)
- GitHub: [bryan0422](https://github.com/bryan0422)

---

## ⭐ Star History

Si este proyecto te ayudó, considera darle una estrella ⭐

---

<p align="center">
  Hecho con ❤️ y ☕ por Bryan Rodriguez
</p>