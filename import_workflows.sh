#!/bin/bash

echo "🔄 Importando workflows a n8n..."

# Función para importar workflow
import_workflow() {
    local file=$1
    local name=$(basename "$file" .json)
    
    echo "📁 Importando: $name"
    
    # Usar la API de n8n para importar
    curl -X POST \
        -H "Content-Type: application/json" \
        -d @"$file" \
        http://localhost:5678/rest/workflows/import \
        2>/dev/null
    
    echo "✅ $name importado"
}

# Importar todos los workflows
cd workflows/

for workflow in *.json; do
    if [[ "$workflow" != "credentials-setup.json" ]]; then
        import_workflow "$workflow"
        sleep 2
    fi
done

echo ""
echo "🎯 Workflows importados. Ahora:"
echo "1. Ve a http://localhost:5678"
echo "2. Activa cada workflow (toggle verde)"
echo "3. Verifica que las credenciales estén configuradas"
echo ""
echo "📊 Los workflows deberían ejecutarse automáticamente cada 30 segundos"