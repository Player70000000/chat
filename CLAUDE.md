# CLAUDE.md - Sistema de Chat Empresa Limpieza

## 🚨 REGLAS CRÍTICAS - LEER OBLIGATORIAMENTE 🚨

### 📍 **REGLA #1: SIEMPRE ESPECIFICAR UBICACIÓN DE TRABAJO**
**OBLIGATORIO**: Antes de cualquier modificación, SIEMPRE especificar:
- **¿DÓNDE estoy trabajando?** (Producción vs Desarrollo)
- **¿QUÉ ÁREA específica?** (Backend, Frontend, Base de datos)
- **¿QUÉ ARCHIVO concreto?** (Ruta completa)

### 📍 **REGLA #2: COMUNICACIÓN 100% EN ESPAÑOL**
**OBLIGATORIO**: TODO en español sin excepción:
- Respuestas y explicaciones
- Comentarios de código
- Mensajes de commit
- Documentación

### 📍 **REGLA #3: CLARIDAD ABSOLUTA DE AMBIENTES**

#### 🏠 **AMBIENTE LOCAL (DESARROLLO)**
- **Ubicación física**: `/home/john/empresa-limpieza-chat/`
- **Backend local**: Puerto 5000 (solo testing)
- **Base de datos local**: NO CONECTA a MongoDB Atlas
- **Frontend**: Apunta SIEMPRE a producción
- **Propósito**: Solo para desarrollar y probar código
- **Impacto**: CERO - no afecta usuarios reales

#### ☁️ **AMBIENTE PRODUCCIÓN (USUARIOS REALES)**
- **Backend URL**: `https://chat-cv1i.onrender.com`
- **Base de datos**: MongoDB Atlas (CorpoTachiraDB)
- **Frontend**: Aplicación móvil de usuarios
- **Propósito**: Sistema real en uso
- **Impacto**: CRÍTICO - afecta usuarios reales

### 📍 **REGLA #4: PROCESO DE DEPLOYMENT OBLIGATORIO**
**Para que cambios lleguen a PRODUCCIÓN**:
1. Modificar código en LOCAL
2. `git add funciones/ *.py`
3. `git commit -m "Descripción en español"`
4. `git push origin main` ← **AQUÍ se actualiza producción**
5. Render redesplega automáticamente (2-3 minutos)

## 🔧 DEPLOYMENT A PRODUCCIÓN

### Proceso de Deploy (MÉTODO PROBADO ✅)
```bash
# 1. Ir al directorio correcto
cd /home/john/empresa-limpieza-chat/produccion/backend/

# 2. Verificar estado actual
git status

# 3. Agregar SOLO archivos de código
git add funciones/
git add *.py

# 4. Hacer commit descriptivo en español
git commit -m "Descripción clara del cambio

🤖 Generated with [Claude Code](https://claude.ai/code)

Co-Authored-By: Claude <noreply@anthropic.com>"

# 5. Push a GitHub (activa auto-deploy automático en Render)
git push origin main

# 6. Verificar deployment (2-3 minutos después)
curl -I "https://chat-cv1i.onrender.com/"
```

### ⚠️ Solución de Problemas GitHub Security
Si GitHub bloquea el push por "secrets detected":
```bash
# Reset y commit limpio (RECOMENDADO)
git reset --soft [COMMIT_ID_ANTERIOR]
git restore --staged CLAUDE.md  # Si contiene tokens
git commit -m "Fix: descripción del cambio"
git push origin main
```

## 📁 ESTRUCTURA DEL PROYECTO

### 🟢 **PRODUCCIÓN - `/produccion/`** (Usuarios Reales)

#### Backend en Render (`/produccion/backend/`)
```
/home/john/empresa-limpieza-chat/produccion/backend/
├── chat_backend.py                    # 🔥 Punto de entrada principal
├── .env                              # 🔐 Variables MongoDB Atlas
├── requirements.txt                   # 📦 Dependencias Python
├── render.yaml                       # ⚙️ Config deployment Render
├── CLAUDE.md                         # 📚 Este archivo
└── funciones/                        # 📂 Módulos especializados
    ├── __init__.py                   # 🔗 Inicialización
    ├── database_functions.py         # 🗄️ Conexión MongoDB Atlas
    ├── personnel_functions.py        # 👥 Gestión personal completa
    ├── chat_functions.py             # 💬 Sistema de chat completo
    └── utils_functions.py            # 🛠️ Utilidades generales
```

