# Chatbot Archivo Patrimonial UAH

Sistema conversacional con IA para la búsqueda y recuperación de documentos del Archivo Patrimonial de la Universidad Alberto Hurtado.

## 📋 Descripción

Este chatbot utiliza técnicas de procesamiento de lenguaje natural y búsqueda semántica para ayudar a los usuarios a encontrar documentos históricos sin necesidad de conocer la terminología archivística.

## 🚀 Características

### Búsqueda Inteligente
- **Búsqueda semántica** con embeddings de Gemini AI
- Retorna hasta **15 documentos relevantes** por consulta
- Enlaces directos a los documentos en el archivo

### Sistema de Categorías (Nuevo)
- **📚 Materias**: 434 categorías únicas (Correspondencia, Derechos Humanos, Dictadura, etc.)
- **👤 Autores**: 635 autores e instituciones
- **📍 Lugares**: 338 ubicaciones geográficas

### Interfaz Moderna
- Diseño premium minimalista
- Acciones rápidas integradas
- Modal de navegación por categorías
- Enlaces que abren en nueva pestaña
- Botón "Volver al inicio"

---

## 🛠️ Archivos Principales

### Backend
| Archivo | Descripción |
|---------|-------------|
| `api_chatbot.py` | API Flask con endpoints de chat y categorías |
| `categories.json` | Categorías extraídas (materias, autores, lugares) |
| `clean_with_metadata.json` | Documentos con metadatos Dublin Core |
| `embeddings_cache.pkl` | Cache de embeddings precalculados |

### Frontend
| Archivo | Descripción |
|---------|-------------|
| `html/index.html` | Interfaz del chatbot con modal de categorías |

---

## 📡 API Endpoints

### POST /api/chat
Búsqueda semántica por consulta en lenguaje natural.

```json
// Request
{ "query": "documentos sobre derechos humanos" }

// Response
{
  "success": true,
  "response": "HTML con documentos encontrados"
}
```

### GET /api/categories
Retorna las categorías disponibles para navegación.

```json
// Response
{
  "success": true,
  "categories": {
    "materias": [{"name": "Correspondencia", "count": 1651}, ...],
    "autores": [...],
    "lugares": [...]
  }
}
```

### POST /api/search-by-category
Busca documentos por categoría específica.

```json
// Request
{
  "category_type": "materias",
  "category_name": "Derechos Humanos"
}

// Response
{
  "success": true,
  "results": [{"title": "...", "href": "..."}, ...]
}
```

### GET /api/health
Estado del servidor.

---

## 📊 Metadatos Dublin Core

Los documentos contienen los siguientes campos:

| Campo | Descripción |
|-------|-------------|
| `dc:title` | Título del documento |
| `dc:creator` | Autor o institución creadora |
| `dc:subject` | Materias y puntos de acceso |
| `dc:identifier` | Link al documento |
| `dc:coverage` | Ubicación geográfica |

---

## 🖥️ Ejecución

### Requisitos
- Python 3.8+
- Docker y Docker Compose
- Clave API de Gemini (`GEMINI_API_KEY`)

### Desarrollo Local
```bash
cd chatbot
pip install -r requirements.txt
python api_chatbot.py
```

### Con Docker
```bash
docker-compose up --build
```

### URLs
- **Frontend**: http://localhost:8080
- **API**: http://localhost:5000

---

## 📝 Registro de Cambios

### v2.1 - Diciembre 2024
- ✅ Sistema de categorías (Materias, Autores, Lugares)
- ✅ Endpoint `/api/categories`
- ✅ Endpoint `/api/search-by-category`
- ✅ Modal de navegación con pestañas
- ✅ Botón "📂 Categorías" en chatbot
- ✅ Retorno de 15 documentos por búsqueda
- ✅ Estilos mejorados para resultados
- ✅ Enlaces abren en nueva pestaña
- ✅ Scroll al inicio en respuestas
- ✅ Botón "Volver al inicio"

### v2.0 - Diciembre 2024
- ✅ Rediseño UI/UX premium
- ✅ Tipografía Playfair Display + Inter
- ✅ Paleta institucional UAH
- ✅ Acciones rápidas

---

## 👥 Equipo

**Jefe de Proyecto**: Sr. Nelson Adriazola - Jefe Archivo Institucional UAH

## 📄 Licencia

CC BY-NC-SA - Creative Commons Atribución-NoComercial-CompartirIgual
