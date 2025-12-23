"""
CLI para AI Test Explorer
Comandos para explorar páginas y generar tests automáticamente
"""

import click
import asyncio
import os
from pathlib import Path
from src.ai_test_generator import AITestGenerator


@click.group()
@click.version_option(version="1.0.0", prog_name="AI Test Explorer")
def cli():
    """
    🤖 AI Test Explorer - Generación automática de tests con Playwright + Claude
    
    Explora páginas web y genera tests con selectores verificados.
    """
    pass


@cli.command()
@click.argument('url')
@click.option('--show-details', '-d', is_flag=True, help='Mostrar detalles de elementos encontrados')
def explore(url, show_details):
    """
    🔍 Explora una página web y muestra elementos encontrados
    
    Ejemplos:
    
        python cli.py explore https://www.saucedemo.com
        
        python cli.py explore https://example.com --show-details
    """
    
    async def run_exploration():
        click.echo("=" * 60)
        click.echo("   🔍 EXPLORACIÓN DE PÁGINA")
        click.echo("=" * 60 + "\n")
        
        generator = AITestGenerator()
        
        try:
            await generator.start_browser()
            
            exploration_data = await generator.explore_page(url)
            
            # Resumen
            click.echo("\n" + "=" * 60)
            click.echo("   📊 RESUMEN")
            click.echo("=" * 60)
            click.echo(f"\n✅ URL: {exploration_data['url']}")
            click.echo(f"✅ Título: {exploration_data['title']}")
            click.echo(f"\n📦 Elementos encontrados:")
            click.echo(f"   • {len(exploration_data['elements']['inputs'])} inputs")
            click.echo(f"   • {len(exploration_data['elements']['buttons'])} botones")
            click.echo(f"   • {len(exploration_data['elements']['links'])} links")
            click.echo(f"   • {len(exploration_data['elements']['selects'])} selects")
            
            if show_details:
                click.echo("\n" + "=" * 60)
                click.echo("   📋 DETALLES")
                click.echo("=" * 60)
                
                # Mostrar inputs
                if exploration_data['elements']['inputs']:
                    click.echo("\n🔹 INPUTS:")
                    for i, inp in enumerate(exploration_data['elements']['inputs'][:5], 1):
                        click.echo(f"   {i}. type={inp['type']}, id={inp['id']}, name={inp['name']}")
                
                # Mostrar botones
                if exploration_data['elements']['buttons']:
                    click.echo("\n🔹 BUTTONS:")
                    for i, btn in enumerate(exploration_data['elements']['buttons'][:5], 1):
                        click.echo(f"   {i}. id={btn['id']}, text={btn['text'][:30]}")
            
            click.echo("\n" + "=" * 60 + "\n")
            
        finally:
            await generator.close_browser()
    
    asyncio.run(run_exploration())


