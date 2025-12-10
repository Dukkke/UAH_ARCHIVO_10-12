"""
API Chatbot del Archivo Patrimonial UAH - Versión con Patrones de Diseño
=========================================================================

PATRONES DE DISEÑO IMPLEMENTADOS:
=================================

1. ABSTRACT FACTORY (Creacional) - services/factory.py
   ├── AbstractServiceFactory (ABC)
   │   ├── GeminiServiceFactory  → Servicios con API de Gemini
   │   ├── LocalServiceFactory   → Servicios locales sin API
   │   └── MockServiceFactory    → Servicios mock para testing
   └── Métodos: create_embedder(), create_responder(), create_llm_proxy()

2. PROXY (Estructural) - services/llm_proxy.py
   ├── LLMProxy (ABC)
   │   ├── GeminiClientProxy     → Protection Proxy (circuit breaker)
   │   ├── CachingLLMProxy       → Caching Proxy (TTL 1 hora)
   │   ├── LoggingLLMProxy       → Logging Proxy (estadísticas)
   │   ├── NullLLMProxy          → Null Object (modo offline)
   │   └── MockLLMProxy          → Mock para testing
   └── Métodos: embed(), generate(), is_available()

3. STRATEGY (Comportamiento) - services/search_strategies.py
   ├── SearchStrategy (ABC)
   │   ├── ExactTitleSearchStrategy   → Match exacto en títulos
   │   ├── TFIDFSearchStrategy        → Búsqueda TF-IDF local
   │   ├── SemanticSearchStrategy     → Embeddings semánticos
   │   ├── MetadataSearchStrategy     → Dublin Core ponderado
   │   └── HybridSearchStrategy       → RRF fusion de estrategias
   └── Context: SearchContext(strategy).search(query, documents)

4. OBSERVER (Comportamiento) - services/events.py
   └── EventBus + LoggingObserver para logging de eventos

PRINCIPIOS SOLID APLICADOS:
===========================

[S] Single Responsibility (SRP):
    - Cada Strategy tiene una única responsabilidad (un algoritmo)
    - Cada Proxy tiene una única responsabilidad (una capa)
    - Cada Factory crea una familia específica de objetos

[O] Open/Closed (OCP):
    - Nuevas estrategias de búsqueda sin modificar SearchContext
    - Nuevas factories sin modificar código cliente
    - Nuevos proxies decorando los existentes

[L] Liskov Substitution (LSP):
    - Todas las SearchStrategy son intercambiables
    - Todos los LLMProxy son intercambiables
    - Todas las AbstractServiceFactory son intercambiables

[I] Interface Segregation (ISP):
    - LLMProxy: solo embed(), generate(), is_available()
    - SearchStrategy: solo search(), get_name()
    - Interfaces mínimas y específicas

[D] Dependency Inversion (DIP):
    - api_chatbot depende de AbstractServiceFactory, no de GeminiServiceFactory
    - SearchContext depende de SearchStrategy, no de implementaciones concretas
    - Inyección de dependencias en constructores

Funcionalidades:
- Detección de conversaciones casuales vs búsquedas
- Respuestas sin búsqueda para saludos/despedidas
- Búsqueda híbrida (exacta + TF-IDF + semántica + metadata)
- Enlaces a documentos específicos
- Manejo de errores robusto
- Puerto 5000 (Flask) + Frontend en 8080 (Nginx)
"""

import re
from datetime import datetime
from typing import List, Dict, Tuple, Optional, Callable
import random
import pickle
import json
import os
import traceback
import pytz

# Flask imports
from flask import Flask, request, jsonify, render_template
from flask_cors import CORS
import markdown

# Google Generative AI
import google.generativeai as genai
from dotenv import load_dotenv

# ============================================================================
# IMPORTACIÓN DE PATRONES DE DISEÑO
# ============================================================================

# ABSTRACT FACTORY Pattern (Creacional)
# Proporciona interfaz para crear familias de objetos relacionados
from services.factory import (
    AbstractServiceFactory,      # Interfaz abstracta (DIP)
    GeminiServiceFactory,        # Factory concreta para Gemini
    LocalServiceFactory,         # Factory concreta para modo offline
    ServiceFactory,              # Alias backward compatible
    create_service_factory       # Factory Method
)

# PROXY Pattern (Estructural)
# Controla acceso al servicio LLM con caching, logging, protección
from services.llm_proxy import (
    LLMProxy,                    # Interfaz abstracta (DIP)
    GeminiClientProxy,           # Protection Proxy
    CachingLLMProxy,             # Caching Proxy
    LoggingLLMProxy,             # Logging Proxy
    NullLLMProxy,                # Null Object Pattern
    create_production_proxy      # Factory Method para proxies
)

# STRATEGY Pattern (Comportamiento)
# Algoritmos de búsqueda intercambiables
from services.search_strategies import (
    SearchStrategy,              # Interfaz abstracta (DIP)
    ExactTitleSearchStrategy,    # Estrategia: match exacto
    TFIDFSearchStrategy,         # Estrategia: TF-IDF
    SemanticSearchStrategy,      # Estrategia: embeddings
    MetadataSearchStrategy,      # Estrategia: Dublin Core
    HybridSearchStrategy,        # Estrategia: combinación RRF
    SearchContext,               # Context del Strategy Pattern
    create_search_strategy       # Factory Method para estrategias
)

# OBSERVER Pattern (Comportamiento) + Strategy adicionales
from services.events import EventBus, LoggingObserver
from services.conversation import (
    ConversationSession, 
    IntentionDetector,           # Strategy: Detección de intención
    EntityExtractorImpl,         # Strategy: Extracción de entidades
    EntityExtractor,             # Alias backward compatible
    DocumentComparator,          # Strategy: Comparación de documentos
    FuzzyEntityExtractor,        # Strategy: Fuzzy matching
    FuzzyDocumentComparator,     # Strategy: Fuzzy similarity
    SynonymExpander,             # Strategy: Expansión de sinónimos
    DateRangeExtractor,          # Strategy: Extracción de fechas
    MetadataSearcher             # Composite: Búsqueda ponderada
)

# Machine Learning
import numpy as np
from sklearn.metrics.pairwise import cosine_similarity

# ============================================================================
# CONFIGURACIÓN INICIAL
# ============================================================================

app = Flask(__name__)
CORS(app)

# Configuración de Gemini
load_dotenv()
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "AIzaSyBnVgg33jVHSypAkDqv-6PFTtqK8-eh3dM")
GENAI_AVAILABLE = False

if GEMINI_API_KEY:
    try:
        genai.configure(api_key=GEMINI_API_KEY)
        GENAI_AVAILABLE = True
    except Exception as _e:
        GENAI_AVAILABLE = False
        print("⚠️ No se pudo inicializar Gemini. Continuando sin GENAI.")

embeddings_ready = False

# ============================================================================
# ABSTRACT FACTORY Pattern - Creación de servicios
# ============================================================================
# Principio DIP: Dependemos de la abstracción AbstractServiceFactory,
# no de la implementación concreta GeminiServiceFactory.
# Esto permite cambiar la factory sin modificar este código.

factory: AbstractServiceFactory = GeminiServiceFactory(genai, GENAI_AVAILABLE)

# ALTERNATIVE: Usar LocalServiceFactory para modo offline
# factory: AbstractServiceFactory = LocalServiceFactory()

# ============================================================================
# OBSERVER Pattern - Sistema de eventos
# ============================================================================
# Principio OCP: Nuevos observers pueden agregarse sin modificar el EventBus.
# Principio SRP: EventBus solo maneja suscripciones, observers manejan acciones.

