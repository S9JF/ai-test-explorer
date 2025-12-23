"""
Manejo de configuración de autenticación
"""

import yaml
from pathlib import Path
from typing import Dict, Optional


class AuthConfig:
    """Lee y maneja configuración de autenticación desde auth.yaml"""
    
    def __init__(self, config_file: str = "auth.yaml"):
        self.config_file = Path(config_file)
        self.config = self._load_config()
    
    def _load_config(self) -> Dict:
        """Carga configuración desde YAML"""
        if not self.config_file.exists():
            return {}
        
        try:
            with open(self.config_file, 'r') as f:
                return yaml.safe_load(f) or {}
        except Exception as e:
            print(f"⚠️  Error leyendo {self.config_file}: {e}")
            return {}
    
    def get_site_config(self, site_name: str) -> Optional[Dict]:
        """Obtiene configuración de un sitio específico"""
        return self.config.get(site_name)
    
    def list_sites(self) -> list:
        """Lista todos los sitios configurados"""
        return list(self.config.keys())
    
    def has_site(self, site_name: str) -> bool:
        """Verifica si un sitio está configurado"""
        return site_name in self.config


def detect_site_from_url(url: str, auth_config: AuthConfig) -> Optional[str]:
    """
    Intenta detectar el sitio desde la URL
    
    Ejemplo:
    URL: https://www.saucedemo.com/inventory.html
    Detecta: 'saucedemo' (si existe en config)
    """
    
    for site_name, config in auth_config.config.items():
        login_url = config.get('login_url', '')
        if login_url and login_url in url:
            return site_name
        
        # También buscar por dominio
        from urllib.parse import urlparse
        url_domain = urlparse(url).netloc
        config_domain = urlparse(login_url).netloc
        
        if url_domain == config_domain:
            return site_name
    
    return None