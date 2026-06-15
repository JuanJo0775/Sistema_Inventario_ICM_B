# ==============================================================================
# STAGE 1: python-deps — Python base + system deps + base requirements
# ==============================================================================
FROM python:3.11-slim AS python-deps

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    libpq-dev gcc postgresql-client \
    && rm -rf /var/lib/apt/lists/*

COPY requirements/base.txt requirements/
RUN pip install --no-cache-dir -r requirements/base.txt

# ==============================================================================
# STAGE 2: dev — Desarrollo local con hot-reload
# ==============================================================================
FROM python-deps AS dev

COPY requirements/development.txt requirements/
RUN pip install --no-cache-dir -r requirements/development.txt

COPY . .
COPY docker/entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh

EXPOSE 8000
ENTRYPOINT ["/entrypoint.sh"]
CMD ["python", "manage.py", "runserver", "0.0.0.0:8000"]

# ==============================================================================
# STAGE 3: test — Ejecución de pruebas
# ==============================================================================
FROM python-deps AS test

COPY requirements/development.txt requirements/
RUN pip install --no-cache-dir -r requirements/development.txt

COPY . .
COPY docker/entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh

ENTRYPOINT ["/entrypoint.sh"]
CMD ["pytest"]

# ==============================================================================
# STAGE 4: production — Producción con Gunicorn
# ==============================================================================
FROM python-deps AS production

COPY requirements/production.txt requirements/
RUN pip install --no-cache-dir -r requirements/production.txt

COPY . .
COPY docker/entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh

EXPOSE 8000
ENTRYPOINT ["/entrypoint.sh"]
CMD ["gunicorn", "config.wsgi:application", "--bind", "0.0.0.0:8000"]
