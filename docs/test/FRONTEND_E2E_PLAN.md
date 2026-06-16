# Frontend E2E Plan — Handoff

Objetivo
-------
Proveer al equipo frontend un conjunto claro de escenarios E2E (contratos + pasos) que permitan implementar pruebas UI reproducibles que validen los flujos críticos del sistema: autenticación por roles y ventanas horarias, registro de entradas que resuelven alertas, y despacho que consume lotes FEFO.

Recomendación de tooling
------------------------
- Playwright (preferido): soporte multi-browser, network interception y runners en CI.
- Cypress: alternativa válida si el equipo ya la usa.

Escenarios prioritarios (cada escenario debe incluir: pasos, datos de prueba, endpoint(s) implicados y aserciones esperadas)
--------------------------------------------------------------------------------

1) Login y renovación de token con restricción horaria (auxiliar)
   - Objetivo: validar que un usuario con rol `AUXILIAR_DESPACHO` no puede renovar token fuera de la ventana permitida.
   - Pasos UI (frontend):
     1. Ingresar credenciales de `auxiliar` (usar fixture/test user proporcionado por backend).
     2. Confirmar login aceptado dentro de la ventana (simular hora local en Playwright network mock o usar endpoint de login con mock de timezone).
     3. Simular paso del tiempo (o forzar refresh con token obtenido) y solicitar `token/refresh` fuera de la ventana.
   - Endpoint(s): `POST /api/v1/auth/token/` y `POST /api/v1/auth/token/refresh/`.
   - Aserciones: respuesta 403 en refresh fuera de ventana para `auxiliar` ; 200 para `almacenista`.

2) Registrar entrada que resuelve alerta de reorden
   - Objetivo: validar que al confirmar una entrada que cubre `reorder_point`, la alerta se marca resuelta y se registra el `movement_id` que la resolvió.
   - Pasos UI:
     1. Pre-condición: crear (o usar) producto con `reorder_point` > 0 y alerta activa (puede crearse via API fixture).
     2. En UI registrar entrada (form) con cantidad suficiente para superar `reorder_point`.
     3. Esperar a que la UI muestre alerta resuelta (polling o refresh automático).
   - Endpoint(s): `POST /api/v1/movements/` (payload de entrada), `GET /api/v1/alerts/`.
   - Aserciones: `alerts` para ese producto ya no aparece en lista de activas; la entrada tiene relation `resolved_alert_id` o la API devuelve referencia al movement que resolvió la alerta.

3) Flujo de despacho FEFO (consumo por vencimiento)
   - Objetivo: validar que el frontend muestra los lotes disponibles y que la confirmación de despacho consume primero el lote con fecha de vencimiento más próxima.
   - Pasos UI:
     1. Pre-condición: crear dos lotes para el mismo producto (`lot_early`, `lot_late`) con cantidades conocidas.
     2. En UI, iniciar despacho para X unidades (X menor que cantidad del primer lote si quieres validar consumo parcial, o mayor para consumir múltiples lotes).
     3. Confirmar despacho y validar en la respuesta / UI qué lotes se usaron.
   - Endpoint(s): `POST /api/v1/movements/` (despacho), `GET /api/v1/inventory/` o `GET /api/v1/reports/expiring_lots/`.
   - Aserciones: el first-out corresponde al lote con fecha de vencimiento más cercana.

Datos de prueba y recomendaciones
--------------------------------
- Proveer endpoints backend para crear fixtures (factories API) o usar APIs públicas de admin para crear usuarios, lotes y productos en un estado conocido.
- Usar Playwright fixtures para interceptar llamadas y mockear timezone cuando sea necesario.
- Evitar dependencias de datos manuales; preferir endpoints de test que creen entidad y devuelvan IDs.

Ejemplo de payloads
-------------------

Crear movimiento (entrada):

```json
POST /api/v1/movements/
{
  "movement_type": "ENTRY",
  "product": "<product_id>",
  "destination_location": "<location_id>",
  "quantity": 20,
  "lot_code": "L-UI-001",
  "lot_expiration_date": "2027-01-01"
}
```

Crear movimiento (despacho):

```json
POST /api/v1/movements/
{
  "movement_type": "DISPATCH",
  "product": "<product_id>",
  "origin_location": "<location_id>",
  "quantity": 5
}
```

Handover checklist para frontend
--------------------------------
- Implementar tests Playwright/Cypress con los escenarios definidos.
- Documentar en `docs/test/FRONTEND_E2E_PLAN.md` cualquier mock o datos adicionales usados.
- Asegurar que la ejecución CI para E2E corre contra un despliegue de backend + Postgres (Docker Compose) o contra un entorno de staging controlado.

---

Archivo creado automáticamente como primer artefacto de handoff; el equipo frontend puede implementarlo usando Playwright o Cypress siguiendo los escenarios y payloads arriba.
