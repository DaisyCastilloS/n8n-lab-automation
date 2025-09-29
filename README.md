# 🤖 Automatización de Análisis de Laboratorio Químico con n8n

## 📋 Descripción del Proyecto

Este proyecto automatiza el análisis de datos del laboratorio químico utilizando **n8n** como orquestador de workflows y **Python** para análisis científico avanzado. El sistema procesa datos de producción de equipos de laboratorio, almacena información en PostgreSQL y genera estadísticas automáticas.

### 🎯 **Estado Actual: CONFIGURADO Y EN PRUEBAS ✅**
- ✅ **Docker Compose**: Servicios n8n y PostgreSQL funcionando
- ✅ **Base de Datos**: Esquemas sincronizados y optimizados
- ✅ **Workflows**: JSON Lab Data Processing activo cada 2 minutos
- ✅ **Datos de Prueba**: Procesando CSV original con 74 registros
- 🧪 **Modo Testing**: Validando automatización antes de producción

## 🧪 Datos Procesados por el Sistema

### **Equipos del Laboratorio Monitoreados:**
- **🔬 pHmetro** - Medición de pH en muestras químicas
- **📊 Espectrofotómetro** - Análisis espectral de compuestos químicos
- **🌀 Centrífuga** - Separación de componentes químicos
- **🩸 Analizador Hematológico** - Análisis de muestras biológicas
- **📈 Control de Turnos** - Seguimiento por turnos (mañana/tarde/noche)
- **📊 Métricas de Rendimiento** - Análisis de eficiencia y calidad

### **Estructura de Datos Actual:**
```json
{
  "record_id": 1,
  "fecha": "2025-09-29",
  "equipo": "phmetro",
  "turno": "mañana",
  "muestras_procesadas": 85,
  "rendimiento": 78,
  "comentario": "ok",
  "tipo_muestra": "Química",
  "estado": "Aprobado"
}
```

### **Tablas de Base de Datos:**
- **`processed_lab_data`**: Datos individuales de cada análisis (actualmente 0 registros - limpia)
- **`lab_statistics`**: Estadísticas agregadas por fecha (actualmente 0 registros - limpia)

## 🔄 Workflows Implementados

### **📊 1. JSON Lab Data Processing** (json-data-processing-workflow.json) ✅ ACTIVO
**Propósito:** Procesamiento automático y continuo de datos de laboratorio químico

**🧪 CONFIGURACIÓN DE PRUEBA ACTUAL:**
- **Schedule Trigger**: Se ejecuta cada **2 minutos** para efectos de testing y validación
- **Fuente de Datos**: Procesa el archivo CSV original `produccion_limpia_final.csv` (no datos externos)
- **Objetivo**: Validar que la automatización funciona correctamente antes de configurar intervalos de producción

**Funcionalidad:**
- **Lectura de CSV Original**: Lee directamente el archivo `produccion_limpia_final.json` generado desde el CSV
- **Procesamiento de Datos Reales**: Utiliza los 74 registros originales del laboratorio químico
- **Generación de IDs Únicos**: Asigna identificadores únicos a cada registro procesado
- **Clasificación Automática**: 
  - **Tipo de muestra**: Todas clasificadas como 'Química'
  - **Estado**: Aprobado si rendimiento ≥ 70%, Rechazado si < 70%
- **Almacenamiento Dual**:
  - Tabla `lab_statistics`: Resúmenes agregados por fecha
  - Tabla `processed_lab_data`: Registros individuales con estructura química completa

**Estructura de Datos del CSV Original:**
```json
{
  "record_id": "LAB_001",
  "fecha": "2025-09-29",
  "equipo": "phmetro",
  "turno": "mañana", 
  "muestras_procesadas": 85,
  "rendimiento": 78.5,
  "comentario": "Análisis completado correctamente",
  "tipo_muestra": "Química",
  "estado": "Aprobado",
  "fecha_procesamiento": "2025-09-29T14:38:59Z"
}
```

