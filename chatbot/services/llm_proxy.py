"""
Proxy Pattern - Control de acceso al servicio LLM
=================================================

Patrón: PROXY (Estructural)
Propósito: Proporcionar un sustituto o marcador de posición para otro objeto
           para controlar el acceso a él.

Variantes implementadas:
1. Protection Proxy: Verifica disponibilidad de API antes de llamar
2. Caching Proxy: Cachea respuestas para evitar llamadas repetidas
3. Logging Proxy: Registra todas las llamadas al servicio
4. Virtual Proxy: Inicialización lazy del modelo

Principios SOLID:
- SRP: Cada proxy tiene una responsabilidad única
- OCP: Nuevos proxies pueden agregarse sin modificar existentes
- LSP: Todos los proxies son intercambiables (misma interfaz)
- ISP: Interfaz mínima en LLMProxy
- DIP: Dependemos de la abstracción LLMProxy
"""

from abc import ABC, abstractmethod
from typing import Any, Dict, Optional, List
from datetime import datetime, timedelta
from functools import lru_cache
import hashlib
import time


# ============================================================================
# ABSTRACCIÓN: Interfaz del Proxy
# ============================================================================

class LLMProxy(ABC):
    """
    Interfaz base del Proxy Pattern.
    
    Define la interfaz que tanto el proxy como el servicio real deben implementar.
    Permite que el proxy sea transparente para el cliente.
    
    Principio LSP: Cualquier implementación de LLMProxy debe ser intercambiable.
    """
    
    @abstractmethod
    def embed(self, text: str, *, model: str, task_type: str) -> Optional[Dict[str, Any]]:
        """Genera embedding para un texto."""
        pass
    
    @abstractmethod
    def generate(self, prompt: str, *, model_name: str) -> Optional[str]:
        """Genera una respuesta basada en el prompt."""
        pass
    
    @abstractmethod
    def is_available(self) -> bool:
        """Verifica si el servicio está disponible."""
        pass


# ============================================================================
# REAL SUBJECT: El servicio real de Gemini
# ============================================================================

class GeminiRealService(LLMProxy):
    """
    Real Subject - El servicio real de Google Gemini.
    
    Esta clase hace las llamadas reales a la API de Gemini.
    Normalmente no se usa directamente, sino a través de un Proxy.
    """
    
    def __init__(self, genai: Any) -> None:
        self._genai = genai
        self._available = True
    
    def embed(self, text: str, *, model: str, task_type: str) -> Optional[Dict[str, Any]]:
        """Llamada real a la API de embeddings."""
        try:
            result = self._genai.embed_content(
                model=model,
                content=text,
                task_type=task_type,
            )
            return {"embedding": result.get("embedding")}
        except Exception as e:
            print(f"❌ Error en embedding: {e}")
            return None
    
    def generate(self, prompt: str, *, model_name: str) -> Optional[str]:
        """Llamada real a la API de generación."""
        try:
            model = self._genai.GenerativeModel(model_name)
            response = model.generate_content(prompt)
            return getattr(response, "text", None)
        except Exception as e:
            print(f"❌ Error en generación: {e}")
            return None
    
    def is_available(self) -> bool:
        return self._available


# ============================================================================
# PROTECTION PROXY: Verifica acceso antes de llamar al servicio
# ============================================================================

class GeminiClientProxy(LLMProxy):
    """
    Protection Proxy - Controla el acceso al servicio Gemini.
    
    Responsabilidades:
    1. Verificar que la API key esté presente antes de cada llamada
    2. Manejar errores de forma graceful
    3. Deshabilitar el servicio si hay fallos repetidos
    
    Principio SRP: Solo se encarga de protección/validación.
    """
    
    def __init__(self, genai: Any, api_key_present: bool) -> None:
        self._genai = genai
        self._enabled = api_key_present
        self._failure_count = 0
        self._max_failures = 5
    
    def embed(self, text: str, *, model: str, task_type: str) -> Optional[Dict[str, Any]]:
        """Protege la llamada de embedding verificando disponibilidad."""
        if not self._enabled:
            return None
        
        if self._failure_count >= self._max_failures:
            return None  # Circuit breaker activado
        
        try:
            result = self._genai.embed_content(
                model=model,
                content=text,
                task_type=task_type,
            )
            self._failure_count = 0  # Reset en éxito
            return {"embedding": result.get("embedding")}
        except Exception as e:
            self._failure_count += 1
            print(f"⚠️ Error en embedding ({self._failure_count}/{self._max_failures}): {e}")
            return None
    
    def generate(self, prompt: str, *, model_name: str) -> Optional[str]:
        """Protege la llamada de generación verificando disponibilidad."""
        if not self._enabled:
            return None
        
        if self._failure_count >= self._max_failures:
            return None  # Circuit breaker activado
        
        try:
            model = self._genai.GenerativeModel(model_name)
            response = model.generate_content(prompt)
            self._failure_count = 0  # Reset en éxito
            return getattr(response, "text", None)
        except Exception as e:
            self._failure_count += 1
            print(f"⚠️ Error en generación ({self._failure_count}/{self._max_failures}): {e}")
            return None
    
    def is_available(self) -> bool:
        return self._enabled and self._failure_count < self._max_failures
    
    def reset_circuit_breaker(self) -> None:
        """Resetea el circuit breaker manualmente."""
        self._failure_count = 0


