# Empresa Limpieza - Mobile App

Aplicación móvil desarrollada con KivyMD para el sistema de chat y gestión de personal de la empresa de limpieza.

## Características

- **Chat**: Sistema de canales de chat en tiempo real
- **Personal**: Gestión de cuadrillas y empleados  
- **Reportes**: Sistema de reportes y estadísticas
- **Material Design**: Interfaz moderna y responsive
- **API REST**: Integración con backend en Render

## Instalación

1. **Prerrequisitos**
   ```bash
   python3 -m pip install --upgrade pip
   ```

2. **Instalar dependencias**
   ```bash
   cd frontend/mobile
   pip install -r requirements.txt
   ```

3. **Configuración**
   ```bash
   # Copiar template de configuración
   cp .env.template .env
   
   # Editar .env con tus valores
   nano .env
   ```

## Ejecución

```bash
cd frontend/mobile
python3 main.py
```

## Estructura del Proyecto

```
frontend/mobile/
├── main.py                 # Punto de entrada principal
├── config.py              # Configuración de la app
├── requirements.txt        # Dependencias Python
├── .env.template          # Template de configuración
├── screens/               # Pantallas de la aplicación
│   ├── __init__.py
│   ├── chat_screen.py     # Sistema de chat
│   ├── personal_screen.py # Gestión de personal
│   └── reportes_screen.py # Sistema de reportes
└── kv/                    # Archivos de layout KivyMD
    ├── main.kv
    ├── chat.kv
    ├── personal.kv
    └── reportes.kv
```

## API Endpoints

La aplicación se conecta a estos endpoints del backend:

### Chat
- `GET /canales` - Listar canales
- `POST /crear_canal` - Crear nuevo canal
- `GET /mensajes/{canal}` - Obtener mensajes
- `POST /enviar` - Enviar mensaje

### Personal
- `GET /api/personnel/cuadrillas` - Listar cuadrillas
- `POST /api/personnel/cuadrillas` - Crear cuadrilla
- `PUT /api/personnel/cuadrillas/{id}` - Actualizar cuadrilla
- `DELETE /api/personnel/cuadrillas/{id}` - Eliminar cuadrilla
- `GET /api/personnel/empleados` - Listar empleados
- `POST /api/personnel/empleados` - Registrar empleado
- `DELETE /api/personnel/empleados/{id}` - Eliminar empleado

### Reportes
- `GET /api/reports/general` - Reporte general
- `GET /api/reports/cuadrillas` - Reporte de cuadrillas
- `GET /api/reports/actividad` - Reporte de actividad

## Configuración

### Variables de Entorno (.env)

```env
API_URL=https://chat-cv1i.onrender.com
USUARIO=UsuarioMovil
REQUEST_TIMEOUT=10
MAX_RETRIES=3
```

### Configuración de Ventana

La aplicación está optimizada para dispositivos móviles con una resolución base de 360x640px.

## Tecnologías

- **KivyMD 1.1+**: Framework de UI Material Design
- **Kivy 2.1+**: Framework de aplicaciones Python multiplataforma
- **Requests**: Cliente HTTP para API REST
- **Python-dotenv**: Gestión de variables de entorno

## Desarrollo

### Estructura de Screens

Cada pantalla hereda de `MDBoxLayout` o `MDScreen` y implementa:

- `setup_ui()`: Configuración de la interfaz
- `load_data()`: Carga de datos desde API
- `handle_errors()`: Manejo de errores de conexión

### Patrones de Navegación

- **BottomNavigation**: Navegación principal entre Chat, Personal y Reportes
- **ScreenManager**: Navegación interna dentro de cada sección
- **Modal Dialogs**: Para formularios y confirmaciones

## Resolución de Problemas

### Error de conexión API
- Verificar que el backend esté funcionando en Render
- Comprobar la URL en el archivo `.env`
- Verificar conexión a internet

### Problemas de dependencias
```bash
pip install --upgrade kivymd kivy requests python-dotenv
```

### Problemas de pantalla
- La aplicación está optimizada para móvil
- Usar `Window.size = (360, 640)` para simular móvil en desktop