**Flujo de Ejecución de Prueba:**
```
⏰ Schedule (2min) → 📄 Read CSV → 🔄 Parse JSON → 📊 Process Records → 💾 Save to DB
```

**🎯 Métricas de Validación:**
- **Registros esperados**: 74 (del CSV original)
- **Frecuencia de prueba**: Cada 2 minutos
- **Tablas actualizadas**: `processed_lab_data` y `lab_statistics`
- **Validación**: Verificar que no se generen duplicados y que todos los registros se procesen correctamente

---

## 🔧 **CONFIGURACIÓN ACTUAL DE PRUEBAS**

### ✅ **Modo Testing Activado**
- **Frecuencia**: Cada **2 minutos** (en lugar de 1 hora de producción)
- **Fuente de datos**: CSV original `produccion_limpia_final.csv` (74 registros reales)
- **Objetivo**: Validar funcionamiento completo de la automatización
- **Base de datos**: Limpia y lista para recibir datos de prueba

### 🎯 **Validaciones en Curso**
- **Conectividad**: n8n ↔ PostgreSQL ✅
- **Lectura de archivos**: CSV/JSON processing ✅  
- **Esquemas de BD**: Columnas sincronizadas ✅
- **Procesamiento**: Transformación de datos ✅
- **Almacenamiento**: Inserción en tablas ✅

### 📊 **Resultados Esperados de Prueba**
- **Tabla `processed_lab_data`**: 74 registros (uno por cada fila del CSV)
- **Tabla `lab_statistics`**: 1+ registros con estadísticas agregadas
- **Frecuencia de actualización**: Cada 2 minutos
- **Sin duplicados**: Cada ejecución debe procesar los mismos 74 registros sin duplicar

### 🔄 **Transición a Producción**
Una vez validado el funcionamiento en modo prueba:
1. **Cambiar frecuencia** de 2 minutos → 1 hora (o según necesidades)
2. **Configurar fuentes externas** (APIs, webhooks, etc.)
3. **Activar monitoreo** y sistema de alertas
4. **Implementar backup** y recuperación de datos

---

## 🔧 **HISTORIAL DE CORRECCIONES Y MEJORAS**

### ✅ **Problema de Duplicados Resuelto**
- **Problema identificado**: Schedule Trigger configurado a 30 segundos causaba duplicación excesiva de registros
- **Síntomas**: 45+ registros en lugar de los 37 esperados del CSV
- **Solución implementada**: 
  - Cambio de frecuencia de 30 segundos → 1 hora (3600 segundos)
  - Limpieza completa de la base de datos
  - Eliminación de registros duplicados
- **Estado actual**: Base de datos limpia (0 registros) lista para procesamiento correcto

### 🎯 **Estrategia de Frecuencia Basada en Fuente de Datos**
- **📄 Fuente Estática (CSV)**: 1 hora - Evita duplicados innecesarios de datos que no cambian
- **🌐 Fuente Dinámica (API Externa)**: Frecuencia más rápida - Cuando se implemente conexión a APIs externas
- **💡 Principio**: La frecuencia debe coincidir con la velocidad de cambio de los datos fuente
- **⚡ Beneficio**: Optimización de recursos y eliminación de datos redundantes

### 🔄 **Optimizaciones Realizadas**:
- **Automatización inteligente**: Frecuencia ajustada según tipo de fuente de datos
- **Eficiencia de recursos**: Reducción del 99.9% en frecuencia de ejecución para CSV estático
- **Calidad de datos**: Eliminación de duplicados y datos inconsistentes
- **Monitoreo mejorado**: Orden lógico de ejecución de workflows establecido
- **Escalabilidad futura**: Preparado para aumentar frecuencia cuando se conecten APIs externas

---

## 📋 **ORDEN LÓGICO DE EJECUCIÓN DE WORKFLOWS**

### 🔄 **Secuencia Recomendada:**