event_bus = EventBus()
event_bus.subscribe('chat.received', LoggingObserver('[chat.received] '))
event_bus.subscribe('chat.type_detected', LoggingObserver('[chat.type_detected] '))
event_bus.subscribe('search.done', LoggingObserver('[search.done] '))
event_bus.subscribe('response.generated', LoggingObserver('[response.generated] '))

# Almacenamiento de sesiones conversacionales (en memoria para MVP)
conversation_sessions = {}

# ============================================================================
# STRATEGY Pattern - Estrategias de conversación (DIP)
# ============================================================================
# Principio DIP: Inyección de dependencias - instancias intercambiables.
# Principio OCP: Nuevas estrategias sin modificar código existente.
# Principio LSP: Todas las estrategias son intercambiables.

# Strategy: Detección de intención del usuario
intention_detector = IntentionDetector()

# Strategy: Extracción de entidades con fuzzy matching (tolera typos)
entity_extractor = FuzzyEntityExtractor()

# Strategy: Comparación de documentos
document_comparator = DocumentComparator()

# Strategy: Expansión de sinónimos para búsquedas
synonym_expander = SynonymExpander()

# Strategy: Extracción de rangos de fechas históricas
date_extractor = DateRangeExtractor()

# ============================================================================
# STRATEGY Pattern - Estrategia de búsqueda híbrida
# ============================================================================
# Principio OCP: Nuevas estrategias de búsqueda sin modificar SearchContext.
# Principio DIP: SearchContext depende de SearchStrategy abstracción.

# Crear estrategia híbrida que combina múltiples algoritmos
search_strategy: SearchStrategy = HybridSearchStrategy()

# Agregar estrategias con sus pesos (principio Composite)
search_strategy.add_strategy(ExactTitleSearchStrategy(), weight=1.5)
search_strategy.add_strategy(MetadataSearchStrategy(), weight=1.2)
search_strategy.add_strategy(TFIDFSearchStrategy(), weight=1.0)

# Context del Strategy Pattern
search_context = SearchContext(search_strategy)

# ============================================================================
# ============================================================================

def load_documents():
    """Carga los documentos desde clean_with_metadata.json"""
    try:
        with open('clean_with_metadata.json', 'r', encoding='utf-8', errors="ignore") as f:
            docs = json.load(f)
        print(f"✅ Documentos cargados: {len(docs)}")
        return docs
    except FileNotFoundError:
        print("❌ Archivo clean_with_metadata.json no encontrado")
        return []
    except Exception as e:
        print(f"❌ Error cargando documentos: {e}")
        return []

documents = load_documents()

# ============================================================================
# ÍNDICE TF-IDF LOCAL (sin necesidad de API)
# ============================================================================

def load_tfidf_index():
    """Carga el índice TF-IDF local para búsqueda sin API"""
    try:
        with open('search_index.pkl', 'rb') as f:
            index_data = pickle.load(f)
        print(f"✅ Índice TF-IDF cargado: {index_data['matrix'].shape[0]} docs x {index_data['matrix'].shape[1]} términos")
        return index_data
    except FileNotFoundError:
        print("⚠️ search_index.pkl no encontrado. Ejecuta create_search_index.py primero.")
        return None
    except Exception as e:
        print(f"⚠️ Error cargando índice TF-IDF: {e}")
        return None

tfidf_index = load_tfidf_index()

def search_exact_title(query, top_k=15):
    """
    Búsqueda EXACTA por título - prioriza matches exactos y parciales.
    Se ejecuta ANTES de TF-IDF para encontrar documentos con título exacto.
    """
    query_lower = query.lower().strip()
    results = []
    
    for idx, doc in enumerate(documents):
        title = doc.get('title', '').lower()
        href = doc.get('href', '').lower()
        
        score = 0
        
        # Match exacto de título (máxima prioridad)
        if query_lower == title:
            score = 1.0
        # Título contiene la query completa
        elif query_lower in title:
            score = 0.9
        # Query contiene el título completo
        elif title and title in query_lower:
            score = 0.85
        # Match en URL/href
        elif query_lower.replace(' ', '-') in href or query_lower.replace(' ', '') in href:
            score = 0.8
        # Match parcial de palabras clave
        else:
            query_words = set(query_lower.split())
            title_words = set(title.split())
            common = query_words & title_words
            if len(common) >= 3:  # Al menos 3 palabras en común
                score = 0.6 + (len(common) / len(query_words)) * 0.2
        
        if score > 0.5:
            doc_copy = doc.copy()
            doc_copy['relevance_score'] = score
            doc_copy['_match_type'] = 'exact_title'
            results.append((score, idx, doc_copy))
    
    # Ordenar por score descendente
    results.sort(key=lambda x: x[0], reverse=True)
    
    return [r[2] for r in results[:top_k]]

def search_with_tfidf(query, top_k=15):
    """Búsqueda usando TF-IDF local (rápida, sin API)"""
    if not tfidf_index:
        return []
    
    try:
        vectorizer = tfidf_index['vectorizer']
        tfidf_matrix = tfidf_index['matrix']
        
        # Vectorizar la consulta
        query_vector = vectorizer.transform([query])
        
        # Calcular similitudes usando coseno
        from sklearn.metrics.pairwise import cosine_similarity
        similarities = cosine_similarity(query_vector, tfidf_matrix).flatten()
        
        # Obtener índices de los top_k más similares
        top_indices = similarities.argsort()[-top_k:][::-1]
        
        results = []
        for idx in top_indices:
            if idx < len(documents) and similarities[idx] > 0.01:  # Umbral mínimo
                doc = documents[idx].copy()
                doc['relevance_score'] = float(similarities[idx])
                results.append(doc)
        
        return results
    except Exception as e:
        print(f"❌ Error en búsqueda TF-IDF: {e}")
        return []

def load_embeddings():
    """
    Carga embeddings desde pickle.
    
    Soporta dos formatos:
    1. Dict con claves 'embeddings', 'texts', 'documents' (embeddings_oficial.pkl)
    2. Dict simple {idx: embedding} (embeddings_cache.pkl antiguo)
    """
    embeddings_files = ['embeddings_compatible.pkl', 'embeddings_oficial.pkl', 'embeddings_cache.pkl']
    
    for filename in embeddings_files:
        try:
            with open(filename, 'rb') as f:
                data = pickle.load(f)
            
            # Formato 1: Dict estructurado con claves 'embeddings', 'texts', 'documents'
            if isinstance(data, dict) and 'embeddings' in data:
                embeddings_array = data['embeddings']
                num_embeddings = len(embeddings_array) if hasattr(embeddings_array, '__len__') else 0
                if num_embeddings > 0:
                    print(f"✅ Embeddings cargados desde {filename}: {num_embeddings} documentos")
                    # Retornar el diccionario completo para acceso a embeddings, texts, documents
                    return data
            
            # Formato 2: Dict simple {idx: embedding}
            elif isinstance(data, dict) and len(data) > 0:
                # Verificar si las claves son índices numéricos
                first_key = next(iter(data.keys()), None)
                if isinstance(first_key, int) or (isinstance(first_key, str) and first_key.isdigit()):
                    print(f"✅ Embeddings cargados desde {filename}: {len(data)} documentos")
                    return data
                    
        except FileNotFoundError:
            continue
        except Exception as e:
            print(f"⚠️ Error cargando {filename}: {e}")
            continue
    
    print("⚠️ No se encontraron embeddings precalculados. Usando búsqueda TF-IDF.")
    return {}

