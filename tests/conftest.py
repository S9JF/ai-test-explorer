"""
Configuración global de Pytest para tests de Playwright
Fixtures compartidas por todos los tests
"""

import pytest_asyncio
from playwright.async_api import async_playwright


@pytest_asyncio.fixture(scope="function")
async def browser():
    """
    Fixture que proporciona un navegador Chromium
    Se crea uno nuevo para cada test (scope="function")
    """
    async with async_playwright() as p:
        browser = await p.chromium.launch(
            headless=False,  # Cambia a True para ejecución sin UI
            slow_mo=100      # Ralentiza acciones para ver qué pasa
        )
        yield browser
        await browser.close()


@pytest_asyncio.fixture(scope="function")
async def page(browser):
    """
    Fixture que proporciona una página del navegador
    Se crea una nueva para cada test
    """
    page = await browser.new_page()
    
    # Configuración opcional de la página
    page.set_default_timeout(30000)  # 30 segundos timeout
    
    yield page
    
    await page.close()


@pytest_asyncio.fixture(scope="function")
async def context(browser):
    """
    Fixture que proporciona un contexto de navegador
    Útil para tests que necesitan múltiples páginas
    """
    context = await browser.new_context(
        viewport={"width": 1920, "height": 1080},
        locale="es-MX"
    )
    
    yield context
    
    await context.close()