#### **1. JSON Lab Data Processing** (Primero - Base de datos)
- **Función**: Procesa y almacena los datos del CSV en la base de datos
- **Frecuencia**: Cada 1 hora (optimizada para fuente estática CSV)
- **Por qué primero**: Es la fuente de datos principal que alimenta las tablas
- **💡 Nota**: Frecuencia ajustada a 1 hora para evitar duplicados de datos estáticos

#### **2. Lab Data Processing Pipeline** (Segundo - Opcional)
- **Función**: Procesa datos adicionales vía webhook
- **Trigger**: Manual o por API
- **Por qué segundo**: Complementa los datos del primer workflow

#### **3. Lab Alert Monitoring** (Tercero - Monitoreo)
- **Función**: Monitorea los datos procesados y genera alertas
- **Frecuencia**: Cada 5 segundos
- **Por qué último**: Necesita que los datos ya estén procesados

### ⚠️ **Consideraciones Importantes:**
- El workflow de alertas **depende** de que haya datos en la base de datos
- El monitoreo (5 segundos) es mucho más frecuente que la generación de datos (1 hora)
- Asegúrate de que la base de datos tenga datos antes de activar el monitoreo
- **🔄 Escalabilidad**: Cuando se conecten fuentes externas (APIs), se podrá reducir la frecuencia del procesamiento principal
- **📊 Estado actual**: `JSON Lab Data Processing` está activo, `Lab Alert Monitoring` y `Lab Data Processing Pipeline` están inactivos

---

### **🚀 2. Lab Data Processing Pipeline** (lab-data-processing-workflow.json) 
**Propósito:** Pipeline completo para procesamiento de archivos de laboratorio químico via webhook

**Funcionalidad:**
- **Webhook Trigger**: Recibe archivos via POST a `/lab-data-upload`
- **Validación de Datos Químicos**: Verifica integridad y formato de archivos CSV/JSON
- **Procesamiento Asíncrono**: 
  - Extrae Job ID para seguimiento
  - Espera procesamiento (5 segundos)
  - Verifica estado de completitud
- **Análisis Estadístico Químico**: 
  - Cuenta total de muestras procesadas por fecha
  - Verifica datos aprobados en `processed_lab_data`
  - Genera reportes automáticos de equipos químicos
- **Gestión de Estados**:
  - ✅ Éxito: Notificación y descarga de resultados
  - ❌ Error: Manejo de errores y reintentos
- **Almacenamiento**: Guarda en tabla `processed_lab_data` con estructura química
- **Respuesta Webhook**: Retorna estado final al cliente

**Estructura de Base de Datos:**
```sql
INSERT INTO processed_lab_data 
(record_id, fecha, equipo, turno, muestras_procesadas, rendimiento, comentario, tipo_muestra, estado)
VALUES (?, ?, ?, ?, ?, ?, ?, 'Química', ?)
```

**Flujo de Ejecución:**
```
📤 Webhook Upload → ✅ Validate → 🔄 Process → ⏳ Wait → 📊 Analyze → 📧 Notify → 📥 Response
```

---

### **🚨 3. Lab Alert Monitoring** (alert-monitoring-workflow.json)
**Propósito:** Sistema de monitoreo en tiempo real con alertas automáticas para datos químicos

**Funcionalidad:**
- **Monitoreo Continuo**: Ejecuta cada 5 segundos (tiempo real)
- **Obtención de Datos Químicos**: Consulta API Gateway `/data/chemical-summary` para datos recientes (últimas 24h)
- **Análisis de Anomalías Químicas**:
  - 📉 **Rendimiento químico bajo** (<75% en análisis)
  - 🔧 **Problemas de equipos químicos** (phmetro, espectrofotómetro, centrífuga, analizador hematológico)
  - 📊 **Baja producción** (<50 muestras procesadas/día)
  - 🔄 **Alta tasa de repeticiones** (>20% de muestras requieren repetir)
  - ⚖️ **Desbalance de turnos** (distribución desigual entre mañana/tarde/noche)