def create_embeddings_fallback():
    """Crea embeddings nuevos de manera optimizada (por lotes)"""
    embeddings = {}
    try:
        if not GENAI_AVAILABLE:
            print("❌ GENAI no disponible; no se pueden crear embeddings nuevos.")
            return {}
        print("🔄 Generando embeddings nuevos (Optimizado por lotes)...")
        
        batch_size = 100
        texts_to_embed = []
        indices_map = []
        
        # Preparar textos
        for idx, doc in enumerate(documents):
            text = f"{doc['title']} {doc['href']}"
            texts_to_embed.append(text)
            indices_map.append(idx)
            
        total_docs = len(texts_to_embed)
        
        # Procesar en lotes
        for i in range(0, total_docs, batch_size):
            batch_texts = texts_to_embed[i:i + batch_size]
            batch_indices = indices_map[i:i + batch_size]
            
            try:
                # Llamada batch a la API
                result = genai.embed_content(
                    model="models/text-embedding-004",
                    content=batch_texts,
                    task_type="retrieval_document"
                )
                
                # Extraer embeddings del resultado
                if 'embedding' in result:
                    batch_embeddings = result['embedding']
                    for j, embed in enumerate(batch_embeddings):
                        original_idx = batch_indices[j]
                        embeddings[original_idx] = embed
                
                print(f"   Procesados {min(i + batch_size, total_docs)}/{total_docs} documentos")
                
            except Exception as e:
                print(f"❌ Error en lote {i}-{i+batch_size}: {e}")
                # Fallback: intentar uno por uno en este lote si falla el batch
                for j, text in enumerate(batch_texts):
                    try:
                        res = genai.embed_content(
                            model="models/text-embedding-004",
                            content=text,
                            task_type="retrieval_document"
                        )
                        embeddings[batch_indices[j]] = res['embedding']
                    except Exception as inner_e:
                        print(f"   ❌ Error en documento individual: {inner_e}")
                        continue
        
        # Guardar cache
        try:
            with open('embeddings_cache.pkl', 'wb') as f:
                pickle.dump(embeddings, f)
            print(f"💾 Cache guardado: embeddings_cache.pkl")
        except Exception as e:
            print(f"⚠️ No se pudo guardar cache: {e}")
            
        print(f"✅ Embeddings creados: {len(embeddings)} documentos")
        return embeddings
        
    except Exception as e:
        print(f"❌ Error crítico creando embeddings: {e}")
        return {}

document_embeddings = load_embeddings()

def get_embeddings_count(emb_data):
    """Helper para obtener el conteo correcto de embeddings."""
    if isinstance(emb_data, dict) and 'embeddings' in emb_data:
        return len(emb_data['embeddings'])
    return len(emb_data) if emb_data else 0

embeddings_ready = bool(document_embeddings)
embeddings_count = get_embeddings_count(document_embeddings)

# ============================================================================
# BÚSQUEDA SEMÁNTICA
# ============================================================================

def search_documents(query, top_k=15, include_suggestions=True):
    """
    Busca documentos usando similitud semántica
    Retorna hasta top_k documentos más relevantes y sugerencias de refinamiento
    """
    try:
        # Normalizar query
        normalized_query = normalize_query(query)
        print(f"🔍 Query normalizada: '{normalized_query}'")
        
        # PASO 1: Buscar matches EXACTOS por título primero
        exact_results = search_exact_title(query, top_k)
        if exact_results:
            print(f"✅ Búsqueda exacta encontró {len(exact_results)} documentos")
            suggestions = generate_search_suggestions(query, exact_results) if include_suggestions else []
            return exact_results, suggestions
        
        # PASO 2: Si no hay matches exactos, usar TF-IDF
        if tfidf_index:
            print("🔄 Usando búsqueda TF-IDF local...")
            results = search_with_tfidf(normalized_query, top_k)
            if results:
                print(f"📄 TF-IDF encontró {len(results)} documentos")
                suggestions = generate_search_suggestions(query, results) if include_suggestions else []
                return results, suggestions
            else:
                print("⚠️ TF-IDF sin resultados; probando keywords...")
        
        # PASO 3: Fallback a búsqueda por keywords
        results = search_by_keywords(normalized_query, top_k)
        suggestions = generate_search_suggestions(query, results) if include_suggestions else []
        return results, suggestions
        
        # Generar embedding de la consulta (via factory/proxy)
        query_embedder = factory.make_query_embedding()
        query_embedding = None
        embed = query_embedder(normalized_query)
        if embed is None:
            # Fallback a búsqueda por keywords si no hay embedding
            print("⚠️ No se pudo generar embedding; usando búsqueda por keywords...")
            results = search_by_keywords(normalized_query, top_k)
            suggestions = generate_search_suggestions(query, results) if include_suggestions else []
            return results, suggestions
        else:
            query_embedding = embed

        # Calcular similitudes
        similarities = []
        for idx, doc_embedding in document_embeddings.items():
            similarity = cosine_similarity(
                [query_embedding],
                [doc_embedding]
            )[0][0]
            similarities.append((idx, similarity))

        # Ordenar por similitud
        similarities.sort(key=lambda x: x[1], reverse=True)

        # Retornar top_k documentos
        results = []
        for idx, score in similarities[:top_k]:
            if idx < len(documents):
                doc = documents[idx].copy()
                doc['relevance_score'] = float(score)
                results.append(doc)

        print(f"📄 Encontrados {len(results)} documentos relevantes")
        
        # Generar sugerencias si se solicita
        suggestions = []
        if include_suggestions:
            suggestions = generate_search_suggestions(query, results)
            if suggestions:
                print(f"💡 Generadas {len(suggestions)} sugerencias de refinamiento")
        
        event_bus.publish('search.done', {'query': normalized_query, 'results_count': len(results), 'suggestions_count': len(suggestions)})
        return results, suggestions
        
    except Exception as e:
        print(f"❌ Error en búsqueda: {e}")
        traceback.print_exc()
        return [], []

# ============================================================================
# NORMALIZACIÓN DE QUERIES
# ============================================================================

def is_query_too_generic(query, min_word_length=15):
    """Detecta si una consulta es muy genérica y necesita refinamiento"""
    # Términos muy amplios que suelen dar muchos resultados poco específicos
    generic_terms = [
        'dictadura', 'gobierno', 'política', 'documentos', 'archivos',
        'historia', 'chile', 'información', 'datos', 'material',
        'fotografías', 'fotos', 'imágenes', 'derechos', 'humanos',
        'partido', 'movimiento', 'organización'
    ]
    
    query_lower = query.lower().strip()
    words = query_lower.split()
    
    # Si la consulta es muy corta (1-2 palabras) y coincide con términos genéricos
    if len(words) <= 2 and len(query_lower) < min_word_length:
        if any(term in query_lower for term in generic_terms):
            return True
    
    return False

def extract_categories_from_results(results):
    """Analiza títulos de resultados para extraer categorías/temas comunes"""
    if not results:
        return []
    
    import re
    from collections import Counter
    
    # Extraer palabras clave significativas de los títulos
    keywords = []
    for doc in results:
        title = doc.get('title', '')
        # Extraer años
        years = re.findall(r'\b(19\d{2}|20\d{2})\b', title)
        keywords.extend(years)
        
        # Extraer palabras significativas (>3 caracteres, no stopwords)
        stopwords = {'de', 'la', 'el', 'los', 'las', 'del', 'para', 'por', 'con', 'en', 'a', 'y', 'o', 'un', 'una'}
        words = re.findall(r'\b[a-záéíóúñ]{4,}\b', title.lower())
        keywords.extend([w for w in words if w not in stopwords])
    
    # Contar frecuencias
    counter = Counter(keywords)
    # Retornar las 5 más comunes (excluyendo la consulta original)
    return [word for word, count in counter.most_common(8) if count > 1]

