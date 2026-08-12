# ==========================================
# ETAPA 1: Construcción y Dependencias (Builder)
# ==========================================
FROM python:3.11-slim AS builder

# Evita que Python escriba archivos .pyc en disco y desactiva el buffering de logs
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

# Instalamos herramientas básicas de compilación si son necesarias
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Copiamos solo el archivo de requerimientos para aprovechar el cache de Docker
COPY requeriments.txt .

# Instalamos las dependencias en una carpeta wheels/ o directamente en el sistema
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requeriments.txt


# ==========================================
# ETAPA 2: Imagen Final de Producción (Runner)
# ==========================================
FROM python:3.11-slim AS runner

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

# Copiamos las librerías instaladas desde la etapa de construcción
COPY --from=builder /usr/local/lib/python3.11/site-packages /usr/local/lib/python3.11/site-packages
COPY --from=builder /usr/local/bin /usr/local/bin

# Copiamos todo el código fuente de nuestra aplicación
COPY . /app

# Buenas prácticas de seguridad: Crear un usuario no-root
RUN useradd -m appuser && chown -R appuser:appuser /app
USER appuser

# Exponemos el puerto estándar donde correrá Uvicorn
EXPOSE 8000

# Comando para ejecutar Uvicorn invocando la app configurada en main.py
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]