- **Sistema de Alertas Multinivel**:
  - 🔴 **Críticas**: Rendimiento <60%, equipos fuera de servicio, repeticiones >30%
  - 🟡 **Medias**: Rendimiento 60-75%, repeticiones 20-30%, baja producción
  - ℹ️ **Advertencias**: Desbalance de turnos, problemas menores
- **Notificaciones Inteligentes**:
  - Emails HTML formateados por severidad
  - Integración con Slack para alertas críticas
  - Escalamiento automático según criticidad

**Métricas Monitoreadas:**
```sql
SELECT 
  COUNT(*) as total_muestras_procesadas,
  AVG(rendimiento) as avg_rendimiento,
  COUNT(CASE WHEN estado = 'Repetir' THEN 1 END) * 1.0 / COUNT(*) as tasa_repeticiones,
  COUNT(DISTINCT equipo) as equipos_activos,
  COUNT(CASE WHEN turno = 'Mañana' THEN 1 END) as turno_manana,
  COUNT(CASE WHEN turno = 'Tarde' THEN 1 END) as turno_tarde,
  COUNT(CASE WHEN turno = 'Noche' THEN 1 END) as turno_noche
FROM processed_lab_data 
WHERE fecha >= CURRENT_DATE - INTERVAL '1 day' AND tipo_muestra = 'Química'
```

**Flujo de Ejecución:**
```
⏰ Cron (5s) → 📊 Get Data → 🔍 Analyze → ❓ Has Alerts? → 🚨 Notify → 📝 Log
```

---

### **🔐 4. Credentials Setup** (credentials-setup.json)
**Propósito:** Configuración centralizada de credenciales para conexiones

**Funcionalidad:**
- **PostgreSQL**: Credenciales para base de datos del laboratorio
  - Host: `lab_postgres` (contenedor Docker)
  - Puerto: 5432 (interno)
  - Base de datos: `lab_analytics`
  - Usuario y contraseña encriptados
- **Configuración de Seguridad**: SSL deshabilitado para red interna Docker

**Archivos Procesados:**
- `data/produccion_limpia_final.json` (20 registros)
- `data/produccion_limpia_final.csv` (datos originales)

## 🏗️ Arquitectura Actual

```
┌─────────────┐    JSON Data    ┌──────────────┐    SQL Insert   ┌─────────────────┐
│     n8n     │ ──────────────► │  PostgreSQL  │ ──────────────► │   Data Tables   │
│ (Scheduler) │                 │   Database   │                 │ lab_statistics  │
└─────────────┘                 └──────────────┘                 │processed_lab_data│
      │                                │                         └─────────────────┘
      ▼                                ▼                              
┌─────────────┐                ┌──────────────┐               
│ JSON Files  │                │   Docker     │               
│ CSV Data    │                │ Containers   │               
│ Scheduling  │                │   Network    │               
└─────────────┘                └──────────────┘               
```

### **Componentes Activos:**
- **n8n**: Orquestador principal (puerto 5678)
- **PostgreSQL**: Base de datos (puerto 5433)
- **Docker Network**: `lab_network` para comunicación interna

## 🔄 Flujo de Automatización Real

**Ejemplo de Uso Diario:**
```
📋 Técnico sube CSV químico → 🤖 n8n valida → 🧪 Procesa datos químicos → 💾 Guarda en BD → 📧 Supervisor recibe alerta
```

1. **Ingesta**: n8n detecta archivo CSV con datos químicos del día
2. **Validación**: Code Node verifica formato y completitud de datos químicos
3. **Procesamiento**: Analiza datos de equipos químicos y calcula métricas
4. **Análisis**: Detección de anomalías en rendimiento químico y cálculo de KPIs
5. **Almacenamiento**: Guardado en PostgreSQL tabla `processed_lab_data` con estructura química
6. **Alertas**: Notificaciones inmediatas por problemas críticos en equipos químicos
7. **Reportes**: Generación automática de informes por turno y equipo químico