def generate_search_suggestions(query, results):
    """Genera sugerencias de refinamiento basadas en consulta y resultados"""
    suggestions = []
    categories = extract_categories_from_results(results)
    
    query_lower = query.lower()
    
    # Sugerencias basadas en categorías encontradas
    if categories:
        # Filtrar categorías que ya están en la query
        new_categories = [cat for cat in categories[:5] if cat not in query_lower]
        if new_categories:
            suggestions.append({
                'type': 'refine_by_category',
                'message': '🎯 **Refina tu búsqueda combinando con estos temas:**',
                'options': new_categories
            })
    
    # Detectar si hay años en los resultados
    import re
    years_in_results = set()
    for doc in results:
        years = re.findall(r'\b(19\d{2}|20\d{2})\b', doc.get('title', ''))
        years_in_results.update(years)
    
    if years_in_results and not re.search(r'\b(19\d{2}|20\d{2})\b', query):
        sorted_years = sorted(years_in_results)[:5]
        suggestions.append({
            'type': 'add_year',
            'message': '📅 **Prueba especificar un año:**',
            'options': sorted_years
        })
    
    # Sugerencias de especificidad
    if is_query_too_generic(query):
        suggestions.append({
            'type': 'be_more_specific',
            'message': '💡 **Tu búsqueda es amplia. Prueba siendo más específico:**',
            'options': [
                f'"{query} años 70"',
                f'"{query} 1973"',
                f'"{query} documentos"',
                f'"{query} fotografías"'
            ]
        })
    
    return suggestions

def normalize_query(query):
    """Normaliza y expande consultas para mejor búsqueda"""
    import unicodedata
    
    if not isinstance(query, str):
        return ""
        
    normalized = query.lower().strip()
    
    # Remover acentos
    normalized = ''.join(
        c for c in unicodedata.normalize('NFD', normalized)
        if unicodedata.category(c) != 'Mn'
    )
    
    # Stemming básico para plurales (igual que en create_search_index.py)
    words = normalized.split()
    stemmed_words = []
    for word in words:
        # Si termina en 'es' (árboles -> árbol, canciones -> cancion)
        if word.endswith('es') and len(word) > 4:
            word = word[:-2]
        # Si termina en 's' (casas -> casa)
        elif word.endswith('s') and len(word) > 3 and not word.endswith('ss'):
            word = word[:-1]
        stemmed_words.append(word)
    
    normalized = ' '.join(stemmed_words)
    
    # Mapeo de términos y abreviaturas comunes
    term_mapping = {
        'dicta': 'dictadura militar',
        'ddhh': 'derechos humanos',
        'dd.hh': 'derechos humanos',
        'dd hh': 'derechos humanos',
        'mir': 'movimiento izquierda revolucionaria',
        'pc': 'partido comunista',
        'ps': 'partido socialista',
        'pdc': 'partido democrata cristiano',
        'golpe': 'golpe estado 1973',
        'pinochet': 'dictadura militar pinochet',
        'allende': 'salvador allende',
        'aylwin': 'patricio aylwin',
        '73': '1973',
        '74': '1974',
        '75': '1975',
        '76': '1976',
        '80': '1980',
        '90': '1990',
        'fotos': 'fotografias',
        'imagenes': 'fotografias',
        'pics': 'fotografias',
    }
    
    # Aplicar mapeo
    for abbrev, full_term in term_mapping.items():
        if abbrev in normalized:
            normalized = normalized.replace(abbrev, full_term)
    
    return normalized

def search_by_keywords(query, top_k=6):
    """Búsqueda fallback por palabras clave cuando GENAI no está disponible"""
    query_lower = query.lower()
    query_words = set(query_lower.split())
    
    scored_docs = []
    for idx, doc in enumerate(documents):
        title_lower = doc['title'].lower()
        # Calcular score basado en coincidencias de palabras
        title_words = set(title_lower.split())
        common_words = query_words.intersection(title_words)
        
        # Score: número de palabras en común + bonus por coincidencia exacta
        score = len(common_words)
        if query_lower in title_lower:
            score += 10  # Bonus por substring exacto
        
        if score > 0:
            doc_copy = doc.copy()
            doc_copy['relevance_score'] = float(score)
            scored_docs.append((score, idx, doc_copy))
    
    # Ordenar por score descendente
    scored_docs.sort(key=lambda x: x[0], reverse=True)
    
    # Retornar top_k
    results = [doc for _, _, doc in scored_docs[:top_k]]
    print(f"📄 Encontrados {len(results)} documentos por keywords")
    return results
    
    # Remover acentos
    normalized = ''.join(
        c for c in unicodedata.normalize('NFD', normalized)
        if unicodedata.category(c) != 'Mn'
    )
    
    # Mapeo de términos y abreviaturas comunes
    term_mapping = {
        'dicta': 'dictadura militar',
        'ddhh': 'derechos humanos',
        'dd.hh': 'derechos humanos',
        'dd hh': 'derechos humanos',
        'mir': 'movimiento izquierda revolucionaria',
        'pc': 'partido comunista',
        'ps': 'partido socialista',
        'pdc': 'partido democrata cristiano',
        'golpe': 'golpe estado 1973',
        'pinochet': 'dictadura militar pinochet',
        'allende': 'salvador allende',
        'aylwin': 'patricio aylwin',
        '73': '1973',
        '74': '1974',
        '75': '1975',
        '76': '1976',
        '80': '1980',
        '90': '1990',
        'fotos': 'fotografias',
        'imagenes': 'fotografias',
        'pics': 'fotografias',
    }
    
    # Aplicar mapeo
    for abbrev, full_term in term_mapping.items():
        if abbrev in normalized:
            normalized = normalized.replace(abbrev, full_term)
    
    return normalized

# ============================================================================
# DETECCIÓN DE TIPO DE CONVERSACIÓN
# ============================================================================

