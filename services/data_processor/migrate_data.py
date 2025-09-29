#!/usr/bin/env python3
"""
Script para migrar datos limpios del CSV a PostgreSQL
"""

import pandas as pd
import psycopg2
from psycopg2.extras import RealDictCursor
import uuid
from datetime import datetime
import os
import sys

# Configuración de la base de datos (extrayendo de DATABASE_URL)
import re

def parse_database_url():
    """Parsear DATABASE_URL para obtener configuración de DB"""
    database_url = os.getenv('DATABASE_URL', 'postgresql://lab_user:lab_password@postgres:5432/lab_analytics')
    
    # Parsear URL: postgresql://user:password@host:port/database
    pattern = r'postgresql://([^:]+):([^@]+)@([^:]+):(\d+)/(.+)'
    match = re.match(pattern, database_url)
    
    if match:
        user, password, host, port, database = match.groups()
        return {
            'host': host,
            'port': int(port),
            'database': database,
            'user': user,
            'password': password
        }
    else:
        # Fallback a valores por defecto
        return {
            'host': 'postgres',
            'port': 5432,
            'database': 'lab_analytics',
            'user': 'lab_user',
            'password': 'lab_password'
        }

DB_CONFIG = parse_database_url()

def connect_to_db():
    """Conectar a la base de datos PostgreSQL"""
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        return conn
    except Exception as e:
        print(f"Error conectando a la base de datos: {e}")
        return None

def load_csv_data(csv_path):
    """Cargar datos del archivo CSV"""
    try:
        df = pd.read_csv(csv_path)
        print(f"Datos cargados: {len(df)} registros")
        return df
    except Exception as e:
        print(f"Error cargando CSV: {e}")
        return None

def insert_equipment(conn, equipment_list):
    """Insertar equipos únicos en la tabla equipment"""
    cursor = conn.cursor()
    
    # Mapeo de nombres de equipos
    equipment_mapping = {
        'phmetro': 'pH Metro',
        'centrifuga': 'Centrífuga',
        'espectrofotometro': 'Espectrofotómetro',
        'analizador hematologico': 'Analizador Hematológico'
    }
    
    equipment_ids = {}
    
    for equipo in equipment_list:
        equipo_clean = equipo.lower().strip()
        equipo_name = equipment_mapping.get(equipo_clean, equipo.title())
        
        # Verificar si el equipo ya existe
        cursor.execute("""
            SELECT id FROM equipment WHERE LOWER(name) = LOWER(%s)
        """, (equipo_name,))
        
        result = cursor.fetchone()
        if result:
            equipment_ids[equipo] = result[0]
            print(f"Equipo existente: {equipo_name}")
        else:
            # Insertar nuevo equipo
            equipment_id = str(uuid.uuid4())
            cursor.execute("""
                INSERT INTO equipment (id, name, type, status, location, created_at)
                VALUES (%s, %s, %s, %s, %s, %s)
            """, (
                equipment_id,
                equipo_name,
                equipo_name.split()[0],  # Tipo basado en la primera palabra
                'active',
                'Lab Principal',
                datetime.now()
            ))
            equipment_ids[equipo] = equipment_id
            print(f"Equipo insertado: {equipo_name}")
    
    conn.commit()
    return equipment_ids

