"""
Strategy Pattern - Algoritmos de búsqueda intercambiables
=========================================================

Patrón: STRATEGY (Comportamiento)
Propósito: Definir una familia de algoritmos, encapsularlos haciendo que sean 
           intercambiables. Strategy permite que el algoritmo varíe 
           independientemente de los clientes que lo usan.

Estrategias implementadas:
1. ExactTitleSearch: Búsqueda exacta por título
2. TFIDFSearch: Búsqueda por TF-IDF
3. SemanticSearch: Búsqueda semántica con embeddings
4. MetadataSearch: Búsqueda ponderada en campos Dublin Core
5. HybridSearch: Combinación de múltiples estrategias

Principios SOLID:
- SRP: Cada estrategia tiene una única responsabilidad (un algoritmo)
- OCP: Nuevas estrategias pueden agregarse sin modificar código existente
- LSP: Todas las estrategias son intercambiables (misma interfaz)
- ISP: Interfaz mínima en SearchStrategy
- DIP: El contexto depende de la abstracción SearchStrategy

Uso:
    context = SearchContext(SemanticSearchStrategy(embedder))
    results = context.search("fotografías de aylwin", documents, top_k=10)
"""

from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional, Callable
import re
from collections import defaultdict


# ============================================================================
# STRATEGY: Interfaz base para estrategias de búsqueda
# ============================================================================

class SearchStrategy(ABC):
    """
    Strategy Pattern - Interfaz para algoritmos de búsqueda.
    
    Define el contrato que todas las estrategias de búsqueda deben cumplir.
    
    Principio DIP: El código cliente (SearchContext) depende de esta 
    abstracción, no de implementaciones concretas.
    """
    
    @abstractmethod
    def search(self, query: str, documents: List[Dict], top_k: int = 10) -> List[Dict]:
        """
        Ejecuta la búsqueda según el algoritmo específico.
        
        Args:
            query: Consulta del usuario
            documents: Lista de documentos a buscar
            top_k: Número máximo de resultados
            
        Returns:
            Lista de documentos ordenados por relevancia
        """
        pass
    
    @abstractmethod
    def get_name(self) -> str:
        """Retorna el nombre de la estrategia para logging."""
        pass


# ============================================================================
# CONCRETE STRATEGY: Búsqueda exacta por título
# ============================================================================

class ExactTitleSearchStrategy(SearchStrategy):
    """
    Estrategia de búsqueda exacta por título.
    
    Prioriza matches exactos y parciales en el título del documento.
    Útil cuando el usuario conoce el nombre exacto del documento.
    
    Ejemplo: "Carta de Aylwin" encontrará "[Carta de Aylwin a ministro...]"
    """
    
    def search(self, query: str, documents: List[Dict], top_k: int = 10) -> List[Dict]:
        query_lower = query.lower().strip()
        query_words = set(query_lower.split())
        
        scored_docs = []
        
        for doc in documents:
            title = doc.get('title', '') or doc.get('dc:title', '')
            if not title:
                continue
            
            title_lower = title.lower()
            
            # Score basado en tipo de match
            score = 0.0
            match_type = None
            
            # Match exacto completo
            if query_lower == title_lower:
                score = 1.0
                match_type = "exact"
            # Query contenido en título
            elif query_lower in title_lower:
                score = 0.9
                match_type = "contains"
            # Título contenido en query
            elif title_lower in query_lower:
                score = 0.85
                match_type = "reverse_contains"
            else:
                # Match por palabras
                title_words = set(title_lower.split())
                overlap = len(query_words.intersection(title_words))
                if overlap > 0:
                    score = overlap / len(query_words) * 0.7
                    match_type = "word_overlap"
            
            if score > 0:
                result = doc.copy()
                result['relevance_score'] = score
                result['_match_type'] = match_type
                result['_strategy'] = 'exact_title'
                scored_docs.append(result)
        
        # Ordenar por score descendente
        scored_docs.sort(key=lambda x: x['relevance_score'], reverse=True)
        return scored_docs[:top_k]
    
    def get_name(self) -> str:
        return "ExactTitleSearch"


# ============================================================================
# CONCRETE STRATEGY: Búsqueda TF-IDF
# ============================================================================

