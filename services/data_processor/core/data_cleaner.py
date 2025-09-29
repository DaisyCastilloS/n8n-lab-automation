"""
Módulo de Limpieza de Datos del Laboratorio Químico
Extrae y modulariza la lógica del notebook original
"""

import pandas as pd
import unicodedata
from datetime import datetime
from typing import Optional, Dict, Any
from loguru import logger


class DataCleaner:
    """Clase para limpiar y normalizar datos del laboratorio"""
    
    def __init__(self):
        self.date_formats = [
            '%d/%m/%Y',  # 17/02/2024
            '%Y-%m-%d',  # 2023-10-13
            '%m-%d-%Y',  # 11-26-2024
            '%d-%m-%Y',  # 17-02-2024
        ]
        
        # Mapeo de equipos para normalización
        self.equipment_mapping = {
            'phmetro': 'phmetro',
            'ph metro': 'phmetro',
            'ph-metro': 'phmetro',
            'espectrofotometro': 'espectrofotometro',
            'espectrofotómetro': 'espectrofotometro',
            'centrifuga': 'centrifuga',
            'centrífuga': 'centrifuga',
            'microscopio': 'microscopio',
            'balanza': 'balanza',
            'autoclave': 'autoclave'
        }
        
        # Mapeo de turnos
        self.shift_mapping = {
            'mañana': 'manana',
            'manana': 'manana',
            'tarde': 'tarde',
            'noche': 'noche',
            'madrugada': 'noche'
        }
    
    def clean_data(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Limpia completamente el DataFrame de datos del laboratorio
        
        Args:
            df: DataFrame con datos sucios
            
        Returns:
            DataFrame limpio y normalizado
        """
        logger.info(f"Iniciando limpieza de datos. Registros originales: {len(df)}")
        
        # Crear copia para no modificar el original
        cleaned_df = df.copy()
        
        # Limpiar fechas
        cleaned_df = self._clean_dates(cleaned_df)
        
        # Limpiar equipos
        cleaned_df = self._clean_equipment(cleaned_df)
        
        # Limpiar turnos
        cleaned_df = self._clean_shifts(cleaned_df)
        
        # Limpiar valores numéricos
        cleaned_df = self._clean_numeric_values(cleaned_df)
        
        # Limpiar comentarios
        cleaned_df = self._clean_comments(cleaned_df)
        
        # Validar datos
        cleaned_df = self._validate_data(cleaned_df)
        
        logger.info(f"Limpieza completada. Registros finales: {len(cleaned_df)}")
        
        return cleaned_df
    
    def _clean_dates(self, df: pd.DataFrame) -> pd.DataFrame:
        """Limpia y normaliza las fechas"""
        if 'fecha' not in df.columns:
            return df
        
        logger.info("Limpiando fechas...")
        
        # Guardar fecha original
        df['fecha_original'] = df['fecha'].copy()
        
        # Limpiar y parsear fechas
        df['fecha'] = df['fecha'].apply(self._parse_date_safe)
        
        # Convertir a formato ISO string
        df['fecha'] = df['fecha'].dt.strftime('%Y-%m-%d')
        
        # Contar fechas inválidas
        invalid_dates = df['fecha'].isna().sum()
        if invalid_dates > 0:
            logger.warning(f"Se encontraron {invalid_dates} fechas inválidas")
        
        return df
    
    def _parse_date_safe(self, date_str: Any) -> Optional[datetime]:
        """
        Parsea fechas de múltiples formatos de forma segura
        
        Args:
            date_str: String de fecha en cualquier formato
            
        Returns:
            Objeto datetime o NaT si no se puede parsear
        """
        if pd.isna(date_str):
            return pd.NaT
        
        # Limpiar string
        date_str = str(date_str).strip().replace(' ', '')
        
        # Intentar cada formato
        for fmt in self.date_formats:
            try:
                return datetime.strptime(date_str, fmt)
            except ValueError:
                continue
        
        logger.warning(f"No se pudo parsear la fecha: {date_str}")
        return pd.NaT
    
    def _clean_equipment(self, df: pd.DataFrame) -> pd.DataFrame:
        """Limpia y normaliza nombres de equipos"""
        if 'equipo' not in df.columns:
            return df
        
        logger.info("Limpiando equipos...")
        
        # Guardar equipo original
        df['equipo_original'] = df['equipo'].copy()
        
        # Limpiar texto
        df['equipo'] = df['equipo'].apply(self._clean_text)
        
        # Aplicar mapeo de equipos
        df['equipo'] = df['equipo'].map(self.equipment_mapping).fillna(df['equipo'])
        
        return df
    
    def _clean_shifts(self, df: pd.DataFrame) -> pd.DataFrame:
        """Limpia y normaliza turnos"""
        if 'turno' not in df.columns:
            return df
        
        logger.info("Limpiando turnos...")
        
        # Guardar turno original
        df['turno_original'] = df['turno'].copy()
        
        # Limpiar texto
        df['turno'] = df['turno'].apply(self._clean_text)
        
        # Aplicar mapeo de turnos
        df['turno'] = df['turno'].map(self.shift_mapping).fillna(df['turno'])
        
        return df
    
    def _clean_text(self, text: Any) -> str:
        """
        Limpia texto: minúsculas, sin espacios, sin tildes
        
        Args:
            text: Texto a limpiar
            
        Returns:
            Texto limpio
        """
        if pd.isna(text):
            return text
        
        # Convertir a string y limpiar
        text = str(text).lower().strip()
        
        # Remover tildes y caracteres especiales
        text = ''.join(
            c for c in unicodedata.normalize('NFD', text)
            if unicodedata.category(c) != 'Mn'
        )
        
        return text
    
    def _clean_numeric_values(self, df: pd.DataFrame) -> pd.DataFrame:
        """Limpia valores numéricos"""
        logger.info("Limpiando valores numéricos...")
        
        # Limpiar muestras procesadas
        if 'muestras_procesadas' in df.columns:
            df['muestras_procesadas'] = pd.to_numeric(
                df['muestras_procesadas'], 
                errors='coerce'
            )
        
        # Limpiar rendimiento
        if 'rendimiento' in df.columns:
            df['rendimiento'] = pd.to_numeric(
                df['rendimiento'], 
                errors='coerce'
            )
            
            # Validar rango de rendimiento (0-100%)
            invalid_performance = (
                (df['rendimiento'] < 0) | 
                (df['rendimiento'] > 100)
            ).sum()
            
            if invalid_performance > 0:
                logger.warning(f"Se encontraron {invalid_performance} valores de rendimiento fuera del rango 0-100%")
        
        return df
    
    def _clean_comments(self, df: pd.DataFrame) -> pd.DataFrame:
        """Limpia comentarios"""
        if 'comentario' not in df.columns:
            return df
        
        logger.info("Limpiando comentarios...")
        
        # Normalizar comentarios
        df['comentario'] = df['comentario'].apply(
            lambda x: self._clean_text(x) if pd.notna(x) else x
        )
        
        # Mapear comentarios comunes
        comment_mapping = {
            'ok': 'ok',
            'bien': 'ok',
            'normal': 'ok',
            'error': 'error',
            'fallo': 'error',
            'problema': 'error',
            'mantenimiento': 'mantenimiento',
            'calibracion': 'calibracion'
        }
        
        df['comentario'] = df['comentario'].map(comment_mapping).fillna(df['comentario'])
        
        return df
    
    def _validate_data(self, df: pd.DataFrame) -> pd.DataFrame:
        """Valida y filtra datos inconsistentes"""
        logger.info("Validando datos...")
        
        initial_count = len(df)
        
        # Remover filas con fecha inválida
        df = df.dropna(subset=['fecha'])
        
        # Remover filas sin equipo
        if 'equipo' in df.columns:
            df = df.dropna(subset=['equipo'])
        
        # Remover filas sin turno
        if 'turno' in df.columns:
            df = df.dropna(subset=['turno'])
        
        # Log de registros removidos
        removed_count = initial_count - len(df)
        if removed_count > 0:
            logger.warning(f"Se removieron {removed_count} registros inválidos")
        
        return df
    
    def get_cleaning_report(self, original_df: pd.DataFrame, cleaned_df: pd.DataFrame) -> Dict[str, Any]:
        """
        Genera reporte de limpieza
        
        Args:
            original_df: DataFrame original
            cleaned_df: DataFrame limpio
            
        Returns:
            Diccionario con estadísticas de limpieza
        """
        return {
            "original_records": len(original_df),
            "cleaned_records": len(cleaned_df),
            "records_removed": len(original_df) - len(cleaned_df),
            "removal_percentage": ((len(original_df) - len(cleaned_df)) / len(original_df)) * 100,
            "columns_processed": list(cleaned_df.columns),
            "unique_equipment": cleaned_df['equipo'].nunique() if 'equipo' in cleaned_df.columns else 0,
            "unique_shifts": cleaned_df['turno'].nunique() if 'turno' in cleaned_df.columns else 0,
            "date_range": {
                "start": cleaned_df['fecha'].min() if 'fecha' in cleaned_df.columns else None,
                "end": cleaned_df['fecha'].max() if 'fecha' in cleaned_df.columns else None
            }
        }