#### Frontend KivyMD (`/produccion/frontend/`)
```
/home/john/empresa-limpieza-chat/produccion/frontend/
├── main.py                           # 🚀 Aplicación principal
├── config.py                         # ⚙️ Configuración API URLs
├── requirements.txt                  # 📦 Dependencias KivyMD
└── screens/                          # 📱 Pantallas de la app
    ├── chat_screen.py                # 💬 Pantalla de chat
    ├── personal_screen.py            # 👥 Gestión completa de personal
    └── reportes_screen.py            # 📊 Reportes y analytics
```

## 🗄️ BASE DE DATOS MONGODB ATLAS

### Conexión Producción
- **URI**: `mongodb+srv://jhon123:jhon123@cluster0.6lfqk.mongodb.net/CorpoTachiraDB`
- **Base**: `CorpoTachiraDB`
- **Estado**: ✅ Activa y funcionando

### Colecciones Principales

#### 👥 Colección `moderadores`
```json
{
  "_id": "ObjectId",
  "nombre": "string (requerido, sin números)",
  "apellidos": "string (requerido, sin números)",
  "cedula": "string (único, 6-10 dígitos)",
  "email": "string (único, formato válido)",
  "telefono": "string (único, mín. 10 dígitos)",
  "talla_ropa": "string (opcional: XS|S|M|L|XL|XXL)",
  "talla_zapatos": "string (opcional: 30-50)",
  "activo": "boolean (default: true)",
  "nivel": "string (default: 'moderador')",
  "fecha_creacion": "Date (auto)",
  "creado_por": "string (default: 'sistema')"
}
```

#### 👷‍♂️ Colección `obreros` (NUEVA v5.0)
```json
{
  "_id": "ObjectId",
  "nombre": "string (requerido, sin números)",
  "apellidos": "string (requerido, sin números)",
  "cedula": "string (único global, 6-10 dígitos)",
  "email": "string (único global, formato válido)",
  "telefono": "string (único global, mín. 10 dígitos)",
  "talla_ropa": "string (opcional: XS|S|M|L|XL|XXL)",
  "talla_zapatos": "string (opcional: 30-50)",
  "activo": "boolean (default: true)",
  "nivel": "string (default: 'obrero')",
  "fecha_creacion": "Date (auto)",
  "creado_por": "string (default: 'sistema')"
}
```

#### 💬 Colección `canales`
```json
{
  "_id": "ObjectId",
  "nombre": "string (único)",
  "descripcion": "string (opcional)",
  "creado": "Date",
  "activo": "boolean"
}
```

#### 📨 Colección `mensajes`
```json
{
  "_id": "ObjectId",
  "canal": "string (referencia a canal)",
  "mensaje": "string (max 1000 chars)",
  "usuario": "string",
  "timestamp": "Date",
  "estado": "string (enviado/entregado/leido/editado)"
}
```

## 📋 ESTADO ACTUAL DEL SISTEMA (v5.0 - ACTUALIZADO)

### ✅ **FUNCIONALIDADES COMPLETAMENTE IMPLEMENTADAS**

#### 🎯 **GESTIÓN DE PERSONAL (100% COMPLETO)**

##### **MODERADORES (v4.0)**
- ✅ **CRUD Completo**: Create, Read, Update, Delete
- ✅ **Interfaz UX avanzada**: Dialogs con scroll, validaciones tiempo real
- ✅ **Eliminación segura**: Doble confirmación con advertencia irreversible
- ✅ **Validaciones robustas**: Nombres sin números, emails formato correcto
- ✅ **Tallas optimizadas**: Dropdown XS-XXL, validación zapatos 30-50

##### **OBREROS (v5.0 - NUEVA FUNCIONALIDAD)**
- ✅ **CRUD Completo**: Create, Read, Update, Delete (idéntico a moderadores)
- ✅ **Interfaz UX consistente**: Mismos dialogs, mismo comportamiento
- ✅ **Validaciones idénticas**: Mismas reglas que moderadores
- ✅ **Navegación fluida**: Flujo igual en ambos módulos
- ✅ **Estilos uniformes**: Colores, botones y layouts coincidentes

##### **🔒 VALIDACIÓN CRUZADA (v5.0 - CRÍTICA)**
- ✅ **Unicidad global**: Cédulas, emails y teléfonos únicos en TODO el sistema
- ✅ **Prevención duplicados**: No se repiten datos entre moderadores y obreros
- ✅ **Funciona en CREATE**: Al crear nuevos registros
- ✅ **Funciona en UPDATE**: Al editar registros existentes
- ✅ **Mensajes específicos**: Indica exactamente dónde está el duplicado

