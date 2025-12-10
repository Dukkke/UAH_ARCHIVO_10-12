"""
Script MEJORADO para crear índice de búsqueda TF-IDF local
Incluye: título, href, dc:subject, dc:creator, dc:coverage
"""
import json
import pickle
from sklearn.feature_extraction.text import TfidfVectorizer
import numpy as np

def load_documents():
    with open('clean_with_metadata.json', 'r', encoding='utf-8', errors='ignore') as f:
        docs = json.load(f)
    print(f"📂 {len(docs)} documentos cargados desde clean_with_metadata.json")
    return docs

import unicodedata

def normalize_text(text):
    """
    Normalización robusta para búsqueda:
    1. Minúsculas
    2. Eliminar acentos
    3. Manejo simple de plurales (stemming básico)
    """
    if not isinstance(text, str):
        text = str(text)
    
    # Minúsculas y eliminación de acentos
    text = text.lower()
    text = ''.join(c for c in unicodedata.normalize('NFD', text) if unicodedata.category(c) != 'Mn')
    
    # Stemming básico para plurales (muy simple para español)
    words = text.split()
    stemmed_words = []
    for word in words:
        # Si termina en 'es' (árboles -> árbol, canciones -> cancion)
        if word.endswith('es') and len(word) > 4:
            word = word[:-2]
        # Si termina en 's' (casas -> casa)
        elif word.endswith('s') and len(word) > 3 and not word.endswith('ss'):
            word = word[:-1]
        stemmed_words.append(word)
    
    return ' '.join(stemmed_words)

def create_search_index(documents):
    """Crea índice TF-IDF COMPLETO para búsqueda"""
    print("🔄 Creando índice de búsqueda TF-IDF MEJORADO (con stemming)...")
    
    texts = []
    for doc in documents:
        parts = []
        
        # TÍTULO (campo principal) - repetido 3 veces para dar más peso
        title = doc.get('title', '')
        parts.append(title)
        parts.append(title)
        parts.append(title)
        
        # HREF (puntos de acceso, contiene palabras clave de la URL)
        href = doc.get('href', '')
        # Extraer palabras de la URL (después del dominio)
        if href:
            url_parts = href.split('/')[-1].replace('-', ' ').replace('_', ' ')
            parts.append(url_parts)
        
        # DC:SUBJECT (materias)
        subjects = doc.get('dc:subject', [])
        if isinstance(subjects, list):
            parts.extend(subjects[:15])
        elif subjects:
            parts.append(str(subjects))
        
        # DC:CREATOR (autores)
        creators = doc.get('dc:creator', [])
        if isinstance(creators, list):
            parts.extend(creators[:10])
        elif creators:
            parts.append(str(creators))
        
        # DC:COVERAGE (lugares)
        coverages = doc.get('dc:coverage', [])
        if isinstance(coverages, list):
            parts.extend(coverages[:5])
        elif coverages:
            parts.append(str(coverages))
        
        # DC:DATE (fechas)
        dates = doc.get('dc:date', [])
        if isinstance(dates, list):
            parts.extend([str(d) for d in dates[:3]])
        elif dates:
            parts.append(str(dates))
        
        # Unir todo y NORMALIZAR
        full_text = ' '.join(str(p) for p in parts if p)
        # Aquí aplicamos la normalización para que el índice contenga términos normalizados
        normalized_text = normalize_text(full_text)
        texts.append(normalized_text)
    
    # Crear vectorizador TF-IDF con configuración optimizada
    vectorizer = TfidfVectorizer(
        max_features=15000,      # Más vocabulario
        ngram_range=(1, 3),      # Hasta trigramas para frases como "Consejo de Gabinete"
        stop_words=None,         # Mantener todas las palabras
        min_df=1,                # Incluir términos raros
        max_df=0.90,             # Excluir términos muy comunes
        token_pattern=r'(?u)\b[\w-]+\b',  # Incluir palabras con guiones
    )
    
    tfidf_matrix = vectorizer.fit_transform(texts)
    
    print(f"✅ Índice creado: {tfidf_matrix.shape[0]} docs x {tfidf_matrix.shape[1]} términos")
    
    return {
        'vectorizer': vectorizer,
        'matrix': tfidf_matrix,
        'texts': texts
    }

def save_index(index_data):
    with open('search_index.pkl', 'wb') as f:
        pickle.dump(index_data, f)
    print("💾 Índice guardado en search_index.pkl")

if __name__ == "__main__":
    print("=" * 50)
    print("🔍 CREACIÓN DE ÍNDICE TF-IDF MEJORADO")
    print("=" * 50)
    
    documents = load_documents()
    index = create_search_index(documents)
    save_index(index)
    
    print("=" * 50)
    print("✅ ÍNDICE LISTO - Incluye título, href, subjects,")
    print("   creators, coverage y dates")
    print("=" * 50)
