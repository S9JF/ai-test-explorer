"""
CLI para AI Test Explorer
Comandos para explorar páginas y generar tests automáticamente
"""

import click
import asyncio
import os
from pathlib import Path
from src.ai_test_generator import AITestGenerator


@click.group()
@click.version_option(version="1.0.0", prog_name="AI Test Explorer")
def cli():
    """
    🤖 AI Test Explorer - Generación automática de tests con Playwright + Claude
    
    Explora páginas web y genera tests con selectores verificados.
    """
    pass


@cli.command()
@click.argument('url')
@click.option('--show-details', '-d', is_flag=True, help='Mostrar detalles de elementos encontrados')
def explore(url, show_details):
    """
    🔍 Explora una página web y muestra elementos encontrados
    
    Ejemplos:
    
        python cli.py explore https://www.saucedemo.com
        
        python cli.py explore https://example.com --show-details
    """
    
    async def run_exploration():
        click.echo("=" * 60)
        click.echo("   🔍 EXPLORACIÓN DE PÁGINA")
        click.echo("=" * 60 + "\n")
        
        generator = AITestGenerator()
        
        try:
            await generator.start_browser()
            
            exploration_data = await generator.explore_page(url)
            
            # Resumen
            click.echo("\n" + "=" * 60)
            click.echo("   📊 RESUMEN")
            click.echo("=" * 60)
            click.echo(f"\n✅ URL: {exploration_data['url']}")
            click.echo(f"✅ Título: {exploration_data['title']}")
            click.echo(f"\n📦 Elementos encontrados:")
            click.echo(f"   • {len(exploration_data['elements']['inputs'])} inputs")
            click.echo(f"   • {len(exploration_data['elements']['buttons'])} botones")
            click.echo(f"   • {len(exploration_data['elements']['links'])} links")
            click.echo(f"   • {len(exploration_data['elements']['selects'])} selects")
            
            if show_details:
                click.echo("\n" + "=" * 60)
                click.echo("   📋 DETALLES")
                click.echo("=" * 60)
                
                # Mostrar inputs
                if exploration_data['elements']['inputs']:
                    click.echo("\n🔹 INPUTS:")
                    for i, inp in enumerate(exploration_data['elements']['inputs'][:5], 1):
                        click.echo(f"   {i}. type={inp['type']}, id={inp['id']}, name={inp['name']}")
                
                # Mostrar botones
                if exploration_data['elements']['buttons']:
                    click.echo("\n🔹 BUTTONS:")
                    for i, btn in enumerate(exploration_data['elements']['buttons'][:5], 1):
                        click.echo(f"   {i}. id={btn['id']}, text={btn['text'][:30]}")
            
            click.echo("\n" + "=" * 60 + "\n")
            
        finally:
            await generator.close_browser()
    
    asyncio.run(run_exploration())


@cli.command()
@click.argument('url')
@click.option('--description', '-desc', help='Descripción del test a generar')
@click.option('--output', '-o', default='tests', help='Directorio de salida')
@click.option('--filename', '-f', help='Nombre del archivo (auto si no se provee)')
def generate(url, description, output, filename):
    """
    🤖 Genera un test de Playwright para la URL especificada
    
    Ejemplos:
    
        python cli.py generate https://www.saucedemo.com
        
        python cli.py generate https://www.saucedemo.com \\
            --description "login con credenciales válidas"
        
        python cli.py generate https://example.com \\
            --filename test_custom.py
    """
    
    async def run_generation():
        click.echo("=" * 60)
        click.echo("   🤖 GENERACIÓN DE TEST")
        click.echo("=" * 60 + "\n")
        
        generator = AITestGenerator()
        
        try:
            # Generar nombre de archivo si no se provee
            if not filename:
                from urllib.parse import urlparse
                domain = urlparse(url).netloc.replace('.', '_').replace('www_', '')
                auto_filename = f"test_{domain}_generated.py"
            else:
                auto_filename = filename
            
            output_path = Path(output) / auto_filename
            
            # Iniciar navegador y explorar
            await generator.start_browser()
            click.echo("🔍 Explorando página...\n")
            exploration_data = await generator.explore_page(url)
            
            # Validar elementos interactivos
            total_interactive = (
                len(exploration_data['elements']['inputs']) + 
                len(exploration_data['elements']['buttons']) + 
                len(exploration_data['elements']['selects'])
            )
            
            if total_interactive == 0:
                click.echo("\n" + "⚠️ " * 20)
                click.echo("   ADVERTENCIA: PÁGINA SIN ELEMENTOS INTERACTIVOS")
                click.echo("⚠️ " * 20)
                click.echo("\n   Esta página no tiene:")
                click.echo("   • Inputs (campos de texto)")
                click.echo("   • Buttons (botones)")
                click.echo("   • Selects (dropdowns)")
                click.echo("\n   El test generado será muy básico")
                click.echo("   (solo verificará carga de página y links)\n")
                
                if not click.confirm("   ¿Continuar de todos modos?", default=False):
                    click.echo("\n   ⏭️  Generación cancelada\n")
                    return
            
            # Generar test desde exploration data
            click.echo("\n🤖 Generando código de test...\n")
            test_code = await generator.generate_test_from_exploration(
                exploration_data,
                description
            )
            
            # Guardar
            if test_code:
                os.makedirs(os.path.dirname(output_path) or ".", exist_ok=True)
                with open(output_path, "w") as f:
                    f.write(test_code)
                
                click.echo("=" * 60)
                click.echo("   ✅ GENERACIÓN EXITOSA")
                click.echo("=" * 60)
                click.echo(f"\n📄 Archivo: {output_path}")
                click.echo(f"📏 Tamaño: {len(test_code)} caracteres")
                click.echo(f"📦 Elementos interactivos: {total_interactive}")
                click.echo(f"\n💡 Para ejecutar:")
                click.echo(f"   python -m pytest {output_path} -v -s")
                click.echo("\n" + "=" * 60 + "\n")
            else:
                click.echo("\n❌ No se pudo generar el test\n")
                
        finally:
            await generator.close_browser()
    
    asyncio.run(run_generation())

