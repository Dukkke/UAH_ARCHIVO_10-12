# Usar imagen base ligera de Python 3.12
FROM python:3.12-slim

# Establecer directorio de trabajo
WORKDIR /app

# Instalar dependencias del sistema necesarias para compilar algun paquete si fuera necesario
# build-essential para gcc (a veces necesario para numpy/pandas/scikit-learn en arquitecturas especificas)
RUN apt-get update && apt-get install -y \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Copiar requirements primero para aprovechar caché de docker
COPY requirements.txt .

# Instalar dependencias de Python
RUN pip install --no-cache-dir -r requirements.txt

# Copiar el resto del código
COPY . .

# Exponer el puerto 5000
EXPOSE 5000

# Variables de entorno por defecto (pueden sobreescribirse en docker-compose)
ENV FLASK_APP=api_chatbot.py
ENV FLASK_RUN_HOST=0.0.0.0

# Comando para arrancar la aplicación
# Generar el índice de búsqueda durante la construcción
RUN python create_search_index.py

# Comando para arrancar la aplicación con Gunicorn para producción
CMD ["gunicorn", "--bind", "0.0.0.0:5000", "api_chatbot:app", "--workers", "1", "--threads", "4", "--timeout", "120"]
