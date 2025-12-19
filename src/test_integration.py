"""
Test de integración - Claude + Playwright directo
Versión simplificada sin MCP SDK (más fácil de debuggear)
"""

import os
import asyncio
from anthropic import Anthropic
from playwright.async_api import async_playwright
from dotenv import load_dotenv

load_dotenv()


async def test_claude_with_playwright():
    """
    Prueba de concepto: Claude explora una página con Playwright
    """
    
    print("=" * 60)
    print("   TEST: CLAUDE + PLAYWRIGHT INTEGRATION")
    print("=" * 60 + "\n")
    
    # 1. Inicializar Claude
    api_key = os.getenv("ANTHROPIC_API_KEY")
    if not api_key:
        print("❌ API Key no encontrada")
        return
    
    client = Anthropic(api_key=api_key)
    print("✅ Cliente Claude inicializado")
    
    # 2. Inicializar Playwright
    playwright = await async_playwright().start()
    browser = await playwright.chromium.launch(headless=False)
    page = await browser.new_page()
    print("✅ Navegador Playwright iniciado\n")
    
    # 3. Navegar a página
    url = "https://www.saucedemo.com"
    print(f"🔍 Navegando a {url}...")
    await page.goto(url)
    await asyncio.sleep(2)  # Esperar carga
    print("✅ Página cargada\n")
    
    # 4. Extraer información de la página
    print("📊 Extrayendo información de la página...\n")
    
    # Obtener título
    title = await page.title()
    print(f"   Título: {title}")
    
    # Buscar inputs
    inputs = await page.query_selector_all("input")
    print(f"   Inputs encontrados: {len(inputs)}")
    
    for i, input_elem in enumerate(inputs[:5]):  # Máximo 5
        input_type = await input_elem.get_attribute("type")
        input_id = await input_elem.get_attribute("id")
        input_name = await input_elem.get_attribute("name")
        input_placeholder = await input_elem.get_attribute("placeholder")
        
        print(f"      [{i}] Type: {input_type}, ID: {input_id}, Name: {input_name}, Placeholder: {input_placeholder}")
    
    # Buscar botones
    buttons = await page.query_selector_all("button, input[type='submit']")
    print(f"\n   Botones encontrados: {len(buttons)}")
    
    for i, button in enumerate(buttons[:5]):
        button_id = await button.get_attribute("id")
        button_class = await button.get_attribute("class")
        button_text = await button.text_content()
        
        print(f"      [{i}] ID: {button_id}, Class: {button_class}, Text: {button_text}")
    
    # 5. Pedir a Claude que analice la información
    print("\n🤖 Consultando a Claude sobre la página...\n")
    
    page_info = f"""
Acabo de explorar la página: {url}

Información encontrada:
- Título: {title}
- Inputs: {len(inputs)} encontrados
- Botones: {len(buttons)} encontrados

Primeros inputs:
"""
    
    for i, input_elem in enumerate(inputs[:3]):
        input_id = await input_elem.get_attribute("id")
        input_type = await input_elem.get_attribute("type")
        page_info += f"\n  • Input {i}: type={input_type}, id={input_id}"
    
    page_info += "\n\nBasándote en esta información, ¿qué tipo de página es y qué tests deberían crearse?"
    
    response = client.messages.create(
        model="claude-sonnet-4-20250514",
        max_tokens=1000,
        messages=[{
            "role": "user",
            "content": page_info
        }]
    )
    
    analysis = response.content[0].text
    
    print("📋 Análisis de Claude:")
    print("─" * 60)
    print(analysis)
    print("─" * 60)
    
    # 6. Tomar screenshot
    screenshot_path = "screenshots/saucedemo_exploration.png"
    os.makedirs("screenshots", exist_ok=True)
    await page.screenshot(path=screenshot_path)
    print(f"\n📸 Screenshot guardado en: {screenshot_path}")
    
    # 7. Cerrar
    await browser.close()
    await playwright.stop()
    
    print("\n" + "=" * 60)
    print("   ✅ TEST COMPLETADO")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(test_claude_with_playwright())