@cli.command()
@click.argument('file', type=click.Path(exists=True))
@click.option('--output', '-o', default='tests', help='Directorio de salida')
def batch(file, output):
    """
    📦 Genera múltiples tests desde un archivo de URLs
    
    El archivo debe contener una URL por línea.
    Líneas vacías y que empiecen con # son ignoradas.
    
    Ejemplo de archivo urls.txt:
    
        https://www.saucedemo.com
        https://example.com
        # Esta línea es un comentario
        https://another-site.com
    
    Uso:
    
        python cli.py batch urls.txt
    """
    
    async def run_batch():
        click.echo("=" * 60)
        click.echo("   📦 GENERACIÓN EN BATCH")
        click.echo("=" * 60 + "\n")
        
        # Leer URLs del archivo
        with open(file, 'r') as f:
            urls = [
                line.strip() 
                for line in f 
                if line.strip() and not line.strip().startswith('#')
            ]
        
        if not urls:
            click.echo("❌ No se encontraron URLs en el archivo\n")
            return
        
        click.echo(f"📋 Se encontraron {len(urls)} URLs\n")
        
        generator = AITestGenerator()
        results = []
        
        try:
            await generator.start_browser()
            
            for i, url in enumerate(urls, 1):
                click.echo(f"[{i}/{len(urls)}] Procesando: {url}")
                
                try:
                    # Generar nombre de archivo
                    from urllib.parse import urlparse
                    domain = urlparse(url).netloc.replace('.', '_').replace('www_', '')
                    filename = f"test_{domain}_generated.py"
                    output_path = Path(output) / filename
                    
                    # Generar test
                    test_code = await generator.generate_test_for_url(
                        url=url,
                        output_file=str(output_path)
                    )
                    
                    if test_code:
                    # Validar que el test tenga contenido útil
                        lines = test_code.strip().split('\n')
                        code_lines = [l for l in lines if l.strip() and not l.strip().startswith('#')]
    
                    # Un test útil debería tener al menos 15 líneas de código
                        if len(code_lines) >= 15:
                            results.append({'url': url, 'file': str(output_path), 'status': 'OK'})
                            click.echo(f"   ✅ Guardado en: {output_path}\n")
                        else:
                            results.append({'url': url, 'file': str(output_path), 'status': 'WARNING: Test muy simple'})
                            click.echo(f"   ⚠️  Advertencia: Test generado pero muy simple\n")
                            click.echo(f"      Guardado en: {output_path}\n")
                    else:
                        results.append({'url': url, 'file': None, 'status': 'FAILED'})
                        click.echo(f"   ❌ Falló\n")
                        
                except Exception as e:
                    results.append({'url': url, 'file': None, 'status': f'ERROR: {str(e)}'})
                    click.echo(f"   ❌ Error: {e}\n")
            
            # Resumen final
            click.echo("\n" + "=" * 60)
            click.echo("   📊 RESUMEN FINAL")
            click.echo("=" * 60 + "\n")
            
            successful = [r for r in results if r['status'] == 'OK']
            warnings = [r for r in results if 'WARNING' in r['status']]
            failed = [r for r in results if r['status'] not in ['OK'] and 'WARNING' not in r['status']]
            
            click.echo(f"✅ Exitosos: {len(successful)}/{len(urls)}")
            click.echo(f"⚠️  Advertencias: {len(warnings)}/{len(urls)}")
            click.echo(f"❌ Fallidos: {len(failed)}/{len(urls)}")
            
            if successful:
                click.echo("\n📄 Tests generados:")
                for r in successful:
                    click.echo(f"   • {r['file']}")
        
            if warnings:
                click.echo("\n⚠️  Tests con advertencias:")
                for r in warnings:
                    click.echo(f"   • {r['file']} - {r['status']}")
        
            if failed:
                click.echo("\n⚠️  URLs con problemas:")
                for r in failed:
                    click.echo(f"   • {r['url']} - {r['status']}")
            
            click.echo("\n" + "=" * 60 + "\n")
            
        finally:
            await generator.close_browser()
    
    asyncio.run(run_batch())


