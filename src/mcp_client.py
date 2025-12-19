"""
Cliente MCP - Conecta Claude con el servidor MCP de Playwright
"""

import os
import asyncio
from anthropic import Anthropic
from dotenv import load_dotenv
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

load_dotenv()


class MCPClient:
    """Cliente que conecta Claude con MCP Server"""
    
    def __init__(self):
        api_key = os.getenv("ANTHROPIC_API_KEY")
        if not api_key:
            raise ValueError("ANTHROPIC_API_KEY no encontrada")
        
        self.client = Anthropic(api_key=api_key)
        self.model = "claude-sonnet-4-20250514"
        self.session = None
    
    async def connect_to_mcp_server(self):
        """Conecta con el servidor MCP de Playwright"""
        
        print("🔌 Conectando con MCP Server...")
        
        # Configuración del servidor MCP
        server_params = StdioServerParameters(
            command="python",
            args=["-m", "mcp.playwright_server"],
            env=None
        )
        
        try:
            # Iniciar sesión con el servidor
            stdio_transport = await stdio_client(server_params)
            self.session = ClientSession(stdio_transport[0], stdio_transport[1])
            
            await self.session.initialize()
            
            print("✅ Conectado a MCP Server")
            
            # Listar herramientas disponibles
            tools = await self.session.list_tools()
            
            print(f"\n🛠️  Herramientas disponibles: {len(tools.tools)}")
            for tool in tools.tools:
                print(f"   • {tool.name}: {tool.description}")
            
            return True
            
        except Exception as e:
            print(f"❌ Error conectando a MCP: {e}")
            return False
    
    async def explore_page_with_mcp(self, url: str):
        """Explora una página usando MCP real"""
        
        if not self.session:
            print("❌ No hay sesión MCP activa")
            return None
        
        print(f"\n🔍 Explorando {url} con MCP...\n")
        
        # Prompt para Claude con instrucciones de usar MCP
        exploration_prompt = f"""
Vas a explorar la página web: {url}

Usa las herramientas MCP disponibles para:

1. Navegar a la URL (herramienta: navigate)
2. Obtener el contenido de la página (herramienta: get_page_content)
3. Buscar elementos interactivos como botones, inputs, forms (herramienta: find_elements)
4. Tomar un screenshot (herramienta: screenshot)

Después de explorar, proporciona un resumen con:
- Título de la página
- Elementos interactivos encontrados (con sus selectores)
- Formularios presentes
- Sugerencias de tests a crear

Formato de respuesta:
{{
    "title": "...",
    "interactive_elements": [
        {{"type": "button", "selector": "...", "text": "..."}}
    ],
    "forms": [...],
    "test_suggestions": [...]
}}
"""
        
        try:
            # Obtener herramientas disponibles
            tools_result = await self.session.list_tools()
            tools = tools_result.tools
            
            # Convertir herramientas MCP a formato Anthropic
            anthropic_tools = []
            for tool in tools:
                anthropic_tools.append({
                    "name": tool.name,
                    "description": tool.description,
                    "input_schema": tool.inputSchema
                })
            
            # Llamar a Claude con herramientas MCP
            response = self.client.messages.create(
                model=self.model,
                max_tokens=4000,
                tools=anthropic_tools,  # ← AQUÍ LE DAMOS LAS HERRAMIENTAS
                messages=[{
                    "role": "user",
                    "content": exploration_prompt
                }]
            )
            
            print("📋 Respuesta de Claude:")
            print("=" * 60)
            
            # Procesar respuesta
            for content_block in response.content:
                if content_block.type == "text":
                    print(content_block.text)
                
                elif content_block.type == "tool_use":
                    # Claude quiere usar una herramienta
                    tool_name = content_block.name
                    tool_input = content_block.input
                    
                    print(f"\n🔧 Claude usa herramienta: {tool_name}")
                    print(f"   Parámetros: {tool_input}")
                    
                    # Ejecutar herramienta en MCP Server
                    result = await self.session.call_tool(tool_name, tool_input)
                    
                    print(f"   Resultado: {result.content[0].text[:200]}...")
            
            print("=" * 60)
            
            return response
            
        except Exception as e:
            print(f"❌ Error en exploración: {e}")
            import traceback
            traceback.print_exc()
            return None
    
    async def close(self):
        """Cierra la sesión MCP"""
        if self.session:
            # Cerrar navegador usando MCP
            try:
                await self.session.call_tool("close_browser", {})
            except:
                pass
            
            print("🔌 Sesión MCP cerrada")


# Test del cliente
async def test_mcp_client():
    """Test de integración completa"""
    
    print("=" * 60)
    print("   TEST DE INTEGRACIÓN MCP")
    print("=" * 60 + "\n")
    
    client = MCPClient()
    
    # Conectar a MCP
    connected = await client.connect_to_mcp_server()
    
    if not connected:
        print("❌ No se pudo conectar a MCP Server")
        return
    
    # Explorar página
    await client.explore_page_with_mcp("https://www.saucedemo.com")
    
    # Cerrar
    await client.close()
    
    print("\n" + "=" * 60)
    print("   TEST COMPLETADO")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(test_mcp_client())