@cli.command('explore-auth')
@click.argument('url')
@click.option('--site', '-s', help='Nombre del sitio en auth.yaml')
@click.option('--login-url', help='URL de login (si no usas --site)')
@click.option('--username', help='Usuario (si no usas --site)')
@click.option('--password', help='Contraseña (si no usas --site)')
@click.option('--show-details', '-d', is_flag=True, help='Mostrar detalles')
def explore_auth(url, site, login_url, username, password, show_details):
    """
    🔐 Explora una página DESPUÉS de hacer login
    
    Dos formas de uso:
    
    1. Con archivo auth.yaml (RECOMENDADO):
    
        python cli.py explore-auth https://www.saucedemo.com/inventory.html -s saucedemo
    
    2. Con credenciales manuales:
    
        python cli.py explore-auth https://www.saucedemo.com/inventory.html \\
            --login-url https://www.saucedemo.com \\
            --username standard_user \\
            --password secret_sauce
    """
    
    async def run_auth_exploration():
        from pathlib import Path
        import sys
        sys.path.insert(0, str(Path(__file__).parent / 'src'))
        from ai_test_generator import AITestGenerator
        from auth_config import AuthConfig, detect_site_from_url
        
        click.echo("=" * 60)
        click.echo("   🔐 EXPLORACIÓN CON AUTENTICACIÓN")
        click.echo("=" * 60 + "\n")
        
        # Cargar configuración
        auth_config = AuthConfig()
        
        # Determinar credenciales
        if site:
            # Usar configuración de auth.yaml
            site_config = auth_config.get_site_config(site)
            
            if not site_config:
                click.echo(f"❌ Sitio '{site}' no encontrado en auth.yaml\n")
                click.echo("Sitios disponibles:")
                for s in auth_config.list_sites():
                    click.echo(f"  • {s}")
                click.echo("\n💡 Agrega la configuración en auth.yaml")
                return
            
            login_url = site_config['login_url']
            username = site_config['username']
            password = site_config['password']
            username_selector = site_config.get('username_selector', '#username,#user-name,input[name="username"]')
            password_selector = site_config.get('password_selector', '#password,#pass,input[name="password"]')
            submit_selector = site_config.get('submit_selector', 'button[type="submit"],#login-button')
            
            click.echo(f"📋 Usando configuración de: {site}")
            
        elif login_url and username and password:
            # Usar credenciales manuales
            username_selector = '#username,#user-name,input[name="username"]'
            password_selector = '#password,#pass,input[name="password"]'
            submit_selector = 'button[type="submit"],#login-button'
            
            click.echo(f"📋 Usando credenciales manuales")
            
        else:
            # Intentar auto-detectar
            detected_site = detect_site_from_url(url, auth_config)
            
            if detected_site:
                click.echo(f"🔍 Auto-detectado sitio: {detected_site}")
                site_config = auth_config.get_site_config(detected_site)
                
                login_url = site_config['login_url']
                username = site_config['username']
                password = site_config['password']
                username_selector = site_config.get('username_selector', '#username')
                password_selector = site_config.get('password_selector', '#password')
                submit_selector = site_config.get('submit_selector', 'button[type="submit"]')
            else:
                click.echo("❌ Debes especificar --site o credenciales manualmente\n")
                click.echo("Opciones:")
                click.echo("  1. Usar --site: python cli.py explore-auth URL -s saucedemo")
                click.echo("  2. Usar credenciales: --login-url --username --password")
                click.echo("\n💡 Sitios configurados en auth.yaml:")
                for s in auth_config.list_sites():
                    click.echo(f"     • {s}")
                return
        
        click.echo(f"🔑 Login URL: {login_url}")
        click.echo(f"👤 Usuario: {username}")
        click.echo(f"🎯 Página objetivo: {url}\n")
        
        generator = AITestGenerator()
        
        try:
            await generator.start_browser()
            
            # Login
            click.echo(f"🔑 Haciendo login...")
            await generator.page.goto(login_url)
            await asyncio.sleep(1)
            
            # Llenar usuario
            for selector in username_selector.split(','):
                try:
                    await generator.page.fill(selector.strip(), username, timeout=2000)
                    click.echo(f"   ✅ Usuario ingresado")
                    break
                except:
                    continue
            
            # Llenar contraseña
            for selector in password_selector.split(','):
                try:
                    await generator.page.fill(selector.strip(), password, timeout=2000)
                    click.echo(f"   ✅ Contraseña ingresada")
                    break
                except:
                    continue
            
            # Click login
            for selector in submit_selector.split(','):
                try:
                    await generator.page.click(selector.strip(), timeout=2000)
                    click.echo(f"   ✅ Click en login")
                    break
                except:
                    continue
            
            await asyncio.sleep(2)
            click.echo(f"   ✅ Login completado\n")
            
            # Navegar a página objetivo
            click.echo(f"🔍 Navegando a: {url}")
            await generator.page.goto(url)
            await asyncio.sleep(2)
            
            # Explorar
            exploration_data = await generator.explore_page(url)
            
            click.echo("\n" + "=" * 60)
            click.echo("   📊 RESUMEN")
            click.echo("=" * 60)
            click.echo(f"\n✅ Título: {exploration_data['title']}")
            click.echo(f"\n📦 Elementos encontrados:")
            click.echo(f"   • {len(exploration_data['elements']['inputs'])} inputs")
            click.echo(f"   • {len(exploration_data['elements']['buttons'])} botones")
            click.echo(f"   • {len(exploration_data['elements']['links'])} links")
            
            if show_details:
                if exploration_data['elements']['inputs']:
                    click.echo("\n🔹 INPUTS:")
                    for i, inp in enumerate(exploration_data['elements']['inputs'][:5], 1):
                        click.echo(f"   {i}. id={inp['id']}, name={inp['name']}, type={inp['type']}")
                
                if exploration_data['elements']['buttons']:
                    click.echo("\n🔹 BUTTONS:")
                    for i, btn in enumerate(exploration_data['elements']['buttons'][:5], 1):
                        click.echo(f"   {i}. id={btn['id']}, text={btn['text'][:30]}")
            
            click.echo("\n" + "=" * 60 + "\n")
            
        except Exception as e:
            click.echo(f"\n❌ Error: {e}\n")
            import traceback
            traceback.print_exc()
            
        finally:
            await generator.close_browser()
    
    asyncio.run(run_auth_exploration())

