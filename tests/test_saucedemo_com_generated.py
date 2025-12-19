import pytest
from playwright.async_api import Page


@pytest.mark.asyncio
async def test_login_completo(page: Page):
    '''Test de login completo con credenciales válidas'''
    
    await page.goto("https://www.saucedemo.com")
    
    # Llenar campos de login
    await page.fill("#user-name", "standard_user")
    await page.fill("#password", "secret_sauce")
    
    # Hacer click en el botón de login
    await page.click("#login-button")
    
    # Verificar que el login fue exitoso
    await page.wait_for_url("**/inventory.html")
    
    # Verificar que estamos en la página de productos
    assert "inventory" in page.url