import pytest
from playwright.async_api import Page


@pytest.mark.asyncio
async def test_login_with_wrong_selectors(page: Page):
    """Test con selectores completamente INCORRECTOS"""
    
    await page.goto("https://www.saucedemo.com")
    
    # Selectores TOTALMENTE inventados
    await page.fill("#email-input", "standard_user")      # ❌ NO EXISTE
    await page.fill("#password-box", "secret_sauce")      # ❌ NO EXISTE
    await page.click("#submit-button")                    # ❌ NO EXISTE
    
    await page.wait_for_url("**/inventory.html")
    assert "inventory.html" in page.url