def insert_samples_and_analyses(conn, df, equipment_ids):
    """Insertar muestras y análisis basados en los datos del CSV"""
    cursor = conn.cursor()
    
    for index, row in df.iterrows():
        try:
            # Crear muestra
            sample_id = str(uuid.uuid4())
            sample_code = f"PROD-{row['fecha'].replace('-', '')}-{index+1:03d}"
            
            cursor.execute("""
                INSERT INTO samples (id, sample_code, sample_type, collection_date, 
                                   received_date, status, description, created_at)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            """, (
                sample_id,
                sample_code,
                'Producción',
                row['fecha'],
                row['fecha'],
                'completed' if row['comentario'] == 'ok' else 'pending',
                f"Análisis de producción - Turno {row['turno']}",
                datetime.now()
            ))
            
            # Crear análisis
            analysis_id = str(uuid.uuid4())
            equipment_id = equipment_ids.get(row['equipo'])
            
            # Determinar estado del análisis
            status = 'completed'
            if row['comentario'] == 'repetir':
                status = 'pending'
            elif row['comentario'] == 'sin_comentario':
                status = 'completed'
            
            cursor.execute("""
                INSERT INTO analyses (id, sample_id, equipment_id, analysis_type, 
                                    parameter, result_value, result_unit, status,
                                    analyst_name, analysis_date, comments, created_at)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """, (
                analysis_id,
                sample_id,
                equipment_id,
                'Rendimiento de Producción',
                'Rendimiento',
                float(row['rendimiento']),
                '%',
                status,
                f"Operador Turno {row['turno'].title()}",
                datetime.strptime(row['fecha'], '%Y-%m-%d'),
                row['comentario'] if row['comentario'] != 'sin_comentario' else None,
                datetime.now()
            ))
            
            # Insertar información adicional sobre muestras procesadas
            if pd.notna(row['muestras_procesadas']):
                analysis_id_2 = str(uuid.uuid4())
                cursor.execute("""
                    INSERT INTO analyses (id, sample_id, equipment_id, analysis_type, 
                                        parameter, result_value, result_unit, status,
                                        analyst_name, analysis_date, comments, created_at)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                """, (
                    analysis_id_2,
                    sample_id,
                    equipment_id,
                    'Productividad',
                    'Muestras Procesadas',
                    int(row['muestras_procesadas']),
                    'unidades',
                    status,
                    f"Operador Turno {row['turno'].title()}",
                    datetime.strptime(row['fecha'], '%Y-%m-%d'),
                    f"Turno: {row['turno']}",
                    datetime.now()
                ))
            
            if (index + 1) % 10 == 0:
                print(f"Procesados {index + 1} registros...")
                
        except Exception as e:
            print(f"Error procesando fila {index}: {e}")
            continue
    
    conn.commit()
    print(f"Migración completada: {len(df)} registros procesados")

def verify_migration(conn):
    """Verificar que los datos se migraron correctamente"""
    cursor = conn.cursor(cursor_factory=RealDictCursor)
    
    # Contar registros
    cursor.execute("SELECT COUNT(*) as count FROM equipment WHERE created_at > NOW() - INTERVAL '1 hour'")
    equipment_count = cursor.fetchone()['count']
    
    cursor.execute("SELECT COUNT(*) as count FROM samples WHERE created_at > NOW() - INTERVAL '1 hour'")
    samples_count = cursor.fetchone()['count']
    
    cursor.execute("SELECT COUNT(*) as count FROM analyses WHERE created_at > NOW() - INTERVAL '1 hour'")
    analyses_count = cursor.fetchone()['count']
    
    print(f"\n=== VERIFICACIÓN DE MIGRACIÓN ===")
    print(f"Equipos insertados: {equipment_count}")
    print(f"Muestras insertadas: {samples_count}")
    print(f"Análisis insertados: {analyses_count}")
    
    # Mostrar algunos ejemplos
    cursor.execute("""
        SELECT s.sample_code, e.name as equipment, a.parameter, a.result_value, a.result_unit
        FROM analyses a
        JOIN samples s ON a.sample_id = s.id
        JOIN equipment e ON a.equipment_id = e.id
        WHERE a.created_at > NOW() - INTERVAL '1 hour'
        LIMIT 5
    """)
    
    examples = cursor.fetchall()
    print(f"\n=== EJEMPLOS DE DATOS MIGRADOS ===")
    for example in examples:
        print(f"Muestra: {example['sample_code']} | Equipo: {example['equipment']} | "
              f"{example['parameter']}: {example['result_value']} {example['result_unit']}")

def main():
    """Función principal"""
    print("=== MIGRACIÓN DE DATOS LIMPIOS A POSTGRESQL ===")
    
    # Ruta del archivo CSV (montado en el contenedor)
    csv_path = "/app/data/produccion_limpia_final.csv"
    
    if not os.path.exists(csv_path):
        print(f"Error: No se encontró el archivo CSV en {csv_path}")
        sys.exit(1)
    
    # Cargar datos
    df = load_csv_data(csv_path)
    if df is None:
        sys.exit(1)
    
    # Conectar a la base de datos
    conn = connect_to_db()
    if conn is None:
        sys.exit(1)
    
    try:
        # Obtener lista única de equipos
        equipment_list = df['equipo'].unique().tolist()
        print(f"Equipos únicos encontrados: {equipment_list}")
        
        # Insertar equipos
        print("\n1. Insertando equipos...")
        equipment_ids = insert_equipment(conn, equipment_list)
        
        # Insertar muestras y análisis
        print("\n2. Insertando muestras y análisis...")
        insert_samples_and_analyses(conn, df, equipment_ids)
        
        # Verificar migración
        print("\n3. Verificando migración...")
        verify_migration(conn)
        
        print("\n✅ Migración completada exitosamente!")
        
    except Exception as e:
        print(f"Error durante la migración: {e}")
        conn.rollback()
    finally:
        conn.close()

if __name__ == "__main__":
    main()