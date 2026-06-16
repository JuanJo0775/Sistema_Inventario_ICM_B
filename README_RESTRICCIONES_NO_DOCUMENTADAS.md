# README de Restricciones No Documentadas - Sistema Inventario ICM

Este informe recoge exclusivamente las dos restricciones reales que se detectaron en el repositorio y que no estaban documentadas de forma explicita en la documentacion principal antes de esta revision.

## Restriccion 1: la imagen de produccion depende de dependencias runtime explicitas

### Clasificacion

Tecnológica.

### Evidencia

- `docker-compose.prod.yml` arranca `gunicorn`.
- `docker/Dockerfile` instala solo `requirements/base.txt`.
- `requirements/production.txt` es el unico archivo donde aparece `gunicorn`.

### Que la causa

La imagen de contenedor se construye con las dependencias base, pero el comando de produccion requiere un servidor WSGI que no esta incluido en esa capa base.

### Como limita el diseno

- La imagen de desarrollo no puede darse por valida para produccion.
- El build de produccion debe incorporar una capa adicional o un requirements distinto.
- El runtime productivo depende de la sincronizacion entre Dockerfile, compose y requirements.

### Riesgos que introduce

- Fallo de arranque en produccion si `gunicorn` no esta instalado.
- Divergencia entre lo que se prueba localmente y lo que realmente se despliega.
- Dificultad para auditar si el artefacto publicado tiene todas las dependencias necesarias.

### Componentes afectados

- `docker/Dockerfile`
- `docker-compose.prod.yml`
- `requirements/base.txt`
- `requirements/production.txt`
- Pipeline de build y despliegue

### Alternativas descartadas

- Ejecutar `runserver` en produccion.
- Instalar dependencias manualmente en tiempo de ejecucion.
- Tratar la imagen base de desarrollo como imagen de produccion.

### ADR relacionado

- Se crea [ADR-012](adr/ADR-012.md) para dejar el requisito de runtime explicito.

## Restriccion 2: la suite de pruebas no reproduce el runtime de produccion

### Clasificacion

Organizacional.

### Evidencia

- `config/settings/test.py` usa SQLite in-memory.
- `config/settings/test.py` desactiva `DEFAULT_THROTTLE_CLASSES`.
- `docs/test/README_TEST.md` describe la suite como rapida y orientada a contratos.

### Que la causa

La configuracion de pruebas prioriza velocidad y aislamiento sobre fidelidad exacta del motor de produccion.

### Como limita el diseno

- No se validan exactamente los mismos bloqueos ni el mismo comportamiento de concurrencia de PostgreSQL.
- No se comprueba el throttling de produccion durante la ejecucion normal de la suite.
- La suite no puede usarse como evidencia unica de comportamiento bajo carga o limites reales.

### Riesgos que introduce

- Falsa confianza en escenarios de concurrencia.
- Deteccion tardia de problemas ligados a `select_for_update()` o locking real.
- Brecha entre la regresion automatizada y el comportamiento en produccion.

### Componentes afectados

- `config/settings/test.py`
- `pytest.ini`
- `tests/ers/`
- `apps/*/tests/`

### Alternativas descartadas

- Usar PostgreSQL real en toda la suite.
- Mantener throttling activo en pruebas de rutina.
- Reemplazar la suite automatizada por pruebas manuales.

### ADR relacionado

- Se actualiza [ADR-011](adr/ADR-011.md) para dejar esta limitacion descrita en la estrategia de testing.

## Conclusión

Estas dos restricciones eran reales, afectaban decisiones de arquitectura y operacion, y no estaban descritas con suficiente precision en la documentacion principal. Ahora quedan trazadas en la documentacion consolidada y en los ADRs correspondientes.