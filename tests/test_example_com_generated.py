import pytest
from playwright.async_api import Page


@pytest.mark.asyncio
async def test_page_loads_successfully(page: Page):
    '''Verifica que la página carga correctamente y muestra el título esperado'''
    
    await page.goto("https://example.com")
    await page.wait_for_load_state("networkidle")
    
    title = await page.title()
    assert title == "Example Domain"


@pytest.mark.asyncio
async def test_page_contains_main_heading(page: Page):
    '''Verifica que la página contiene el heading principal'''
    
    await page.goto("https://example.com")
    await page.wait_for_load_state("networkidle")
    
    heading = page.locator("h1")
    await heading.wait_for()
    assert await heading.is_visible()


@pytest.mark.asyncio
async def test_learn_more_link_exists_and_is_clickable(page: Page):
    '''Verifica que el link "Learn more" existe y es clickeable'''
    
    await page.goto("https://example.com")
    await page.wait_for_load_state("networkidle")
    
    learn_more_link = page.locator('a[href="https://iana.org/domains/example"]')
    await learn_more_link.wait_for()
    
    assert await learn_more_link.is_visible()
    link_text = await learn_more_link.text_content()
    assert link_text == "Learn more"


@pytest.mark.asyncio
async def test_learn_more_link_navigation(page: Page):
    '''Verifica que el link "Learn more" navega correctamente'''
    
    await page.goto("https://example.com")
    await page.wait_for_load_state("networkidle")
    
    learn_more_link = page.locator('a[href="https://iana.org/domains/example"]')
    
    # Verificar que el link tiene el href correcto
    href = await learn_more_link.get_attribute("href")
    assert href == "https://iana.org/domains/example"


@pytest.mark.asyncio
async def test_page_structure_and_content(page: Page):
    '''Verifica la estructura básica y contenido de la página'''
    
    await page.goto("https://example.com")
    await page.wait_for_load_state("networkidle")
    
    # Verificar que hay contenido en la página
    body = page.locator("body")
    await body.wait_for()
    assert await body.is_visible()
    
    # Verificar que la página no está vacía
    content = await page.content()
    assert len(content) > 0
    assert "Example Domain" in content