@cli.command('list')
@click.option('--path', '-p', default='tests', help='Directorio de tests')
def list_test(path):
    """
    📋 Lista todos los tests generados
    
    Ejemplo:
    
        python cli.py list
        python cli.py list --path tests
    """
    
    click.echo("=" * 60)
    click.echo("   📋 TESTS GENERADOS")
    click.echo("=" * 60 + "\n")
    
    test_dir = Path(path)
    
    if not test_dir.exists():
        click.echo(f"❌ Directorio no existe: {test_dir}\n")
        return
    
    # Buscar archivos de test
    test_files = sorted(test_dir.glob("test_*.py"))
    
    if not test_files:
        click.echo(f"📭 No se encontraron tests en {test_dir}\n")
        return
    
    click.echo(f"✅ Se encontraron {len(test_files)} tests:\n")
    
    for i, test_file in enumerate(sorted(test_files), 1):
        size = test_file.stat().st_size
        click.echo(f"{i:2}. {test_file.name}")
        click.echo(f"    Tamaño: {size} bytes")
        click.echo(f"    Ruta: {test_file}")
        click.echo()
    
    click.echo("=" * 60)
    click.echo(f"\n💡 Para ejecutar todos:")
    click.echo(f"   python -m pytest {path} -v\n")


@cli.command()
@click.option('--path', '-p', default='tests', help='Directorio de tests')
@click.option('--verbose', '-v', is_flag=True, help='Modo verbose')
def run(path, verbose):
    """
    ▶️  Ejecuta todos los tests generados
    
    Ejemplo:
    
        python cli.py run
        python cli.py run --verbose
        python cli.py run --path tests
    """
    
    import subprocess
    
    click.echo("=" * 60)
    click.echo("   ▶️  EJECUTANDO TESTS")
    click.echo("=" * 60 + "\n")
    
    test_dir = Path(path)
    
    if not test_dir.exists():
        click.echo(f"❌ Directorio no existe: {test_dir}\n")
        return
    
    # Construir comando pytest
    cmd = ["python", "-m", "pytest", str(test_dir)]
    
    if verbose:
        cmd.append("-v")
        cmd.append("-s")
    
    click.echo(f"🚀 Comando: {' '.join(cmd)}\n")
    click.echo("=" * 60 + "\n")
    
    # Ejecutar pytest
    result = subprocess.run(cmd)
    
    click.echo("\n" + "=" * 60)
    if result.returncode == 0:
        click.echo("   ✅ TODOS LOS TESTS PASARON")
    else:
        click.echo("   ❌ ALGUNOS TESTS FALLARON")
    click.echo("=" * 60 + "\n")

@cli.command()
@click.argument('test_file', type=click.Path(exists=True))
@click.option('--error', '-e', default='', help='Mensaje de error (opcional)')
@click.option('--dry-run', is_flag=True, help='Preview sin aplicar cambios')
def heal(test_file, error, dry_run):
    """
    🔧 Repara un test con selectores rotos automáticamente
    
    Detecta selectores que cambiaron, re-explora la página,
    y actualiza el test con los selectores correctos.
    
    Ejemplos:
    
        # Preview de cambios (recomendado primero)
        python cli.py heal tests/test_broken.py --dry-run
        
        # Aplicar reparación
        python cli.py heal tests/test_broken.py
        
        # Con mensaje de error específico
        python cli.py heal tests/test_broken.py --error "timeout waiting for #login"
    """
    
    async def run_healing():
    # Arreglar imports
        import sys
        from pathlib import Path
        sys.path.insert(0, str(Path(__file__).parent / 'src'))
        from auto_healer import TestAutoHealer
    
        click.echo("=" * 60)
        click.echo("   🔧 AUTO-HEALING DE TEST")
        click.echo("=" * 60 + "\n")
    
        if dry_run:
            click.echo("🔍 Modo PREVIEW - No se aplicarán cambios\n")
    
        healer = TestAutoHealer()
    
        if not error:
            error_msg = "Test timeout - selector not found"
        else:
            error_msg = error
    
        await healer.heal_test(test_file, error_msg, dry_run)
    
    asyncio.run(run_healing())    


if __name__ == "__main__":
    cli()