**Base de Datos n8n:**
- **Tabla Principal**: `processed_lab_data` - Almacena todos los registros químicos individuales
- **Tabla Estadísticas**: `lab_statistics` - Resúmenes agregados por fecha
- **Estructura Química**: Campos específicos para equipos de laboratorio químico
- **Monitoreo**: Consultas SQL optimizadas para análisis en tiempo real

## 🚀 **INICIO RÁPIDO**

### **⚡ Pasos para Activar el Sistema:**

1. **Verificar servicios activos:**
   ```bash
   docker-compose ps  # Verificar que n8n y PostgreSQL estén corriendo
   ```

2. **Acceder a n8n:** http://localhost:5678

3. **Activar workflows en orden:**
   ⚠️ **Estado actual**: `JSON Lab Data Processing` está activo
   - ✅ **Primero**: `JSON Lab Data Processing` (ACTIVO) - Genera los datos base cada hora
   - **Segundo**: `Lab Alert Monitoring` (INACTIVO) - Monitorea los datos generados
   - **Tercero**: `Lab Data Processing Pipeline` (INACTIVO) - Para procesamiento manual

4. **Verificar funcionamiento:**
   ```bash
   # Comprobar registros procesados
   docker exec lab_postgres psql -U lab_user -d lab_analytics -c "SELECT COUNT(*) FROM processed_lab_data;"
   ```

### **🎯 Resultado Esperado:**
- `processed_lab_data`: 37 registros (del CSV original)
- `lab_statistics`: 1+ registros de estadísticas
- Alertas automáticas funcionando cada 5 segundos

---

## 🚀 **TECNOLOGÍAS**

- **n8n**: Orquestador de workflows
- **FastAPI**: APIs de servicios
- **PostgreSQL**: Base de datos
- **Python**: Procesamiento de datos
- **Docker**: Contenedorización
- **Pandas**: Manipulación de datos

## 📊 Características

- ✅ **Procesamiento automático de datos químicos** basado en CSV de producción
- ✅ **Normalización de equipos químicos** (phmetro, espectrofotómetro, centrífuga, analizador hematológico)
- ✅ **Detección de anomalías en rendimiento químico** (<75% threshold)
- ✅ **Monitoreo de muestras procesadas** por turno y equipo
- ✅ **Sistema de alertas químicas** multinivel (críticas/medias/advertencias)
- ✅ **Base de datos n8n PostgreSQL** con estructura química optimizada
- ✅ **API REST para integración** con endpoints específicos para datos químicos
- ✅ **Monitoreo en tiempo real** cada 5 segundos
- ✅ **Arquitectura escalable y modular** con Docker
- ✅ **Gestión de turnos** (mañana/tarde/noche) con análisis de distribución
- ✅ **Control de calidad** con estados (Aprobado/Repetir) y comentarios

## 🛠️ Instalación y Configuración

### **Requisitos Previos:**
- Docker y Docker Compose instalados
- Puerto 5678 (n8n) y 5433 (PostgreSQL) disponibles

### **Instalación Paso a Paso:**

```bash
# 1. Clonar el repositorio
git clone <repo>
cd n8n-lab-automation

# 2. Configurar variables de entorno
cp .env.example .env  # Editar con tus credenciales

# 3. Levantar servicios
docker-compose up -d

# 4. Verificar que los servicios estén corriendo
docker-compose ps
```

### **Variables de Entorno Requeridas:**
Asegúrate de configurar estas variables en tu archivo `.env`:
```bash
# n8n Configuration
N8N_BASIC_AUTH_USER=tu_usuario
N8N_BASIC_AUTH_PASSWORD=tu_contraseña_segura

# PostgreSQL Configuration
POSTGRES_DB=lab_analytics
POSTGRES_USER=tu_usuario_db
POSTGRES_PASSWORD=tu_contraseña_db_segura
```

### **Configuración de n8n:**

1. **Acceder a n8n**: http://localhost:5678
2. **Credenciales iniciales**:
   - Usuario: `[Ver archivo .env]`
   - Contraseña: `[Ver archivo .env]`

3. **Importar workflow**:
   - Ir a "Workflows" → "Import from file"
   - Seleccionar `workflows/json-data-processing-workflow.json`

