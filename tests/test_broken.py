import pytest
from playwright.async_api import Page


@pytest.mark.asyncio
async def test_login_with_broken_selectors(page: Page):
    """Test con selectores ROTOS a propósito"""
    
    await page.goto("https://www.saucedemo.com")
    
    # Selectores CORREGIDOS
    await page.fill("#user-name", "standard_user")
    await page.fill("#password", "secret_sauce")
    await page.click("#login-button")
    
    await page.wait_for_url("**/inventory.html")
    assert "inventory.html" in page.url