"""
API Gateway para integración con n8n
"""

from fastapi import FastAPI, HTTPException, BackgroundTasks, UploadFile, File, Query
from fastapi.responses import FileResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional, List, Dict, Any
import httpx
import asyncio
import os
import json
from datetime import datetime
import logging
import asyncpg
from contextlib import asynccontextmanager

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

import urllib.parse

# Configuración de PostgreSQL
password = urllib.parse.quote_plus(os.getenv("POSTGRES_PASSWORD", "vgR9jGlmsOSGxLFGoHCu+sJf1L7kCqB/9MVjAQqxrPg="))
DATABASE_URL = os.getenv("DATABASE_URL", f"postgresql://lab_user:{password}@lab_postgres:5432/lab_analytics")

# Pool de conexiones PostgreSQL
db_pool = None

@asynccontextmanager
async def get_db_connection():
    """Obtener conexión a la base de datos"""
    global db_pool
    if db_pool is None:
        try:
            db_pool = await asyncpg.create_pool(DATABASE_URL, min_size=1, max_size=10)
            logger.info(f"Pool de conexiones PostgreSQL creado exitosamente")
        except Exception as e:
            logger.error(f"Error creando pool de conexiones: {e}")
            raise
    
    try:
        async with db_pool.acquire() as connection:
            yield connection
    except Exception as e:
        logger.error(f"Error obteniendo conexión del pool: {e}")
        raise

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Gestión del ciclo de vida de la aplicación"""
    global db_pool
    try:
        # Inicializar pool de conexiones al arrancar
        db_pool = await asyncpg.create_pool(DATABASE_URL, min_size=1, max_size=10)
        logger.info("Pool de conexiones PostgreSQL inicializado")
        yield
    except Exception as e:
        logger.error(f"Error inicializando pool de conexiones: {e}")
        raise
    finally:
        # Cerrar pool al terminar
        if db_pool:
            await db_pool.close()
            logger.info("Pool de conexiones PostgreSQL cerrado")

app = FastAPI(
    title="Lab Analytics API Gateway",
    description="API Gateway para automatización de análisis de laboratorio con n8n",
    version="1.0.0",
    lifespan=lifespan
)

# Configurar CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Configuración
DATA_PROCESSOR_URL = os.getenv("DATA_PROCESSOR_URL", "http://data_processor:8001")
N8N_WEBHOOK_URL = os.getenv("N8N_WEBHOOK_URL", "http://n8n:5678/webhook")

# Modelos Pydantic
class ProcessingRequest(BaseModel):
    file_path: str
    processing_type: str = "full"
    notify_webhook: Optional[str] = None
    parameters: Optional[Dict[str, Any]] = {}

class AnalysisRequest(BaseModel):
    data_id: str
    analysis_type: str = "complete"
    parameters: Optional[Dict[str, Any]] = {}

class WebhookNotification(BaseModel):
    job_id: str
    status: str
    message: str
    data: Optional[Dict[str, Any]] = {}
    timestamp: datetime

# Cliente HTTP para comunicación con servicios
async def get_http_client():
    return httpx.AsyncClient(timeout=30.0)

@app.get("/")
async def root():
    """Endpoint raíz"""
    return {
        "message": "Lab Analytics API Gateway",
        "version": "1.0.0",
        "status": "active",
        "timestamp": datetime.now().isoformat()
    }

@app.get("/health")
async def health_check():
    """Verificar estado de salud del gateway y servicios conectados"""
    services_status = {}
    
    async with httpx.AsyncClient() as client:
        # Verificar Data Processor
        try:
            response = await client.get(f"{DATA_PROCESSOR_URL}/health")
            services_status["data_processor"] = {
                "status": "healthy" if response.status_code == 200 else "unhealthy",
                "response_time": response.elapsed.total_seconds()
            }
        except Exception as e:
            services_status["data_processor"] = {
                "status": "unreachable",
                "error": str(e)
            }
    
    return {
        "gateway": "healthy",
        "services": services_status,
        "timestamp": datetime.now().isoformat()
    }

@app.post("/process/upload")
async def upload_and_process(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    processing_type: str = Query("full", description="Tipo de procesamiento"),
    notify_webhook: Optional[str] = Query(None, description="URL de webhook para notificaciones")
):
    """Subir archivo y iniciar procesamiento"""
    
    try:
        # Enviar archivo al procesador de datos
        async with httpx.AsyncClient() as client:
            files = {"file": (file.filename, await file.read(), file.content_type)}
            data = {"processing_type": processing_type}
            
            response = await client.post(
                f"{DATA_PROCESSOR_URL}/process/upload",
                files=files,
                data=data
            )
            
            if response.status_code != 200:
                raise HTTPException(status_code=response.status_code, detail=response.text)
            
            result = response.json()
            job_id = result["job_id"]
            
            # Programar notificación si se especifica webhook
            if notify_webhook:
                background_tasks.add_task(
                    monitor_processing_job,
                    job_id,
                    notify_webhook
                )
            
            return result
            
    except Exception as e:
        logger.error(f"Error en upload_and_process: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/process/status/{job_id}")
async def get_processing_status(job_id: str):
    """Obtener estado de procesamiento"""
    
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(f"{DATA_PROCESSOR_URL}/process/status/{job_id}")
            
            if response.status_code != 200:
                raise HTTPException(status_code=response.status_code, detail=response.text)
            
            return response.json()
            
    except Exception as e:
        logger.error(f"Error en get_processing_status: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/process/download/{job_id}")
async def download_processed_file(job_id: str):
    """Descargar archivo procesado"""
    
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(f"{DATA_PROCESSOR_URL}/process/download/{job_id}")
            
            if response.status_code != 200:
                raise HTTPException(status_code=response.status_code, detail=response.text)
            
            # Retornar el archivo
            return FileResponse(
                path=response.headers.get("file-path"),
                filename=response.headers.get("filename"),
                media_type=response.headers.get("content-type")
            )
            
    except Exception as e:
        logger.error(f"Error en download_processed_file: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/analysis/run")
async def run_analysis(
    request: AnalysisRequest,
    background_tasks: BackgroundTasks
):
    """Ejecutar análisis de datos"""
    
    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{DATA_PROCESSOR_URL}/analysis/run",
                json=request.dict()
            )
            
            if response.status_code != 200:
                raise HTTPException(status_code=response.status_code, detail=response.text)
            
            return response.json()
            
    except Exception as e:
        logger.error(f"Error en run_analysis: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/data/summary")
async def get_data_summary(
    start_date: Optional[str] = Query(None),
    end_date: Optional[str] = Query(None),
    equipment: Optional[str] = Query(None)
):
    """Obtener resumen de datos directamente desde PostgreSQL"""
    
    try:
        # Usar conexión directa en lugar del pool para debugging
        password = urllib.parse.quote_plus(os.getenv("POSTGRES_PASSWORD", "vgR9jGlmsOSGxLFGoHCu+sJf1L7kCqB/9MVjAQqxrPg="))
        connection_string = f"postgresql://lab_user:{password}@lab_postgres:5432/lab_analytics"
        
        logger.info(f"Intentando conectar a: postgresql://lab_user:***@lab_postgres:5432/lab_analytics")
        
        conn = await asyncpg.connect(connection_string)
        
        # Query simplificada para verificar que funciona
        result = await conn.fetchrow("""
            SELECT 
                COUNT(*) as total_samples,
                COUNT(DISTINCT sample_type) as unique_sample_types,
                NOW() as query_time
            FROM samples
        """)
        
        await conn.close()
        
        logger.info(f"Query ejecutada exitosamente: {result}")
        
        return {
            "total_samples": result["total_samples"] or 0,
            "unique_sample_types": result["unique_sample_types"] or 0,
            "query_time": result["query_time"].isoformat(),
            "status": "success",
            "message": "Conexión PostgreSQL funcionando correctamente"
        }
        
    except Exception as e:
        logger.error(f"Error en get_data_summary: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/webhook/n8n")
async def n8n_webhook(data: Dict[str, Any]):
    """Webhook para recibir datos desde n8n"""
    
    try:
        logger.info(f"Webhook recibido desde n8n: {data}")
        
        # Procesar según el tipo de webhook
        webhook_type = data.get("type", "unknown")
        
        if webhook_type == "file_upload":
            # Procesar archivo subido desde n8n
            file_path = data.get("file_path")
            if file_path:
                # Iniciar procesamiento
                async with httpx.AsyncClient() as client:
                    response = await client.post(
                        f"{DATA_PROCESSOR_URL}/process/file",
                        json={"file_path": file_path}
                    )
                    return response.json()
        
        elif webhook_type == "schedule_analysis":
            # Análisis programado
            analysis_params = data.get("parameters", {})
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{DATA_PROCESSOR_URL}/analysis/scheduled",
                    json=analysis_params
                )
                return response.json()
        
        return {"status": "received", "type": webhook_type}
        
    except Exception as e:
        logger.error(f"Error en n8n_webhook: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

async def monitor_processing_job(job_id: str, webhook_url: str):
    """Monitorear trabajo de procesamiento y notificar cuando termine"""
    
    max_attempts = 60  # 5 minutos máximo
    attempt = 0
    
    while attempt < max_attempts:
        try:
            async with httpx.AsyncClient() as client:
                # Verificar estado del trabajo
                response = await client.get(f"{DATA_PROCESSOR_URL}/process/status/{job_id}")
                
                if response.status_code == 200:
                    status_data = response.json()
                    status = status_data.get("status")
                    
                    if status in ["completed", "failed"]:
                        # Enviar notificación
                        notification = WebhookNotification(
                            job_id=job_id,
                            status=status,
                            message=status_data.get("message", ""),
                            data=status_data,
                            timestamp=datetime.now()
                        )
                        
                        await client.post(webhook_url, json=notification.dict())
                        break
                
                await asyncio.sleep(5)  # Esperar 5 segundos
                attempt += 1
                
        except Exception as e:
            logger.error(f"Error monitoreando trabajo {job_id}: {str(e)}")
            break

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)