def detect_conversation_type(query):
    """
    Detecta el tipo de conversación del usuario
    Retorna: 'greeting', 'farewell', 'gratitude', 'help', 'smalltalk', 'search'
    """
    query_lower = query.lower().strip()
    
    # Eliminar puntuación
    query_clean = re.sub(r'[¿?¡!.,;:]', '', query_lower)
    
    # Patrones de saludos
    greetings = [
        r'^(hola|hello|hi|hey|ola)\s*(,|buenas?|días?|dias?|noches?|tardes?)?$',  # "hola", "hola buenas", "hola días"
        r'^(buenas|buenos)\s*(noches?|días?|dias?|tardes?)?$',  # "buenas", "buenas noches"
        r'^buen(os|as)?\s+(día|dia|días|dias|tarde|tardes|noche|noches)$',
        r'^(qué|que)\s+tal$',
        r'^cómo\s+(estás|estas|está|esta)$',
        r'^saludos$',
        r'^\s*(hola\s+)?buen(os|as)?\s*$',  # "buenos" o "hola buenos"
    ]
    
    # Patrones de despedida
    farewells = [
        r'\b(adiós|adios|chao|chau|bye|hasta\s+luego|nos\s+vemos)\b',
        r'\bgracias?\s+(por\s+todo|y\s+adiós|y\s+adios)\b',
        r'^(chao|adios|adiós|bye)$',
    ]
    
    # Patrones de agradecimiento
    gratitude = [
        r'^(gracias|muchas\s+gracias|mil\s+gracias)$',
        r'^(gracias|thank\s+you)$',
        r'^(excelente|genial|perfecto|muy\s+bien)$',
        r'^\bte\s+agradezco\b$',
    ]
    
    # Patrones de ayuda
    help_patterns = [
        r'\b(ayuda|ayudar|ayúdame|help)\b',
        r'^(qué|que)\s+(puedes?|hace|ofrece|tiene)$',
        r'^cómo\s+(funciona|usar|buscar|te\s+uso)$',
        r'^(información|info|explica|cuéntame)\s+(sobre|del|de)?\s*(bot|chatbot|ti)?$',
        r'^qué\s+es\s+esto$',
        r'^para\s+qué\s+sirve',
    ]
    
    # Patrones de smalltalk
    smalltalk = [
        r'^(cómo|como)\s+(te\s+llamas?|eres|funcionas)$',
        r'^(quién|quien)\s+eres$',
        r'^(qué|que)\s+(eres|haces)$',
        r'^\bestás\s+(bien|ahí)$',
        r'^eres\s+(un\s+)?(bot|robot|ia|inteligencia)$',
    ]
    
    # Verificar cada categoría
    for pattern in greetings:
        if re.search(pattern, query_clean):
            return 'greeting'
    
    for pattern in farewells:
        if re.search(pattern, query_clean):
            return 'farewell'
    
    for pattern in gratitude:
        if re.search(pattern, query_clean):
            return 'gratitude'
    
    for pattern in help_patterns:
        if re.search(pattern, query_clean):
            return 'help'
    
    for pattern in smalltalk:
        if re.search(pattern, query_clean):
            return 'smalltalk'
    
    # Palabras casuales cortas
    words = query_clean.split()
    if len(words) <= 2 and len(query_clean) < 15:
        casual_words = ['ok', 'vale', 'ya', 'si', 'sí', 'no', 'bien', 'mal', 'bueno']
        if any(word in casual_words for word in words):
            return 'smalltalk'
    
    # Por defecto, es una búsqueda
    return 'search'

# ============================================================================
# RESPUESTAS CONVERSACIONALES
# ============================================================================

def generate_conversational_response(query, conversation_type):
    """Genera respuestas naturales según el tipo de conversación"""
    
    # Obtener hora en zona horaria de Chile (Santiago)
    chile_tz = pytz.timezone('America/Santiago')
    hour = datetime.now(chile_tz).hour
    time_greeting = "Buenos días" if 5 <= hour < 12 else "Buenas tardes" if 12 <= hour < 20 else "Buenas noches"
    
    responses = {
        'greeting': [
            f"¡{time_greeting}! 👋 Soy el asistente del Archivo Patrimonial UAH.\n\n¿Qué documento histórico buscas hoy?",
            
            f"¡Hola! 😊 Archivo Patrimonial UAH a tu servicio.\n\nPuedo ayudarte con documentos, fotos y material histórico de Chile (1973-actualidad).\n\n¿Qué buscas?",
            
            f"{time_greeting}! 📚 Bienvenido al Archivo Patrimonial.\n\nEscribe tu búsqueda o usa **📂 Categorías** para explorar."
        ],
        
        'farewell': [
            "¡Hasta pronto! 👋 Vuelve cuando quieras.",
            "¡Adiós! 🌟 Fue un gusto ayudarte.",
            "¡Nos vemos! � Aquí estaré."
        ],
        
        'gratitude': [
            "¡De nada! 😊 ¿Algo más?",
            "¡Con gusto! ¿Otra búsqueda?",
            "¡Me alegra ayudar! 📚"
        ],
        
        'help': [
            """📚 **Archivo Patrimonial UAH**

Busco documentos históricos: dictadura, DDHH, fotos, música.

**Ejemplos:** "fotos Aylwin", "documentos MIR", "dictadura años 80"

O usa **� Categorías** para explorar. ¿Qué buscas?""",
            
            """Soy tu asistente del Archivo Patrimonial. 🔍

Tengo: documentos, fotos, música (1973-actualidad)

Escribe tu búsqueda o prueba **📂 Categorías**."""
        ],
        
        'smalltalk': [
            """¡Buena pregunta! 🤖 

Soy un asistente inteligente especializado en el **Archivo Patrimonial de la Universidad Alberto Hurtado**.

**Mi propósito:**
Ayudar a las personas a descubrir y explorar documentos históricos sobre Chile, especialmente:
• Período de dictadura militar (1973-1990)
• Movimientos sociales y DDHH
• Memoria colectiva y patrimonio cultural
• Historia política reciente

**¿Qué me hace especial?**
📚 Conozco en detalle los documentos del archivo
🔍 Puedo encontrar material específico rápidamente
💡 Entiendo contexto histórico y términos relacionados
🎯 Te ayudo a explorar temas que te interesen

¿Te gustaría que busque algo sobre la historia de Chile?""",
            
            """😊 Soy el chatbot del Archivo Patrimonial UAH.

Piensa en mí como un **bibliotecario digital especializado** que conoce muy bien el archivo y puede ayudarte a encontrar exactamente lo que buscas sobre la historia de Chile.

**Datos sobre mí:**
• Acceso a miles de documentos históricos
• Especialidad en historia reciente de Chile
• Conocimiento sobre dictadura, DDHH, movimientos sociales
• Disponible 24/7 para ayudarte

Cuéntame, ¿qué tema te interesa explorar? 📚"""
        ]
    }
    
    # Seleccionar respuesta aleatoria
    if conversation_type in responses:
        return random.choice(responses[conversation_type])
    
    return None

# ============================================================================
# GENERACIÓN DE RESPUESTAS CON IA
# ============================================================================

