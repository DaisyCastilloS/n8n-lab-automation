#!/bin/bash

echo "🔧 Configurando credenciales en n8n..."

# Esperar a que n8n esté listo
echo "⏳ Esperando a que n8n esté disponible..."
sleep 5

# Crear las credenciales usando la API de n8n
echo "📝 Creando credenciales PostgreSQL..."

curl -X POST http://localhost:5678/rest/credentials \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Lab PostgreSQL",
    "type": "postgres",
    "data": {
      "host": "lab_postgres",
      "port": 5432,
      "database": "lab_analytics",
      "user": "lab_user",
      "password": "lab_password_2024",
      "ssl": false,
      "allowUnauthorizedCerts": false
    }
  }' 2>/dev/null

echo ""
echo "✅ Credenciales configuradas"
echo ""
echo "🎯 Ahora puedes:"
echo "1. Ir a http://localhost:5678"
echo "2. Verificar que las credenciales 'Lab PostgreSQL' existan"
echo "3. Activar el workflow 'JSON Lab Data Processing'"
echo ""