4. **Configurar credenciales PostgreSQL**:
   - Nombre: `Lab PostgreSQL`
   - Host: `lab_postgres`
   - Database: `lab_analytics`
   - User: `[Usar valor de POSTGRES_USER del .env]`
   - Password: `[Usar valor de POSTGRES_PASSWORD del .env]`
   - Port: `5432`

5. **Activar el workflow** y verificar ejecución

## 🌐 **INTERFACES DE ACCESO**

### 🎯 **Dashboard Principal - n8n**
- **URL**: http://localhost:5678
- **Usuario**: `[Ver archivo .env]`
- **Contraseña**: `[Ver archivo .env]`
- **Función**: Crear workflows, monitorear datos, automatizar procesos

### 🗄️ **Base de Datos PostgreSQL**
- **Host**: localhost
- **Puerto**: `5433` (¡Importante! No es el 5432 estándar)
- **Base de datos**: `lab_analytics`
- **Usuario**: `[Ver archivo .env]`
- **Contraseña**: `[Ver archivo .env]`

## 🔒 **Seguridad y Mejores Prácticas**

### **⚠️ IMPORTANTE - Datos Sensibles:**
- **NUNCA** commitear el archivo `.env` al repositorio
- Usar contraseñas fuertes y únicas para cada servicio
- Cambiar las credenciales por defecto antes de usar en producción
- Mantener las credenciales en variables de entorno, no en código

### **Configuración Segura:**
```bash
# Generar contraseñas seguras
openssl rand -base64 32  # Para PostgreSQL
openssl rand -base64 16  # Para n8n

# Verificar que .env no esté en git
git status  # .env NO debe aparecer en la lista
```

### **Acceso Restringido:**
- Cambiar puertos por defecto en producción
- Usar HTTPS en lugar de HTTP
- Configurar firewall para limitar acceso a puertos específicos
- Implementar autenticación de dos factores cuando sea posible

## 🔍 **Verificación del Sistema**

### **Comprobar que los datos se están guardando:**

```bash
# Verificar registros en lab_statistics
docker exec lab_postgres psql -U $POSTGRES_USER -d lab_analytics -c "SELECT COUNT(*) FROM lab_statistics;"

# Ver últimos registros procesados
docker exec lab_postgres psql -U $POSTGRES_USER -d lab_analytics -c "SELECT * FROM processed_lab_data ORDER BY record_id DESC LIMIT 5;"

# Verificar estadísticas por fecha
docker exec lab_postgres psql -U $POSTGRES_USER -d lab_analytics -c "SELECT fecha, total_records, turnos_unicos, equipos_unicos FROM lab_statistics ORDER BY fecha DESC;"
```

## 🚨 **Troubleshooting**

### **Problemas Comunes:**

1. **Error de credenciales en n8n:**
   - Verificar que las credenciales PostgreSQL estén configuradas correctamente
   - Usar `lab_postgres` como host (no `localhost`)
   - Verificar que las credenciales coincidan con las del archivo `.env`

2. **Workflow no se ejecuta:**
   - Verificar que el workflow esté activado
   - Comprobar que el archivo JSON existe en `data/produccion_limpia_final.json`
   - Revisar los logs de ejecución en n8n

3. **Contenedores no inician:**
   ```bash
   # Verificar estado de contenedores
   docker-compose ps
   
   # Ver logs de errores
   docker-compose logs n8n
   docker-compose logs postgres
   ```

4. **Base de datos no conecta:**
   - Verificar que PostgreSQL esté corriendo en puerto 5433
   - Comprobar conectividad de red entre contenedores
   ```bash
   docker exec lab_n8n ping lab_postgres
   ```

## 📈 Workflows Disponibles

1. **Procesamiento Diario**: Análisis automático de datos diarios
2. **Alertas de Rendimiento**: Notificaciones por bajo rendimiento
3. **Reportes Semanales**: Generación automática de informes
4. **Backup de Datos**: Respaldo automático de información procesada