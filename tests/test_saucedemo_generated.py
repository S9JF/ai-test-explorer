import pytest
from playwright.async_api import Page


@pytest.mark.asyncio
async def test_login_with_valid_credentials_and_verify_redirect(page: Page):
    '''Test login with valid credentials and verify redirection to inventory page'''
    
    # Navigate to login page
    await page.goto("https://www.saucedemo.com")    
    
    # Fill login credentials
    await page.fill("#user-name", "standard_user")
    await page.fill("#password", "secret_sauce")
    
    # Click login button
    await page.click("#login-button")
    
    # Verify successful login by checking URL redirection
    await page.wait_for_url("**/inventory.html")
    
    # Additional verification - check if we're on the inventory page
    assert "inventory" in page.url
    assert await page.is_visible(".inventory_list")