"""
Gestor de Base de Datos para el Laboratorio Químico
"""

import asyncpg
import pandas as pd
from typing import List, Dict, Any, Optional
from datetime import datetime
import os
from loguru import logger

class DatabaseManager:
    """Gestor de conexiones y operaciones con PostgreSQL"""
    
    def __init__(self):
        self.host = os.getenv('POSTGRES_HOST', 'postgres')
        self.port = int(os.getenv('POSTGRES_PORT', '5432'))
        self.database = os.getenv('POSTGRES_DB', 'lab_analytics')
        self.user = os.getenv('POSTGRES_USER', 'lab_user')
        self.password = os.getenv('POSTGRES_PASSWORD', 'lab_password')
        self.pool = None
    
    async def connect(self):
        """Crear pool de conexiones"""
        try:
            self.pool = await asyncpg.create_pool(
                host=self.host,
                port=self.port,
                database=self.database,
                user=self.user,
                password=self.password,
                min_size=1,
                max_size=10
            )
            logger.info("Conexión a PostgreSQL establecida")
        except Exception as e:
            logger.error(f"Error conectando a PostgreSQL: {e}")
            raise
    
    async def disconnect(self):
        """Cerrar pool de conexiones"""
        if self.pool:
            await self.pool.close()
            logger.info("Conexión a PostgreSQL cerrada")
    
    async def save_measurements(self, measurements: List[Dict[str, Any]]) -> bool:
        """Guardar mediciones del laboratorio"""
        try:
            async with self.pool.acquire() as conn:
                # Crear tabla si no existe
                await conn.execute("""
                    CREATE TABLE IF NOT EXISTS mediciones_lab (
                        id SERIAL PRIMARY KEY,
                        timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        equipo VARCHAR(100),
                        parametro VARCHAR(100),
                        valor DECIMAL(10,4),
                        unidad VARCHAR(20),
                        operador VARCHAR(100),
                        lote VARCHAR(50),
                        observaciones TEXT
                    )
                """)
                
                # Insertar mediciones
                for measurement in measurements:
                    await conn.execute("""
                        INSERT INTO mediciones_lab 
                        (equipo, parametro, valor, unidad, operador, lote, observaciones)
                        VALUES ($1, $2, $3, $4, $5, $6, $7)
                    """, 
                    measurement.get('equipo'),
                    measurement.get('parametro'),
                    measurement.get('valor'),
                    measurement.get('unidad'),
                    measurement.get('operador'),
                    measurement.get('lote'),
                    measurement.get('observaciones')
                    )
                
                logger.info(f"Guardadas {len(measurements)} mediciones")
                return True
                
        except Exception as e:
            logger.error(f"Error guardando mediciones: {e}")
            return False
    
    async def get_measurements(self, 
                             date_from: Optional[datetime] = None,
                             date_to: Optional[datetime] = None,
                             equipment: Optional[str] = None) -> List[Dict[str, Any]]:
        """Obtener mediciones con filtros"""
        try:
            async with self.pool.acquire() as conn:
                query = "SELECT * FROM mediciones_lab WHERE 1=1"
                params = []
                
                if date_from:
                    query += " AND timestamp >= $" + str(len(params) + 1)
                    params.append(date_from)
                
                if date_to:
                    query += " AND timestamp <= $" + str(len(params) + 1)
                    params.append(date_to)
                
                if equipment:
                    query += " AND equipo = $" + str(len(params) + 1)
                    params.append(equipment)
                
                query += " ORDER BY timestamp DESC"
                
                rows = await conn.fetch(query, *params)
                return [dict(row) for row in rows]
                
        except Exception as e:
            logger.error(f"Error obteniendo mediciones: {e}")
            return []
    
    async def get_summary_stats(self) -> Dict[str, Any]:
        """Obtener estadísticas resumen"""
        try:
            async with self.pool.acquire() as conn:
                # Total de mediciones
                total = await conn.fetchval("SELECT COUNT(*) FROM mediciones_lab")
                
                # Mediciones por equipo
                equipment_stats = await conn.fetch("""
                    SELECT equipo, COUNT(*) as cantidad 
                    FROM mediciones_lab 
                    GROUP BY equipo 
                    ORDER BY cantidad DESC
                """)
                
                # Últimas mediciones
                latest = await conn.fetch("""
                    SELECT * FROM mediciones_lab 
                    ORDER BY timestamp DESC 
                    LIMIT 10
                """)
                
                return {
                    'total_measurements': total,
                    'equipment_stats': [dict(row) for row in equipment_stats],
                    'latest_measurements': [dict(row) for row in latest]
                }
                
        except Exception as e:
            logger.error(f"Error obteniendo estadísticas: {e}")
            return {}

    async def get_data_summary(self) -> Dict[str, Any]:
        """Obtener resumen de datos del laboratorio"""
        try:
            async with self.pool.acquire() as conn:
                # Estadísticas de equipos
                equipment_count = await conn.fetchval("SELECT COUNT(*) FROM equipment")
                equipment_list = await conn.fetch("SELECT id, name, type FROM equipment ORDER BY name")
                
                # Estadísticas de muestras
                samples_count = await conn.fetchval("SELECT COUNT(*) FROM samples")
                samples_recent = await conn.fetch("""
                    SELECT sample_code, sample_type, collection_date, status 
                    FROM samples 
                    ORDER BY collection_date DESC 
                    LIMIT 5
                """)
                
                # Estadísticas de análisis
                analyses_count = await conn.fetchval("SELECT COUNT(*) FROM analyses")
                analyses_by_parameter = await conn.fetch("""
                    SELECT parameter, COUNT(*) as count, AVG(result_value) as avg_value
                    FROM analyses 
                    WHERE result_value IS NOT NULL
                    GROUP BY parameter 
                    ORDER BY count DESC
                """)
                
                # Análisis recientes
                recent_analyses = await conn.fetch("""
                    SELECT a.parameter, a.result_value, a.result_unit, 
                           s.sample_code, e.name as equipment_name, a.analysis_date
                    FROM analyses a
                    JOIN samples s ON a.sample_id = s.id
                    JOIN equipment e ON a.equipment_id = e.id
                    ORDER BY a.analysis_date DESC
                    LIMIT 10
                """)
                
                return {
                    'equipment': {
                        'total': equipment_count,
                        'list': [dict(row) for row in equipment_list]
                    },
                    'samples': {
                        'total': samples_count,
                        'recent': [dict(row) for row in samples_recent]
                    },
                    'analyses': {
                        'total': analyses_count,
                        'by_parameter': [dict(row) for row in analyses_by_parameter],
                        'recent': [dict(row) for row in recent_analyses]
                    },
                    'timestamp': datetime.now().isoformat()
                }
                
        except Exception as e:
            logger.error(f"Error obteniendo resumen de datos: {e}")
            return {}

    async def initialize(self):
        """Inicializar conexión a la base de datos"""
        await self.connect()

    async def check_connection(self) -> bool:
        """Verificar conexión a la base de datos"""
        try:
            if not self.pool:
                return False
            async with self.pool.acquire() as conn:
                await conn.fetchval("SELECT 1")
                return True
        except Exception as e:
            logger.error(f"Error verificando conexión: {e}")
            return False