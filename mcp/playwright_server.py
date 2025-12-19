"""
MCP Server para Playwright
Proporciona herramientas de navegador a Claude
"""

import asyncio
from typing import Any, Sequence
from mcp.server import Server
from mcp.types import Tool, TextContent
from playwright.async_api import async_playwright, Browser, Page
import json


class PlaywrightMCPServer:
    """Servidor MCP que expone herramientas de Playwright a Claude"""
    
    def __init__(self):
        self.server = Server("playwright-server")
        self.browser: Browser | None = None
        self.page: Page | None = None
        self.playwright = None
        
        # Registrar herramientas
        self._register_tools()
    
    def _register_tools(self):
        """Registra las herramientas disponibles para Claude"""
        
        @self.server.list_tools()
        async def list_tools() -> list[Tool]:
            """Lista todas las herramientas disponibles"""
            return [
                Tool(
                    name="navigate",
                    description="Navega a una URL específica",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "url": {
                                "type": "string",
                                "description": "URL a navegar"
                            }
                        },
                        "required": ["url"]
                    }
                ),
                Tool(
                    name="get_page_content",
                    description="Obtiene el contenido HTML de la página actual",
                    inputSchema={
                        "type": "object",
                        "properties": {}
                    }
                ),
                Tool(
                    name="find_elements",
                    description="Encuentra elementos en la página usando un selector CSS",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "selector": {
                                "type": "string",
                                "description": "Selector CSS para buscar elementos"
                            }
                        },
                        "required": ["selector"]
                    }
                ),
                Tool(
                    name="screenshot",
                    description="Toma una captura de pantalla de la página actual",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "path": {
                                "type": "string",
                                "description": "Ruta donde guardar el screenshot"
                            }
                        },
                        "required": ["path"]
                    }
                ),
                Tool(
                    name="close_browser",
                    description="Cierra el navegador",
                    inputSchema={
                        "type": "object",
                        "properties": {}
                    }
                )
            ]
        
        @self.server.call_tool()
        async def call_tool(name: str, arguments: Any) -> Sequence[TextContent]:
            """Ejecuta una herramienta"""
            
            if name == "navigate":
                return await self._navigate(arguments["url"])
            
            elif name == "get_page_content":
                return await self._get_page_content()
            
            elif name == "find_elements":
                return await self._find_elements(arguments["selector"])
            
            elif name == "screenshot":
                return await self._screenshot(arguments["path"])
            
            elif name == "close_browser":
                return await self._close_browser()
            
            else:
                raise ValueError(f"Herramienta desconocida: {name}")
    
    async def _ensure_browser(self):
        """Asegura que el navegador esté iniciado"""
        if not self.browser:
            self.playwright = await async_playwright().start()
            self.browser = await self.playwright.chromium.launch(headless=False)
            self.page = await self.browser.new_page()
    
    async def _navigate(self, url: str) -> Sequence[TextContent]:
        """Navega a una URL"""
        await self._ensure_browser()
        
        try:
            await self.page.goto(url)
            title = await self.page.title()
            
            return [TextContent(
                type="text",
                text=f"✅ Navegado a: {url}\nTítulo: {title}"
            )]
        except Exception as e:
            return [TextContent(
                type="text",
                text=f"❌ Error navegando: {str(e)}"
            )]
    
    async def _get_page_content(self) -> Sequence[TextContent]:
        """Obtiene el contenido de la página"""
        if not self.page:
            return [TextContent(
                type="text",
                text="❌ No hay página abierta. Navega primero."
            )]
        
        try:
            content = await self.page.content()
            # Limitar a primeros 5000 caracteres
            content = content[:5000] + "..." if len(content) > 5000 else content
            
            return [TextContent(
                type="text",
                text=f"HTML Content:\n{content}"
            )]
        except Exception as e:
            return [TextContent(
                type="text",
                text=f"❌ Error obteniendo contenido: {str(e)}"
            )]
    
    async def _find_elements(self, selector: str) -> Sequence[TextContent]:
        """Encuentra elementos con un selector"""
        if not self.page:
            return [TextContent(
                type="text",
                text="❌ No hay página abierta. Navega primero."
            )]
        
        try:
            elements = await self.page.query_selector_all(selector)
            
            if not elements:
                return [TextContent(
                    type="text",
                    text=f"No se encontraron elementos con selector: {selector}"
                )]
            
            # Obtener información de cada elemento
            elements_info = []
            for i, element in enumerate(elements[:10]):  # Máximo 10 elementos
                tag_name = await element.evaluate("el => el.tagName")
                text_content = await element.evaluate("el => el.textContent")
                id_attr = await element.evaluate("el => el.id")
                class_attr = await element.evaluate("el => el.className")
                
                elements_info.append({
                    "index": i,
                    "tag": tag_name,
                    "text": text_content[:100] if text_content else "",
                    "id": id_attr,
                    "class": class_attr
                })
            
            result = f"✅ Encontrados {len(elements)} elementos con '{selector}':\n\n"
            result += json.dumps(elements_info, indent=2)
            
            return [TextContent(
                type="text",
                text=result
            )]
        except Exception as e:
            return [TextContent(
                type="text",
                text=f"❌ Error buscando elementos: {str(e)}"
            )]
    
    async def _screenshot(self, path: str) -> Sequence[TextContent]:
        """Toma screenshot"""
        if not self.page:
            return [TextContent(
                type="text",
                text="❌ No hay página abierta. Navega primero."
            )]
        
        try:
            await self.page.screenshot(path=path)
            
            return [TextContent(
                type="text",
                text=f"✅ Screenshot guardado en: {path}"
            )]
        except Exception as e:
            return [TextContent(
                type="text",
                text=f"❌ Error tomando screenshot: {str(e)}"
            )]
    
    async def _close_browser(self) -> Sequence[TextContent]:
        """Cierra el navegador"""
        if self.browser:
            await self.browser.close()
            await self.playwright.stop()
            self.browser = None
            self.page = None
            self.playwright = None
            
            return [TextContent(
                type="text",
                text="✅ Navegador cerrado"
            )]
        
        return [TextContent(
            type="text",
            text="No hay navegador abierto"
        )]
    
    async def run(self):
        """Inicia el servidor MCP"""
        # El servidor MCP maneja la comunicación
        async with self.server:
            await self.server.run()


# Para testing directo
if __name__ == "__main__":
    server = PlaywrightMCPServer()
    asyncio.run(server.run())