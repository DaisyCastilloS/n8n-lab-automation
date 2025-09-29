#!/usr/bin/env python3
"""
Script para convertir el CSV limpio a formato JSON para n8n
"""

import pandas as pd
import json
from datetime import datetime
import os

def convert_csv_to_json():
    """Convertir CSV limpio a JSON"""
    
    # Rutas de archivos
    csv_path = "/tmp/produccion_limpia_final.csv"
    json_path = "/tmp/produccion_limpia_final.json"
    
    try:
        print(f"Leyendo CSV desde: {csv_path}")
        
        # Leer el CSV
        df = pd.read_csv(csv_path)
        
        print(f"CSV leído exitosamente. Filas: {len(df)}, Columnas: {len(df.columns)}")
        print(f"Columnas: {list(df.columns)}")
        
        # Convertir a JSON con formato legible
        json_data = {
            "metadata": {
                "source": "produccion_limpia_final.csv",
                "converted_at": datetime.now().isoformat(),
                "total_records": len(df),
                "columns": list(df.columns)
            },
            "data": df.to_dict('records')
        }
        
        # Guardar como JSON
        with open(json_path, 'w', encoding='utf-8') as f:
            json.dump(json_data, f, indent=2, ensure_ascii=False, default=str)
        
        print(f"✅ JSON creado exitosamente en: {json_path}")
        print(f"Total de registros convertidos: {len(df)}")
        
        # Mostrar una muestra de los datos
        print("\n📋 Muestra de los primeros 3 registros:")
        for i, record in enumerate(json_data["data"][:3]):
            print(f"  Registro {i+1}: {record}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error durante la conversión: {str(e)}")
        return False

if __name__ == "__main__":
    success = convert_csv_to_json()
    exit(0 if success else 1)