class TFIDFSearchStrategy(SearchStrategy):
    """
    Estrategia de búsqueda TF-IDF (Term Frequency-Inverse Document Frequency).
    
    Algoritmo clásico de recuperación de información que pondera las palabras
    según su frecuencia en el documento y su rareza en el corpus.
    
    No requiere API externa, ideal para modo offline.
    """
    
    def __init__(self, tfidf_index: Optional[Any] = None):
        """
        Args:
            tfidf_index: Índice TF-IDF pre-calculado (sklearn TfidfVectorizer)
        """
        self._index = tfidf_index
    
    def set_index(self, tfidf_index: Any) -> None:
        """Configura el índice TF-IDF."""
        self._index = tfidf_index
    
    def search(self, query: str, documents: List[Dict], top_k: int = 10) -> List[Dict]:
        if not self._index:
            # Fallback: búsqueda simple por keywords
            return self._keyword_fallback(query, documents, top_k)
        
        try:
            from sklearn.metrics.pairwise import cosine_similarity
            
            # Transformar query
            query_vec = self._index['vectorizer'].transform([query])
            
            # Calcular similaridad
            similarities = cosine_similarity(query_vec, self._index['matrix']).flatten()
            
            # Obtener top_k
            top_indices = similarities.argsort()[::-1][:top_k]
            
            results = []
            for idx in top_indices:
                if similarities[idx] > 0.01:  # Threshold mínimo
                    doc = documents[idx].copy()
                    doc['relevance_score'] = float(similarities[idx])
                    doc['_strategy'] = 'tfidf'
                    results.append(doc)
            
            return results
            
        except Exception as e:
            print(f"⚠️ Error en TF-IDF: {e}")
            return self._keyword_fallback(query, documents, top_k)
    
    def _keyword_fallback(self, query: str, documents: List[Dict], top_k: int) -> List[Dict]:
        """Búsqueda simple por keywords cuando TF-IDF no está disponible."""
        query_words = set(re.findall(r'\b\w{3,}\b', query.lower()))
        
        scored_docs = []
        for doc in documents:
            text = f"{doc.get('title', '')} {' '.join(doc.get('dc:subject', []))}"
            doc_words = set(re.findall(r'\b\w{3,}\b', text.lower()))
            
            overlap = len(query_words.intersection(doc_words))
            if overlap > 0:
                result = doc.copy()
                result['relevance_score'] = overlap / len(query_words)
                result['_strategy'] = 'keyword_fallback'
                scored_docs.append(result)
        
        scored_docs.sort(key=lambda x: x['relevance_score'], reverse=True)
        return scored_docs[:top_k]
    
    def get_name(self) -> str:
        return "TFIDFSearch"


# ============================================================================
# CONCRETE STRATEGY: Búsqueda semántica con embeddings
# ============================================================================

class SemanticSearchStrategy(SearchStrategy):
    """
    Estrategia de búsqueda semántica usando embeddings.
    
    Usa modelos de embeddings (Gemini) para encontrar documentos 
    semánticamente similares a la query.
    
    Ventajas:
    - Entiende sinónimos y conceptos relacionados
    - Mejor para consultas en lenguaje natural
    
    Requiere API de embeddings disponible.
    """
    
    def __init__(self, 
                 query_embedder: Optional[Callable[[str], Optional[List[float]]]] = None,
                 document_embeddings: Optional[Dict[int, List[float]]] = None):
        """
        Args:
            query_embedder: Función para generar embedding de la query
            document_embeddings: Embeddings pre-calculados de documentos
        """
        self._embedder = query_embedder
        self._doc_embeddings = document_embeddings or {}
    
    def set_embedder(self, embedder: Callable[[str], Optional[List[float]]]) -> None:
        """Configura el embedder."""
        self._embedder = embedder
    
    def set_document_embeddings(self, embeddings: Dict[int, List[float]]) -> None:
        """Configura los embeddings de documentos."""
        self._doc_embeddings = embeddings
    
    def search(self, query: str, documents: List[Dict], top_k: int = 10) -> List[Dict]:
        if not self._embedder or not self._doc_embeddings:
            return []  # No disponible
        
        try:
            import numpy as np
            from sklearn.metrics.pairwise import cosine_similarity
            
            # Generar embedding de la query
            query_embedding = self._embedder(query)
            if not query_embedding:
                return []
            
            query_vec = np.array(query_embedding).reshape(1, -1)
            
            # Calcular similaridad con cada documento
            results = []
            for idx, doc in enumerate(documents):
                if idx not in self._doc_embeddings:
                    continue
                
                doc_vec = np.array(self._doc_embeddings[idx]).reshape(1, -1)
                similarity = cosine_similarity(query_vec, doc_vec)[0][0]
                
                if similarity > 0.3:  # Threshold mínimo
                    result = doc.copy()
                    result['relevance_score'] = float(similarity)
                    result['_strategy'] = 'semantic'
                    results.append(result)
            
            results.sort(key=lambda x: x['relevance_score'], reverse=True)
            return results[:top_k]
            
        except Exception as e:
            print(f"⚠️ Error en búsqueda semántica: {e}")
            return []
    
    def get_name(self) -> str:
        return "SemanticSearch"