def generate_response(query, context_docs, suggestions=None):
    """
    Genera respuesta con IA usando Gemini
    Esta función SOLO se llama para búsquedas reales (conversation_type='search')
    Ahora incluye sugerencias de refinamiento si se proporcionan
    
    IMPORTANTE: La detección de temas administrativos SOLO aplica si NO se
    encontraron documentos. Si hay documentos coincidentes, siempre los muestra.
    """
    suggestions = suggestions or []
    
    # =========================================================================
    # PRIMERO: Si hay documentos encontrados, SIEMPRE mostrarlos
    # Esto evita falsos positivos con palabras como "financiamiento", "programa"
    # que pueden aparecer en títulos de documentos históricos válidos.
    # =========================================================================
    
    if context_docs:
        # HAY DOCUMENTOS - No verificar keywords administrativas
        # Los documentos encontrados son la prioridad
        pass  # Continuar con la generación de respuesta normal
    else:
        # NO HAY DOCUMENTOS - Ahora sí verificar si es tema administrativo
        # Solo estas keywords aplican cuando NO se encontró nada
        administrative_keywords = [
            'matricula', 'matrícula', 'inscripción', 'inscripcion',
            'horario', 'horarios', 'clases', 'notas', 'calificaciones',
            'malla', 'curricular', 'admisión', 'admision', 'postular',
            'aranceles', 'becas', 'pago', 'cuota', 'arancel',
            'profesor', 'docente', 'contacto universidad', 'email uah',
            'carrera', 'carreras', 'postgrado', 'magister', 'magíster',
            'como me inscribo', 'donde queda la universidad', 'telefono uah'
        ]
        
        query_lower = query.lower()
        is_administrative = any(keyword in query_lower for keyword in administrative_keywords)
        
        if is_administrative:
            return """🎓 Esta consulta está fuera del alcance del Archivo Patrimonial.

📚 El **Archivo Patrimonial UAH** se enfoca en documentos históricos y patrimonio cultural chileno (1973-actualidad).

Para información sobre **matrículas, horarios, admisión y temas académicos**, por favor visita:

🌐 **Sitio web oficial**: [www.uahurtado.cl](https://www.uahurtado.cl)
📱 **Instagram UAH**: [@uahurtado](https://www.instagram.com/uahurtado/)
📧 **Email**: [email protected]

---

💡 **¿Sabías que...?** Nuestro archivo contiene documentos fascinantes sobre la historia de Chile. ¿Te gustaría explorar algún tema histórico?"""
    
    # Si no hay documentos relevantes - respuesta ejecutiva corta
    if not context_docs:
        return """No encontré resultados para esa búsqueda. 🔍

**Prueba con:**
• Aylwin, dictadura, derechos humanos
• fotografías, documentos, música

O usa **📂 Categorías** para explorar el archivo.

¿Qué tema buscas?"""
    
    # Si no hay GENAI disponible, respuesta básica
    if not GENAI_AVAILABLE:
        response = "📚 **He encontrado estos documentos relevantes:**\n\n"
        for i, doc in enumerate(context_docs, 1):
            response += f"{i}. **{doc['title']}**\n"
            response += f"   🔗 [Ver documento]({doc['href']})\n\n"
        return response
    
    # Construir contexto para la IA
    try:
        context = "Documentos relevantes encontrados:\n\n"
        for i, doc in enumerate(context_docs, 1):
            score = doc.get('relevance_score', 0)
            context += f"{i}. {doc['title']} (relevancia: {score:.2f})\n"
            context += f"   URL: {doc['href']}\n\n"
        
        # Construir sección de sugerencias si existen
        suggestions_text = ""
        if suggestions:
            suggestions_text = "\n\nSUGERENCIAS DE REFINAMIENTO PARA EL USUARIO:\n"
            for sug in suggestions:
                suggestions_text += f"- {sug['message']}\n"
                if sug.get('options'):
                    for opt in sug['options'][:3]:  # Limitar a 3 opciones
                        suggestions_text += f"  • {opt}\n"
        
        prompt = f"""Eres el Asistente Virtual experto del Archivo Patrimonial de la Universidad Alberto Hurtado. Tu misión principal es ayudar a investigadores y estudiantes que NO son expertos en archivística a encontrar documentos históricos.

CONTEXTO DEL ARCHIVO:
El archivo se organiza jerárquicamente en FONDOS (la colección mayor, el origen) y SERIES (las categorías internas).

Los FONDOS principales son:
1. **Presidente Patricio Aylwin (1990-1994)**: Documentos políticos, cartas, videos del período de transición democrática.
2. **Iglesias y Dictadura**: Derechos Humanos, Vicarías, revista "No podemos callar" (1973-1990).
3. **Música Docta Chilena**: Partituras y grabaciones del siglo XX.
4. **Volantes Políticos**: Panfletos y propaganda de 1973-1990.
5. **Programa Padres e Hijos (CIDE)**: Fotografías educativas de Juan Maino (1974-1976).

ANALOGÍAS PARA EXPLICAR (usa cuando el usuario pregunte):
- Fondo = Una serie de TV completa | Serie = Las temporadas o capítulos
- Fondo = Un árbol completo | Serie = Las ramas del árbol

DOCUMENTOS ENCONTRADOS:
{context}

CONSULTA DEL USUARIO: "{query}"{suggestions_text}

INSTRUCCIONES DE COMPORTAMIENTO:
1. EDUCA AL USUARIO: Si busca algo genérico (ej: "fotos"), explica brevemente que están organizadas en Fondos específicos y sugiere uno.
2. USA ANALOGÍAS: Si preguntan qué es un Fondo o Serie, usa las analogías de arriba.
3. POTENCIA TU VALOR: Recuérdales que puedes filtrar por contexto (ej: "He encontrado esto en la Serie de Correspondencia del Fondo Aylwin").
4. CONTEXTUALIZA: Añade breves notas históricas cuando sean relevantes.

FORMATO DE RESPUESTA:
1. **Saludo contextual** breve (ej: "¡Encontré material interesante!")
2. **Lista de documentos** con enlaces: [Título](URL)
3. **Contexto del Fondo/Serie** cuando sea relevante
4. **Breve contexto histórico** si añade valor
5. **Sugerencias** o invitación a explorar más

TONO:
- Amable, universitario, claro y pedagógico
- Evita tecnicismos archivísticos sin explicarlos
- Usa emojis estratégicamente (📚 📄 🔍 💡 ✨ 📂)
- Celebra cuando encuentras material relevante
- Sé empático si no hay resultados

IMPORTANTE: 
- Los enlaces llevan directamente a los documentos
- Si la consulta es muy amplia, sugiere términos más específicos
- Siempre termina invitando a hacer más preguntas

Responde de forma natural, útil y educativa:"""

        responder = factory.create_responder()
        resp_text = responder(prompt)
        if resp_text is not None:
            return resp_text

        # Fallback: si no hay GENAI disponible, respuesta básica con sugerencias
        response = "📚 **Encontré estos documentos relevantes:**\n\n"
        for i, doc in enumerate(context_docs, 1):
            response += f"{i}. **{doc['title']}**\n"
            response += f"   🔗 [Ver documento]({doc['href']})\n\n"
        
        # Añadir sugerencias si existen
        if suggestions:
            response += "\n---\n\n"
            for sug in suggestions:
                response += f"{sug['message']}\n"
                if sug.get('options'):
                    for opt in sug['options'][:4]:
                        response += f"  • {opt}\n"
                response += "\n"
        
        response += "\n💡 **Nota:** Si estos documentos no son exactamente lo que buscabas, intenta refinar tu búsqueda con términos más específicos."
        return response
        
    except Exception as e:
        print(f"❌ Error con Gemini: {e}")
        traceback.print_exc()

        # Fallback: respuesta sin IA
        response = "📚 **Encontré estos documentos relevantes:**\n\n"
        for i, doc in enumerate(context_docs, 1):
            response += f"{i}. **{doc['title']}**\n"
            response += f"   🔗 [Ver documento]({doc['href']})\n\n"
        response += "\n💡 **Nota:** Estoy experimentando limitaciones técnicas, pero aquí están los documentos que coinciden con tu búsqueda."
        return response

# ============================================================================
# LÓGICA DE CONVERSACIÓN MULTI-TURNO
# ============================================================================

def get_or_create_session(session_id: str) -> ConversationSession:
    """Obtiene o crea una sesión conversacional para un usuario"""
    if session_id not in conversation_sessions:
        conversation_sessions[session_id] = ConversationSession(session_id)
    return conversation_sessions[session_id]

