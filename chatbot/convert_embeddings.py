"""
Script para convertir embeddings a formato compatible con todas las versiones de numpy.
Convierte numpy arrays a listas de Python nativas.
"""
import pickle
import numpy as np

def convert_embeddings():
    print("Cargando embeddings_oficial.pkl...")
    
    with open('embeddings_oficial.pkl', 'rb') as f:
        data = pickle.load(f)
    
    print(f"Embeddings originales: {len(data['embeddings'])}")
    
    # Crear nuevo diccionario con listas en lugar de numpy arrays
    new_data = {}
    
    for key, value in data.items():
        if isinstance(value, np.ndarray):
            print(f"  Convirtiendo {key}: {value.shape}")
            new_data[key] = value.tolist()
        elif isinstance(value, list) and len(value) > 0 and isinstance(value[0], np.ndarray):
            print(f"  Convirtiendo lista de arrays {key}: {len(value)} items")
            new_data[key] = [v.tolist() if isinstance(v, np.ndarray) else v for v in value]
        else:
            new_data[key] = value
    
    # Guardar con protocolo 4 (compatible con Python 3.8+)
    print("Guardando versión compatible...")
    with open('embeddings_compatible.pkl', 'wb') as f:
        pickle.dump(new_data, f, protocol=4)
    
    print("✅ embeddings_compatible.pkl creado")
    print(f"   Embeddings: {len(new_data.get('embeddings', []))}")

if __name__ == '__main__':
    convert_embeddings()
