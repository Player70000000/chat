# Backend Unificado - Empresa Limpieza Chat

Backend modularizado y unificado para el sistema de chat de empresa de limpieza, con arquitectura Flask + MongoDB.

## Estructura del Proyecto

```
backend/
├── api/                    # Endpoints de la API REST
│   ├── auth/              # Autenticación y validación
│   ├── channels/          # Gestión de canales de chat
│   ├── messages/          # Gestión de mensajes
│   ├── personnel/         # Gestión de personal y cuadrillas
│   └── reports/           # Sistema de reportes y análisis
├── config/                # Configuraciones
│   └── database.py        # Conexión a MongoDB
├── utils/                 # Utilidades y validadores
├── main.py               # Punto de entrada principal
├── app.py                # Factory de aplicación Flask
├── config.py             # Configuración centralizada
└── requirements.txt      # Dependencias

## Instalación

1. **Crear entorno virtual:**
```bash
python -m venv .venv
source .venv/bin/activate  # Linux/Mac
# o
.venv\Scripts\activate     # Windows
```

2. **Instalar dependencias:**
```bash
pip install -r requirements.txt
```

3. **Configurar variables de entorno:**
```bash
cp .env.example .env
# Editar .env con tu configuración
```

4. **Ejecutar el servidor:**
```bash
python main.py
```

## Configuración

### Variables de Entorno

Copia `.env.example` a `.env` y configura:

- `MONGO_URI`: URI de conexión a MongoDB
- `SECRET_KEY`: Clave secreta para Flask
- `DEBUG`: Modo debug (true/false)
- `HOST`: Host del servidor (por defecto 0.0.0.0)
- `PORT`: Puerto del servidor (por defecto 5000)

### Entornos

El backend soporta múltiples entornos:

- `development`: Desarrollo local
- `production`: Producción
- `testing`: Pruebas

Configurar con `FLASK_ENV=production` en .env

## API Endpoints

### Autenticación
- `GET /api/auth/info` - Información del servidor
- `GET /api/auth/status` - Estado del servidor y BD
- `POST /api/auth/validate` - Validar usuario

### Canales
- `GET /api/channels/` - Listar canales
- `POST /api/channels/` - Crear canal
- `GET /api/channels/<nombre>` - Información de canal
- `PUT /api/channels/<nombre>` - Editar canal
- `DELETE /api/channels/<nombre>` - Eliminar canal

### Mensajes
- `POST /api/messages/` - Enviar mensaje
- `GET /api/messages/canal/<canal>` - Obtener mensajes de canal
- `PUT /api/messages/<id>` - Editar mensaje
- `DELETE /api/messages/<id>` - Eliminar mensaje
- `PUT /api/messages/<id>/estado` - Actualizar estado de mensaje

### Rutas Legacy (Compatibilidad)
- `GET /` - Página de inicio
- `GET /verificar` - Verificar conexión
- `POST /crear_canal` - Crear canal (legacy)
- `GET /canales` - Listar canales (legacy)
- Y más endpoints de compatibilidad...

## Base de Datos

### Configuración MongoDB

**Nombre de base de datos:** `chat_app`

#### MongoDB Local
```bash
MONGO_URI=mongodb://localhost:27017/chat_app
```

#### MongoDB Atlas (Recomendado para Producción)
```bash
# Formato general
MONGO_URI=mongodb+srv://<username>:<password>@<cluster>.mongodb.net/chat_app?retryWrites=true&w=majority

# Ejemplo
MONGO_URI=mongodb+srv://empresalimpieza:miPassword123@cluster0.abc123.mongodb.net/chat_app?retryWrites=true&w=majority
```

**Pasos para configurar MongoDB Atlas:**
1. Crear cuenta en [MongoDB Atlas](https://www.mongodb.com/cloud/atlas)
2. Crear un nuevo cluster
3. Crear usuario de base de datos
4. Configurar Network Access (IP Whitelist)
5. Obtener connection string y actualizar `.env`

### MongoDB Schema

**Colección: canales**
```json
{
  "nombre": "string (unique)",
  "descripcion": "string",
  "creado": "datetime",
  "activo": "boolean"
}
```

**Colección: mensajes**
```json
{
  "canal": "string",
  "usuario": "string", 
  "contenido": "string",
  "timestamp": "datetime",
  "estado": "enviado|entregado|leido",
  "editado": "boolean",
  "fecha_edicion": "datetime"
}
```

**Colección: cuadrillas**
```json
{
  "numero_cuadrilla": "string (unique)",
  "actividad": "string",
  "creada": "datetime",
  "activa": "boolean"
}
```

**Colección: personal_obrero**
```json
{
  "nombre": "string",
  "apellido": "string",
  "cedula": "string (unique)",
  "registrado": "datetime",
  "activo": "boolean"
}
```

### Índices
**Sistema de Chat:**
- `canales.nombre` (único)
- `mensajes.canal + timestamp` (descendente)
- `mensajes.usuario + _id`

**Sistema de Personal:**
- `cuadrillas.numero_cuadrilla` (único)
- `cuadrillas.actividad + activa`
- `personal_obrero.cedula` (único)
- `personal_obrero.nombre + apellido`

## Características

- ✅ API REST modular con Flask Blueprints
- ✅ Conexión optimizada a MongoDB con manejo de errores
- ✅ Validación robusta de datos de entrada
- ✅ Soporte para estados de mensajes
- ✅ Compatibilidad con sistema legacy
- ✅ Configuración por entornos
- ✅ Logging estructurado
- ✅ Manejo de CORS
- ✅ Error handling centralizado

## Desarrollo

### Estructura de Archivos
- `api/`: Endpoints organizados por funcionalidad
- `config/`: Configuraciones de base de datos y aplicación
- `utils/`: Validadores y utilidades reutilizables

### Logging
El sistema usa logging estándar de Python. Los logs incluyen:
- Errores de base de datos
- Operaciones CRUD
- Validaciones fallidas
- Estado de conexiones

### Testing
Para ejecutar en modo testing:
```bash
FLASK_ENV=testing python main.py
```

## Producción

Para despliegue en producción:

1. **Con Gunicorn:**
```bash
gunicorn -w 4 -b 0.0.0.0:5000 backend.main:app
```

2. **Con Docker (ejemplo Dockerfile):**
```dockerfile
FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY . .
EXPOSE 5000
CMD ["gunicorn", "-w", "4", "-b", "0.0.0.0:5000", "backend.main:app"]
```

## Compatibilidad

Este backend mantiene compatibilidad total con el sistema anterior mediante rutas legacy, permitiendo migración gradual del frontend.