#### **Sistema de Chat (100% Funcional)**
- ✅ **Canales**: Crear, editar, eliminar canales
- ✅ **Mensajes**: Enviar, recibir, editar, eliminar mensajes
- ✅ **Estados**: Seguimiento de estados de mensajes
- ✅ **Tiempo real**: Actualizaciones inmediatas

#### **Base de Datos (100% Operativa)**
- ✅ **MongoDB Atlas**: Conectada y funcionando
- ✅ **Índices únicos**: Configurados para integridad
- ✅ **Validaciones**: Robustas en servidor
- ✅ **Respaldos**: Automáticos en Atlas

#### **Deployment (100% Automatizado)**
- ✅ **Render + GitHub**: Integración automática
- ✅ **Deploy continuo**: Push automático activa redespliegue
- ✅ **Monitoreo**: Sistema en producción estable

### 🔧 **ENDPOINTS API DISPONIBLES**
```
# GESTIÓN DE PERSONAL (COMPLETO)
GET    /api/personnel/moderadores/           # Listar moderadores
POST   /api/personnel/moderadores/           # Crear moderador
PUT    /api/personnel/moderadores/           # Actualizar moderador
DELETE /api/personnel/moderadores/           # Eliminar moderador

GET    /api/personnel/obreros/               # ✨ NUEVO: Listar obreros
POST   /api/personnel/obreros/               # ✨ NUEVO: Crear obrero
PUT    /api/personnel/obreros/               # ✨ NUEVO: Actualizar obrero
DELETE /api/personnel/obreros/               # ✨ NUEVO: Eliminar obrero

# SISTEMA DE CHAT (COMPLETO)
GET    /canales                             # Listar canales
POST   /crear_canal                         # Crear canal
GET    /canal/<nombre>                      # Obtener canal
PUT    /canal/<nombre>                      # Editar canal
DELETE /canal/<nombre>                      # Eliminar canal
POST   /enviar                              # Enviar mensaje
GET    /mensajes/<canal>                    # Obtener mensajes
PUT    /mensaje/<id>                        # Editar mensaje
DELETE /mensaje/<id>                        # Eliminar mensaje

# UTILIDADES (COMPLETO)
GET    /                                    # Página inicio
GET    /verificar                           # Verificar conexión
GET    /api/auth/status                     # Estado autenticación
```

## 🎯 **CARACTERÍSTICAS CLAVE v5.0**

### **Validaciones Avanzadas**
- ✅ Nombres/apellidos sin números (client + server)
- ✅ Emails formato correcto (@dominio.ext)
- ✅ Cédulas únicas globalmente (6-10 dígitos)
- ✅ Teléfonos únicos globalmente (mín. 10 dígitos)
- ✅ Tallas ropa dropdown (XS-XXL)
- ✅ Tallas zapatos validadas (30-50)
- ✅ Capitalización automática
- ✅ Validación cruzada moderadores ↔ obreros

### **Experiencia de Usuario**
- ✅ Diseño Material Design consistente
- ✅ Dialogs con scroll automático
- ✅ Confirmaciones de eliminación (doble)
- ✅ Mensajes de error específicos
- ✅ Navegación intuitiva
- ✅ Actualización automática de listas
- ✅ Campos prellenados en edición

### **Integridad de Datos**
- ✅ Validación cruzada entre módulos
- ✅ Prevención duplicados globales
- ✅ Timestamps de modificación
- ✅ Logging y auditoría
- ✅ Manejo robusto de errores

## 🚧 **FUNCIONALIDADES FUTURAS**
- 🚧 **Gestión de cuadrillas**: UI base creada
- 🚧 **Sistema de reportes avanzados**: Exportación de datos
- 🚧 **Autenticación de usuarios**: Login/logout
- 🚧 **Roles y permisos**: Control de acceso granular

## 🔍 **DEBUGGING Y VERIFICACIÓN**

### Verificar Estado del Sistema
```bash
# Verificar API producción
curl -I "https://chat-cv1i.onrender.com/"

# Verificar moderadores
curl -s "https://chat-cv1i.onrender.com/api/personnel/moderadores/" | python3 -m json.tool

# Verificar obreros
curl -s "https://chat-cv1i.onrender.com/api/personnel/obreros/" | python3 -m json.tool

# Probar validación cruzada
curl -X POST "https://chat-cv1i.onrender.com/api/personnel/obreros/" \
  -H "Content-Type: application/json" \
  -d '{"nombre": "Test", "apellidos": "Validacion", "cedula": "99999999", "email": "EMAIL_EXISTENTE_MODERADOR", "telefono": "04241111111"}'
```

