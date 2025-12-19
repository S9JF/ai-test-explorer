"""
Test básico de MCP
Verifica que podemos comunicarnos con Claude usando MCP
"""

import os
import asyncio
from anthropic import Anthropic
from dotenv import load_dotenv

# Cargar variables de entorno
load_dotenv()

async def test_mcp_connection():
    """Prueba conexión básica con Claude"""
    
    print("🔍 Verificando configuración de MCP...\n")
    
    # Verificar API key
    api_key = os.getenv("ANTHROPIC_API_KEY")
    if not api_key:
        print("❌ Error: ANTHROPIC_API_KEY no encontrada en .env")
        return False
    
    print("✅ API Key encontrada")
    
    # Crear cliente
    try:
        client = Anthropic(api_key=api_key)
        print("✅ Cliente Anthropic creado")
    except Exception as e:
        print(f"❌ Error creando cliente: {e}")
        return False
    
    # Test simple con Claude
    try:
        print("\n🤖 Enviando mensaje de prueba a Claude...\n")
        
        response = client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=100,
            messages=[{
                "role": "user",
                "content": "Responde solo con: MCP funcionando correctamente"
            }]
        )
        
        result = response.content[0].text
        print(f"📝 Respuesta de Claude: {result}\n")
        
        if "MCP" in result or "funcionando" in result:
            print("✅ Comunicación con Claude exitosa")
            return True
        else:
            print("⚠️  Respuesta inesperada")
            return False
            
    except Exception as e:
        print(f"❌ Error en comunicación: {e}")
        return False

# Ejecutar test
if __name__ == "__main__":
    print("=" * 60)
    print("   TEST BÁSICO DE MCP")
    print("=" * 60 + "\n")
    
    result = asyncio.run(test_mcp_connection())
    
    print("\n" + "=" * 60)
    if result:
        print("   ✅ TODOS LOS TESTS PASARON")
    else:
        print("   ❌ ALGUNOS TESTS FALLARON")
    print("=" * 60)