@cli.command('generate-auth')
@click.argument('url')
@click.option('--site', '-s', help='Nombre del sitio en auth.yaml')
@click.option('--description', '-desc', help='Descripción del test (opcional)')
@click.option('--interactive', '-i', is_flag=True, help='Modo interactivo (conversación con Claude)')
@click.option('--output', '-o', default='tests', help='Directorio de salida')
@click.option('--filename', '-f', help='Nombre del archivo')
def generate_auth(url, site, description, interactive, output, filename):
    """
    🤖 Genera test para página que requiere autenticación
    
    Dos modos:
    
    1. AUTOMÁTICO (sin descripción):
       Claude explora y genera tests de flows principales
       
       python cli.py generate-auth https://mi-app.com/dashboard -s mi-app
    
    2. INTERACTIVO (con --interactive):
       Conversación con Claude sobre qué testear
       
       python cli.py generate-auth https://mi-app.com/dashboard -s mi-app --interactive
    
    3. ESPECÍFICO (con --description):
       Test específico que describas
       
       python cli.py generate-auth https://mi-app.com/dashboard -s mi-app \\
           --description "exportar reporte con fechas"
    """
    
    async def run_auth_generation():
        from pathlib import Path
        import sys
        sys.path.insert(0, str(Path(__file__).parent / 'src'))
        from ai_test_generator import AITestGenerator
        from auth_config import AuthConfig
        
        click.echo("=" * 60)
        click.echo("   🤖 GENERACIÓN DE TEST CON AUTENTICACIÓN")
        click.echo("=" * 60 + "\n")
        
        # Cargar config
        auth_config = AuthConfig()
        
        if not site:
            click.echo("❌ Debes especificar --site (-s)\n")
            click.echo("Sitios disponibles:")
            for s in auth_config.list_sites():
                click.echo(f"  • {s}")
            return
        
        site_config = auth_config.get_site_config(site)
        if not site_config:
            click.echo(f"❌ Sitio '{site}' no encontrado en auth.yaml\n")
            return
        
        login_url = site_config['login_url']
        username = site_config['username']
        password = site_config['password']
        username_selector = site_config.get('username_selector', '#username')
        password_selector = site_config.get('password_selector', '#password')
        submit_selector = site_config.get('submit_selector', 'button[type="submit"]')
        
        click.echo(f"📋 Sitio: {site}")
        click.echo(f"🔑 Login URL: {login_url}")
        click.echo(f"🎯 Página objetivo: {url}\n")
        
        generator = AITestGenerator()
        
        try:
            await generator.start_browser()
            
            # LOGIN
            click.echo(f"🔑 Haciendo login...")
            await generator.page.goto(login_url)
            await asyncio.sleep(1)
            
            for selector in username_selector.split(','):
                try:
                    await generator.page.fill(selector.strip(), username, timeout=2000)
                    break
                except:
                    continue
            
            for selector in password_selector.split(','):
                try:
                    await generator.page.fill(selector.strip(), password, timeout=2000)
                    break
                except:
                    continue
            
            for selector in submit_selector.split(','):
                try:
                    await generator.page.click(selector.strip(), timeout=2000)
                    break
                except:
                    continue
            
            await asyncio.sleep(2)
            click.echo(f"   ✅ Login completado\n")
            
            # NAVEGAR Y EXPLORAR
            click.echo(f"🔍 Explorando {url}...")
            await generator.page.goto(url)
            await asyncio.sleep(2)
            
            # Explorar página (sin hacer goto de nuevo)
            title = await generator.page.title()
            
            elements = {
                "inputs": [],
                "buttons": [],
                "links": [],
                "selects": []
            }
            
            # Extraer inputs
            input_elements = await generator.page.query_selector_all("input")
            for input_elem in input_elements[:10]:
                try:
                    info = {
                        "type": await input_elem.get_attribute("type") or "text",
                        "id": await input_elem.get_attribute("id") or "",
                        "name": await input_elem.get_attribute("name") or "",
                        "placeholder": await input_elem.get_attribute("placeholder") or "",
                    }
                    elements["inputs"].append(info)
                except:
                    continue
            
            # Extraer buttons
            button_elements = await generator.page.query_selector_all("button, input[type='submit'], input[type='button']")
            for button in button_elements[:10]:
                try:
                    info = {
                        "id": await button.get_attribute("id") or "",
                        "class": await button.get_attribute("class") or "",
                        "text": (await button.text_content() or "").strip()[:50],
                    }
                    elements["buttons"].append(info)
                except:
                    continue
            
            exploration_data = {
                "url": url,
                "title": title,
                "elements": elements,
                "login_url": login_url,
                "username": username,
                "password": password,
                "site": site
            }
            
            click.echo(f"   ✅ Exploración completa\n")
            
            # MODO INTERACTIVO
            if interactive:
                click.echo("💬 MODO INTERACTIVO\n")
                click.echo(f"Elementos encontrados en la página:")
                click.echo(f"  • {len(elements['inputs'])} inputs")
                click.echo(f"  • {len(elements['buttons'])} botones")
                
                if elements['buttons']:
                    click.echo(f"\nBotones principales:")
                    for i, btn in enumerate(elements['buttons'][:5], 1):
                        btn_text = btn['text'] or btn['id'] or btn['class']
                        click.echo(f"  {i}. {btn_text}")
                
                click.echo(f"\n💡 ¿Qué quieres testear? (describe en una frase)")
                user_input = click.prompt("Tú")
                
                description = user_input
            
            # GENERAR TEST
            click.echo(f"\n🤖 Generando test con Claude...\n")
            
            # Preparar prompt
            if description:
                task = f"Genera UN test que: {description}"
            else:
                task = "Genera tests (2-4 tests) para los flows principales de esta página"
            
            # Crear prompt especial para auth
            generation_prompt = f"""
Genera tests de Playwright para una página que REQUIERE AUTENTICACIÓN.

INFORMACIÓN DE LOGIN:
- URL de login: {login_url}
- Usuario: {username}
- Password: {password}

PÁGINA OBJETIVO (post-login):
- URL: {url}
- Título: {title}

ELEMENTOS ENCONTRADOS:
Inputs: {len(elements['inputs'])}
{chr(10).join([f"  • id={inp['id']}, name={inp['name']}, type={inp['type']}" for inp in elements['inputs'][:5]])}

Buttons: {len(elements['buttons'])}
{chr(10).join([f"  • id={btn['id']}, text={btn['text']}" for btn in elements['buttons'][:5]])}

TAREA:
{task}

ESTRUCTURA REQUERIDA:
```python
import pytest
from playwright.async_api import Page

@pytest.mark.asyncio
async def test_nombre_descriptivo(page: Page):
    '''Descripción del test'''
    
    # PASO 1: Login
    await page.goto("{login_url}")
    await page.fill("selector-usuario", "{username}")
    await page.fill("selector-password", "{password}")
    await page.click("selector-login-button")
    await page.wait_for_load_state("networkidle")
    
    # PASO 2: Navegar a página objetivo
    await page.goto("{url}")
    
    # PASO 3: Realizar acciones en la página
    # ... tu código aquí usando selectores REALES ...
    
    # PASO 4: Verificaciones
    # ... assertions ...
```

REGLAS:
- USA selectores REALES de los elementos arriba
- SIEMPRE incluye login al inicio
- NO uses fixtures (conftest.py las maneja)
- Imports: solo pytest y Page
- Genera código completo y funcional

Genera SOLO el código Python.
"""
            
            response = generator.client.messages.create(
                model=generator.model,
                max_tokens=3000,
                messages=[{
                    "role": "user",
                    "content": generation_prompt
                }]
            )
            
            test_code = response.content[0].text
            
            # Limpiar
            if "```python" in test_code:
                test_code = test_code.split("```python")[1].split("```")[0]
            elif "```" in test_code:
                test_code = test_code.split("```")[1].split("```")[0]
            
            test_code = test_code.strip()
  
            # Guardar
            if not filename:
                from urllib.parse import urlparse
                domain = urlparse(url).netloc.replace('.', '_').replace('www_', '')
                path_part = urlparse(url).path.replace('/', '_').replace('.', '_').strip('_') or 'index'
                path_part = path_part.replace('.', '_').replace('-', '_')
                
                base_filename = f"test_{domain}_{path_part}_auth"
                auto_filename = f"{base_filename}.py"
                output_path = Path(output) / auto_filename
                
                # Si el archivo ya existe, preguntar qué hacer
                if output_path.exists():
                    # Calcular nombre del nuevo archivo
                    counter = 2
                    new_filename = f"{base_filename}_{counter}.py"
                    new_output_path = Path(output) / new_filename
                    
                    while new_output_path.exists():
                        counter += 1
                        new_filename = f"{base_filename}_{counter}.py"
                        new_output_path = Path(output) / new_filename
                    
                    click.echo(f"\n⚠️  El archivo {auto_filename} ya existe\n")
                    click.echo("¿Qué quieres hacer?")
                    click.echo(f"  1. Sobrescribir (se creará backup: {auto_filename}.backup)")
                    click.echo(f"  2. Crear nuevo ({new_filename})")
                    click.echo(f"  3. Cancelar")
                    
                    choice = click.prompt("\nOpción", type=click.Choice(['1', '2', '3']), show_choices=False)
                    
                    if choice == '1':
                        # Sobrescribir con backup
                        import shutil
                        backup_path = str(output_path) + ".backup"
                        shutil.copy(output_path, backup_path)
                        click.echo(f"\n💾 Backup creado: {backup_path}")
                        click.echo(f"📝 Sobrescribiendo: {auto_filename}\n")
                    elif choice == '2':
                        # Crear nuevo
                        auto_filename = new_filename
                        output_path = new_output_path
                        click.echo(f"\n📝 Creando nuevo archivo: {auto_filename}\n")
                    else:
                        # Cancelar
                        click.echo("\n❌ Generación cancelada\n")
                        await generator.close_browser()
                        return
                else:
                    click.echo(f"\n📝 Creando: {auto_filename}\n")

            else:
                auto_filename = filename
                output_path = Path(output) / auto_filename
                
                # Si el usuario especificó nombre y existe, preguntar
                if output_path.exists():
                    click.echo(f"\n⚠️  El archivo {auto_filename} ya existe\n")
                    click.echo("¿Qué quieres hacer?")
                    click.echo(f"  1. Sobrescribir (se creará backup)")
                    click.echo(f"  2. Cancelar")
                    
                    choice = click.prompt("\nOpción", type=click.Choice(['1', '2']), show_choices=False)
                    
                    if choice == '1':
                        import shutil
                        backup_path = str(output_path) + ".backup"
                        shutil.copy(output_path, backup_path)
                        click.echo(f"\n💾 Backup creado: {backup_path}")
                        click.echo(f"📝 Sobrescribiendo: {auto_filename}\n")
                    else:
                        click.echo("\n❌ Generación cancelada\n")
                        await generator.close_browser()
                        return
                else:
                    click.echo(f"\n📝 Creando: {auto_filename}\n")      
            
            os.makedirs(os.path.dirname(output_path) or ".", exist_ok=True)
            
            with open(output_path, "w") as f:
                f.write(test_code)
            
            click.echo("=" * 60)
            click.echo("   ✅ TEST GENERADO")
            click.echo("=" * 60)
            click.echo(f"\n📄 Archivo: {output_path}")
            click.echo(f"📏 Tamaño: {len(test_code)} caracteres")
            click.echo(f"\n💡 Para ejecutar:")
            click.echo(f"   python -m pytest {output_path} -v -s")
            click.echo("\n" + "=" * 60 + "\n")
            
        except Exception as e:
            click.echo(f"\n❌ Error: {e}\n")
            import traceback
            traceback.print_exc()
            
        finally:
            await generator.close_browser()
    
    asyncio.run(run_auth_generation())