def handle_follow_up_message(query: str, session: ConversationSession) -> tuple:
    """
    Maneja mensajes de seguimiento (no es la primera búsqueda).
    Retorna: (debe_hacer_nueva_busqueda: bool, nueva_query: str, respuesta_ramificacion: str or None)
    
    Usa estrategias inyectadas (DIP): intention_detector, entity_extractor
    """
    # PASO 1: Eliminar saludos del mensaje para detectar intención real
    cleaned_query = intention_detector.remove_greetings(query)
    print(f"🧹 Mensaje limpiado de saludos: '{query}' → '{cleaned_query}'")
    
    # PASO 2: Detectar si hay búsqueda explícita
    has_search = intention_detector.has_explicit_search(cleaned_query)
    print(f"🔍 ¿Hay búsqueda explícita? {has_search}")
    
    # PASO 3: Si NO hay búsqueda explícita, detectar intención (satisfecho, insatisfecho, etc)
    if not has_search:
        intention = intention_detector.detect(cleaned_query)
        print(f"🎯 Intención detectada: {intention}")
        
        # Caso 1: Usuario satisfecho
        if intention == 'satisfied':
            response = "¡Excelente! 😊 Me alegra haber encontrado lo que buscabas.\n\n¿Hay algo más que quieras explorar en el Archivo Patrimonial?"
            return False, None, response
        
        # Caso 2: Usuario insatisfecho SIN información adicional
        if intention == 'unsatisfied':
            response = """❓ Entiendo que no encontraste lo que buscabas. \n\n**Para poder ayudarte mejor, ¿podrías ser más específico?** 🤔\n\n💡 Por ejemplo:\n• **Período:** ¿De qué años? (1973-1990, 1980-1985, etc.)\n• **Tipo:** ¿Fotografías, testimonios, documentos, reportes?\n• **Tema:** ¿Hay un aspecto específico? (DDHH, partido político, organización)\n• **Persona:** ¿Hay alguien específico involucrado?\n\nCuéntame más y haré una búsqueda más dirigida. 📚"""
            return False, None, response
    
    # PASO 4: Si HAY búsqueda explícita, hacer nueva búsqueda
    # (ignorar intención de satisfacción/insatisfacción si hay términos de búsqueda claros)
    entities = entity_extractor.extract(cleaned_query)
    query_parts = []
    
    if entities['topics']:
        query_parts.extend(entities['topics'])
    if entities['years']:
        query_parts.append(f"{min(entities['years'])}")
    if entities['doc_types']:
        query_parts.extend(entities['doc_types'])
    
    # Si no extrajimos nada, usar el query limpiado
    new_query = ' '.join(query_parts) if query_parts else cleaned_query
    print(f"🔍 Nueva búsqueda será: '{new_query}'")
    
    return True, new_query, None

def compare_and_format_results(new_docs: List[Dict], session: ConversationSession, original_query: str) -> str:
    """
    Compara resultados nuevos con anteriores y formatea respuesta apropiada.
    """
    truly_new, similar = DocumentComparator.find_similar(new_docs, session.get_previous_hrefs())
    
    response = ""
    
    if similar:
        response += "📌 **Documentos encontrados (algunos similares a búsquedas anteriores):**\n\n"
        for i, doc in enumerate(new_docs, 1):
            is_similar = "🔄 " if doc in similar else "✨ "
            response += f"{is_similar}{i}. **{doc['title']}**\n"
            response += f"   🔗 [Ver documento]({doc['href']})\n\n"
    else:
        response += "📚 **Aquí están los documentos encontrados con tu búsqueda refinada:**\n\n"
        for i, doc in enumerate(new_docs, 1):
            response += f"{i}. **{doc['title']}**\n"
            response += f"   🔗 [Ver documento]({doc['href']})\n\n"
    
    # Calcular similitud temática
    topic_similarity = DocumentComparator.by_topic_similarity(
        session.last_results,
        new_docs
    )
    
    if truly_new:
        response += f"\n💡 Encontré **{len(truly_new)} documento(s) nuevo(s)** en esta búsqueda que no aparecían antes.\n"
    
    if topic_similarity > 0.6:
        response += f"🔗 Estos resultados tienen alta similitud temática con tu búsqueda anterior.\n"
    elif topic_similarity > 0.3:
        response += f"🔄 Estos resultados comparten algunos temas con la búsqueda anterior.\n"
    else:
        response += f"🆕 Estos resultados son bastante diferentes a los anteriores.\n"
    
    response += "\n**¿Encontraste lo que buscabas?** Si no, cuéntame más y seguiremos buscando. 😊"
    
    return response

# ============================================================================
# RUTAS DE LA API
# ============================================================================


@app.route('/api/chat', methods=['POST', 'OPTIONS'])
def chat():
    """
    Endpoint principal del chatbot
    Detecta tipo de conversación y responde apropiadamente
    """
    # Manejar preflight CORS
    if request.method == 'OPTIONS':
        response = jsonify({'status': 'ok'})
        response.headers.add('Access-Control-Allow-Origin', '*')
        response.headers.add('Access-Control-Allow-Headers', 'Content-Type')
        response.headers.add('Access-Control-Allow-Methods', 'POST, OPTIONS')
        return response, 200
    
    query = ""
    session_id = ""
    try:
        print(f"\n{'='*60}")
        print(f"📥 Nueva solicitud recibida")
        print(f"{'='*60}")
        print(f"🔥 Método: {request.method}")
        print(f"🔥 Content-Type: {request.content_type}")

        # Obtener query de JSON o form
        data = request.get_json(silent=True)
        if data and isinstance(data, dict):
            query = data.get('query', '')
            session_id = data.get('session_id', 'default')
            print(f"✅ Query from JSON: '{query}'")
        else:
            query = request.form.get('query', '')
            session_id = request.form.get('session_id', 'default')
            print(f"✅ Query from form: '{query}'")

        query = query.strip()
        print(f"🔎 Query procesada: '{query}'")
        print(f"🆔 Session ID: {session_id}")
        event_bus.publish('chat.received', {'query': query})

        if not query:
            print("❌ Query vacía")
            return jsonify({
                'success': False,
                'error': 'No query provided', 
                'details': 'La consulta no puede estar vacía.'
            }), 400

        # Obtener o crear sesión del usuario
        session = get_or_create_session(session_id)
        print(f"📋 Session creada/recuperada. Historial: {len(session.search_history)} búsquedas")

        # ============ PASO 1: DETECTAR TIPO DE CONVERSACIÓN PRIMERO ============
        # Esto asegura que saludos, despedidas, etc. se respondan conversacionalmente
        # INCLUSO en mensajes de seguimiento (si es solo "Hola buenas", no debe hacer búsqueda)
        conversation_type = detect_conversation_type(query)
        print(f"🎯 Tipo detectado: {conversation_type}")
        event_bus.publish('chat.type_detected', {'type': conversation_type})
        
        # ============ PASO 2: SI ES CONVERSACIÓN CASUAL, RESPONDER SIN BUSCAR ============
        if conversation_type in ['greeting', 'farewell', 'gratitude', 'help', 'smalltalk']:
            print(f"💬 Respuesta conversacional (sin búsqueda)")
            response_text = generate_conversational_response(query, conversation_type)
            
            if response_text:
                response_html = markdown.markdown(response_text)
                event_bus.publish('response.generated', {'chars': len(response_text), 'docs': 0})
                
                return jsonify({
                    'success': True,
                    'response': response_html,
                    'documents': [],
                    'embeddings_ready': embeddings_ready,
                    'conversation_type': conversation_type,
                    'session_id': session_id
                })

        # Verificar si es seguimiento ANTES de agregar la búsqueda actual
        is_follow_up = session.is_follow_up()
        
        # ============ LÓGICA DE SEGUIMIENTO ============
        # Si es un mensaje de seguimiento (no la primera búsqueda)
        if is_follow_up:
            print(f"🔄 Mensaje de seguimiento detectado (búsquedas previas: {len(session.search_history)})")
            should_search, refined_query, branch_response = handle_follow_up_message(query, session)
            
            if branch_response:
                # Es una ramificación de la lógica (satisfecho, pedir detalles, etc)
                print(f"💬 Respuesta de ramificación: {len(branch_response)} caracteres")
                response_html = markdown.markdown(branch_response)
                event_bus.publish('response.generated', {'chars': len(branch_response), 'docs': 0})
                
                return jsonify({
                    'success': True,
                    'response': response_html,
                    'documents': [],
                    'embeddings_ready': embeddings_ready,
                    'conversation_type': 'follow_up_branch',
                    'session_id': session_id
                })
            
            if not should_search:
                # No hay nueva búsqueda que hacer
                return jsonify({
                    'success': True,
                    'response': markdown.markdown("✅ ¿En qué más te puedo ayudar?"),
                    'documents': [],
                    'embeddings_ready': embeddings_ready,
                    'conversation_type': 'follow_up_satisfied',
                    'session_id': session_id
                })
            
            # Hay nueva búsqueda que hacer
            query = refined_query
            print(f"🔍 Nueva búsqueda con query refinada: '{query}'")

        # ============ FLUJO NORMAL (primera búsqueda o búsqueda refinada) ============
        # PASO 3: SI ES 'search', BUSCAR DOCUMENTOS (6 documentos) Y SUGERENCIAS
        print(f"🔍 Realizando búsqueda de documentos...")
        relevant_docs, suggestions = search_documents(query, top_k=6, include_suggestions=True)
        print(f"📄 Encontrados {len(relevant_docs)} documentos")
        if suggestions:
            print(f"💡 Generadas {len(suggestions)} sugerencias")
        
        # Registrar búsqueda en la sesión
        session.add_search(query, relevant_docs)

        # PASO 4: GENERAR RESPUESTA CON IA (incluyendo sugerencias)
        print(f"🤖 Generando respuesta con IA...")
        response_text = generate_response(query, relevant_docs, suggestions)
        print(f"✅ Respuesta generada: {len(response_text)} caracteres")

        # Convertir markdown a HTML
        response_html = markdown.markdown(response_text)
        event_bus.publish('response.generated', {'chars': len(response_text), 'docs': len(relevant_docs)})

        return jsonify({
            'success': True,
            'response': response_html,
            'documents': relevant_docs,
            'embeddings_ready': embeddings_ready,
            'conversation_type': conversation_type,
            'session_id': session_id
        })

    except Exception as e:
        print(f"\n❌ ERROR EN /chat:")
        print(f"{'='*60}")
        traceback.print_exc()
        print(f"{'='*60}\n")
        
        return jsonify({
            'success': False,
            'error': 'Error procesando la consulta',
            'details': str(e)
        }), 500

