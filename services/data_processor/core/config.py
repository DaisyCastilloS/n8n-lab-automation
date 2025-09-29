"""
Configuración del Servicio de Procesamiento de Datos
"""

import os
from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    """Configuración de la aplicación"""
    
    # Base de datos
    database_url: str = "postgresql://lab_user:lab_password@localhost:5432/lab_analytics"
    
    # API
    api_host: str = "0.0.0.0"
    api_port: int = 8001
    api_debug: bool = False
    
    # Archivos
    data_input_path: str = "/app/data/input"
    data_output_path: str = "/app/data/output"
    data_temp_path: str = "/app/data/temp"
    
    # Procesamiento
    max_file_size_mb: int = 100
    batch_size: int = 1000
    processing_timeout: int = 300
    
    # Logging
    log_level: str = "INFO"
    log_file: str = "/app/logs/data_processor.log"
    
    class Config:
        env_file = ".env"
        case_sensitive = False


# Instancia global de configuración
settings = Settings()