# --- Etapa 1: Builder ---
FROM python:3.11-slim AS builder

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /app

RUN apt-get update && apt-get install -y \
    build-essential \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# 1. Instalación de dependencias pesadas (Torch CPU)
RUN pip install --no-cache-dir \
    "torch==2.3.1+cpu" \
    "torchvision==0.18.1+cpu" \
    "ultralytics==8.3.153" \
    --index-url https://download.pytorch.org/whl/cpu \
    --extra-index-url https://pypi.org/simple

# 2. Resto de requerimientos
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# --- CLEANUP STEP (Modified) ---
# Removed the deletion of "test" folders to prevent breaking Django
RUN find /opt/venv -name "__pycache__" -type d -exec rm -rf {} + \
    && find /opt/venv -name "*.pyc" -delete \
    && find /opt/venv -name "tests" -type d -exec rm -rf {} + \
    # REMOVED: && find /opt/venv -name "test" -type d -exec rm -rf {} + \
    && pip uninstall -y pip setuptools \
    && find /opt/venv -name "*.so" -exec strip --strip-unneeded {} + || true

# 3. Copiamos el código
COPY contenedor_inteligente_web/ .

# 4. Recopilamos estáticos
RUN python manage.py collectstatic --noinput


# --- Etapa 2: Final ---
FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV YOLO_CONFIG_DIR="/tmp" 

WORKDIR /app

# Dependencias de sistema mínimas
RUN apt-get update && apt-get install -y \
    libgl1 \
    libglib2.0-0 \
    libstdc++6 \
    && rm -rf /var/lib/apt/lists/*

# Copiamos todo desde el builder
COPY --from=builder /opt/venv /opt/venv
COPY --from=builder /app /app
COPY --from=builder /app/staticfiles /app/staticfiles

ENV PATH="/opt/venv/bin:$PATH"

EXPOSE 8000

CMD ["uvicorn", "contenedor_inteligente_web.asgi:application", "--host", "0.0.0.0", "--port", "8000"]