"""
Servicio de Procesamiento de Datos del Laboratorio Químico
Automatización con n8n - Arquitectura Limpia
"""

from fastapi import FastAPI, HTTPException, UploadFile, File, BackgroundTasks
from fastapi.responses import JSONResponse, FileResponse
from pydantic import BaseModel
from typing import Optional, List, Dict, Any
import pandas as pd
import os
import uuid
from datetime import datetime
import asyncio
from loguru import logger

from core.data_cleaner import DataCleaner
from core.data_analyzer import DataAnalyzer
from core.database import DatabaseManager
from core.config import settings

# Configurar logging
logger.add("logs/data_processor.log", rotation="1 day", retention="30 days")

app = FastAPI(
    title="Lab Data Processor API",
    description="Servicio de procesamiento de datos del laboratorio químico",
    version="1.0.0"
)

# Inicializar componentes
data_cleaner = DataCleaner()
data_analyzer = DataAnalyzer()
db_manager = DatabaseManager()

# Modelos Pydantic
class ProcessingRequest(BaseModel):
    file_path: str
    processing_options: Optional[Dict[str, Any]] = {}
    output_format: Optional[str] = "csv"
    notify_webhook: Optional[str] = None

class ProcessingResponse(BaseModel):
    job_id: str
    status: str
    message: str
    file_path: Optional[str] = None
    processing_time: Optional[float] = None
    records_processed: Optional[int] = None

class AnalysisRequest(BaseModel):
    data_source: str  # 'file' o 'database'
    source_path: Optional[str] = None
    date_range: Optional[Dict[str, str]] = None
    equipment_filter: Optional[List[str]] = None

# Almacén de trabajos en memoria (en producción usar Redis)
processing_jobs = {}

@app.on_event("startup")
async def startup_event():
    """Inicializar servicios al arrancar"""
    logger.info("Iniciando servicio de procesamiento de datos")
    await db_manager.initialize()
    
    # Crear directorios necesarios
    os.makedirs("data/input", exist_ok=True)
    os.makedirs("data/output", exist_ok=True)
    os.makedirs("data/temp", exist_ok=True)

@app.get("/")
async def root():
    """Endpoint de salud"""
    return {
        "service": "Lab Data Processor",
        "status": "running",
        "version": "1.0.0",
        "timestamp": datetime.now().isoformat()
    }