@app.route('/api/health', methods=['GET'])
def health():
    """Endpoint de health check"""
    return jsonify({
        'status': 'ok',
        'documents_loaded': len(documents),
        'embeddings_loaded': get_embeddings_count(document_embeddings),
        'genai_available': GENAI_AVAILABLE
    })

@app.route('/api/categories', methods=['GET'])
def get_categories():
    """
    Retorna las categorías disponibles para navegación
    Incluye: materias (dc:subject), autores (dc:creator), lugares (dc:coverage)
    """
    try:
        # Cargar categorías desde archivo
        categories_file = os.path.join(os.path.dirname(__file__), 'categories.json')
        
        if os.path.exists(categories_file):
            with open(categories_file, 'r', encoding='utf-8') as f:
                all_categories = json.load(f)
            
            # Limitar a top 100 por categoría para UI
            result = {
                'materias': all_categories.get('materias', [])[:100],
                'autores': all_categories.get('autores', [])[:100],
                'lugares': all_categories.get('lugares', [])[:100]
            }
            
            return jsonify({
                'success': True,
                'categories': result,
                'total': {
                    'materias': len(all_categories.get('materias', [])),
                    'autores': len(all_categories.get('autores', [])),
                    'lugares': len(all_categories.get('lugares', []))
                }
            })
        else:
            return jsonify({
                'success': False,
                'error': 'Archivo de categorías no encontrado'
            }), 404
            
    except Exception as e:
        print(f"Error cargando categorías: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/search-by-category', methods=['POST'])
def search_by_category():
    """
    Busca documentos filtrando por categoría específica
    Body: { category_type: 'materias'|'autores'|'lugares', category_name: 'Derechos Humanos' }
    """
    try:
        data = request.get_json()
        category_type = data.get('category_type', '')
        category_name = data.get('category_name', '')
        
        if not category_type or not category_name:
            return jsonify({
                'success': False,
                'error': 'Se requiere category_type y category_name'
            }), 400
        
        # Mapeo de tipos a campos del JSON
        field_map = {
            'materias': 'dc:subject',
            'autores': 'dc:creator',
            'lugares': 'dc:coverage'
        }
        
        field = field_map.get(category_type)
        if not field:
            return jsonify({
                'success': False,
                'error': 'Tipo de categoría inválido'
            }), 400
        
        # Cargar documentos con metadatos
        metadata_file = os.path.join(os.path.dirname(__file__), 'clean_with_metadata.json')
        
        if os.path.exists(metadata_file):
            with open(metadata_file, 'r', encoding='utf-8', errors='ignore') as f:
                docs_with_metadata = json.load(f)
        else:
            # Fallback a documentos normales
            docs_with_metadata = documents
        
        # Filtrar documentos que contengan la categoría
        results = []
        category_lower = category_name.lower()
        
        for doc in docs_with_metadata:
            field_values = doc.get(field, [])
            if isinstance(field_values, list):
                for val in field_values:
                    if category_lower in val.lower():
                        results.append({
                            'title': doc.get('title', doc.get('dc:title', 'Sin título')),
                            'href': doc.get('href', ''),
                            'subject': doc.get('dc:subject', [])[:3],
                            'creator': doc.get('dc:creator', [])[:2],
                            'coverage': doc.get('dc:coverage', [])
                        })
                        break
            
            if len(results) >= 15:
                break
        
        return jsonify({
            'success': True,
            'category_type': category_type,
            'category_name': category_name,
            'results': results,
            'count': len(results)
        })
        
    except Exception as e:
        print(f"Error en búsqueda por categoría: {e}")
        traceback.print_exc()
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/', methods=['GET'])
def index():
    """Ruta raíz que carga el Frontend unificado"""
    return render_template('index.html')


# ============================================================================
# MAIN: EJECUTAR APLICACIÓN
# ============================================================================

if __name__ == '__main__':
    print("\n" + "="*70)
    print("🚀 INICIANDO CHATBOT DEL ARCHIVO PATRIMONIAL UAH")
    print("="*70)
    print(f"📊 Documentos cargados: {len(documents)}")
    print(f"🧠 Embeddings disponibles: {get_embeddings_count(document_embeddings)}")
    print(f"🤖 Gemini API: {'✅ Disponible' if GENAI_AVAILABLE else '❌ No disponible'}")
    print(f"🌐 Servidor Flask: http://localhost:5000")
    print(f"🔗 Frontend esperado: http://localhost:8080 (vía Nginx)")
    print(f"📡 Endpoint principal: POST /api/chat")
    print(f"❤️ Health check: GET /api/health")
    print("="*70)
    print("✅ Sistema listo para recibir consultas!\n")

    app.run(
        debug=False,
        host='0.0.0.0',
        port=5000,
        threaded=True
    )