"""
AI Test Generator - Genera tests usando exploración real con MCP
Combina Playwright + Claude para crear tests con selectores verificados
"""

import os
import asyncio
from anthropic import Anthropic
from playwright.async_api import async_playwright
from dotenv import load_dotenv
import json

load_dotenv()


class AITestGenerator:
    """
    Generador de tests que usa exploración real de páginas
    """
    
    def __init__(self):
        api_key = os.getenv("ANTHROPIC_API_KEY")
        if not api_key:
            raise ValueError("ANTHROPIC_API_KEY no encontrada")
        
        self.client = Anthropic(api_key=api_key)
        self.model = "claude-sonnet-4-20250514"
        self.browser = None
        self.page = None
        self.playwright = None
    
    async def start_browser(self):
        """Inicia el navegador Playwright"""
        print("🌐 Iniciando navegador...")
        self.playwright = await async_playwright().start()
        self.browser = await self.playwright.chromium.launch(headless=False)
        self.page = await self.browser.new_page()
        print("✅ Navegador listo\n")
    
    async def close_browser(self):
        """Cierra el navegador"""
        if self.browser:
            await self.browser.close()
        if self.playwright:
            await self.playwright.stop()
        print("🔌 Navegador cerrado")
    
    async def explore_page(self, url: str) -> dict:
        """
        Explora una página y extrae información estructurada
        
        Args:
            url: URL de la página a explorar
            
        Returns:
            dict con elementos encontrados
        """
        
        print(f"🔍 Explorando {url}...\n")
        
        # Navegar
        await self.page.goto(url, wait_until="networkidle")
        await asyncio.sleep(1)  # Dar tiempo a JavaScript
        
        # Extraer título
        title = await self.page.title()
        print(f"   📄 Título: {title}")
        
        # Extraer URL actual (por si hubo redirect)
        current_url = self.page.url
        
        # Buscar elementos interactivos
        elements = {
            "inputs": [],
            "buttons": [],
            "links": [],
            "selects": []
        }
        
        # INPUTS
        print("\n   🔍 Buscando inputs...")
        input_elements = await self.page.query_selector_all("input")
        for input_elem in input_elements[:10]:  # Máximo 10
            try:
                info = {
                    "type": await input_elem.get_attribute("type") or "text",
                    "id": await input_elem.get_attribute("id") or "",
                    "name": await input_elem.get_attribute("name") or "",
                    "placeholder": await input_elem.get_attribute("placeholder") or "",
                    "class": await input_elem.get_attribute("class") or ""
                }
                elements["inputs"].append(info)
                print(f"      • Input: type={info['type']}, id={info['id']}, name={info['name']}")
            except:
                continue
        
        # BUTTONS
        print("\n   🔍 Buscando botones...")
        button_elements = await self.page.query_selector_all("button, input[type='submit'], input[type='button']")
        for button in button_elements[:10]:
            try:
                info = {
                    "id": await button.get_attribute("id") or "",
                    "class": await button.get_attribute("class") or "",
                    "text": (await button.text_content() or "").strip()[:50],
                    "type": await button.get_attribute("type") or "button"
                }
                elements["buttons"].append(info)
                print(f"      • Button: id={info['id']}, text={info['text']}")
            except:
                continue
        
        # LINKS
        print("\n   🔍 Buscando links...")
        link_elements = await self.page.query_selector_all("a[href]")
        for link in link_elements[:10]:
            try:
                info = {
                    "href": await link.get_attribute("href") or "",
                    "text": (await link.text_content() or "").strip()[:50],
                    "id": await link.get_attribute("id") or ""
                }
                elements["links"].append(info)
                print(f"      • Link: href={info['href'][:30]}..., text={info['text']}")
            except:
                continue
        
        # SELECTS
        select_elements = await self.page.query_selector_all("select")
        for select in select_elements[:5]:
            try:
                info = {
                    "id": await select.get_attribute("id") or "",
                    "name": await select.get_attribute("name") or ""
                }
                elements["selects"].append(info)
            except:
                continue
        
        print(f"\n   ✅ Exploración completa:")
        print(f"      - {len(elements['inputs'])} inputs")
        print(f"      - {len(elements['buttons'])} botones")
        print(f"      - {len(elements['links'])} links")
        print(f"      - {len(elements['selects'])} selects\n")
        
        return {
            "url": url,
            "current_url": current_url,
            "title": title,
            "elements": elements
        }
    
    async def generate_test_from_exploration(self, exploration_data: dict, test_description: str = None) -> str:
        """
        Genera código de test basado en datos de exploración REAL
        
        Args:
            exploration_data: Datos de explore_page()
            test_description: Descripción opcional del test a generar
            
        Returns:
            Código del test generado
        """
        
        print("🤖 Generando test con Claude...\n")
        
        # Preparar información para Claude
        elements_summary = f"""
URL: {exploration_data['url']}
Título: {exploration_data['title']}

INPUTS encontrados:
{json.dumps(exploration_data['elements']['inputs'], indent=2)}

BUTTONS encontrados:
{json.dumps(exploration_data['elements']['buttons'], indent=2)}

LINKS encontrados (primeros 5):
{json.dumps(exploration_data['elements']['links'][:5], indent=2)}
"""
        
        # Prompt para Claude
        if test_description:
            task_prompt = f"""
        Genera UN SOLO test específico que haga lo siguiente:
        {test_description}

        El test debe ser completo pero enfocado en esta funcionalidad específica.
        """
        else:
            task_prompt = """
        Genera una SUITE COMPLETA de tests (entre 2-5 tests) que cubran:
        - Los flujos principales de la página
        - Escenarios positivos (happy path)
        - 1-2 escenarios negativos si aplica

        Cada test debe ser independiente y enfocado en una funcionalidad específica.
        NO generes tests redundantes.
        """
        
        generation_prompt = f"""
Eres un experto en Playwright que genera tests basándote en exploración REAL de páginas.

INFORMACIÓN DE LA PÁGINA (EXPLORADA CON PLAYWRIGHT):
{elements_summary}

TAREA:
{task_prompt}

⚠️ REGLAS ABSOLUTAS - NO NEGOCIABLES:

1. NO INCLUYAS FIXTURES
   - Las fixtures ya existen en tests/conftest.py
   - NO escribas @pytest.fixture
   - NO escribas @pytest_asyncio.fixture
   - NO definas browser() o page()

2. IMPORTS PERMITIDOS:
```python
   import pytest
   from playwright.async_api import Page
```
   - NO importes async_playwright
   - NO importes pytest_asyncio

3. ESTRUCTURA EXACTA:
```python
   import pytest
   from playwright.async_api import Page


   @pytest.mark.asyncio
   async def test_nombre_descriptivo(page: Page):
       '''Descripción del test'''
       
       # Tu código aquí
       await page.goto("url")
       ...
```

4. USA SOLO SELECTORES REALES
   - Los selectores vienen de la exploración arriba
   - NO inventes selectores
   - USA los IDs, names, classes exactos que aparecen

GENERA SOLO EL CÓDIGO DEL TEST.
NO incluyas explicaciones.
NO incluyas fixtures.
EMPIEZA directamente con los imports.
"""
        
        try:
            response = self.client.messages.create(
                model=self.model,
                max_tokens=3000,
                messages=[{
                    "role": "user",
                    "content": generation_prompt
                }]
            )
            
            code = response.content[0].text
            
            # Limpiar código (quitar markdown si lo incluyó)
            if "```python" in code:
                code = code.split("```python")[1].split("```")[0]
            elif "```" in code:
                code = code.split("```")[1].split("```")[0]
            
            code = code.strip()
            
            print("✅ Test generado\n")
            
            return code
            
        except Exception as e:
            print(f"❌ Error generando test: {e}")
            return None
    
    async def generate_test_for_url(self, url: str, test_description: str = None, output_file: str = None) -> str:
        """
        Workflow completo: Explora página + Genera test
        
        Args:
            url: URL a explorar
            test_description: Qué debe hacer el test
            output_file: Archivo donde guardar (opcional)
            
        Returns:
            Código del test
        """
        
        print("=" * 60)
        print("   🚀 GENERACIÓN DE TEST CON EXPLORACIÓN REAL")
        print("=" * 60 + "\n")
        
        # 1. Iniciar navegador si no está iniciado
        if not self.browser:
            await self.start_browser()
        
        # 2. Explorar página
        exploration_data = await self.explore_page(url)
        
        # 3. Generar test
        test_code = await self.generate_test_from_exploration(
            exploration_data,
            test_description
        )
        
        if not test_code:
            print("❌ No se pudo generar el test")
            return None
        
        # 4. Guardar si se especificó archivo
        if output_file:
            os.makedirs(os.path.dirname(output_file) or ".", exist_ok=True)
            with open(output_file, "w") as f:
                f.write(test_code)
            print(f"💾 Test guardado en: {output_file}\n")
        
        # 5. Mostrar preview
        print("📄 CÓDIGO GENERADO:")
        print("─" * 60)
        print(test_code[:500] + "..." if len(test_code) > 500 else test_code)
        print("─" * 60)
        
        return test_code


# Test del generador
async def test_generator():
    """Demo del generador"""
    
    generator = AITestGenerator()
    
    try:
        # Generar test para Sauce Demo
        test_code = await generator.generate_test_for_url(
            url="https://www.saucedemo.com",
            test_description="hacer login con credenciales válidas y verificar redirección",
            output_file="tests/test_saucedemo_generated.py"
        )
        
        if test_code:
            print("\n" + "=" * 60)
            print("   ✅ TEST GENERADO EXITOSAMENTE")
            print("=" * 60)
            print("\n💡 Para ejecutarlo:")
            print("   python -m pytest tests/test_saucedemo_generated.py -v -s\n")
        
    finally:
        await generator.close_browser()


if __name__ == "__main__":
    asyncio.run(test_generator())
