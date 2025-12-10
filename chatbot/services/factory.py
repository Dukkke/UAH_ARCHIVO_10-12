"""
Abstract Factory Pattern - Creación de servicios del chatbot
============================================================

Patrón: ABSTRACT FACTORY (Creacional)
Propósito: Proporcionar una interfaz para crear familias de objetos relacionados
           sin especificar sus clases concretas.

Principios SOLID:
- SRP: Cada factory tiene una única responsabilidad
- OCP: Extensible agregando nuevas factories concretas
- DIP: Dependemos de abstracciones, no de implementaciones concretas

Estructura:
    AbstractServiceFactory (ABC)
        ├── GeminiServiceFactory   → Servicios usando Google Gemini
        ├── LocalServiceFactory    → Servicios locales sin API
        └── MockServiceFactory     → Servicios mock para testing
"""

import os
from abc import ABC, abstractmethod
from typing import Any, Dict, Optional, Callable, List

from .llm_proxy import GeminiClientProxy, LLMProxy


# ============================================================================
# ABSTRACT FACTORY: Interfaz base para crear familias de servicios
# ============================================================================

class AbstractServiceFactory(ABC):
    """
    Abstract Factory Pattern - Interfaz para crear familias de servicios.
    
    Define los métodos factory que las subclases concretas deben implementar.
    Cada familia de servicios (Gemini, Local, Mock) implementa esta interfaz.
    
    Principio DIP: El código cliente depende de esta abstracción, no de
    implementaciones concretas como GeminiServiceFactory.
    """
    
    @abstractmethod
    def create_embedder(self) -> Callable[[str], Optional[List[float]]]:
        """Crea un servicio de embeddings para búsqueda semántica."""
        pass
    
    @abstractmethod
    def create_query_embedder(self) -> Callable[[str], Optional[List[float]]]:
        """Crea un servicio de embeddings optimizado para queries."""
        pass
    
    @abstractmethod
    def create_responder(self) -> Callable[[str], Optional[str]]:
        """Crea un servicio de generación de respuestas."""
        pass
    
    @abstractmethod
    def create_llm_proxy(self) -> 'LLMProxy':
        """Crea un proxy para el servicio LLM."""
        pass
    
    @abstractmethod
    def is_available(self) -> bool:
        """Indica si los servicios de esta factory están disponibles."""
        pass


# ============================================================================
# CONCRETE FACTORY: Implementación para Google Gemini
# ============================================================================

class GeminiServiceFactory(AbstractServiceFactory):
    """
    Concrete Factory para servicios de Google Gemini.
    
    Crea productos concretos:
    - Embedder usando text-embedding-004
    - Responder usando gemini-2.0-flash-exp
    - Proxy con rate limiting y fallback
    
    Uso:
        factory = GeminiServiceFactory(genai, api_key_present=True)
        embedder = factory.create_embedder()
        embedding = embedder("texto a buscar")
    """
    
    def __init__(self, genai: Any, api_key_present: bool) -> None:
        """
        Args:
            genai: Módulo google.generativeai configurado
            api_key_present: Si la API key está disponible
        """
        self._genai = genai
        self._available = api_key_present
        self._proxy = GeminiClientProxy(genai, api_key_present)
    
    def create_embedder(self) -> Callable[[str], Optional[List[float]]]:
        """Crea embedder para documentos (retrieval_document)."""
        def _embed(text: str) -> Optional[List[float]]:
            if not self._available:
                return None
            result = self._proxy.embed(
                text, 
                model="models/text-embedding-004", 
                task_type="retrieval_document"
            )
            return result.get("embedding") if result else None
        return _embed
    
    def create_query_embedder(self) -> Callable[[str], Optional[List[float]]]:
        """Crea embedder para queries (retrieval_query)."""
        def _embed_query(text: str) -> Optional[List[float]]:
            if not self._available:
                return None
            result = self._proxy.embed(
                text, 
                model="models/text-embedding-004", 
                task_type="retrieval_query"
            )
            return result.get("embedding") if result else None
        return _embed_query
    
    def create_responder(self) -> Callable[[str], Optional[str]]:
        """Crea generador de respuestas con Gemini Flash."""
        def _respond(prompt: str) -> Optional[str]:
            if not self._available:
                return None
            return self._proxy.generate(prompt, model_name="gemini-2.0-flash-exp")
        return _respond
    
    def create_llm_proxy(self) -> 'LLMProxy':
        """Retorna el proxy de Gemini."""
        return self._proxy
    
    def is_available(self) -> bool:
        """Verifica si Gemini está disponible."""
        return self._available


