"""
Explorer - Explora páginas web usando MCP
"""

import os
from anthropic import Anthropic
from dotenv import load_dotenv

load_dotenv()


class PageExplorer:
    """Explora páginas web usando Claude + MCP"""
    
    def __init__(self):
        api_key = os.getenv("ANTHROPIC_API_KEY")
        if not api_key:
            raise ValueError("ANTHROPIC_API_KEY no encontrada en .env")
        
        self.client = Anthropic(api_key=api_key)
        self.model = "claude-sonnet-4-20250514"
    
    async def explore_page(self, url: str) -> dict:
        """
        Explora una página web y retorna información estructurada
        
        Args:
            url: URL de la página a explorar
            
        Returns:
            dict con información encontrada
        """
        
        print(f"\n🔍 Explorando {url}...\n")
        
        # Por ahora, simulamos la exploración
        # En la próxima versión conectaremos con MCP real
        
        exploration_prompt = f"""
        Imagina que estás explorando la página web: {url}
        
        Basándote en el conocimiento común de esa página, describe:
        
        1. Elementos interactivos principales (botones, campos, links)
        2. Formularios presentes
        3. Navegación principal
        
        Responde en formato JSON:
        {{
            "url": "{url}",
            "title": "título estimado",
            "interactive_elements": [
                {{"type": "button", "description": "...", "estimated_selector": "..."}}
            ],
            "forms": [...],
            "navigation": [...]
        }}
        """
        
        try:
            response = self.client.messages.create(
                model=self.model,
                max_tokens=2000,
                messages=[{
                    "role": "user",
                    "content": exploration_prompt
                }]
            )
            
            result = response.content[0].text
            
            print("📋 Resultado de exploración:")
            print(result)
            
            return {
                "success": True,
                "url": url,
                "analysis": result
            }
            
        except Exception as e:
            print(f"❌ Error en exploración: {e}")
            return {
                "success": False,
                "url": url,
                "error": str(e)
            }
    
    def suggest_tests(self, exploration_result: dict) -> list[str]:
        """
        Sugiere tests basados en la exploración
        
        Args:
            exploration_result: Resultado de explore_page()
            
        Returns:
            Lista de sugerencias de tests
        """
        
        if not exploration_result.get("success"):
            return ["No se pudo generar sugerencias - exploración falló"]
        
        # Por ahora sugerencias genéricas
        # Después usaremos los datos reales de MCP
        
        suggestions = [
            "Test de navegación básica",
            "Test de elementos interactivos",
            "Test de formularios (si existen)",
            "Test de validación visual"
        ]
        
        return suggestions


# Test rápido
if __name__ == "__main__":
    import asyncio
    
    async def test_explorer():
        explorer = PageExplorer()
        result = await explorer.explore_page("https://www.saucedemo.com")
        
        print("\n" + "="*60)
        print("SUGERENCIAS DE TESTS:")
        print("="*60)
        
        suggestions = explorer.suggest_tests(result)
        for i, suggestion in enumerate(suggestions, 1):
            print(f"{i}. {suggestion}")
    
    asyncio.run(test_explorer())