@cli.command()
@click.argument('url')
@click.option('--description', '-desc', help='Descripción del test a generar')
@click.option('--output', '-o', default='tests', help='Directorio de salida')
@click.option('--filename', '-f', help='Nombre del archivo (auto si no se provee)')
def generate(url, description, output, filename):
    """
    🤖 Genera un test de Playwright para la URL especificada
    
    Ejemplos:
    
        python cli.py generate https://www.saucedemo.com
        
        python cli.py generate https://www.saucedemo.com \\
            --description "login con credenciales válidas"
        
        python cli.py generate https://example.com \\
            --filename test_custom.py
    """
    
    async def run_generation():
        click.echo("=" * 60)
        click.echo("   🤖 GENERACIÓN DE TEST")
        click.echo("=" * 60 + "\n")
        
        generator = AITestGenerator()
        
        try:
            # Generar nombre de archivo si no se provee
            if not filename:
                from urllib.parse import urlparse
                domain = urlparse(url).netloc.replace('.', '_').replace('www_', '')
                auto_filename = f"test_{domain}_generated.py"
            else:
                auto_filename = filename
            
            output_path = Path(output) / auto_filename
            
            # Iniciar navegador y explorar
            await generator.start_browser()
            click.echo("🔍 Explorando página...\n")
            exploration_data = await generator.explore_page(url)
            
            # Validar elementos interactivos
            total_interactive = (
                len(exploration_data['elements']['inputs']) + 
                len(exploration_data['elements']['buttons']) + 
                len(exploration_data['elements']['selects'])
            )
            
            if total_interactive == 0:
                click.echo("\n" + "⚠️ " * 20)
                click.echo("   ADVERTENCIA: PÁGINA SIN ELEMENTOS INTERACTIVOS")
                click.echo("⚠️ " * 20)
                click.echo("\n   Esta página no tiene:")
                click.echo("   • Inputs (campos de texto)")
                click.echo("   • Buttons (botones)")
                click.echo("   • Selects (dropdowns)")
                click.echo("\n   El test generado será muy básico")
                click.echo("   (solo verificará carga de página y links)\n")
                
                if not click.confirm("   ¿Continuar de todos modos?", default=False):
                    click.echo("\n   ⏭️  Generación cancelada\n")
                    return
            
            # Generar test desde exploration data
            click.echo("\n🤖 Generando código de test...\n")
            test_code = await generator.generate_test_from_exploration(
                exploration_data,
                description
            )
            
            # Guardar
            if test_code:
                os.makedirs(os.path.dirname(output_path) or ".", exist_ok=True)
                with open(output_path, "w") as f:
                    f.write(test_code)
                
                click.echo("=" * 60)
                click.echo("   ✅ GENERACIÓN EXITOSA")
                click.echo("=" * 60)
                click.echo(f"\n📄 Archivo: {output_path}")
                click.echo(f"📏 Tamaño: {len(test_code)} caracteres")
                click.echo(f"📦 Elementos interactivos: {total_interactive}")
                click.echo(f"\n💡 Para ejecutar:")
                click.echo(f"   python -m pytest {output_path} -v -s")
                click.echo("\n" + "=" * 60 + "\n")
            else:
                click.echo("\n❌ No se pudo generar el test\n")
                
        finally:
            await generator.close_browser()
    
    asyncio.run(run_generation())