# ============================================================================
# CONCRETE STRATEGY: Búsqueda ponderada en metadata
# ============================================================================

class MetadataSearchStrategy(SearchStrategy):
    """
    Estrategia de búsqueda ponderada en campos Dublin Core.
    
    Asigna diferentes pesos a cada campo de metadata:
    - title: 3.0 (más importante)
    - dc:subject: 2.0 (materias)
    - dc:creator: 1.5 (autores)
    - dc:coverage: 1.0 (lugares)
    
    Con expansión de sinónimos integrada.
    """
    
    FIELD_WEIGHTS = {
        'title': 3.0,
        'dc:title': 3.0,
        'dc:subject': 2.0,
        'dc:creator': 1.5,
        'dc:coverage': 1.0,
    }
    
    SYNONYMS = {
        'fotos': ['fotografías', 'imágenes'],
        'cartas': ['correspondencia', 'misivas'],
        'dictadura': ['régimen militar', 'pinochet'],
        'derechos humanos': ['ddhh', 'violaciones'],
    }
    
    def search(self, query: str, documents: List[Dict], top_k: int = 10) -> List[Dict]:
        # Expandir query con sinónimos
        queries = self._expand_query(query)
        
        scored_docs = []
        
        for doc in documents:
            doc_score = 0.0
            
            for q in queries:
                q_lower = q.lower()
                q_words = set(re.findall(r'\b\w{3,}\b', q_lower))
                
                for field, weight in self.FIELD_WEIGHTS.items():
                    field_value = doc.get(field, '')
                    
                    if isinstance(field_value, list):
                        field_text = ' '.join(str(v) for v in field_value)
                    else:
                        field_text = str(field_value)
                    
                    field_words = set(re.findall(r'\b\w{3,}\b', field_text.lower()))
                    
                    if q_words:
                        overlap = len(q_words.intersection(field_words)) / len(q_words)
                        doc_score += overlap * weight
            
            if doc_score > 0:
                result = doc.copy()
                result['relevance_score'] = doc_score
                result['_strategy'] = 'metadata'
                scored_docs.append(result)
        
        scored_docs.sort(key=lambda x: x['relevance_score'], reverse=True)
        return scored_docs[:top_k]
    
    def _expand_query(self, query: str) -> List[str]:
        """Expande la query con sinónimos."""
        expansions = [query]
        query_lower = query.lower()
        
        for term, synonyms in self.SYNONYMS.items():
            if term in query_lower:
                for syn in synonyms:
                    expansions.append(query_lower.replace(term, syn))
        
        return expansions
    
    def get_name(self) -> str:
        return "MetadataSearch"


# ============================================================================
# CONCRETE STRATEGY: Búsqueda híbrida (combina múltiples estrategias)
# ============================================================================