@app.get("/health")
async def health_check():
    """Verificación de salud del servicio"""
    try:
        # Verificar conexión a base de datos
        db_status = await db_manager.check_connection()
        
        return {
            "status": "healthy",
            "database": "connected" if db_status else "disconnected",
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(f"Error en health check: {e}")
        raise HTTPException(status_code=503, detail="Service unhealthy")

@app.post("/process/upload", response_model=ProcessingResponse)
async def upload_and_process(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    processing_options: str = "{}"
):
    """Subir archivo y procesar en background"""
    try:
        # Generar ID único para el trabajo
        job_id = str(uuid.uuid4())
        
        # Validar tipo de archivo
        if not file.filename.endswith(('.csv', '.xlsx', '.xls')):
            raise HTTPException(
                status_code=400, 
                detail="Formato de archivo no soportado. Use CSV o Excel."
            )
        
        # Guardar archivo temporal
        temp_path = f"data/temp/{job_id}_{file.filename}"
        with open(temp_path, "wb") as buffer:
            content = await file.read()
            buffer.write(content)
        
        # Inicializar trabajo
        processing_jobs[job_id] = {
            "status": "queued",
            "created_at": datetime.now(),
            "file_path": temp_path,
            "original_filename": file.filename
        }
        
        # Procesar en background
        background_tasks.add_task(
            process_file_background, 
            job_id, 
            temp_path, 
            processing_options
        )
        
        logger.info(f"Archivo {file.filename} subido y encolado para procesamiento: {job_id}")
        
        return ProcessingResponse(
            job_id=job_id,
            status="queued",
            message="Archivo subido exitosamente. Procesamiento iniciado."
        )
        
    except Exception as e:
        logger.error(f"Error al subir archivo: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/process/file", response_model=ProcessingResponse)
async def process_existing_file(
    background_tasks: BackgroundTasks,
    request: ProcessingRequest
):
    """Procesar archivo existente"""
    try:
        # Verificar que el archivo existe
        if not os.path.exists(request.file_path):
            raise HTTPException(status_code=404, detail="Archivo no encontrado")
        
        job_id = str(uuid.uuid4())
        
        # Inicializar trabajo
        processing_jobs[job_id] = {
            "status": "queued",
            "created_at": datetime.now(),
            "file_path": request.file_path
        }
        
        # Procesar en background
        background_tasks.add_task(
            process_file_background,
            job_id,
            request.file_path,
            request.processing_options,
            request.output_format,
            request.notify_webhook
        )
        
        return ProcessingResponse(
            job_id=job_id,
            status="queued",
            message="Procesamiento iniciado"
        )
        
    except Exception as e:
        logger.error(f"Error al procesar archivo: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/process/status/{job_id}")
async def get_processing_status(job_id: str):
    """Obtener estado del procesamiento"""
    if job_id not in processing_jobs:
        raise HTTPException(status_code=404, detail="Trabajo no encontrado")
    
    return processing_jobs[job_id]

@app.get("/process/download/{job_id}")
async def download_processed_file(job_id: str):
    """Descargar archivo procesado"""
    if job_id not in processing_jobs:
        raise HTTPException(status_code=404, detail="Trabajo no encontrado")
    
    job = processing_jobs[job_id]
    
    if job["status"] != "completed":
        raise HTTPException(status_code=400, detail="Procesamiento no completado")
    
    if "output_path" not in job:
        raise HTTPException(status_code=404, detail="Archivo procesado no encontrado")
    
    return FileResponse(
        job["output_path"],
        filename=f"processed_{job_id}.csv",
        media_type="text/csv"
    )

@app.post("/analyze/data")
async def analyze_data(request: AnalysisRequest):
    """Realizar análisis estadístico de los datos"""
    try:
        if request.data_source == "file" and request.source_path:
            # Cargar datos desde archivo
            df = pd.read_csv(request.source_path)
        elif request.data_source == "database":
            # Cargar datos desde base de datos
            df = await db_manager.get_processed_data(
                date_range=request.date_range,
                equipment_filter=request.equipment_filter
            )
        else:
            raise HTTPException(status_code=400, detail="Fuente de datos inválida")
        
        # Realizar análisis
        analysis_results = data_analyzer.perform_analysis(df)
        
        return {
            "status": "success",
            "analysis": analysis_results,
            "records_analyzed": len(df),
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error en análisis: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/data/summary")
async def get_data_summary():
    """Obtener resumen de datos procesados"""
    try:
        summary = await db_manager.get_data_summary()
        return summary
    except Exception as e:
        logger.error(f"Error al obtener resumen: {e}")
        raise HTTPException(status_code=500, detail=str(e))

async def process_file_background(
    job_id: str, 
    file_path: str, 
    processing_options: Dict[str, Any] = {},
    output_format: str = "csv",
    notify_webhook: Optional[str] = None
):
    """Procesar archivo en background"""
    try:
        # Actualizar estado
        processing_jobs[job_id]["status"] = "processing"
        processing_jobs[job_id]["started_at"] = datetime.now()
        
        logger.info(f"Iniciando procesamiento del trabajo {job_id}")
        
        # Cargar datos
        if file_path.endswith('.csv'):
            df = pd.read_csv(file_path)
        else:
            df = pd.read_excel(file_path)
        
        # Limpiar datos
        cleaned_df = data_cleaner.clean_data(df)
        
        # Realizar análisis básico
        analysis = data_analyzer.perform_analysis(cleaned_df)
        
        # Guardar en base de datos
        await db_manager.save_processed_data(cleaned_df, job_id)
        
        # Generar archivo de salida
        output_path = f"data/output/processed_{job_id}.{output_format}"
        
        if output_format == "csv":
            cleaned_df.to_csv(output_path, index=False)
        elif output_format == "excel":
            cleaned_df.to_excel(output_path, index=False)
        
        # Actualizar estado final
        processing_jobs[job_id].update({
            "status": "completed",
            "completed_at": datetime.now(),
            "output_path": output_path,
            "records_processed": len(cleaned_df),
            "analysis": analysis,
            "processing_time": (datetime.now() - processing_jobs[job_id]["started_at"]).total_seconds()
        })
        
        logger.info(f"Procesamiento completado para trabajo {job_id}")
        
        # Notificar webhook si se proporcionó
        if notify_webhook:
            # Implementar notificación webhook
            pass
            
    except Exception as e:
        logger.error(f"Error en procesamiento background {job_id}: {e}")
        processing_jobs[job_id].update({
            "status": "failed",
            "error": str(e),
            "failed_at": datetime.now()
        })

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)