@cli.command()
@click.argument('file', type=click.Path(exists=True))
@click.option('--output', '-o', default='tests', help='Directorio de salida')
def batch(file, output):
    """
    📦 Genera múltiples tests desde un archivo de URLs
    
    El archivo debe contener una URL por línea.
    Líneas vacías y que empiecen con # son ignoradas.
    
    Ejemplo de archivo urls.txt:
    
        https://www.saucedemo.com
        https://example.com
        # Esta línea es un comentario
        https://another-site.com
    
    Uso:
    
        python cli.py batch urls.txt
    """
    
    async def run_batch():
        click.echo("=" * 60)
        click.echo("   📦 GENERACIÓN EN BATCH")
        click.echo("=" * 60 + "\n")
        
        # Leer URLs del archivo
        with open(file, 'r') as f:
            urls = [
                line.strip() 
                for line in f 
                if line.strip() and not line.strip().startswith('#')
            ]
        
        if not urls:
            click.echo("❌ No se encontraron URLs en el archivo\n")
            return
        
        click.echo(f"📋 Se encontraron {len(urls)} URLs\n")
        
        generator = AITestGenerator()
        results = []
        
        try:
            await generator.start_browser()
            
            for i, url in enumerate(urls, 1):
                click.echo(f"[{i}/{len(urls)}] Procesando: {url}")
                
                try:
                    # Generar nombre de archivo
                    from urllib.parse import urlparse
                    domain = urlparse(url).netloc.replace('.', '_').replace('www_', '')
                    filename = f"test_{domain}_generated.py"
                    output_path = Path(output) / filename
                    
                    # Generar test
                    test_code = await generator.generate_test_for_url(
                        url=url,
                        output_file=str(output_path)
                    )
                    
                    if test_code:
                    # Validar que el test tenga contenido útil
                        lines = test_code.strip().split('\n')
                        code_lines = [l for l in lines if l.strip() and not l.strip().startswith('#')]
    
                    # Un test útil debería tener al menos 15 líneas de código
                        if len(code_lines) >= 15:
                            results.append({'url': url, 'file': str(output_path), 'status': 'OK'})
                            click.echo(f"   ✅ Guardado en: {output_path}\n")
                        else:
                            results.append({'url': url, 'file': str(output_path), 'status': 'WARNING: Test muy simple'})
                            click.echo(f"   ⚠️  Advertencia: Test generado pero muy simple\n")
                            click.echo(f"      Guardado en: {output_path}\n")
                    else:
                        results.append({'url': url, 'file': None, 'status': 'FAILED'})
                        click.echo(f"   ❌ Falló\n")
                        
                except Exception as e:
                    results.append({'url': url, 'file': None, 'status': f'ERROR: {str(e)}'})
                    click.echo(f"   ❌ Error: {e}\n")
            
            # Resumen final
            click.echo("\n" + "=" * 60)
            click.echo("   📊 RESUMEN FINAL")
            click.echo("=" * 60 + "\n")
            
            successful = [r for r in results if r['status'] == 'OK']
            warnings = [r for r in results if 'WARNING' in r['status']]
            failed = [r for r in results if r['status'] not in ['OK'] and 'WARNING' not in r['status']]
            
            click.echo(f"✅ Exitosos: {len(successful)}/{len(urls)}")
            click.echo(f"⚠️  Advertencias: {len(warnings)}/{len(urls)}")
            click.echo(f"❌ Fallidos: {len(failed)}/{len(urls)}")
            
            if successful:
                click.echo("\n📄 Tests generados:")
                for r in successful:
                    click.echo(f"   • {r['file']}")
        
            if warnings:
                click.echo("\n⚠️  Tests con advertencias:")
                for r in warnings:
                    click.echo(f"   • {r['file']} - {r['status']}")
        
            if failed:
                click.echo("\n⚠️  URLs con problemas:")
                for r in failed:
                    click.echo(f"   • {r['url']} - {r['status']}")
            
            click.echo("\n" + "=" * 60 + "\n")
            
        finally:
            await generator.close_browser()
    
    asyncio.run(run_batch())


