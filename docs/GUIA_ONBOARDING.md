# Guía de Onboarding — Sistema Inventario ICM

Bienvenido/a al proyecto. Esta guía contiene los comandos rápidos y exactos que necesitas para configurar tu entorno de desarrollo local paso a paso.

Para operación de integración y despliegue (pipelines, backups, promoción y rollback), consulta también:

- [README_CICD.md](CI/README_CICD.md)

## 1. Clonar el repositorio y entrar a la carpeta

Si aún no lo has hecho, clona el proyecto y entra al directorio:

```bash
git clone <https://github.com/JuanJo0775/Sistema_Inventario_ICM_B.git>
cd Sistema_Inventario_ICM
```

## 2. Configurar el entorno virtual (Python 3.11+)

Recomendamos usar `venv` para aislar las dependencias del proyecto. Asegúrate de tener Python instalado y en tu PATH.

```cmd
python -m venv .venv
.venv\Scripts\activate
```

## 3. Instalar dependencias

Una vez activado el entorno virtual, instala las dependencias de desarrollo (que ya incluyen las dependencias base):

```bash
pip install -r requirements/development.txt
```

## 4. Configurar variables de entorno

El proyecto usa variables de entorno para su configuración y conexión a la base de datos PostgreSQL local.

```cmd
copy .env.example .env
```

Abre el archivo `.env` recién creado en tu editor. Ajusta las siguientes variables mínimas:

- **Base de datos** — `DB_NAME`, `DB_USER`, `DB_PASSWORD`, `DB_HOST`, `DB_PORT` para tu PostgreSQL local.
- **Usuario inicial** — `ALMACENISTA_PASSWORD` (contraseña del primer usuario; requerida por `create_almacenista`).
- **Email (opcional en desarrollo)** — `EMAIL_HOST`, `EMAIL_HOST_USER`, `EMAIL_HOST_PASSWORD`, `EMAIL_PORT`, `EMAIL_USE_TLS` para probar el flujo de recuperación de contraseña con [Mailtrap](https://mailtrap.io).
- **Frontend** — `FRONTEND_URL` (default `http://localhost:3000`) determina la URL base del enlace en el email de recuperación.
- **Token de recuperación** — `PASSWORD_RESET_TOKEN_EXPIRY_MINUTES` (default `10`) controla el tiempo de expiración del link de reset.

> Para una referencia completa de cada variable con ejemplos para desarrollo, staging y producción, consulta:
> **[docs/guias/ENV_GUIDE.md](guias/ENV_GUIDE.md)**

## 5. Ejecutar migraciones

Con la base de datos PostgreSQL creada localmente y el entorno virtual activado, aplica las migraciones de Django:

```bash
python manage.py makemigrations

python manage.py migrate
```

## 6. Cargar datos semilla (Opcional pero recomendado)

Para tener datos iniciales (usuarios predeterminados, productos, ubicaciones) y poder probar el sistema de inmediato:

```bash
python manage.py create_almacenista
python scripts/seed_db/run.py
```

## 7. Crear superusuario (Opcional)

Si necesitas acceso completo al panel de administración (Django admin):

```bash
python manage.py createsuperuser
```

## 8. Iniciar el servidor de desarrollo

Ya tienes todo listo, ahora levanta el servidor local:

```bash
python manage.py runserver 0.0.0.0:8000
```

El proyecto estará disponible en:
- **Swagger UI (Documentación de API):** [http://localhost:8000/api/docs/](http://localhost:8000/api/docs/)
- **ReDoc:** [http://localhost:8000/api/redoc/](http://localhost:8000/api/redoc/)
- **API (Base Path):** `http://localhost:8000/api/v1/`
- **Django Admin:** `http://localhost:8000/admin/`

## 9. Comandos Útiles (Testing y Formateo)

Para asegurar la calidad del código, puedes usar los siguientes comandos en tu día a día:

```bash
# Ejecutar todos los tests 
pytest

# Ejecutar tests de una aplicación específica
pytest apps/movements/tests/

# Ejecutar tests con reporte de cobertura
pytest --cov=apps

# Formatear el código (Black y isort)
black apps/ shared/ config/
isort apps/ shared/ config/
```

## 10. Management Commands del sistema

El sistema incluye los siguientes comandos de gestión operativa:

```bash
# Escanear y generar alertas de stock/vencimiento (idempotente)
python manage.py scan_alerts
python manage.py scan_alerts --types stock,expiry,location
python manage.py scan_alerts --dry-run   # simular sin cambios

# Verificar integridad de stock (caché vs. ledger)
python manage.py verify_stock_integrity
python manage.py verify_stock_integrity --fix  # reparar divergencias

# Entregar webhooks pendientes en la cola (seguro para cron paralelo)
python manage.py deliver_webhooks
python manage.py deliver_webhooks --batch-size 100

# Archivar logs de auditoría antiguos
python manage.py archive_old_audit_logs --older-than-days 365
python manage.py archive_old_audit_logs --dry-run  # ver cuántos sin modificar
```

**Cron recomendado en producción:**
```
*/2  * * * *  python manage.py deliver_webhooks           # cada 2 min
0    */6 * * *  python manage.py scan_alerts               # cada 6 horas
0    2   * * *  python manage.py verify_stock_integrity    # diario 2am
0    3   1 * *  python manage.py archive_old_audit_logs    # mensual
```

## 11. CI/CD y operación de despliegue

Si vas a participar en despliegues o soporte operativo, revisa el runbook completo:

- [README_CICD.md](CI/README_CICD.md)

Ahí se documenta:

- flujo CI con checks bloqueantes,
- despliegue a staging,
- promoción manual a production por digest,
- política de backups, restauración y rollback,
- manejo de secretos y controles de seguridad.