### Problemas Comunes y Soluciones
1. **"Validación cruzada no funciona"**
   - ✅ Verificar: ¿Cambios desplegados en producción?
   - ✅ Hacer: `git push origin main` y esperar 2-3 minutos

2. **"API no responde"**
   - ✅ Verificar: `curl -I "https://chat-cv1i.onrender.com/"`
   - ✅ Revisar: Logs de Render

3. **"Push bloqueado por GitHub security"**
   - ✅ Usar: `git reset --soft [COMMIT_ANTERIOR]`
   - ✅ Evitar: Agregar CLAUDE.md con tokens

## 🏗️ **NUEVA ARQUITECTURA FRONTEND v6.0 - SISTEMA MODULAR**

### **🔥 ACTUALIZACIÓN CRÍTICA: MODULARIZACIÓN COMPLETA**
- **Problema Resuelto**: Dialog de edición de cuadrillas con layout roto
- **Arquitectura**: Sistema modular vs archivo monolítico (5,116 líneas)
- **Separación**: 8 módulos especializados + coordinador principal
- **Mantenibilidad**: 94% reducción en archivo principal

### **📂 Nueva Estructura Frontend**
```
/produccion/frontend/screens/
├── personal_screen.py              # 🎯 COORDINADOR (322 líneas)
└── personal_modules/               # 📂 MÓDULOS ESPECIALIZADOS
    ├── cuadrillas_manager.py      # 🚧 Gestión cuadrillas + FIX dialog
    ├── moderadores_manager.py     # 👤 Gestión moderadores
    ├── obreros_manager.py         # 👷 Gestión obreros
    ├── api_client.py              # 🌐 Cliente HTTP centralizado
    ├── validators.py              # ✅ Validaciones centralizadas
    ├── ui_components.py           # 🎨 Componentes reutilizables
    ├── utils.py                   # 🛠️ Utilidades generales
    └── __init__.py                # 📦 Configuración módulos
```

### **✅ Funcionalidades Mejoradas v6.0**
- ✅ **Dialog de Cuadrillas**: Fix completo del problema de layout
- ✅ **Managers Independientes**: CRUD completo por módulo
- ✅ **Navegación Optimizada**: MenuPrincipal → Managers especializados
- ✅ **Componentes Reutilizables**: Dialogs, validaciones, API client
- ✅ **Compatibilidad**: 100% retrocompatible con main.py

### **🔧 Problemas Técnicos Resueltos**
- ✅ **Layout roto**: `adaptive_height + MDScrollView` → altura fija calculada
- ✅ **Código duplicado**: Centralizado en módulos especializados
- ✅ **Mantenibilidad**: Archivos de 200-800 líneas vs 5,116
- ✅ **Escalabilidad**: Fácil agregar nuevos managers

## 📊 **RESUMEN TÉCNICO**

### **Versión Actual**
- **Sistema**: `v6.0 - Arquitectura Modular + Fixes Críticos`
- **Backend**: Flask + MongoDB Atlas
- **Frontend**: KivyMD Material Design Modular
- **Deployment**: Render + GitHub (automático)
- **Estado**: ✅ **100% OPERATIVO EN PRODUCCIÓN**

### **Últimos Commits Importantes v6.0**
- **Modularización completa**: personal_screen.py → 8 módulos especializados
- **Fix crítico**: Dialog de edición de cuadrillas completamente funcional
- **Coordinador**: personal_screen.py como puente entre módulos y main.py
- **Compatibilidad**: Integración sin romper funcionalidad existente

### **Módulos Completados**
- ✅ **Gestión de Personal**: Moderadores + Obreros + Cuadrillas (CRUD modular)
- ✅ **Sistema de Chat**: Canales + Mensajes (funcional)
- ✅ **Base de Datos**: MongoDB Atlas (operativa)
- ✅ **Deployment**: Automático (GitHub → Render)
- ✅ **Arquitectura Modular**: Sistema escalable y mantenible

---

**📅 Última actualización**: Arquitectura modular frontend v6.0
**🏷️ Versión actual**: `PRODUCCIÓN v6.0 - Sistema Modular + Fixes Críticos`
**📊 Estado**: ✅ **SISTEMA COMPLETAMENTE OPERATIVO Y OPTIMIZADO**
**🆕 Funcionalidad**: Arquitectura modular + Dialog cuadrillas arreglado
**🔒 Seguridad**: Unicidad garantizada + validaciones centralizadas
**🏗️ Arquitectura**: Mantenible, escalable y bien estructurada