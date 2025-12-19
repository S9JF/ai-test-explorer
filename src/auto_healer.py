"""
Auto-Healer - Detecta y repara tests rotos automáticamente
Cuando selectores cambian, re-explora la página y actualiza el test
"""

import os
import re
import asyncio
from pathlib import Path
from typing import Dict, List, Optional
from ai_test_generator import AITestGenerator
from anthropic import Anthropic
from dotenv import load_dotenv

load_dotenv()


class TestAutoHealer:
    """
    Sistema de auto-reparación de tests
    Detecta selectores rotos y los actualiza automáticamente
    """
    
    def __init__(self):
        api_key = os.getenv("ANTHROPIC_API_KEY")
        if not api_key:
            raise ValueError("ANTHROPIC_API_KEY no encontrada")
        
        self.client = Anthropic(api_key=api_key)
        self.model = "claude-sonnet-4-20250514"
        self.generator = AITestGenerator()
    
    def extract_url_from_test(self, test_code: str) -> Optional[str]:
        """
        Extrae la URL del código del test
        
        Args:
            test_code: Código del test
            
        Returns:
            URL encontrada o None
        """
        
        # Buscar pattern: page.goto("url") o page.goto('url')
        patterns = [
            r'page\.goto\(["\']([^"\']+)["\']\)',
            r'await page\.goto\(["\']([^"\']+)["\']\)'
        ]
        
        for pattern in patterns:
            match = re.search(pattern, test_code)
            if match:
                return match.group(1)
        
        return None
    
    def extract_selectors_from_test(self, test_code: str) -> List[str]:
        """
        Extrae todos los selectores del código del test
        
        Args:
            test_code: Código del test
            
        Returns:
            Lista de selectores encontrados
        """
        
        selectors = []
        
        # Patterns para diferentes métodos de Playwright
        patterns = [
            r'page\.fill\(["\']([^"\']+)["\']',
            r'page\.click\(["\']([^"\']+)["\']',
            r'page\.locator\(["\']([^"\']+)["\']',
            r'page\.get_by_role\(["\']([^"\']+)["\']',
            r'page\.query_selector\(["\']([^"\']+)["\']',
        ]
        
        for pattern in patterns:
            matches = re.findall(pattern, test_code)
            selectors.extend(matches)
        
        return list(set(selectors))  # Eliminar duplicados
    
    async def analyze_test_failure(self, test_file: str, error_message: str) -> Dict:
        """
        Analiza el fallo de un test y determina si es reparable
        
        Args:
            test_file: Path al archivo de test
            error_message: Mensaje de error de pytest
            
        Returns:
            Dict con análisis del fallo
        """
        
        print("=" * 60)
        print("   🔍 ANALIZANDO FALLO DE TEST")
        print("=" * 60 + "\n")
        
        # Leer test
        with open(test_file, 'r') as f:
            test_code = f.read()
        
        # Extraer información
        url = self.extract_url_from_test(test_code)
        selectors = self.extract_selectors_from_test(test_code)
        
        print(f"📄 Test: {test_file}")
        print(f"🌐 URL: {url}")
        print(f"🎯 Selectores encontrados: {len(selectors)}")
        for sel in selectors[:5]:
            print(f"   • {sel}")
        
        # Determinar tipo de error
        is_selector_error = any(keyword in error_message.lower() for keyword in [
            'timeout', 'not found', 'not visible', 'selector', 'locator'
        ])
        
        analysis = {
            'test_file': test_file,
            'test_code': test_code,
            'url': url,
            'selectors': selectors,
            'error_message': error_message,
            'is_selector_error': is_selector_error,
            'is_healable': is_selector_error and url is not None
        }
        
        if analysis['is_healable']:
            print("\n⚠️  Analizando si requiere reparación...")
            print("   (Se verificarán selectores en la página actual)")
        else:
            print("\n❌ Este error NO es reparable automáticamente")
            if not url:
                print("   Razón: No se pudo extraer URL del test")
            if not is_selector_error:
                print("   Razón: No parece ser un problema de selectores")
        
        print()
        
        return analysis
    
    async def heal_test(self, test_file: str, error_message: str, dry_run: bool = False) -> bool:
        """
        Intenta reparar un test automáticamente
        
        Args:
            test_file: Path al archivo de test
            error_message: Mensaje de error
            dry_run: Si True, solo muestra cambios sin aplicarlos
            
        Returns:
            True si se reparó exitosamente
        """
        
        print("=" * 60)
        print("   🔧 AUTO-HEALING DE TEST")
        print("=" * 60 + "\n")
        
        # Analizar fallo
        analysis = await self.analyze_test_failure(test_file, error_message)
        
        if not analysis['is_healable']:
            print("❌ No se puede reparar automáticamente\n")
            return False
        
        # Re-explorar página
        print("🔍 Re-explorando página para encontrar selectores actualizados...\n")
        
        await self.generator.start_browser()
        
        try:
            exploration_data = await self.generator.explore_page(analysis['url'])
            
            # Pedir a Claude que genere versión fixed
            print("🤖 Generando versión reparada del test...\n")
            
            healing_prompt = f"""
Tienes un test de Playwright que está FALLANDO.

TEST ORIGINAL:
```python
{analysis['test_code']}
```

ERROR:
{error_message}

NUEVA EXPLORACIÓN DE LA PÁGINA (DATOS ACTUALES):
URL: {exploration_data['url']}
Título: {exploration_data['title']}

INPUTS encontrados:
{self._format_elements(exploration_data['elements']['inputs'])}

BUTTONS encontrados:
{self._format_elements(exploration_data['elements']['buttons'])}

LINKS encontrados (primeros 5):
{self._format_elements(exploration_data['elements']['links'][:5])}

TAREA:
Genera una versión REPARADA del test usando los selectores ACTUALES de la exploración.

REGLAS:
1. Mantén la MISMA funcionalidad del test original
2. USA SOLO los selectores que aparecen en la exploración actual
3. Si un selector cambió, usa el nuevo
4. Mantén la misma estructura y assertions
5. NO incluyas fixtures (ya están en conftest.py)
6. Imports: solo pytest y Page

Genera SOLO el código Python reparado, sin explicaciones.
"""
            
            response = self.client.messages.create(
                model=self.model,
                max_tokens=3000,
                messages=[{
                    "role": "user",
                    "content": healing_prompt
                }]
            )
            
            fixed_code = response.content[0].text
            
            # Limpiar código
            if "```python" in fixed_code:
                fixed_code = fixed_code.split("```python")[1].split("```")[0]
            elif "```" in fixed_code:
                fixed_code = fixed_code.split("```")[1].split("```")[0]
            
            fixed_code = fixed_code.strip()
            
            print("✅ Versión reparada generada\n")
            
            # Mostrar preview de cambios
            print("=" * 60)
            print("   📋 ANÁLISIS DE CAMBIOS")
            print("=" * 60 + "\n")

            # Extraer selectores del código original y nuevo
            original_selectors = set(analysis['selectors'])
            new_selectors = set(self.extract_selectors_from_test(fixed_code))

            # Detectar cambios
            removed_selectors = original_selectors - new_selectors
            added_selectors = new_selectors - original_selectors
            unchanged_selectors = original_selectors & new_selectors
            
            # Confirmar si realmente necesita reparación
            needs_healing = bool(removed_selectors or added_selectors)
            
            if needs_healing:
                print("✅ CONFIRMADO: Test necesita reparación (selectores cambiaron)\n")
            else:
                print("ℹ️  ANÁLISIS COMPLETO: Test no necesita reparación (selectores están correctos)\n")

            # Mostrar preview de cambios
            print("=" * 60)
            print("   📋 ANÁLISIS DE CAMBIOS")
            print("=" * 60 + "\n")
            
            
            # Mostrar según haya cambios o no
            if removed_selectors or added_selectors:
                print("⚠️  SE DETECTARON CAMBIOS EN SELECTORES:\n")
    
                if removed_selectors:
                   print("🔴 REMOVIDOS:")
                   for sel in sorted(removed_selectors):
                        print(f"   • {sel}")
                   print()
    
                if added_selectors:
                    print("🟢 AGREGADOS:")
                    for sel in sorted(added_selectors):
                        print(f"   • {sel}")
                    print()
    
                if unchanged_selectors:
                    print("⚪ SIN CAMBIOS:")
                    for sel in sorted(list(unchanged_selectors)[:3]):
                        print(f"   • {sel}")
                    if len(unchanged_selectors) > 3:
                        print(f"   ... y {len(unchanged_selectors) - 3} más")
                    print()
            else:
                print("✅ NO HAY CAMBIOS EN SELECTORES")
                print("\nTodos los selectores siguen siendo válidos:")
                for sel in sorted(list(unchanged_selectors)[:5]):
                    print(f"   • {sel}")
                if len(unchanged_selectors) > 5:
                    print(f"   ... y {len(unchanged_selectors) - 5} más")
                print()
    
                print("💡 El test original ya usa selectores correctos.")
                print("   No es necesario aplicar cambios.\n")

            print("=" * 60 + "\n")

            if dry_run:
                print("🔍 DRY RUN - No se aplicaron cambios")
    
                # Mensaje según si hay cambios o no
                if not (removed_selectors or added_selectors):
                    print("\nℹ️  No hay cambios que aplicar - el test ya está correcto\n")
                else:
                    print(f"\n💾 Para aplicar cambios, ejecuta:")
                    print(f"   python cli.py heal {test_file}\n")
    
            return True
            
            # Guardar backup
            backup_file = test_file + ".backup"
            with open(test_file, 'r') as f:
                original = f.read()
            with open(backup_file, 'w') as f:
                f.write(original)
            
            print(f"💾 Backup guardado: {backup_file}")
            
            # Aplicar fix
            with open(test_file, 'w') as f:
                f.write(fixed_code)
            
            print(f"✅ Test reparado: {test_file}")
            print("\n" + "=" * 60)
            print("   🎉 AUTO-HEALING COMPLETADO")
            print("=" * 60)
            print(f"\n💡 Para ejecutar:")
            print(f"   python -m pytest {test_file} -v -s\n")
            
            return True
            
        except Exception as e:
            print(f"❌ Error durante healing: {e}\n")
            return False
            
        finally:
            await self.generator.close_browser()
    
    def _format_elements(self, elements: List[Dict]) -> str:
        """Formatea lista de elementos para el prompt"""
        if not elements:
            return "(ninguno)"
        
        lines = []
        for i, elem in enumerate(elements[:5], 1):
            if 'id' in elem:
                lines.append(f"{i}. id='{elem.get('id', '')}', name='{elem.get('name', '')}', type='{elem.get('type', '')}'")
            elif 'text' in elem:
                lines.append(f"{i}. text='{elem.get('text', '')[:30]}', href='{elem.get('href', '')[:30]}'")
        
        return "\n".join(lines)


async def heal_test_file(test_file: str, error_message: str = "", dry_run: bool = False):
    """
    Función helper para reparar un test
    
    Args:
        test_file: Path al test
        error_message: Mensaje de error (opcional)
        dry_run: Si True, solo muestra cambios
    """
    
    healer = TestAutoHealer()
    
    if not error_message:
        error_message = "Test timeout - selector not found"
    
    success = await healer.heal_test(test_file, error_message, dry_run)
    
    return success


# Para testing
if __name__ == "__main__":
    import sys
    
    if len(sys.argv) < 2:
        print("Uso: python src/auto_healer.py <test_file> [--dry-run]")
        sys.exit(1)
    
    test_file = sys.argv[1]
    dry_run = "--dry-run" in sys.argv
    
    asyncio.run(heal_test_file(test_file, dry_run=dry_run))