"""
Módulo de Análisis de Datos del Laboratorio Químico
Genera métricas, estadísticas y detecta anomalías
"""

import pandas as pd
import numpy as np
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
from loguru import logger
import matplotlib.pyplot as plt
import seaborn as sns
import io
import base64


class DataAnalyzer:
    """Clase para análisis estadístico de datos del laboratorio"""
    
    def __init__(self):
        self.performance_thresholds = {
            'low': 60.0,      # Rendimiento bajo
            'medium': 80.0,   # Rendimiento medio
            'high': 95.0      # Rendimiento alto
        }
        
        self.sample_thresholds = {
            'low': 20,        # Pocas muestras
            'medium': 50,     # Muestras normales
            'high': 100       # Muchas muestras
        }
    
    def perform_analysis(self, df: pd.DataFrame) -> Dict[str, Any]:
        """
        Realiza análisis completo de los datos
        
        Args:
            df: DataFrame con datos limpios
            
        Returns:
            Diccionario con resultados del análisis
        """
        logger.info(f"Iniciando análisis de {len(df)} registros")
        
        analysis = {
            "summary": self._get_basic_summary(df),
            "performance_analysis": self._analyze_performance(df),
            "equipment_analysis": self._analyze_equipment(df),
            "shift_analysis": self._analyze_shifts(df),
            "temporal_analysis": self._analyze_temporal_patterns(df),
            "anomalies": self._detect_anomalies(df),
            "quality_metrics": self._calculate_quality_metrics(df),
            "recommendations": self._generate_recommendations(df)
        }
        
        logger.info("Análisis completado")
        return analysis
    
    def _get_basic_summary(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Genera resumen básico de los datos"""
        summary = {
            "total_records": len(df),
            "date_range": {
                "start": df['fecha'].min() if 'fecha' in df.columns else None,
                "end": df['fecha'].max() if 'fecha' in df.columns else None,
                "days_covered": None
            },
            "columns": list(df.columns),
            "missing_values": df.isnull().sum().to_dict()
        }
        
        # Calcular días cubiertos
        if 'fecha' in df.columns and summary["date_range"]["start"]:
            start_date = pd.to_datetime(summary["date_range"]["start"])
            end_date = pd.to_datetime(summary["date_range"]["end"])
            summary["date_range"]["days_covered"] = (end_date - start_date).days + 1
        
        return summary
    
    def _analyze_performance(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Analiza métricas de rendimiento"""
        if 'rendimiento' not in df.columns:
            return {"error": "Columna 'rendimiento' no encontrada"}
        
        performance_data = df['rendimiento'].dropna()
        
        analysis = {
            "statistics": {
                "mean": float(performance_data.mean()),
                "median": float(performance_data.median()),
                "std": float(performance_data.std()),
                "min": float(performance_data.min()),
                "max": float(performance_data.max()),
                "q25": float(performance_data.quantile(0.25)),
                "q75": float(performance_data.quantile(0.75))
            },
            "distribution": {
                "low_performance": len(performance_data[performance_data < self.performance_thresholds['low']]),
                "medium_performance": len(performance_data[
                    (performance_data >= self.performance_thresholds['low']) & 
                    (performance_data < self.performance_thresholds['medium'])
                ]),
                "high_performance": len(performance_data[performance_data >= self.performance_thresholds['medium']])
            },
            "trends": self._calculate_performance_trends(df)
        }
        
        # Calcular porcentajes
        total = len(performance_data)
        if total > 0:
            analysis["distribution_percentage"] = {
                "low": (analysis["distribution"]["low_performance"] / total) * 100,
                "medium": (analysis["distribution"]["medium_performance"] / total) * 100,
                "high": (analysis["distribution"]["high_performance"] / total) * 100
            }
        
        return analysis
    
    def _analyze_equipment(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Analiza rendimiento por equipo"""
        if 'equipo' not in df.columns:
            return {"error": "Columna 'equipo' no encontrada"}
        
        equipment_stats = {}
        
        for equipment in df['equipo'].unique():
            if pd.isna(equipment):
                continue
                
            equipment_data = df[df['equipo'] == equipment]
            
            stats = {
                "total_records": len(equipment_data),
                "usage_percentage": (len(equipment_data) / len(df)) * 100
            }
            
            # Estadísticas de rendimiento si existe la columna
            if 'rendimiento' in df.columns:
                perf_data = equipment_data['rendimiento'].dropna()
                if len(perf_data) > 0:
                    stats.update({
                        "avg_performance": float(perf_data.mean()),
                        "performance_std": float(perf_data.std()),
                        "min_performance": float(perf_data.min()),
                        "max_performance": float(perf_data.max())
                    })
            
            # Estadísticas de muestras si existe la columna
            if 'muestras_procesadas' in df.columns:
                sample_data = equipment_data['muestras_procesadas'].dropna()
                if len(sample_data) > 0:
                    stats.update({
                        "avg_samples": float(sample_data.mean()),
                        "total_samples": float(sample_data.sum()),
                        "samples_std": float(sample_data.std())
                    })
            
            equipment_stats[equipment] = stats
        
        # Ranking de equipos por rendimiento
        if 'rendimiento' in df.columns:
            equipment_ranking = []
            for eq, stats in equipment_stats.items():
                if 'avg_performance' in stats:
                    equipment_ranking.append({
                        "equipment": eq,
                        "avg_performance": stats['avg_performance'],
                        "total_records": stats['total_records']
                    })
            
            equipment_ranking.sort(key=lambda x: x['avg_performance'], reverse=True)
        else:
            equipment_ranking = []
        
        return {
            "equipment_stats": equipment_stats,
            "equipment_ranking": equipment_ranking,
            "total_equipment": len(equipment_stats)
        }
    
    def _analyze_shifts(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Analiza rendimiento por turno"""
        if 'turno' not in df.columns:
            return {"error": "Columna 'turno' no encontrada"}
        
        shift_stats = {}
        
        for shift in df['turno'].unique():
            if pd.isna(shift):
                continue
                
            shift_data = df[df['turno'] == shift]
            
            stats = {
                "total_records": len(shift_data),
                "usage_percentage": (len(shift_data) / len(df)) * 100
            }
            
            # Estadísticas de rendimiento
            if 'rendimiento' in df.columns:
                perf_data = shift_data['rendimiento'].dropna()
                if len(perf_data) > 0:
                    stats.update({
                        "avg_performance": float(perf_data.mean()),
                        "performance_std": float(perf_data.std()),
                        "min_performance": float(perf_data.min()),
                        "max_performance": float(perf_data.max())
                    })
            
            shift_stats[shift] = stats
        
        return {
            "shift_stats": shift_stats,
            "best_shift": max(shift_stats.items(), 
                            key=lambda x: x[1].get('avg_performance', 0))[0] if shift_stats else None
        }
    
    def _analyze_temporal_patterns(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Analiza patrones temporales"""
        if 'fecha' not in df.columns:
            return {"error": "Columna 'fecha' no encontrada"}
        
        # Convertir fechas
        df_temp = df.copy()
        df_temp['fecha'] = pd.to_datetime(df_temp['fecha'])
        df_temp['day_of_week'] = df_temp['fecha'].dt.day_name()
        df_temp['month'] = df_temp['fecha'].dt.month
        df_temp['week'] = df_temp['fecha'].dt.isocalendar().week
        
        analysis = {
            "daily_patterns": self._analyze_daily_patterns(df_temp),
            "weekly_patterns": self._analyze_weekly_patterns(df_temp),
            "monthly_patterns": self._analyze_monthly_patterns(df_temp)
        }
        
        return analysis
    
    def _analyze_daily_patterns(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Analiza patrones diarios"""
        daily_stats = df.groupby('day_of_week').agg({
            'rendimiento': ['count', 'mean', 'std'] if 'rendimiento' in df.columns else 'count',
            'muestras_procesadas': ['sum', 'mean'] if 'muestras_procesadas' in df.columns else 'count'
        }).round(2)
        
        return daily_stats.to_dict() if not daily_stats.empty else {}
    
    def _analyze_weekly_patterns(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Analiza patrones semanales"""
        weekly_stats = df.groupby('week').agg({
            'rendimiento': ['count', 'mean'] if 'rendimiento' in df.columns else 'count',
            'muestras_procesadas': 'sum' if 'muestras_procesadas' in df.columns else 'count'
        }).round(2)
        
        return weekly_stats.to_dict() if not weekly_stats.empty else {}
    
    def _analyze_monthly_patterns(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Analiza patrones mensuales"""
        monthly_stats = df.groupby('month').agg({
            'rendimiento': ['count', 'mean'] if 'rendimiento' in df.columns else 'count',
            'muestras_procesadas': 'sum' if 'muestras_procesadas' in df.columns else 'count'
        }).round(2)
        
        return monthly_stats.to_dict() if not monthly_stats.empty else {}
    
    def _detect_anomalies(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Detecta anomalías en los datos"""
        anomalies = {
            "performance_anomalies": [],
            "sample_anomalies": [],
            "temporal_anomalies": []
        }
        
        # Anomalías de rendimiento
        if 'rendimiento' in df.columns:
            perf_data = df['rendimiento'].dropna()
            if len(perf_data) > 0:
                # Usar IQR para detectar outliers
                Q1 = perf_data.quantile(0.25)
                Q3 = perf_data.quantile(0.75)
                IQR = Q3 - Q1
                lower_bound = Q1 - 1.5 * IQR
                upper_bound = Q3 + 1.5 * IQR
                
                outliers = df[
                    (df['rendimiento'] < lower_bound) | 
                    (df['rendimiento'] > upper_bound)
                ]
                
                anomalies["performance_anomalies"] = [
                    {
                        "index": int(idx),
                        "fecha": row['fecha'] if 'fecha' in row else None,
                        "equipo": row['equipo'] if 'equipo' in row else None,
                        "rendimiento": float(row['rendimiento']),
                        "type": "low" if row['rendimiento'] < lower_bound else "high"
                    }
                    for idx, row in outliers.iterrows()
                ]
        
        # Anomalías de muestras
        if 'muestras_procesadas' in df.columns:
            sample_data = df['muestras_procesadas'].dropna()
            if len(sample_data) > 0:
                # Detectar valores extremadamente altos o bajos
                mean_samples = sample_data.mean()
                std_samples = sample_data.std()
                
                extreme_samples = df[
                    (df['muestras_procesadas'] > mean_samples + 3 * std_samples) |
                    (df['muestras_procesadas'] < max(0, mean_samples - 3 * std_samples))
                ]
                
                anomalies["sample_anomalies"] = [
                    {
                        "index": int(idx),
                        "fecha": row['fecha'] if 'fecha' in row else None,
                        "equipo": row['equipo'] if 'equipo' in row else None,
                        "muestras_procesadas": float(row['muestras_procesadas']),
                        "expected_range": f"{mean_samples - 2*std_samples:.1f} - {mean_samples + 2*std_samples:.1f}"
                    }
                    for idx, row in extreme_samples.iterrows()
                ]
        
        return anomalies
    
    def _calculate_performance_trends(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Calcula tendencias de rendimiento"""
        if 'fecha' not in df.columns or 'rendimiento' not in df.columns:
            return {}
        
        # Agrupar por fecha y calcular promedio diario
        df_temp = df.copy()
        df_temp['fecha'] = pd.to_datetime(df_temp['fecha'])
        daily_performance = df_temp.groupby('fecha')['rendimiento'].mean()
        
        if len(daily_performance) < 2:
            return {"trend": "insufficient_data"}
        
        # Calcular tendencia simple
        x = np.arange(len(daily_performance))
        y = daily_performance.values
        
        # Regresión lineal simple
        slope = np.polyfit(x, y, 1)[0]
        
        trend_analysis = {
            "slope": float(slope),
            "trend_direction": "increasing" if slope > 0.1 else "decreasing" if slope < -0.1 else "stable",
            "daily_avg_performance": daily_performance.to_dict(),
            "performance_volatility": float(daily_performance.std())
        }
        
        return trend_analysis
    
    def _calculate_quality_metrics(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Calcula métricas de calidad de datos"""
        metrics = {
            "completeness": {},
            "consistency": {},
            "accuracy": {}
        }
        
        # Completitud (porcentaje de valores no nulos)
        for col in df.columns:
            non_null_count = df[col].notna().sum()
            metrics["completeness"][col] = (non_null_count / len(df)) * 100
        
        # Consistencia (valores únicos vs total)
        for col in df.select_dtypes(include=['object']).columns:
            unique_count = df[col].nunique()
            metrics["consistency"][col] = {
                "unique_values": unique_count,
                "uniqueness_ratio": (unique_count / len(df)) * 100
            }
        
        return metrics
    
    def _generate_recommendations(self, df: pd.DataFrame) -> List[Dict[str, Any]]:
        """Genera recomendaciones basadas en el análisis"""
        recommendations = []
        
        # Recomendaciones de rendimiento
        if 'rendimiento' in df.columns:
            avg_performance = df['rendimiento'].mean()
            
            if avg_performance < self.performance_thresholds['medium']:
                recommendations.append({
                    "type": "performance",
                    "priority": "high",
                    "title": "Rendimiento Bajo Detectado",
                    "description": f"El rendimiento promedio ({avg_performance:.1f}%) está por debajo del umbral recomendado ({self.performance_thresholds['medium']}%)",
                    "action": "Revisar procesos y equipos con bajo rendimiento"
                })
        
        # Recomendaciones de equipos
        if 'equipo' in df.columns and 'rendimiento' in df.columns:
            equipment_performance = df.groupby('equipo')['rendimiento'].mean()
            worst_equipment = equipment_performance.idxmin()
            worst_performance = equipment_performance.min()
            
            if worst_performance < self.performance_thresholds['low']:
                recommendations.append({
                    "type": "equipment",
                    "priority": "medium",
                    "title": f"Equipo con Bajo Rendimiento: {worst_equipment}",
                    "description": f"El equipo {worst_equipment} tiene un rendimiento promedio de {worst_performance:.1f}%",
                    "action": "Programar mantenimiento o calibración"
                })
        
        # Recomendaciones de datos faltantes
        missing_data = df.isnull().sum()
        high_missing = missing_data[missing_data > len(df) * 0.1]  # Más del 10% faltante
        
        for col in high_missing.index:
            recommendations.append({
                "type": "data_quality",
                "priority": "low",
                "title": f"Datos Faltantes en {col}",
                "description": f"La columna {col} tiene {high_missing[col]} valores faltantes ({(high_missing[col]/len(df)*100):.1f}%)",
                "action": "Revisar proceso de captura de datos"
            })
        
        return recommendations