@cli.command('list')
@click.option('--path', '-p', default='tests', help='Directorio de tests')
def list_test(path):
    """
    📋 Lista todos los tests generados
    
    Ejemplo:
    
        python cli.py list
        python cli.py list --path tests
    """
    
    click.echo("=" * 60)
    click.echo("   📋 TESTS GENERADOS")
    click.echo("=" * 60 + "\n")
    
    test_dir = Path(path)
    
    if not test_dir.exists():
        click.echo(f"❌ Directorio no existe: {test_dir}\n")
        return
    
    # Buscar archivos de test
    test_files = sorted(test_dir.glob("test_*.py"))
    
    if not test_files:
        click.echo(f"📭 No se encontraron tests en {test_dir}\n")
        return
    
    click.echo(f"✅ Se encontraron {len(test_files)} tests:\n")
    
    for i, test_file in enumerate(sorted(test_files), 1):
        size = test_file.stat().st_size
        click.echo(f"{i:2}. {test_file.name}")
        click.echo(f"    Tamaño: {size} bytes")
        click.echo(f"    Ruta: {test_file}")
        click.echo()
    
    click.echo("=" * 60)
    click.echo(f"\n💡 Para ejecutar todos:")
    click.echo(f"   python -m pytest {path} -v\n")


@cli.command()
@click.option('--path', '-p', default='tests', help='Directorio de tests')
@click.option('--verbose', '-v', is_flag=True, help='Modo verbose')
def run(path, verbose):
    """
    ▶️  Ejecuta todos los tests generados
    
    Ejemplo:
    
        python cli.py run
        python cli.py run --verbose
        python cli.py run --path tests
    """
    
    import subprocess
    
    click.echo("=" * 60)
    click.echo("   ▶️  EJECUTANDO TESTS")
    click.echo("=" * 60 + "\n")
    
    test_dir = Path(path)
    
    if not test_dir.exists():
        click.echo(f"❌ Directorio no existe: {test_dir}\n")
        return
    
    # Construir comando pytest
    cmd = ["python", "-m", "pytest", str(test_dir)]
    
    if verbose:
        cmd.append("-v")
        cmd.append("-s")
    
    click.echo(f"🚀 Comando: {' '.join(cmd)}\n")
    click.echo("=" * 60 + "\n")
    
    # Ejecutar pytest
    result = subprocess.run(cmd)
    
    click.echo("\n" + "=" * 60)
    if result.returncode == 0:
        click.echo("   ✅ TODOS LOS TESTS PASARON")
    else:
        click.echo("   ❌ ALGUNOS TESTS FALLARON")
    click.echo("=" * 60 + "\n")