# ============================================================================
# CACHING PROXY: Cachea respuestas para optimizar costos
# ============================================================================

class CachingLLMProxy(LLMProxy):
    """
    Caching Proxy - Cachea respuestas para evitar llamadas repetidas.
    
    Optimiza costos y latencia cacheando:
    - Embeddings por texto (muy útil para documentos)
    - Respuestas por prompt (menos útil, pero posible)
    
    Principio SRP: Solo se encarga de caching.
    Principio OCP: Decora cualquier LLMProxy sin modificarlo.
    """
    
    def __init__(self, wrapped: LLMProxy, cache_ttl_seconds: int = 3600) -> None:
        """
        Args:
            wrapped: El proxy real a decorar
            cache_ttl_seconds: Tiempo de vida del cache en segundos
        """
        self._wrapped = wrapped
        self._cache_ttl = cache_ttl_seconds
        self._embedding_cache: Dict[str, tuple] = {}  # {hash: (embedding, timestamp)}
        self._response_cache: Dict[str, tuple] = {}   # {hash: (response, timestamp)}
    
    def _hash_key(self, *args) -> str:
        """Genera un hash único para los argumentos."""
        key = "|".join(str(a) for a in args)
        return hashlib.md5(key.encode()).hexdigest()
    
    def _is_valid(self, timestamp: datetime) -> bool:
        """Verifica si una entrada de cache es válida."""
        return datetime.now() - timestamp < timedelta(seconds=self._cache_ttl)
    
    def embed(self, text: str, *, model: str, task_type: str) -> Optional[Dict[str, Any]]:
        """Embedding con cache."""
        cache_key = self._hash_key(text, model, task_type)
        
        # Buscar en cache
        if cache_key in self._embedding_cache:
            cached, timestamp = self._embedding_cache[cache_key]
            if self._is_valid(timestamp):
                return cached
        
        # Llamar al servicio real
        result = self._wrapped.embed(text, model=model, task_type=task_type)
        
        # Guardar en cache
        if result:
            self._embedding_cache[cache_key] = (result, datetime.now())
        
        return result
    
    def generate(self, prompt: str, *, model_name: str) -> Optional[str]:
        """Generación con cache (opcional, generalmente no se usa)."""
        # Para respuestas generativas, normalmente no cacheamos
        # pero lo dejamos preparado por si se necesita
        return self._wrapped.generate(prompt, model_name=model_name)
    
    def is_available(self) -> bool:
        return self._wrapped.is_available()
    
    def clear_cache(self) -> None:
        """Limpia todo el cache."""
        self._embedding_cache.clear()
        self._response_cache.clear()
    
    def get_cache_stats(self) -> Dict[str, int]:
        """Retorna estadísticas del cache."""
        return {
            "embedding_entries": len(self._embedding_cache),
            "response_entries": len(self._response_cache),
        }


# ============================================================================
# LOGGING PROXY: Registra todas las llamadas
# ============================================================================