class HybridSearchStrategy(SearchStrategy):
    """
    Estrategia híbrida que combina múltiples estrategias.
    
    Ejecuta varias estrategias y combina sus resultados con pesos
    configurables.
    
    RRF (Reciprocal Rank Fusion) para combinar rankings.
    """
    
    def __init__(self, strategies: List[tuple] = None):
        """
        Args:
            strategies: Lista de (SearchStrategy, peso) tuples
        """
        self._strategies = strategies or []
    
    def add_strategy(self, strategy: SearchStrategy, weight: float = 1.0) -> None:
        """Agrega una estrategia con su peso."""
        self._strategies.append((strategy, weight))
    
    def search(self, query: str, documents: List[Dict], top_k: int = 10) -> List[Dict]:
        if not self._strategies:
            return []
        
        # Recopilar resultados de todas las estrategias
        all_results: Dict[str, Dict] = {}  # href -> combined doc
        all_scores: Dict[str, float] = defaultdict(float)  # href -> combined score
        
        for strategy, weight in self._strategies:
            results = strategy.search(query, documents, top_k=top_k * 2)
            
            for rank, doc in enumerate(results, 1):
                href = doc.get('href', str(id(doc)))
                
                # RRF score: 1 / (k + rank)
                rrf_score = weight / (60 + rank)
                all_scores[href] += rrf_score
                
                if href not in all_results:
                    all_results[href] = doc.copy()
                    all_results[href]['_strategies_used'] = []
                
                all_results[href]['_strategies_used'].append(strategy.get_name())
        
        # Ordenar por score combinado
        sorted_hrefs = sorted(all_scores.keys(), key=lambda h: all_scores[h], reverse=True)
        
        results = []
        for href in sorted_hrefs[:top_k]:
            doc = all_results[href]
            doc['relevance_score'] = all_scores[href]
            doc['_strategy'] = 'hybrid'
            results.append(doc)
        
        return results
    
    def get_name(self) -> str:
        strategy_names = [s.get_name() for s, _ in self._strategies]
        return f"HybridSearch({'+'.join(strategy_names)})"


# ============================================================================
# CONTEXT: Clase que usa las estrategias
# ============================================================================

class SearchContext:
    """
    Context del Strategy Pattern.
    
    Mantiene una referencia a una estrategia y delega el trabajo de búsqueda.
    Permite cambiar la estrategia en runtime.
    
    Uso:
        context = SearchContext(ExactTitleSearchStrategy())
        results = context.search("aylwin", documents)
        
        # Cambiar estrategia
        context.set_strategy(SemanticSearchStrategy(embedder))
        results = context.search("fotos históricas", documents)
    """
    
    def __init__(self, strategy: SearchStrategy):
        self._strategy = strategy
    
    def set_strategy(self, strategy: SearchStrategy) -> None:
        """Cambia la estrategia de búsqueda."""
        self._strategy = strategy
    
    def search(self, query: str, documents: List[Dict], top_k: int = 10) -> List[Dict]:
        """Ejecuta la búsqueda usando la estrategia actual."""
        print(f"🔍 Buscando con estrategia: {self._strategy.get_name()}")
        return self._strategy.search(query, documents, top_k)
    
    def get_strategy_name(self) -> str:
        """Retorna el nombre de la estrategia actual."""
        return self._strategy.get_name()


# ============================================================================
# FACTORY METHOD: Crear estrategia apropiada según contexto
# ============================================================================

def create_search_strategy(
    genai_available: bool = False,
    query_embedder: Callable = None,
    doc_embeddings: Dict = None,
    tfidf_index: Any = None
) -> SearchStrategy:
    """
    Factory Method para crear la estrategia de búsqueda más apropiada.
    
    Args:
        genai_available: Si la API de Gemini está disponible
        query_embedder: Función para embeddings de queries
        doc_embeddings: Embeddings pre-calculados de documentos
        tfidf_index: Índice TF-IDF pre-calculado
    
    Returns:
        SearchStrategy: La estrategia más apropiada según los recursos disponibles
    """
    # Crear estrategia híbrida con lo disponible
    hybrid = HybridSearchStrategy()
    
    # Siempre agregar búsqueda exacta por título (peso alto)
    hybrid.add_strategy(ExactTitleSearchStrategy(), weight=1.5)
    
    # Agregar búsqueda en metadata
    hybrid.add_strategy(MetadataSearchStrategy(), weight=1.2)
    
    # Agregar TF-IDF si está disponible
    if tfidf_index:
        tfidf_strategy = TFIDFSearchStrategy(tfidf_index)
        hybrid.add_strategy(tfidf_strategy, weight=1.0)
    
    # Agregar búsqueda semántica si está disponible
    if genai_available and query_embedder and doc_embeddings:
        semantic_strategy = SemanticSearchStrategy(query_embedder, doc_embeddings)
        hybrid.add_strategy(semantic_strategy, weight=1.3)
    
    return hybrid