@cli.command()
@click.argument('test_file', type=click.Path(exists=True))
@click.option('--error', '-e', default='', help='Mensaje de error (opcional)')
@click.option('--dry-run', is_flag=True, help='Preview sin aplicar cambios')
def heal(test_file, error, dry_run):
    """
    🔧 Repara un test con selectores rotos automáticamente
    
    Detecta selectores que cambiaron, re-explora la página,
    y actualiza el test con los selectores correctos.
    
    Ejemplos:
    
        # Preview de cambios (recomendado primero)
        python cli.py heal tests/test_broken.py --dry-run
        
        # Aplicar reparación
        python cli.py heal tests/test_broken.py
        
        # Con mensaje de error específico
        python cli.py heal tests/test_broken.py --error "timeout waiting for #login"
    """
    
    async def run_healing():
    # Arreglar imports
        import sys
        from pathlib import Path
        sys.path.insert(0, str(Path(__file__).parent / 'src'))
        from auto_healer import TestAutoHealer
    
        click.echo("=" * 60)
        click.echo("   🔧 AUTO-HEALING DE TEST")
        click.echo("=" * 60 + "\n")
    
        if dry_run:
            click.echo("🔍 Modo PREVIEW - No se aplicarán cambios\n")
    
        healer = TestAutoHealer()
    
        if not error:
            error_msg = "Test timeout - selector not found"
        else:
            error_msg = error
    
        await healer.heal_test(test_file, error_msg, dry_run)
    
    asyncio.run(run_healing())    


if __name__ == "__main__":
    cli()