class LoggingLLMProxy(LLMProxy):
    """
    Logging Proxy - Registra todas las llamadas al servicio LLM.
    
    Útil para:
    - Debugging
    - Monitoreo de uso
    - Auditoría
    - Análisis de rendimiento
    
    Principio SRP: Solo se encarga de logging.
    """
    
    def __init__(self, wrapped: LLMProxy, logger_prefix: str = "[LLM]") -> None:
        self._wrapped = wrapped
        self._prefix = logger_prefix
        self._call_count = 0
        self._total_time = 0.0
    
    def embed(self, text: str, *, model: str, task_type: str) -> Optional[Dict[str, Any]]:
        """Embedding con logging."""
        self._call_count += 1
        start = time.time()
        
        print(f"{self._prefix} 📊 Embedding request #{self._call_count}")
        print(f"{self._prefix}    Model: {model}, Task: {task_type}")
        print(f"{self._prefix}    Text length: {len(text)} chars")
        
        result = self._wrapped.embed(text, model=model, task_type=task_type)
        
        elapsed = time.time() - start
        self._total_time += elapsed
        
        status = "✅ Success" if result else "❌ Failed"
        print(f"{self._prefix}    {status} in {elapsed:.2f}s")
        
        return result
    
    def generate(self, prompt: str, *, model_name: str) -> Optional[str]:
        """Generación con logging."""
        self._call_count += 1
        start = time.time()
        
        print(f"{self._prefix} 🤖 Generate request #{self._call_count}")
        print(f"{self._prefix}    Model: {model_name}")
        print(f"{self._prefix}    Prompt length: {len(prompt)} chars")
        
        result = self._wrapped.generate(prompt, model_name=model_name)
        
        elapsed = time.time() - start
        self._total_time += elapsed
        
        if result:
            print(f"{self._prefix}    ✅ Response: {len(result)} chars in {elapsed:.2f}s")
        else:
            print(f"{self._prefix}    ❌ Failed in {elapsed:.2f}s")
        
        return result
    
    def is_available(self) -> bool:
        return self._wrapped.is_available()
    
    def get_stats(self) -> Dict[str, Any]:
        """Retorna estadísticas de uso."""
        return {
            "total_calls": self._call_count,
            "total_time_seconds": self._total_time,
            "avg_time_seconds": self._total_time / max(1, self._call_count),
        }


# ============================================================================
# NULL PROXY: Implementación nula para modo offline
# ============================================================================

class NullLLMProxy(LLMProxy):
    """
    Null Object Pattern como Proxy.
    
    Retorna None para todas las operaciones.
    Útil cuando no hay API disponible.
    """
    
    def embed(self, text: str, *, model: str, task_type: str) -> Optional[Dict[str, Any]]:
        return None
    
    def generate(self, prompt: str, *, model_name: str) -> Optional[str]:
        return None
    
    def is_available(self) -> bool:
        return False


# ============================================================================
# MOCK PROXY: Para testing
# ============================================================================

class MockLLMProxy(LLMProxy):
    """
    Mock Proxy para testing.
    
    Retorna respuestas predefinidas para pruebas unitarias.
    """
    
    def __init__(self, mock_response: str = "Mock response") -> None:
        self._mock_response = mock_response
        self._mock_embedding = [0.0] * 768
    
    def set_mock_embedding(self, embedding: List[float]) -> None:
        self._mock_embedding = embedding
    
    def set_mock_response(self, response: str) -> None:
        self._mock_response = response
    
    def embed(self, text: str, *, model: str, task_type: str) -> Optional[Dict[str, Any]]:
        return {"embedding": self._mock_embedding.copy()}
    
    def generate(self, prompt: str, *, model_name: str) -> Optional[str]:
        return self._mock_response
    
    def is_available(self) -> bool:
        return True


# ============================================================================
# DECORATOR: Combinar múltiples proxies
# ============================================================================

def create_production_proxy(genai: Any, api_key_present: bool) -> LLMProxy:
    """
    Factory Method para crear un proxy de producción con todas las capas.
    
    Cadena: Protection → Caching → Logging → Real Service
    
    Ejemplo:
        proxy = create_production_proxy(genai, True)
        result = proxy.generate("¿Qué es un Fondo?", model_name="gemini-2.0-flash-exp")
    """
    # Capa base: Protection Proxy
    base_proxy = GeminiClientProxy(genai, api_key_present)
    
    # Opcional: Agregar caching
    cached_proxy = CachingLLMProxy(base_proxy, cache_ttl_seconds=3600)
    
    # Opcional: Agregar logging (solo en desarrollo)
    # logged_proxy = LoggingLLMProxy(cached_proxy, "[Gemini]")
    
    return cached_proxy
