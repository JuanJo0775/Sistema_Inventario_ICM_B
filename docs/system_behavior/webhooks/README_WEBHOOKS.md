# Módulo de Webhooks

## 1. Resumen

El módulo `webhooks` permite notificar sistemas externos mediante HTTP POST firmados cuando ocurren eventos del sistema. Soporta suscripción por tipo de evento, reintentos con backoff exponencial y entrega paralela segura.

**NEW-03** — Notificaciones a sistemas externos vía webhooks.

---

## 2. Modelos

### 2.1 WebhookEndpoint

| Campo | Tipo | Descripción |
|-------|------|-------------|
| `id` | UUID (PK) | Identificador único |
| `url` | URLField(500) | URL destino del webhook |
| `secret` | CharField(128) | Clave compartida HMAC-SHA256 |
| `events` | JSONField(default=list) | Tipos de evento suscritos, ej: `["STOCK_CRITICO"]` |
| `is_active` | BooleanField(default=True) | Endpoint activo/inactivo para recepción |
| `deleted_at` | DateTimeField (nullable) | SoftDeleteModel — eliminación lógica, separada de `is_active` |
| `max_retries` | PositiveSmallIntegerField(default=3) | Reintentos máximos |
| `created_by` | FK -> User (nullable) | Almacenista que creó |
| `created_at` / `updated_at` | DateTimeField | Automáticos |

### 2.2 WebhookDelivery

| Campo | Tipo | Descripción |
|-------|------|-------------|
| `id` | UUID (PK) | Identificador único |
| `endpoint` | FK -> WebhookEndpoint | Destino |
| `event_type` | CharField(64) | Tipo de evento |
| `payload` | JSONField | Cuerpo del evento |
| `status` | CharField(16) | PENDING / DELIVERED / FAILED |
| `attempts` | PositiveSmallIntegerField(default=0) | Intentos realizados |
| `last_attempt_at` | DateTimeField (nullable) | Último intento |
| `next_retry_at` | DateTimeField (nullable) | Próximo reintento |
| `response_code` | PositiveSmallIntegerField (nullable) | Código HTTP de respuesta |
| `response_body` | TextField(default="") | Cuerpo de respuesta |

---

## 3. Servicios

| Función | Descripción |
|---------|-------------|
| `queue_webhook_event(event_type, payload)` | Encola evento a todos los endpoints activos suscritos |
| `deliver_pending_webhooks(batch_size=50)` | Procesa entregas pendientes con select_for_update(skip_locked=True) para paralelismo seguro |
| `_sign_payload(secret, body)` | Genera firma HMAC-SHA256: `sha256=<hex>` |
| `_attempt_delivery(delivery)` | HTTP POST con headers X-ICM-Signature, X-ICM-Event; captura respuesta |
| `_schedule_retry(delivery, max_retries)` | Backoff exponencial: 1min, 5min, 30min; max intentos → FAILED |

### Flujo de entrega

```
queue_webhook_event(event_type, payload)
  → Filtra endpoints activos con event_type suscrito
  → bulk_create WebhookDelivery (PENDING, next_retry_at=now)
  → Retorna count de deliveries creados

deliver_pending_webhooks(batch_size)
  → select_for_update(skip_locked=True) sobre deliveries pendientes
  → Por cada delivery:
      → Serializa payload → JSON
      → Firma con HMAC-SHA256
      → HTTP POST a endpoint.url
      → 2xx → DELIVERED
      → Error → _schedule_retry() (backoff)
      → attempts ≥ max_retries → FAILED
```

---

## 4. Endpoints

Bajo `/api/v1/webhooks/`. Solo almacenistas.

| Método | Ruta | Descripción |
|--------|------|-------------|
| GET/POST | `endpoints/` | Listar / crear endpoints |
| GET/PUT/PATCH | `endpoints/<pk>/` | Detalle / actualizar |
| DELETE | `endpoints/<pk>/` | Almacenista | Soft delete (eliminación lógica) |
| POST | `endpoints/<pk>/restore/` | Almacenista | Restaurar endpoint |
| POST | `endpoints/<pk>/test/` | Enviar evento de prueba |
| GET | `deliveries/` | Historial de entregas |
| GET | `stats/` | Estadísticas de entregas |

---

## 5. Seguridad

- **HMAC-SHA256**: payload firmado con `secret` compartido, header `X-ICM-Signature`.
- **Soft delete**: endpoints heredan de `SoftDeleteModel`. `deleted_at` controla existencia lógica; `is_active` controla disponibilidad para recepción de eventos.
- **Paralelismo seguro**: `select_for_update(skip_locked=True)` evita doble-entrega con múltiples workers.

Management command `deliver_webhooks` para cron jobs.

---

## 6. Escenarios esperados

**WEBH-S01:** Crear endpoint con eventos suscritos → 201 + endpoint activo.
**WEBH-S02:** Evento del sistema dispara webhook → deliveries creados para todos los endpoints suscritos.
**WEBH-S03:** Delivery exitoso → status DELIVERED, response_code capturado.
**WEBH-S04:** Delivery falla → reintento a los 1min, 5min, 30min; luego FAILED.
**WEBH-S05:** Desactivar endpoint → is_active=False, no recibe nuevos eventos, deliveries históricas preservadas.
**WEBH-S06:** Endpoint de prueba → POST test con payload custom.
**WEBH-S07:** Múltiples workers procesan deliveries en paralelo → sin doble-entrega (skip_locked).