# ============================================================================
# CONCRETE FACTORY: Implementación local sin API externa
# ============================================================================

class LocalServiceFactory(AbstractServiceFactory):
    """
    Concrete Factory para servicios locales (sin API externa).
    
    Útil cuando no hay API key disponible o para reducir costos.
    Usa TF-IDF local en lugar de embeddings semánticos.
    
    Principio OCP: Podemos agregar esta factory sin modificar el código
    existente que usa AbstractServiceFactory.
    """
    
    def __init__(self) -> None:
        self._available = True
    
    def create_embedder(self) -> Callable[[str], Optional[List[float]]]:
        """Retorna None - usa TF-IDF local en su lugar."""
        def _local_embed(text: str) -> Optional[List[float]]:
            return None  # Señala al sistema que use búsqueda TF-IDF
        return _local_embed
    
    def create_query_embedder(self) -> Callable[[str], Optional[List[float]]]:
        """Retorna None - usa TF-IDF local en su lugar."""
        def _local_embed_query(text: str) -> Optional[List[float]]:
            return None
        return _local_embed_query
    
    def create_responder(self) -> Callable[[str], Optional[str]]:
        """Respuestas formateadas sin IA generativa."""
        def _local_respond(prompt: str) -> Optional[str]:
            return None  # Señala al sistema que use respuesta template
        return _local_respond
    
    def create_llm_proxy(self) -> 'LLMProxy':
        """Retorna un proxy nulo."""
        from .llm_proxy import NullLLMProxy
        return NullLLMProxy()
    
    def is_available(self) -> bool:
        """Siempre disponible (es local)."""
        return True


# ============================================================================
# CONCRETE FACTORY: Implementación mock para testing
# ============================================================================

class MockServiceFactory(AbstractServiceFactory):
    """
    Concrete Factory para testing.
    
    Retorna respuestas predefinidas para pruebas unitarias.
    
    Uso:
        factory = MockServiceFactory()
        factory.set_mock_embedding([0.1, 0.2, 0.3])
        factory.set_mock_response("Respuesta de prueba")
    """
    
    def __init__(self) -> None:
        self._mock_embedding: List[float] = [0.0] * 768
        self._mock_response: str = "Mock response"
    
    def set_mock_embedding(self, embedding: List[float]) -> None:
        """Configura el embedding mock."""
        self._mock_embedding = embedding
    
    def set_mock_response(self, response: str) -> None:
        """Configura la respuesta mock."""
        self._mock_response = response
    
    def create_embedder(self) -> Callable[[str], Optional[List[float]]]:
        """Retorna embedding mock configurado."""
        def _mock_embed(text: str) -> Optional[List[float]]:
            return self._mock_embedding.copy()
        return _mock_embed
    
    def create_query_embedder(self) -> Callable[[str], Optional[List[float]]]:
        """Retorna embedding mock configurado."""
        return self.create_embedder()
    
    def create_responder(self) -> Callable[[str], Optional[str]]:
        """Retorna respuesta mock configurada."""
        def _mock_respond(prompt: str) -> Optional[str]:
            return self._mock_response
        return _mock_respond
    
    def create_llm_proxy(self) -> 'LLMProxy':
        """Retorna un proxy mock."""
        from .llm_proxy import MockLLMProxy
        return MockLLMProxy(self._mock_response)
    
    def is_available(self) -> bool:
        """Siempre disponible para testing."""
        return True


# ============================================================================
# FACTORY METHOD: Selector automático de factory
# ============================================================================

def create_service_factory(genai: Any = None, api_key: str = None) -> AbstractServiceFactory:
    """
    Factory Method para crear la factory apropiada según el entorno.
    
    Args:
        genai: Módulo google.generativeai (opcional)
        api_key: API key de Gemini (opcional)
    
    Returns:
        AbstractServiceFactory: La factory más apropiada
    
    Ejemplo:
        factory = create_service_factory(genai, os.getenv("GEMINI_API_KEY"))
        responder = factory.create_responder()
    """
    if genai and api_key:
        return GeminiServiceFactory(genai, api_key_present=True)
    return LocalServiceFactory()


# ============================================================================
# ALIAS para compatibilidad backward
# ============================================================================

class ServiceFactory(GeminiServiceFactory):
    """Alias para compatibilidad con código existente."""
    
    def make_embedding(self):
        """Alias para create_embedder."""
        return self.create_embedder()
    
    def make_query_embedding(self):
        """Alias para create_query_embedder."""
        return self.create_query_embedder()
    
    def make_responder(self):
        """Alias para create_responder."""
        return self.create_responder()
