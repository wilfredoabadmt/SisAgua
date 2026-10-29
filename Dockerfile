FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PORT=8000

WORKDIR /app

# Dependencias del sistema
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    libpq-dev \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Instalar dependencias Python
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copiar código del proyecto
COPY . .

# Recolectar estáticos
RUN python manage.py collectstatic --noinput

EXPOSE 8000

# Comando de inicio: migración, carga de datos semilla y gunicorn
CMD ["sh", "-c", "python manage.py migrate --noinput && python manage.py loaddata fixtures/seed_roles_permisos.json fixtures/seed_datos_maestros.json fixtures/seed_menus.json && gunicorn config.wsgi:application --bind 0.0.0.0:${PORT:-8000} --workers 2 --timeout 120"]
