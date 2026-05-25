

<!-- file: RF001-S01.md -->

# Inicio de sesión exitoso como Almacenista

## Nombre del test

`tests/ers/test_gherkin_dynamic.py::test_RF001_S01`

## Propósito

Validar el criterio de aceptación Gherkin del ERS ICM para **RF001** — escenario 1.

## Requisito o caso de negocio asociado

- **Requisito:** `RF001` (ver `docs/requisitos/ERS_ICM_Requisitos.md`).
- **Fuente complementaria:** `docs/requisitos/ICM_Informe_Elicitacion_v2_plus.docx.md` (contexto de negocio y BR cuando aplica).

## Inputs (Given / When — extracto ERS)

**Given (Dado que):**
- El usuario tiene un rol de "Almacenista"
- Sus credenciales están activas en el sistema

**When (Cuando):**
- Ingresa su nombre de usuario y contraseña correctos
- Hace clic en "Iniciar sesión"

**Then (Entonces):**
- El sistema autentica al usuario correctamente
- Lo redirige al dashboard del Almacenista
- Registra el evento de inicio de sesión con el UserID y timestamp exacto

---

## Resultado esperado (Then)

Ver sección **Then** en el extracto anterior del ERS. En automatización backend, el test asociado comprueba el contrato API/servicio equivalente o queda explícitamente marcado como pendiente si el criterio es solo UI, infraestructura o legalidad operativa fuera del alcance de pytest.

## Link directo al test

Ejecutar:

```bash
pytest tests/ers/test_gherkin_dynamic.py::test_RF001_S01 -v
```

Archivo de definición dinámica: [`tests/ers/test_gherkin_dynamic.py`](../../tests/ers/test_gherkin_dynamic.py)

Implementaciones concretas (cuando existan) pueden delegarse en módulos bajo `tests/ers/impl/`.

---

## Estado de automatización backend

Implementada en `tests/ers/gherkin_impl.py` (comprueba API/servicios equivalentes al Then del ERS).


<!-- file: RF001-S02.md -->

# Inicio de sesión exitoso como Auxiliar de Despacho dentro del horario permitido

## Nombre del test

`tests/ers/test_gherkin_dynamic.py::test_RF001_S02`

## Propósito

Validar el criterio de aceptación Gherkin del ERS ICM para **RF001** — escenario 2.

## Requisito o caso de negocio asociado

- **Requisito:** `RF001` (ver `docs/requisitos/ERS_ICM_Requisitos.md`).
- **Fuente complementaria:** `docs/requisitos/ICM_Informe_Elicitacion_v2_plus.docx.md` (contexto de negocio y BR cuando aplica).

## Inputs (Given / When — extracto ERS)

**Given (Dado que):**
- El usuario tiene rol "Auxiliar de Despacho"
- La hora actual está dentro de la franja 07:00–12:00 o 14:00–17:00
- Sus credenciales están activas

**When (Cuando):**
- Ingresa sus credenciales correctas y hace clic en "Iniciar sesión"

**Then (Entonces):**
- El sistema lo autentica y redirige a la vista del Auxiliar de Despacho

---

## Resultado esperado (Then)

Ver sección **Then** en el extracto anterior del ERS. En automatización backend, el test asociado comprueba el contrato API/servicio equivalente o queda explícitamente marcado como pendiente si el criterio es solo UI, infraestructura o legalidad operativa fuera del alcance de pytest.

## Link directo al test

Ejecutar:

```bash
pytest tests/ers/test_gherkin_dynamic.py::test_RF001_S02 -v
```

Archivo de definición dinámica: [`tests/ers/test_gherkin_dynamic.py`](../../tests/ers/test_gherkin_dynamic.py)

Implementaciones concretas (cuando existan) pueden delegarse en módulos bajo `tests/ers/impl/`.

---

## Estado de automatización backend

Implementada en `tests/ers/gherkin_impl.py` (comprueba API/servicios equivalentes al Then del ERS).


<!-- file: RF001-S03.md -->

# Intento de inicio de sesión de Auxiliar fuera del horario permitido

## Nombre del test

`tests/ers/test_gherkin_dynamic.py::test_RF001_S03`

## Propósito

Validar el criterio de aceptación Gherkin del ERS ICM para **RF001** — escenario 3.

## Requisito o caso de negocio asociado

- **Requisito:** `RF001` (ver `docs/requisitos/ERS_ICM_Requisitos.md`).
- **Fuente complementaria:** `docs/requisitos/ICM_Informe_Elicitacion_v2_plus.docx.md` (contexto de negocio y BR cuando aplica).

## Inputs (Given / When — extracto ERS)

**Given (Dado que):**
- El usuario tiene rol "Auxiliar de Despacho"
- La hora actual está fuera de las franjas 07:00–12:00 y 14:00–17:00

**When (Cuando):**
- Ingresa sus credenciales correctas y hace clic en "Iniciar sesión"

**Then (Entonces):**
- El sistema bloquea el acceso
- Muestra un mensaje indicando que su horario de acceso no está activo
- No genera sesión ni redirige a ninguna vista

---

## Resultado esperado (Then)

Ver sección **Then** en el extracto anterior del ERS. En automatización backend, el test asociado comprueba el contrato API/servicio equivalente o queda explícitamente marcado como pendiente si el criterio es solo UI, infraestructura o legalidad operativa fuera del alcance de pytest.

## Link directo al test

Ejecutar:

```bash
pytest tests/ers/test_gherkin_dynamic.py::test_RF001_S03 -v
```

Archivo de definición dinámica: [`tests/ers/test_gherkin_dynamic.py`](../../tests/ers/test_gherkin_dynamic.py)

Implementaciones concretas (cuando existan) pueden delegarse en módulos bajo `tests/ers/impl/`.

---

## Estado de automatización backend

Implementada en `tests/ers/gherkin_impl.py` (comprueba API/servicios equivalentes al Then del ERS).


<!-- file: RF001-S04.md -->

# Intento de inicio de sesión con credenciales incorrectas

## Nombre del test

`tests/ers/test_gherkin_dynamic.py::test_RF001_S04`

## Propósito

Validar el criterio de aceptación Gherkin del ERS ICM para **RF001** — escenario 4.

## Requisito o caso de negocio asociado

- **Requisito:** `RF001` (ver `docs/requisitos/ERS_ICM_Requisitos.md`).
- **Fuente complementaria:** `docs/requisitos/ICM_Informe_Elicitacion_v2_plus.docx.md` (contexto de negocio y BR cuando aplica).

## Inputs (Given / When — extracto ERS)

**Given (Dado que):**
- Existe un usuario registrado en el sistema

**When (Cuando):**
- Ingresa una contraseña o nombre de usuario incorrecto

**Then (Entonces):**
- El sistema rechaza el acceso
- Muestra un mensaje de error genérico sin revelar si el fallo fue en usuario o contraseña
- No genera sesión activa

---

## Resultado esperado (Then)

Ver sección **Then** en el extracto anterior del ERS. En automatización backend, el test asociado comprueba el contrato API/servicio equivalente o queda explícitamente marcado como pendiente si el criterio es solo UI, infraestructura o legalidad operativa fuera del alcance de pytest.

## Link directo al test

Ejecutar:

```bash
pytest tests/ers/test_gherkin_dynamic.py::test_RF001_S04 -v
```

Archivo de definición dinámica: [`tests/ers/test_gherkin_dynamic.py`](../../tests/ers/test_gherkin_dynamic.py)

Implementaciones concretas (cuando existan) pueden delegarse en módulos bajo `tests/ers/impl/`.

---

## Estado de automatización backend

Implementada en `tests/ers/gherkin_impl.py` (comprueba API/servicios equivalentes al Then del ERS).


<!-- file: RF001-S05.md -->

# Inicio de sesión como Administrador fuera del horario laboral

## Nombre del test

`tests/ers/test_gherkin_dynamic.py::test_RF001_S05`

## Propósito

Validar el criterio de aceptación Gherkin del ERS ICM para **RF001** — escenario 5.

## Requisito o caso de negocio asociado

- **Requisito:** `RF001` (ver `docs/requisitos/ERS_ICM_Requisitos.md`).
- **Fuente complementaria:** `docs/requisitos/ICM_Informe_Elicitacion_v2_plus.docx.md` (contexto de negocio y BR cuando aplica).

## Inputs (Given / When — extracto ERS)

**Given (Dado que):**
- El usuario tiene rol "Administrador/Jefe"
- La hora actual es fuera del horario laboral convencional

**When (Cuando):**
- Ingresa sus credenciales correctas

**Then (Entonces):**
- El sistema lo autentica sin restricción horaria
- Lo redirige al dashboard gerencial de solo lectura

## Resultado esperado (Then)

Ver sección **Then** en el extracto anterior del ERS. En automatización backend, el test asociado comprueba el contrato API/servicio equivalente o queda explícitamente marcado como pendiente si el criterio es solo UI, infraestructura o legalidad operativa fuera del alcance de pytest.

## Link directo al test

Ejecutar:

```bash
pytest tests/ers/test_gherkin_dynamic.py::test_RF001_S05 -v
```

Archivo de definición dinámica: [`tests/ers/test_gherkin_dynamic.py`](../../tests/ers/test_gherkin_dynamic.py)

Implementaciones concretas (cuando existan) pueden delegarse en módulos bajo `tests/ers/impl/`.

---

## Estado de automatización backend

Implementada en `tests/ers/gherkin_impl.py` (comprueba API/servicios equivalentes al Then del ERS).


<!-- file: RF002-S01.md -->

# Almacenista crea una nueva cuenta de usuario

## Nombre del test

`tests/ers/test_gherkin_dynamic.py::test_RF002_S01`

## Propósito

Validar el criterio de aceptación Gherkin del ERS ICM para **RF002** — escenario 1.

## Requisito o caso de negocio asociado

- **Requisito:** `RF002` (ver `docs/requisitos/ERS_ICM_Requisitos.md`).
- **Fuente complementaria:** `docs/requisitos/ICM_Informe_Elicitacion_v2_plus.docx.md` (contexto de negocio y BR cuando aplica).

## Inputs (Given / When — extracto ERS)

**Given (Dado que):**
- El usuario autenticado tiene rol "Almacenista"

**When (Cuando):**
- Accede al módulo de gestión de credenciales
- Completa el formulario con nombre de usuario, contraseña temporal y rol asignado
- Hace clic en "Crear usuario"

**Then (Entonces):**
- El sistema crea la cuenta con un UserID único e irrepetible
- La cuenta queda activa y asociada al rol seleccionado
- El evento de creación queda registrado en el log de auditoría con el UserID del Almacenista y el timestamp

---

## Resultado esperado (Then)

Ver sección **Then** en el extracto anterior del ERS. En automatización backend, el test asociado comprueba el contrato API/servicio equivalente o queda explícitamente marcado como pendiente si el criterio es solo UI, infraestructura o legalidad operativa fuera del alcance de pytest.

## Link directo al test

Ejecutar:

```bash
pytest tests/ers/test_gherkin_dynamic.py::test_RF002_S01 -v
```

Archivo de definición dinámica: [`tests/ers/test_gherkin_dynamic.py`](../../tests/ers/test_gherkin_dynamic.py)

Implementaciones concretas (cuando existan) pueden delegarse en módulos bajo `tests/ers/impl/`.

---

## Estado de automatización backend

Implementada en `tests/ers/gherkin_impl.py` (comprueba API/servicios equivalentes al Then del ERS).


<!-- file: RF002-S02.md -->

# Almacenista modifica la contraseña de un usuario existente

## Nombre del test

`tests/ers/test_gherkin_dynamic.py::test_RF002_S02`

## Propósito

Validar el criterio de aceptación Gherkin del ERS ICM para **RF002** — escenario 2.

## Requisito o caso de negocio asociado

- **Requisito:** `RF002` (ver `docs/requisitos/ERS_ICM_Requisitos.md`).
- **Fuente complementaria:** `docs/requisitos/ICM_Informe_Elicitacion_v2_plus.docx.md` (contexto de negocio y BR cuando aplica).

## Inputs (Given / When — extracto ERS)

**Given (Dado que):**
- El usuario autenticado tiene rol "Almacenista"
- Existe una cuenta activa en el sistema

**When (Cuando):**
- Selecciona la cuenta y elige la opción "Modificar contraseña"
- Ingresa la nueva contraseña y confirma la acción

**Then (Entonces):**
- El sistema actualiza la contraseña de la cuenta seleccionada
- El cambio queda registrado en el log de auditoría con UserID del Almacenista y timestamp

---

## Resultado esperado (Then)

Ver sección **Then** en el extracto anterior del ERS. En automatización backend, el test asociado comprueba el contrato API/servicio equivalente o queda explícitamente marcado como pendiente si el criterio es solo UI, infraestructura o legalidad operativa fuera del alcance de pytest.

## Link directo al test

Ejecutar:

```bash
pytest tests/ers/test_gherkin_dynamic.py::test_RF002_S02 -v
```

Archivo de definición dinámica: [`tests/ers/test_gherkin_dynamic.py`](../../tests/ers/test_gherkin_dynamic.py)

Implementaciones concretas (cuando existan) pueden delegarse en módulos bajo `tests/ers/impl/`.

---

## Estado de automatización backend

Implementada en `tests/ers/gherkin_impl.py` (comprueba API/servicios equivalentes al Then del ERS).


<!-- file: RF002-S03.md -->

# Almacenista deshabilita una cuenta activa

## Nombre del test

`tests/ers/test_gherkin_dynamic.py::test_RF002_S03`

## Propósito

Validar el criterio de aceptación Gherkin del ERS ICM para **RF002** — escenario 3.

## Requisito o caso de negocio asociado

- **Requisito:** `RF002` (ver `docs/requisitos/ERS_ICM_Requisitos.md`).
- **Fuente complementaria:** `docs/requisitos/ICM_Informe_Elicitacion_v2_plus.docx.md` (contexto de negocio y BR cuando aplica).

## Inputs (Given / When — extracto ERS)

**Given (Dado que):**
- El usuario autenticado tiene rol "Almacenista"
- Existe una cuenta de usuario activa en el sistema

**When (Cuando):**
- Selecciona la cuenta y elige la opción "Deshabilitar"
- Confirma la acción

**Then (Entonces):**
- El sistema deshabilita la cuenta inmediatamente
- Si el usuario tenía una sesión activa, ésta se termina en ese momento
- El usuario deshabilitado no puede iniciar sesión hasta que el Almacenista reactive la cuenta
- El evento queda registrado en el log de auditoría

---

## Resultado esperado (Then)

Ver sección **Then** en el extracto anterior del ERS. En automatización backend, el test asociado comprueba el contrato API/servicio equivalente o queda explícitamente marcado como pendiente si el criterio es solo UI, infraestructura o legalidad operativa fuera del alcance de pytest.

## Link directo al test

Ejecutar:

```bash
pytest tests/ers/test_gherkin_dynamic.py::test_RF002_S03 -v
```

Archivo de definición dinámica: [`tests/ers/test_gherkin_dynamic.py`](../../tests/ers/test_gherkin_dynamic.py)

Implementaciones concretas (cuando existan) pueden delegarse en módulos bajo `tests/ers/impl/`.

---

## Estado de automatización backend

Implementada en `tests/ers/gherkin_impl.py` (comprueba API/servicios equivalentes al Then del ERS).


<!-- file: RF002-S04.md -->

# Auxiliar de Despacho intenta modificar su propio perfil

## Nombre del test

`tests/ers/test_gherkin_dynamic.py::test_RF002_S04`

## Propósito

Validar el criterio de aceptación Gherkin del ERS ICM para **RF002** — escenario 4.

## Requisito o caso de negocio asociado

- **Requisito:** `RF002` (ver `docs/requisitos/ERS_ICM_Requisitos.md`).
- **Fuente complementaria:** `docs/requisitos/ICM_Informe_Elicitacion_v2_plus.docx.md` (contexto de negocio y BR cuando aplica).

## Inputs (Given / When — extracto ERS)

**Given (Dado que):**
- El usuario autenticado tiene rol "Auxiliar de Despacho"

**When (Cuando):**
- Intenta acceder a cualquier opción de edición de credenciales propias o ajenas

**Then (Entonces):**
- El sistema bloquea la acción
- Muestra un mensaje indicando que no tiene permisos para realizar esa operación
- No realiza ningún cambio en el sistema

---

## Resultado esperado (Then)

Ver sección **Then** en el extracto anterior del ERS. En automatización backend, el test asociado comprueba el contrato API/servicio equivalente o queda explícitamente marcado como pendiente si el criterio es solo UI, infraestructura o legalidad operativa fuera del alcance de pytest.

## Link directo al test

Ejecutar:

```bash
pytest tests/ers/test_gherkin_dynamic.py::test_RF002_S04 -v
```

Archivo de definición dinámica: [`tests/ers/test_gherkin_dynamic.py`](../../tests/ers/test_gherkin_dynamic.py)

Implementaciones concretas (cuando existan) pueden delegarse en módulos bajo `tests/ers/impl/`.

---

## Estado de automatización backend

Implementada en `tests/ers/gherkin_impl.py` (comprueba API/servicios equivalentes al Then del ERS).


<!-- file: RF002-S05.md -->

# Intento de crear una cuenta con un nombre de usuario ya existente

## Nombre del test

`tests/ers/test_gherkin_dynamic.py::test_RF002_S05`

## Propósito

Validar el criterio de aceptación Gherkin del ERS ICM para **RF002** — escenario 5.

## Requisito o caso de negocio asociado

- **Requisito:** `RF002` (ver `docs/requisitos/ERS_ICM_Requisitos.md`).
- **Fuente complementaria:** `docs/requisitos/ICM_Informe_Elicitacion_v2_plus.docx.md` (contexto de negocio y BR cuando aplica).

## Inputs (Given / When — extracto ERS)

**Given (Dado que):**
- El usuario autenticado tiene rol "Almacenista"
- Ya existe una cuenta con el nombre de usuario "auxiliar01" en el sistema

**When (Cuando):**
- Intenta crear una nueva cuenta con el mismo nombre de usuario "auxiliar01"

**Then (Entonces):**
- El sistema rechaza la creación
- Muestra un mensaje indicando que el nombre de usuario ya está en uso
- No genera ninguna cuenta duplicada

## Resultado esperado (Then)

Ver sección **Then** en el extracto anterior del ERS. En automatización backend, el test asociado comprueba el contrato API/servicio equivalente o queda explícitamente marcado como pendiente si el criterio es solo UI, infraestructura o legalidad operativa fuera del alcance de pytest.

## Link directo al test

Ejecutar:

```bash
pytest tests/ers/test_gherkin_dynamic.py::test_RF002_S05 -v
```

Archivo de definición dinámica: [`tests/ers/test_gherkin_dynamic.py`](../../tests/ers/test_gherkin_dynamic.py)

Implementaciones concretas (cuando existan) pueden delegarse en módulos bajo `tests/ers/impl/`.

---

## Estado de automatización backend

Implementada en `tests/ers/gherkin_impl.py` (comprueba API/servicios equivalentes al Then del ERS).


<!-- file: RF003-S01.md -->

# Almacenista registra un producto nuevo con todos los atributos obligatorios

## Nombre del test

`tests/ers/test_gherkin_dynamic.py::test_RF003_S01`

## Propósito

Validar el criterio de aceptación Gherkin del ERS ICM para **RF003** — escenario 1.

## Requisito o caso de negocio asociado

- **Requisito:** `RF003` (ver `docs/requisitos/ERS_ICM_Requisitos.md`).
- **Fuente complementaria:** `docs/requisitos/ICM_Informe_Elicitacion_v2_plus.docx.md` (contexto de negocio y BR cuando aplica).

## Inputs (Given / When — extracto ERS)

**Given (Dado que):**
- El usuario autenticado tiene rol "Almacenista"

**When (Cuando):**
- Accede al formulario de creación de producto
- Completa todos los campos obligatorios: nombre, categoría, subcategoría, código de barras, fecha de vencimiento, peso unitario y punto de reorden
- Hace clic en "Guardar producto"

**Then (Entonces):**
- El sistema crea el producto con un SKU único
- Lo registra en el catálogo con stock inicial en cero para cada ubicación
- El evento de creación queda en el log de auditoría con UserID y timestamp

---

## Resultado esperado (Then)

Ver sección **Then** en el extracto anterior del ERS. En automatización backend, el test asociado comprueba el contrato API/servicio equivalente o queda explícitamente marcado como pendiente si el criterio es solo UI, infraestructura o legalidad operativa fuera del alcance de pytest.

## Link directo al test

Ejecutar:

```bash
pytest tests/ers/test_gherkin_dynamic.py::test_RF003_S01 -v
```

Archivo de definición dinámica: [`tests/ers/test_gherkin_dynamic.py`](../../tests/ers/test_gherkin_dynamic.py)

Implementaciones concretas (cuando existan) pueden delegarse en módulos bajo `tests/ers/impl/`.

---

## Estado de automatización backend

Implementada en `tests/ers/gherkin_impl.py` (comprueba API/servicios equivalentes al Then del ERS).


<!-- file: RF003-S02.md -->

# Registro de producto de marca propia "Can"

## Nombre del test

`tests/ers/test_gherkin_dynamic.py::test_RF003_S02`

## Propósito

Validar el criterio de aceptación Gherkin del ERS ICM para **RF003** — escenario 2.

## Requisito o caso de negocio asociado

- **Requisito:** `RF003` (ver `docs/requisitos/ERS_ICM_Requisitos.md`).
- **Fuente complementaria:** `docs/requisitos/ICM_Informe_Elicitacion_v2_plus.docx.md` (contexto de negocio y BR cuando aplica).

## Inputs (Given / When — extracto ERS)

**Given (Dado que):**
- El usuario autenticado tiene rol "Almacenista"

**When (Cuando):**
- Registra un producto indicando que pertenece a la marca propia "Can"

**Then (Entonces):**
- El sistema acepta el SKU proporcionado por el usuario siempre que cumpla el patrón 1–4 letras, un guion y 1–4 dígitos
- No permite guardar el producto si el SKU no cumple el formato requerido

---

## Resultado esperado (Then)

Ver sección **Then** en el extracto anterior del ERS. En automatización backend, el test asociado comprueba el contrato API/servicio equivalente o queda explícitamente marcado como pendiente si el criterio es solo UI, infraestructura o legalidad operativa fuera del alcance de pytest.

## Link directo al test

Ejecutar:

```bash
pytest tests/ers/test_gherkin_dynamic.py::test_RF003_S02 -v
```

Archivo de definición dinámica: [`tests/ers/test_gherkin_dynamic.py`](../../tests/ers/test_gherkin_dynamic.py)

Implementaciones concretas (cuando existan) pueden delegarse en módulos bajo `tests/ers/impl/`.

---

## Estado de automatización backend

Implementada en `tests/ers/gherkin_impl.py` (comprueba API/servicios equivalentes al Then del ERS).


<!-- file: RF003-S03.md -->

# Registro de producto de categoría Electroterapia

## Nombre del test

`tests/ers/test_gherkin_dynamic.py::test_RF003_S03`

## Propósito

Validar el criterio de aceptación Gherkin del ERS ICM para **RF003** — escenario 3.

## Requisito o caso de negocio asociado

- **Requisito:** `RF003` (ver `docs/requisitos/ERS_ICM_Requisitos.md`).
- **Fuente complementaria:** `docs/requisitos/ICM_Informe_Elicitacion_v2_plus.docx.md` (contexto de negocio y BR cuando aplica).

## Inputs (Given / When — extracto ERS)

**Given (Dado que):**
- El usuario autenticado tiene rol "Almacenista"

**When (Cuando):**
- Registra un producto con categoría "Electroterapia"

**Then (Entonces):**
- El sistema habilita y marca como obligatorio el campo "Número de Serie"
- No permite guardar el producto si ese campo está vacío

---

## Resultado esperado (Then)

Ver sección **Then** en el extracto anterior del ERS. En automatización backend, el test asociado comprueba el contrato API/servicio equivalente o queda explícitamente marcado como pendiente si el criterio es solo UI, infraestructura o legalidad operativa fuera del alcance de pytest.

## Link directo al test

Ejecutar:

```bash
pytest tests/ers/test_gherkin_dynamic.py::test_RF003_S03 -v
```

Archivo de definición dinámica: [`tests/ers/test_gherkin_dynamic.py`](../../tests/ers/test_gherkin_dynamic.py)

Implementaciones concretas (cuando existan) pueden delegarse en módulos bajo `tests/ers/impl/`.

---

## Estado de automatización backend

Implementada en `tests/ers/gherkin_impl.py` (comprueba API/servicios equivalentes al Then del ERS).


<!-- file: RF003-S04.md -->

# Registro de producto con código de barras como alias de escaneo

## Nombre del test

`tests/ers/test_gherkin_dynamic.py::test_RF003_S04`

## Propósito

Validar el criterio de aceptación Gherkin del ERS ICM para **RF003** — escenario 4.

## Requisito o caso de negocio asociado

- **Requisito:** `RF003` (ver `docs/requisitos/ERS_ICM_Requisitos.md`).
- **Fuente complementaria:** `docs/requisitos/ICM_Informe_Elicitacion_v2_plus.docx.md` (contexto de negocio y BR cuando aplica).

## Inputs (Given / When — extracto ERS)

**Given (Dado que):**
- El usuario autenticado tiene rol "Almacenista"

**When (Cuando):**
- Registra un producto e ingresa un código de barras en el campo correspondiente

**Then (Entonces):**
- El sistema almacena el código como atributo adicional del producto
- Lo vincula internamente al SKU sin reemplazarlo
- Cuando ese código sea escaneado o ingresado manualmente en cualquier módulo, el sistema resuelve la correspondencia al SKU correcto

---

## Resultado esperado (Then)

Ver sección **Then** en el extracto anterior del ERS. En automatización backend, el test asociado comprueba el contrato API/servicio equivalente o queda explícitamente marcado como pendiente si el criterio es solo UI, infraestructura o legalidad operativa fuera del alcance de pytest.

## Link directo al test

Ejecutar:

```bash
pytest tests/ers/test_gherkin_dynamic.py::test_RF003_S04 -v
```

Archivo de definición dinámica: [`tests/ers/test_gherkin_dynamic.py`](../../tests/ers/test_gherkin_dynamic.py)

Implementaciones concretas (cuando existan) pueden delegarse en módulos bajo `tests/ers/impl/`.

---

## Estado de automatización backend

Implementada en `tests/ers/gherkin_impl.py` (comprueba API/servicios equivalentes al Then del ERS).


<!-- file: RF003-S05.md -->

# Registro de producto que requiere cadena de frío

## Nombre del test

`tests/ers/test_gherkin_dynamic.py::test_RF003_S05`

## Propósito

Validar el criterio de aceptación Gherkin del ERS ICM para **RF003** — escenario 5.

## Requisito o caso de negocio asociado

- **Requisito:** `RF003` (ver `docs/requisitos/ERS_ICM_Requisitos.md`).
- **Fuente complementaria:** `docs/requisitos/ICM_Informe_Elicitacion_v2_plus.docx.md` (contexto de negocio y BR cuando aplica).

## Inputs (Given / When — extracto ERS)

**Given (Dado que):**
- El usuario autenticado tiene rol "Almacenista"

**When (Cuando):**
- Registra un producto y activa el indicador de "Cadena de frío"

**Then (Entonces):**
- El sistema almacena esa condición especial en la ficha del producto
- Desplegará una alerta visual persistente en cualquier módulo donde ese producto sea manipulado

---

## Resultado esperado (Then)

Ver sección **Then** en el extracto anterior del ERS. En automatización backend, el test asociado comprueba el contrato API/servicio equivalente o queda explícitamente marcado como pendiente si el criterio es solo UI, infraestructura o legalidad operativa fuera del alcance de pytest.

## Link directo al test

Ejecutar:

```bash
pytest tests/ers/test_gherkin_dynamic.py::test_RF003_S05 -v
```

Archivo de definición dinámica: [`tests/ers/test_gherkin_dynamic.py`](../../tests/ers/test_gherkin_dynamic.py)

Implementaciones concretas (cuando existan) pueden delegarse en módulos bajo `tests/ers/impl/`.

---

## Estado de automatización backend

Implementada en `tests/ers/gherkin_impl.py` (comprueba API/servicios equivalentes al Then del ERS).


<!-- file: RF003-S06.md -->

# Creación de un Combo o Kit con múltiples SKUs

## Nombre del test

`tests/ers/test_gherkin_dynamic.py::test_RF003_S06`

## Propósito

Validar el criterio de aceptación Gherkin del ERS ICM para **RF003** — escenario 6.

## Requisito o caso de negocio asociado

- **Requisito:** `RF003` (ver `docs/requisitos/ERS_ICM_Requisitos.md`).
- **Fuente complementaria:** `docs/requisitos/ICM_Informe_Elicitacion_v2_plus.docx.md` (contexto de negocio y BR cuando aplica).

## Inputs (Given / When — extracto ERS)

**Given (Dado que):**
- El usuario autenticado tiene rol "Almacenista"
- Existen al menos dos productos registrados en el catálogo

**When (Cuando):**
- Crea un nuevo ítem de tipo "Combo" y asocia dos o más SKUs existentes

**Then (Entonces):**
- El sistema registra el Combo con un identificador propio
- Permite despacharlo como una sola unidad de salida
- Al confirmar un despacho de ese Combo, descuenta el stock de cada SKU componente en sus respectivas ubicaciones

---

## Resultado esperado (Then)

Ver sección **Then** en el extracto anterior del ERS. En automatización backend, el test asociado comprueba el contrato API/servicio equivalente o queda explícitamente marcado como pendiente si el criterio es solo UI, infraestructura o legalidad operativa fuera del alcance de pytest.

## Link directo al test

Ejecutar:

```bash
pytest tests/ers/test_gherkin_dynamic.py::test_RF003_S06 -v
```

Archivo de definición dinámica: [`tests/ers/test_gherkin_dynamic.py`](../../tests/ers/test_gherkin_dynamic.py)

Implementaciones concretas (cuando existan) pueden delegarse en módulos bajo `tests/ers/impl/`.

---

## Estado de automatización backend

Implementada en `tests/ers/gherkin_impl.py` (comprueba API/servicios equivalentes al Then del ERS).


<!-- file: RF003-S07.md -->

# Intento de guardar un producto sin completar campos obligatorios

## Nombre del test

`tests/ers/test_gherkin_dynamic.py::test_RF003_S07`

## Propósito

Validar el criterio de aceptación Gherkin del ERS ICM para **RF003** — escenario 7.

## Requisito o caso de negocio asociado

- **Requisito:** `RF003` (ver `docs/requisitos/ERS_ICM_Requisitos.md`).
- **Fuente complementaria:** `docs/requisitos/ICM_Informe_Elicitacion_v2_plus.docx.md` (contexto de negocio y BR cuando aplica).

## Inputs (Given / When — extracto ERS)

**Given (Dado que):**
- El usuario autenticado tiene rol "Almacenista"

**When (Cuando):**
- Intenta guardar un producto dejando uno o más campos obligatorios vacíos

**Then (Entonces):**
- El sistema rechaza el guardado
- Señala visualmente los campos faltantes
- No crea ningún registro parcial en el catálogo

## Resultado esperado (Then)

Ver sección **Then** en el extracto anterior del ERS. En automatización backend, el test asociado comprueba el contrato API/servicio equivalente o queda explícitamente marcado como pendiente si el criterio es solo UI, infraestructura o legalidad operativa fuera del alcance de pytest.

## Link directo al test

Ejecutar:

```bash
pytest tests/ers/test_gherkin_dynamic.py::test_RF003_S07 -v
```

Archivo de definición dinámica: [`tests/ers/test_gherkin_dynamic.py`](../../tests/ers/test_gherkin_dynamic.py)

Implementaciones concretas (cuando existan) pueden delegarse en módulos bajo `tests/ers/impl/`.

---

## Estado de automatización backend

Implementada en `tests/ers/gherkin_impl.py` (comprueba API/servicios equivalentes al Then del ERS).


<!-- file: RF004-S01.md -->

# Consulta de stock navegando por filtros multinivel

## Nombre del test

`tests/ers/test_gherkin_dynamic.py::test_RF004_S01`

## Propósito

Validar el criterio de aceptación Gherkin del ERS ICM para **RF004** — escenario 1.

## Requisito o caso de negocio asociado

- **Requisito:** `RF004` (ver `docs/requisitos/ERS_ICM_Requisitos.md`).
- **Fuente complementaria:** `docs/requisitos/ICM_Informe_Elicitacion_v2_plus.docx.md` (contexto de negocio y BR cuando aplica).

## Inputs (Given / When — extracto ERS)

**Given (Dado que):**
- El usuario está autenticado con cualquier rol

**When (Cuando):**
- Selecciona una categoría (por ejemplo "Electroterapia")
- Luego selecciona una subcategoría (por ejemplo "Agujas de Punción Seca")

**Then (Entonces):**
- El sistema muestra únicamente los productos que corresponden a esa combinación de categoría y subcategoría
- Para cada producto despliega el stock disponible en Vitrina, Bodega 1, Bodega 2 y el total consolidado

---

## Resultado esperado (Then)

Ver sección **Then** en el extracto anterior del ERS. En automatización backend, el test asociado comprueba el contrato API/servicio equivalente o queda explícitamente marcado como pendiente si el criterio es solo UI, infraestructura o legalidad operativa fuera del alcance de pytest.

## Link directo al test

Ejecutar:

```bash
pytest tests/ers/test_gherkin_dynamic.py::test_RF004_S01 -v
```

Archivo de definición dinámica: [`tests/ers/test_gherkin_dynamic.py`](../../tests/ers/test_gherkin_dynamic.py)

Implementaciones concretas (cuando existan) pueden delegarse en módulos bajo `tests/ers/impl/`.

---

## Estado de automatización backend

Implementada en `tests/ers/gherkin_impl.py` (comprueba API/servicios equivalentes al Then del ERS).


<!-- file: RF004-S02.md -->

# Búsqueda de producto por nombre con autocompletado

## Nombre del test

`tests/ers/test_gherkin_dynamic.py::test_RF004_S02`

## Propósito

Validar el criterio de aceptación Gherkin del ERS ICM para **RF004** — escenario 2.

## Requisito o caso de negocio asociado

- **Requisito:** `RF004` (ver `docs/requisitos/ERS_ICM_Requisitos.md`).
- **Fuente complementaria:** `docs/requisitos/ICM_Informe_Elicitacion_v2_plus.docx.md` (contexto de negocio y BR cuando aplica).

## Inputs (Given / When — extracto ERS)

**Given (Dado que):**
- El usuario está autenticado con cualquier rol

**When (Cuando):**
- Escribe al menos tres caracteres del nombre de un producto en el campo de búsqueda

**Then (Entonces):**
- El sistema despliega en tiempo real una lista de sugerencias que coinciden con los caracteres ingresados
- Al seleccionar un producto de la lista, muestra su ficha con el stock por ubicación y el total consolidado

---

## Resultado esperado (Then)

Ver sección **Then** en el extracto anterior del ERS. En automatización backend, el test asociado comprueba el contrato API/servicio equivalente o queda explícitamente marcado como pendiente si el criterio es solo UI, infraestructura o legalidad operativa fuera del alcance de pytest.

## Link directo al test

Ejecutar:

```bash
pytest tests/ers/test_gherkin_dynamic.py::test_RF004_S02 -v
```

Archivo de definición dinámica: [`tests/ers/test_gherkin_dynamic.py`](../../tests/ers/test_gherkin_dynamic.py)

Implementaciones concretas (cuando existan) pueden delegarse en módulos bajo `tests/ers/impl/`.

---

## Estado de automatización backend

Implementada en `tests/ers/gherkin_impl.py` (comprueba API/servicios equivalentes al Then del ERS).


<!-- file: RF004-S03.md -->

# Búsqueda de producto por código de barras escaneado

## Nombre del test

`tests/ers/test_gherkin_dynamic.py::test_RF004_S03`

## Propósito

Validar el criterio de aceptación Gherkin del ERS ICM para **RF004** — escenario 3.

## Requisito o caso de negocio asociado

- **Requisito:** `RF004` (ver `docs/requisitos/ERS_ICM_Requisitos.md`).
- **Fuente complementaria:** `docs/requisitos/ICM_Informe_Elicitacion_v2_plus.docx.md` (contexto de negocio y BR cuando aplica).

## Inputs (Given / When — extracto ERS)

**Given (Dado que):**
- El usuario está autenticado con cualquier rol
- Hay un lector de código de barras conectado en modo HID

**When (Cuando):**
- Escanea el código de barras impreso en el empaque de un producto

**Then (Entonces):**
- El sistema resuelve el código al SKU interno correspondiente
- Muestra la ficha del producto con su stock por ubicación y el total consolidado en menos de 2 segundos

---

## Resultado esperado (Then)

Ver sección **Then** en el extracto anterior del ERS. En automatización backend, el test asociado comprueba el contrato API/servicio equivalente o queda explícitamente marcado como pendiente si el criterio es solo UI, infraestructura o legalidad operativa fuera del alcance de pytest.

## Link directo al test

Ejecutar:

```bash
pytest tests/ers/test_gherkin_dynamic.py::test_RF004_S03 -v
```

Archivo de definición dinámica: [`tests/ers/test_gherkin_dynamic.py`](../../tests/ers/test_gherkin_dynamic.py)

Implementaciones concretas (cuando existan) pueden delegarse en módulos bajo `tests/ers/impl/`.

---

## Estado de automatización backend

Implementada en `tests/ers/gherkin_impl.py` (comprueba API/servicios equivalentes al Then del ERS).


<!-- file: RF004-S04.md -->

# Búsqueda de producto por código de barras ingresado manualmente

## Nombre del test

`tests/ers/test_gherkin_dynamic.py::test_RF004_S04`

## Propósito

Validar el criterio de aceptación Gherkin del ERS ICM para **RF004** — escenario 4.

## Requisito o caso de negocio asociado

- **Requisito:** `RF004` (ver `docs/requisitos/ERS_ICM_Requisitos.md`).
- **Fuente complementaria:** `docs/requisitos/ICM_Informe_Elicitacion_v2_plus.docx.md` (contexto de negocio y BR cuando aplica).

## Inputs (Given / When — extracto ERS)

**Given (Dado que):**
- El usuario está autenticado con cualquier rol
- No hay un lector de código de barras disponible

**When (Cuando):**
- Escribe manualmente el código de barras en el campo de búsqueda

**Then (Entonces):**
- El sistema resuelve el código al SKU interno correspondiente
- Muestra la misma ficha y resultado que si hubiera sido escaneado

---

## Resultado esperado (Then)

Ver sección **Then** en el extracto anterior del ERS. En automatización backend, el test asociado comprueba el contrato API/servicio equivalente o queda explícitamente marcado como pendiente si el criterio es solo UI, infraestructura o legalidad operativa fuera del alcance de pytest.

## Link directo al test

Ejecutar:

```bash
pytest tests/ers/test_gherkin_dynamic.py::test_RF004_S04 -v
```

Archivo de definición dinámica: [`tests/ers/test_gherkin_dynamic.py`](../../tests/ers/test_gherkin_dynamic.py)

Implementaciones concretas (cuando existan) pueden delegarse en módulos bajo `tests/ers/impl/`.

---

## Estado de automatización backend

Implementada en `tests/ers/gherkin_impl.py` (comprueba API/servicios equivalentes al Then del ERS).


<!-- file: RF004-S05.md -->

# Consulta de producto con alerta de cadena de frío

## Nombre del test

`tests/ers/test_gherkin_dynamic.py::test_RF004_S05`

## Propósito

Validar el criterio de aceptación Gherkin del ERS ICM para **RF004** — escenario 5.

## Requisito o caso de negocio asociado

- **Requisito:** `RF004` (ver `docs/requisitos/ERS_ICM_Requisitos.md`).
- **Fuente complementaria:** `docs/requisitos/ICM_Informe_Elicitacion_v2_plus.docx.md` (contexto de negocio y BR cuando aplica).

## Inputs (Given / When — extracto ERS)

**Given (Dado que):**
- El usuario está autenticado con cualquier rol

**When (Cuando):**
- Consulta un producto que tiene activado el indicador de cadena de frío

**Then (Entonces):**
- El sistema despliega una alerta visual persistente y de alta visibilidad junto a la ficha del producto
- Recuerda las condiciones especiales de manejo

---

## Resultado esperado (Then)

Ver sección **Then** en el extracto anterior del ERS. En automatización backend, el test asociado comprueba el contrato API/servicio equivalente o queda explícitamente marcado como pendiente si el criterio es solo UI, infraestructura o legalidad operativa fuera del alcance de pytest.

## Link directo al test

Ejecutar:

```bash
pytest tests/ers/test_gherkin_dynamic.py::test_RF004_S05 -v
```

Archivo de definición dinámica: [`tests/ers/test_gherkin_dynamic.py`](../../tests/ers/test_gherkin_dynamic.py)

Implementaciones concretas (cuando existan) pueden delegarse en módulos bajo `tests/ers/impl/`.

---

## Estado de automatización backend

Implementada en `tests/ers/gherkin_impl.py` (comprueba API/servicios equivalentes al Then del ERS).


<!-- file: RF004-S06.md -->

# Consulta de producto con alerta de seguridad eléctrica

## Nombre del test

`tests/ers/test_gherkin_dynamic.py::test_RF004_S06`

## Propósito

Validar el criterio de aceptación Gherkin del ERS ICM para **RF004** — escenario 6.

## Requisito o caso de negocio asociado

- **Requisito:** `RF004` (ver `docs/requisitos/ERS_ICM_Requisitos.md`).
- **Fuente complementaria:** `docs/requisitos/ICM_Informe_Elicitacion_v2_plus.docx.md` (contexto de negocio y BR cuando aplica).

## Inputs (Given / When — extracto ERS)

**Given (Dado que):**
- El usuario está autenticado con cualquier rol

**When (Cuando):**
- Consulta un producto de la categoría Electroterapia

**Then (Entonces):**
- El sistema despliega una advertencia visual sobre los protocolos de manejo seguro aplicables a equipos eléctricos

---

## Resultado esperado (Then)

Ver sección **Then** en el extracto anterior del ERS. En automatización backend, el test asociado comprueba el contrato API/servicio equivalente o queda explícitamente marcado como pendiente si el criterio es solo UI, infraestructura o legalidad operativa fuera del alcance de pytest.

## Link directo al test

Ejecutar:

```bash
pytest tests/ers/test_gherkin_dynamic.py::test_RF004_S06 -v
```

Archivo de definición dinámica: [`tests/ers/test_gherkin_dynamic.py`](../../tests/ers/test_gherkin_dynamic.py)

Implementaciones concretas (cuando existan) pueden delegarse en módulos bajo `tests/ers/impl/`.

---

## Estado de automatización backend

Implementada en `tests/ers/gherkin_impl.py` (comprueba API/servicios equivalentes al Then del ERS).


<!-- file: RF004-S07.md -->

# Búsqueda de un producto inexistente en el catálogo

## Nombre del test

`tests/ers/test_gherkin_dynamic.py::test_RF004_S07`

## Propósito

Validar el criterio de aceptación Gherkin del ERS ICM para **RF004** — escenario 7.

## Requisito o caso de negocio asociado

- **Requisito:** `RF004` (ver `docs/requisitos/ERS_ICM_Requisitos.md`).
- **Fuente complementaria:** `docs/requisitos/ICM_Informe_Elicitacion_v2_plus.docx.md` (contexto de negocio y BR cuando aplica).

## Inputs (Given / When — extracto ERS)

**Given (Dado que):**
- El usuario está autenticado con cualquier rol

**When (Cuando):**
- Realiza una búsqueda por nombre, SKU o código de barras que no corresponde a ningún producto registrado

**Then (Entonces):**
- El sistema muestra un mensaje claro indicando que no se encontraron resultados para ese criterio de búsqueda
- No genera ningún error ni interrupción en la interfaz

## Resultado esperado (Then)

Ver sección **Then** en el extracto anterior del ERS. En automatización backend, el test asociado comprueba el contrato API/servicio equivalente o queda explícitamente marcado como pendiente si el criterio es solo UI, infraestructura o legalidad operativa fuera del alcance de pytest.

## Link directo al test

Ejecutar:

```bash
pytest tests/ers/test_gherkin_dynamic.py::test_RF004_S07 -v
```

Archivo de definición dinámica: [`tests/ers/test_gherkin_dynamic.py`](../../tests/ers/test_gherkin_dynamic.py)

Implementaciones concretas (cuando existan) pueden delegarse en módulos bajo `tests/ers/impl/`.

---

## Estado de automatización backend

Implementada en `tests/ers/gherkin_impl.py` (comprueba API/servicios equivalentes al Then del ERS).


<!-- file: RF005-S01.md -->

# Recepción exitosa de producto estándar sin discrepancia

## Nombre del test

`tests/ers/test_gherkin_dynamic.py::test_RF005_S01`

## Propósito

Validar el criterio de aceptación Gherkin del ERS ICM para **RF005** — escenario 1.

## Requisito o caso de negocio asociado

- **Requisito:** `RF005` (ver `docs/requisitos/ERS_ICM_Requisitos.md`).
- **Fuente complementaria:** `docs/requisitos/ICM_Informe_Elicitacion_v2_plus.docx.md` (contexto de negocio y BR cuando aplica).

## Inputs (Given / When — extracto ERS)

**Given (Dado que):**
- El usuario autenticado tiene rol "Auxiliar de Despacho" o "Almacenista"
- El producto existe en el catálogo
- La hora actual está dentro de la franja horaria permitida

**When (Cuando):**
- Inicia un registro de entrada
- Selecciona el producto por escaneo de código de barras o búsqueda por nombre
- Ingresa la cantidad recibida igual a la cantidad facturada
- Selecciona la ubicación de destino (Vitrina, Bodega 1 o Bodega 2)
- Confirma la entrada

**Then (Entonces):**
- El sistema incrementa el stock del producto en la ubicación seleccionada
- Recalcula el stock total consolidado
- Genera un movimiento de entrada inmutable con UserID, timestamp, ubicación de destino, cantidad, stock previo y stock resultante

---

## Resultado esperado (Then)

Ver sección **Then** en el extracto anterior del ERS. En automatización backend, el test asociado comprueba el contrato API/servicio equivalente o queda explícitamente marcado como pendiente si el criterio es solo UI, infraestructura o legalidad operativa fuera del alcance de pytest.

## Link directo al test

Ejecutar:

```bash
pytest tests/ers/test_gherkin_dynamic.py::test_RF005_S01 -v
```

Archivo de definición dinámica: [`tests/ers/test_gherkin_dynamic.py`](../../tests/ers/test_gherkin_dynamic.py)

Implementaciones concretas (cuando existan) pueden delegarse en módulos bajo `tests/ers/impl/`.

---

## Estado de automatización backend

Implementada en `tests/ers/gherkin_impl.py` (comprueba API/servicios equivalentes al Then del ERS).


<!-- file: RF005-S02.md -->

# Recepción con discrepancia entre cantidad recibida y facturada

## Nombre del test

`tests/ers/test_gherkin_dynamic.py::test_RF005_S02`

## Propósito

Validar el criterio de aceptación Gherkin del ERS ICM para **RF005** — escenario 2.

## Requisito o caso de negocio asociado

- **Requisito:** `RF005` (ver `docs/requisitos/ERS_ICM_Requisitos.md`).
- **Fuente complementaria:** `docs/requisitos/ICM_Informe_Elicitacion_v2_plus.docx.md` (contexto de negocio y BR cuando aplica).

## Inputs (Given / When — extracto ERS)

**Given (Dado que):**
- El usuario autenticado tiene rol "Auxiliar de Despacho" o "Almacenista"
- El producto existe en el catálogo

**When (Cuando):**
- Ingresa una cantidad recibida diferente a la cantidad facturada o esperada
- Intenta confirmar la entrada sin registrar una nota de discrepancia

**Then (Entonces):**
- El sistema bloquea la confirmación
- Muestra un mensaje indicando que es obligatorio registrar una nota que explique la diferencia
- No genera ningún movimiento hasta que la nota sea completada

---

## Resultado esperado (Then)

Ver sección **Then** en el extracto anterior del ERS. En automatización backend, el test asociado comprueba el contrato API/servicio equivalente o queda explícitamente marcado como pendiente si el criterio es solo UI, infraestructura o legalidad operativa fuera del alcance de pytest.

## Link directo al test

Ejecutar:

```bash
pytest tests/ers/test_gherkin_dynamic.py::test_RF005_S02 -v
```

Archivo de definición dinámica: [`tests/ers/test_gherkin_dynamic.py`](../../tests/ers/test_gherkin_dynamic.py)

Implementaciones concretas (cuando existan) pueden delegarse en módulos bajo `tests/ers/impl/`.

---

## Estado de automatización backend

Implementada en `tests/ers/gherkin_impl.py` (comprueba API/servicios equivalentes al Then del ERS).


<!-- file: RF005-S03.md -->

# Recepción exitosa con discrepancia documentada

## Nombre del test

`tests/ers/test_gherkin_dynamic.py::test_RF005_S03`

## Propósito

Validar el criterio de aceptación Gherkin del ERS ICM para **RF005** — escenario 3.

## Requisito o caso de negocio asociado

- **Requisito:** `RF005` (ver `docs/requisitos/ERS_ICM_Requisitos.md`).
- **Fuente complementaria:** `docs/requisitos/ICM_Informe_Elicitacion_v2_plus.docx.md` (contexto de negocio y BR cuando aplica).

## Inputs (Given / When — extracto ERS)

**Given (Dado que):**
- El usuario autenticado tiene rol "Auxiliar de Despacho" o "Almacenista"
- La cantidad recibida difiere de la facturada

**When (Cuando):**
- Registra la nota de discrepancia obligatoria
- Confirma la entrada

**Then (Entonces):**
- El sistema acepta la operación
- Genera el movimiento de entrada vinculando la nota de discrepancia al registro
- El movimiento queda inmutable con todos los atributos de trazabilidad

---

## Resultado esperado (Then)

Ver sección **Then** en el extracto anterior del ERS. En automatización backend, el test asociado comprueba el contrato API/servicio equivalente o queda explícitamente marcado como pendiente si el criterio es solo UI, infraestructura o legalidad operativa fuera del alcance de pytest.

## Link directo al test

Ejecutar:

```bash
pytest tests/ers/test_gherkin_dynamic.py::test_RF005_S03 -v
```

Archivo de definición dinámica: [`tests/ers/test_gherkin_dynamic.py`](../../tests/ers/test_gherkin_dynamic.py)

Implementaciones concretas (cuando existan) pueden delegarse en módulos bajo `tests/ers/impl/`.

---

## Estado de automatización backend

Implementada en `tests/ers/gherkin_impl.py` (comprueba API/servicios equivalentes al Then del ERS).


<!-- file: RF005-S04.md -->

# Recepción de producto de categoría Electroterapia sin número de serie

## Nombre del test

`tests/ers/test_gherkin_dynamic.py::test_RF005_S04`

## Propósito

Validar el criterio de aceptación Gherkin del ERS ICM para **RF005** — escenario 4.

## Requisito o caso de negocio asociado

- **Requisito:** `RF005` (ver `docs/requisitos/ERS_ICM_Requisitos.md`).
- **Fuente complementaria:** `docs/requisitos/ICM_Informe_Elicitacion_v2_plus.docx.md` (contexto de negocio y BR cuando aplica).

## Inputs (Given / When — extracto ERS)

**Given (Dado que):**
- El usuario autenticado tiene rol "Auxiliar de Despacho" o "Almacenista"
- El producto seleccionado pertenece a la categoría "Electroterapia"

**When (Cuando):**
- Completa el formulario de entrada dejando vacío el campo "Número de Serie"
- Intenta confirmar la entrada

**Then (Entonces):**
- El sistema bloquea la confirmación
- Muestra un mensaje indicando que el número de serie es obligatorio para productos de Electroterapia
- No genera ningún movimiento ni actualización de stock

---

## Resultado esperado (Then)

Ver sección **Then** en el extracto anterior del ERS. En automatización backend, el test asociado comprueba el contrato API/servicio equivalente o queda explícitamente marcado como pendiente si el criterio es solo UI, infraestructura o legalidad operativa fuera del alcance de pytest.

## Link directo al test

Ejecutar:

```bash
pytest tests/ers/test_gherkin_dynamic.py::test_RF005_S04 -v
```

Archivo de definición dinámica: [`tests/ers/test_gherkin_dynamic.py`](../../tests/ers/test_gherkin_dynamic.py)

Implementaciones concretas (cuando existan) pueden delegarse en módulos bajo `tests/ers/impl/`.

---

## Estado de automatización backend

Implementada en `tests/ers/gherkin_impl.py` (comprueba API/servicios equivalentes al Then del ERS).


<!-- file: RF005-S05.md -->

# Recepción exitosa de producto de Electroterapia con número de serie

## Nombre del test

`tests/ers/test_gherkin_dynamic.py::test_RF005_S05`

## Propósito

Validar el criterio de aceptación Gherkin del ERS ICM para **RF005** — escenario 5.

## Requisito o caso de negocio asociado

- **Requisito:** `RF005` (ver `docs/requisitos/ERS_ICM_Requisitos.md`).
- **Fuente complementaria:** `docs/requisitos/ICM_Informe_Elicitacion_v2_plus.docx.md` (contexto de negocio y BR cuando aplica).

## Inputs (Given / When — extracto ERS)

**Given (Dado que):**
- El usuario autenticado tiene rol "Auxiliar de Despacho" o "Almacenista"
- El producto pertenece a la categoría "Electroterapia"

**When (Cuando):**
- Ingresa el número de serie de cada unidad recibida
- Completa los demás campos obligatorios y confirma la entrada

**Then (Entonces):**
- El sistema registra cada unidad vinculada a su número de serie individual
- Actualiza el stock en la ubicación de destino seleccionada
- Genera el movimiento con trazabilidad completa incluyendo los seriales

---

## Resultado esperado (Then)

Ver sección **Then** en el extracto anterior del ERS. En automatización backend, el test asociado comprueba el contrato API/servicio equivalente o queda explícitamente marcado como pendiente si el criterio es solo UI, infraestructura o legalidad operativa fuera del alcance de pytest.

## Link directo al test

Ejecutar:

```bash
pytest tests/ers/test_gherkin_dynamic.py::test_RF005_S05 -v
```

Archivo de definición dinámica: [`tests/ers/test_gherkin_dynamic.py`](../../tests/ers/test_gherkin_dynamic.py)

Implementaciones concretas (cuando existan) pueden delegarse en módulos bajo `tests/ers/impl/`.

---

## Estado de automatización backend

Implementada en `tests/ers/gherkin_impl.py` (comprueba API/servicios equivalentes al Then del ERS).


<!-- file: RF005-S06.md -->

# Identificación del producto por código de barras escaneado durante recepción

## Nombre del test

`tests/ers/test_gherkin_dynamic.py::test_RF005_S06`

## Propósito

Validar el criterio de aceptación Gherkin del ERS ICM para **RF005** — escenario 6.

## Requisito o caso de negocio asociado

- **Requisito:** `RF005` (ver `docs/requisitos/ERS_ICM_Requisitos.md`).
- **Fuente complementaria:** `docs/requisitos/ICM_Informe_Elicitacion_v2_plus.docx.md` (contexto de negocio y BR cuando aplica).

## Inputs (Given / When — extracto ERS)

**Given (Dado que):**
- El usuario autenticado tiene rol "Auxiliar de Despacho" o "Almacenista"
- Hay un lector de código de barras conectado en modo HID

**When (Cuando):**
- Escanea el código de barras del producto a recepcionar

**Then (Entonces):**
- El sistema resuelve el código al SKU interno
- Autocompleta el formulario con el nombre, categoría y demás atributos del producto
- El operario solo debe completar cantidad, ubicación y los campos variables de esa entrada

---

## Resultado esperado (Then)

Ver sección **Then** en el extracto anterior del ERS. En automatización backend, el test asociado comprueba el contrato API/servicio equivalente o queda explícitamente marcado como pendiente si el criterio es solo UI, infraestructura o legalidad operativa fuera del alcance de pytest.

## Link directo al test

Ejecutar:

```bash
pytest tests/ers/test_gherkin_dynamic.py::test_RF005_S06 -v
```

Archivo de definición dinámica: [`tests/ers/test_gherkin_dynamic.py`](../../tests/ers/test_gherkin_dynamic.py)

Implementaciones concretas (cuando existan) pueden delegarse en módulos bajo `tests/ers/impl/`.

---

## Estado de automatización backend

Implementada en `tests/ers/gherkin_impl.py` (comprueba API/servicios equivalentes al Then del ERS).


<!-- file: RF005-S07.md -->

# Recepción cuando el lector de código de barras no está disponible

## Nombre del test

`tests/ers/test_gherkin_dynamic.py::test_RF005_S07`

## Propósito

Validar el criterio de aceptación Gherkin del ERS ICM para **RF005** — escenario 7.

## Requisito o caso de negocio asociado

- **Requisito:** `RF005` (ver `docs/requisitos/ERS_ICM_Requisitos.md`).
- **Fuente complementaria:** `docs/requisitos/ICM_Informe_Elicitacion_v2_plus.docx.md` (contexto de negocio y BR cuando aplica).

## Inputs (Given / When — extracto ERS)

**Given (Dado que):**
- El usuario autenticado tiene rol "Auxiliar de Despacho" o "Almacenista"
- El lector de código de barras no está conectado o no es reconocido

**When (Cuando):**
- El sistema detecta la ausencia del lector

**Then (Entonces):**
- Muestra una notificación visible informando que el lector no está disponible
- Permite continuar el flujo de recepción mediante búsqueda por nombre, ingreso manual del código de barras o ingreso directo del SKU
- No interrumpe ni bloquea el proceso de entrada bajo ninguna circunstancia

## Resultado esperado (Then)

Ver sección **Then** en el extracto anterior del ERS. En automatización backend, el test asociado comprueba el contrato API/servicio equivalente o queda explícitamente marcado como pendiente si el criterio es solo UI, infraestructura o legalidad operativa fuera del alcance de pytest.

## Link directo al test

Ejecutar:

```bash
pytest tests/ers/test_gherkin_dynamic.py::test_RF005_S07 -v
```

Archivo de definición dinámica: [`tests/ers/test_gherkin_dynamic.py`](../../tests/ers/test_gherkin_dynamic.py)

Implementaciones concretas (cuando existan) pueden delegarse en módulos bajo `tests/ers/impl/`.

---

## Estado de automatización backend

Implementada en `tests/ers/gherkin_impl.py` (comprueba API/servicios equivalentes al Then del ERS).


<!-- file: RF006-S01.md -->

# Despacho exitoso de venta al por mayor con validación cruzada

## Nombre del test

`tests/ers/test_gherkin_dynamic.py::test_RF006_S01`

## Propósito

Validar el criterio de aceptación Gherkin del ERS ICM para **RF006** — escenario 1.

## Requisito o caso de negocio asociado

- **Requisito:** `RF006` (ver `docs/requisitos/ERS_ICM_Requisitos.md`).
- **Fuente complementaria:** `docs/requisitos/ICM_Informe_Elicitacion_v2_plus.docx.md` (contexto de negocio y BR cuando aplica).

## Inputs (Given / When — extracto ERS)

**Given (Dado que):**
- El usuario autenticado tiene rol "Auxiliar de Despacho" o "Almacenista"
- Existe una orden de despacho con uno o más productos
- El stock disponible en la ubicación de origen es suficiente

**When (Cuando):**
- Selecciona el tipo de salida "Venta al por Mayor"
- Registra los datos completos del cliente receptor (nombre o razón social, correo, teléfono, dirección)
- Escanea o ingresa el código del producto a despachar
- El código coincide con el SKU de la orden
- Confirma el despacho

**Then (Entonces):**
- El sistema descuenta el stock del producto en la ubicación de origen
- Recalcula el stock total consolidado
- Genera un movimiento de salida inmutable con UserID, timestamp, tipo de salida, cliente, SKU, cantidad, ubicación de origen, stock previo y stock resultante
- Genera automáticamente una factura digital en PDF con numeración secuencial que incluye todos los datos del despacho
- La factura queda almacenada de forma persistente en el historial

---

## Resultado esperado (Then)

Ver sección **Then** en el extracto anterior del ERS. En automatización backend, el test asociado comprueba el contrato API/servicio equivalente o queda explícitamente marcado como pendiente si el criterio es solo UI, infraestructura o legalidad operativa fuera del alcance de pytest.

## Link directo al test

Ejecutar:

```bash
pytest tests/ers/test_gherkin_dynamic.py::test_RF006_S01 -v
```

Archivo de definición dinámica: [`tests/ers/test_gherkin_dynamic.py`](../../tests/ers/test_gherkin_dynamic.py)

Implementaciones concretas (cuando existan) pueden delegarse en módulos bajo `tests/ers/impl/`.

---

## Estado de automatización backend

Implementada en `tests/ers/gherkin_impl.py` (comprueba API/servicios equivalentes al Then del ERS).


<!-- file: RF006-S02.md -->

# Validación cruzada falla por código escaneado incorrecto

## Nombre del test

`tests/ers/test_gherkin_dynamic.py::test_RF006_S02`

## Propósito

Validar el criterio de aceptación Gherkin del ERS ICM para **RF006** — escenario 2.

## Requisito o caso de negocio asociado

- **Requisito:** `RF006` (ver `docs/requisitos/ERS_ICM_Requisitos.md`).
- **Fuente complementaria:** `docs/requisitos/ICM_Informe_Elicitacion_v2_plus.docx.md` (contexto de negocio y BR cuando aplica).

## Inputs (Given / When — extracto ERS)

**Given (Dado que):**
- El usuario autenticado tiene rol "Auxiliar de Despacho" o "Almacenista"
- Existe una orden de despacho para el SKU "ELEC-0001"

**When (Cuando):**
- Escanea físicamente un producto cuyo código corresponde a un SKU diferente

**Then (Entonces):**
- El sistema bloquea la confirmación del despacho
- Muestra un mensaje de error descriptivo indicando que el producto escaneado no corresponde al producto de la orden
- No genera ningún movimiento ni descuento de stock
- No genera factura hasta que la validación sea superada

---

## Resultado esperado (Then)

Ver sección **Then** en el extracto anterior del ERS. En automatización backend, el test asociado comprueba el contrato API/servicio equivalente o queda explícitamente marcado como pendiente si el criterio es solo UI, infraestructura o legalidad operativa fuera del alcance de pytest.

## Link directo al test

Ejecutar:

```bash
pytest tests/ers/test_gherkin_dynamic.py::test_RF006_S02 -v
```

Archivo de definición dinámica: [`tests/ers/test_gherkin_dynamic.py`](../../tests/ers/test_gherkin_dynamic.py)

Implementaciones concretas (cuando existan) pueden delegarse en módulos bajo `tests/ers/impl/`.

---

## Estado de automatización backend

Implementada en `tests/ers/gherkin_impl.py` (comprueba API/servicios equivalentes al Then del ERS).


<!-- file: RF006-S03.md -->

# Despacho de venta al por menor sin registro obligatorio de cliente

## Nombre del test

`tests/ers/test_gherkin_dynamic.py::test_RF006_S03`

## Propósito

Validar el criterio de aceptación Gherkin del ERS ICM para **RF006** — escenario 3.

## Requisito o caso de negocio asociado

- **Requisito:** `RF006` (ver `docs/requisitos/ERS_ICM_Requisitos.md`).
- **Fuente complementaria:** `docs/requisitos/ICM_Informe_Elicitacion_v2_plus.docx.md` (contexto de negocio y BR cuando aplica).

## Inputs (Given / When — extracto ERS)

**Given (Dado que):**
- El usuario autenticado tiene rol "Auxiliar de Despacho" o "Almacenista"

**When (Cuando):**
- Selecciona el tipo de salida "Venta al por Menor"
- Completa el formulario sin registrar datos del cliente
- La validación cruzada del producto es exitosa
- Confirma el despacho

**Then (Entonces):**
- El sistema acepta la operación sin exigir datos del cliente
- Genera el movimiento de salida con trazabilidad completa
- Genera la factura o remisión digital en PDF

---

## Resultado esperado (Then)

Ver sección **Then** en el extracto anterior del ERS. En automatización backend, el test asociado comprueba el contrato API/servicio equivalente o queda explícitamente marcado como pendiente si el criterio es solo UI, infraestructura o legalidad operativa fuera del alcance de pytest.

## Link directo al test

Ejecutar:

```bash
pytest tests/ers/test_gherkin_dynamic.py::test_RF006_S03 -v
```

Archivo de definición dinámica: [`tests/ers/test_gherkin_dynamic.py`](../../tests/ers/test_gherkin_dynamic.py)

Implementaciones concretas (cuando existan) pueden delegarse en módulos bajo `tests/ers/impl/`.

---

## Estado de automatización backend

Implementada en `tests/ers/gherkin_impl.py` (comprueba API/servicios equivalentes al Then del ERS).


<!-- file: RF006-S04.md -->

# Registro de baja por daño

## Nombre del test

`tests/ers/test_gherkin_dynamic.py::test_RF006_S04`

## Propósito

Validar el criterio de aceptación Gherkin del ERS ICM para **RF006** — escenario 4.

## Requisito o caso de negocio asociado

- **Requisito:** `RF006` (ver `docs/requisitos/ERS_ICM_Requisitos.md`).
- **Fuente complementaria:** `docs/requisitos/ICM_Informe_Elicitacion_v2_plus.docx.md` (contexto de negocio y BR cuando aplica).

## Inputs (Given / When — extracto ERS)

**Given (Dado que):**
- El usuario autenticado tiene rol "Auxiliar de Despacho" o "Almacenista"

**When (Cuando):**
- Selecciona el tipo de salida "Daño"
- Ingresa el número de unidades afectadas
- Registra una nota descriptiva del daño detectado
- Confirma la operación

**Then (Entonces):**
- El sistema descuenta las unidades del stock en la ubicación correspondiente
- Registra el movimiento como "baja por daño", no como venta
- La nota descriptiva queda vinculada de forma inmutable al movimiento
- Genera el documento de remisión en PDF reflejando el tipo de baja

---

## Resultado esperado (Then)

Ver sección **Then** en el extracto anterior del ERS. En automatización backend, el test asociado comprueba el contrato API/servicio equivalente o queda explícitamente marcado como pendiente si el criterio es solo UI, infraestructura o legalidad operativa fuera del alcance de pytest.

## Link directo al test

Ejecutar:

```bash
pytest tests/ers/test_gherkin_dynamic.py::test_RF006_S04 -v
```

Archivo de definición dinámica: [`tests/ers/test_gherkin_dynamic.py`](../../tests/ers/test_gherkin_dynamic.py)

Implementaciones concretas (cuando existan) pueden delegarse en módulos bajo `tests/ers/impl/`.

---

## Estado de automatización backend

Implementada en `tests/ers/gherkin_impl.py` (comprueba API/servicios equivalentes al Then del ERS).


<!-- file: RF006-S05.md -->

# Registro de baja por vencimiento

## Nombre del test

`tests/ers/test_gherkin_dynamic.py::test_RF006_S05`

## Propósito

Validar el criterio de aceptación Gherkin del ERS ICM para **RF006** — escenario 5.

## Requisito o caso de negocio asociado

- **Requisito:** `RF006` (ver `docs/requisitos/ERS_ICM_Requisitos.md`).
- **Fuente complementaria:** `docs/requisitos/ICM_Informe_Elicitacion_v2_plus.docx.md` (contexto de negocio y BR cuando aplica).

## Inputs (Given / When — extracto ERS)

**Given (Dado que):**
- El usuario autenticado tiene rol "Auxiliar de Despacho" o "Almacenista"
- Existen productos con alertas de vencimiento activas

**When (Cuando):**
- Selecciona el tipo de salida "Vencimiento"
- Selecciona el producto y el lote afectado
- Confirma la operación

**Then (Entonces):**
- El sistema descuenta las unidades del stock en la ubicación correspondiente
- Registra el movimiento como "baja por vencimiento"
- Vincula la fecha de vencimiento del lote al registro del movimiento
- El movimiento queda inmutable con trazabilidad completa

---

## Resultado esperado (Then)

Ver sección **Then** en el extracto anterior del ERS. En automatización backend, el test asociado comprueba el contrato API/servicio equivalente o queda explícitamente marcado como pendiente si el criterio es solo UI, infraestructura o legalidad operativa fuera del alcance de pytest.

## Link directo al test

Ejecutar:

```bash
pytest tests/ers/test_gherkin_dynamic.py::test_RF006_S05 -v
```

Archivo de definición dinámica: [`tests/ers/test_gherkin_dynamic.py`](../../tests/ers/test_gherkin_dynamic.py)

Implementaciones concretas (cuando existan) pueden delegarse en módulos bajo `tests/ers/impl/`.

---

## Estado de automatización backend

Implementada en `tests/ers/gherkin_impl.py` (comprueba API/servicios equivalentes al Then del ERS).


<!-- file: RF006-S06.md -->

# Advertencia por peso total del despacho excede capacidad del vehículo

## Nombre del test

`tests/ers/test_gherkin_dynamic.py::test_RF006_S06`

## Propósito

Validar el criterio de aceptación Gherkin del ERS ICM para **RF006** — escenario 6.

## Requisito o caso de negocio asociado

- **Requisito:** `RF006` (ver `docs/requisitos/ERS_ICM_Requisitos.md`).
- **Fuente complementaria:** `docs/requisitos/ICM_Informe_Elicitacion_v2_plus.docx.md` (contexto de negocio y BR cuando aplica).

## Inputs (Given / When — extracto ERS)

**Given (Dado que):**
- El usuario autenticado tiene rol "Auxiliar de Despacho" o "Almacenista"
- El tipo de salida es "Venta al por Mayor"
- El sistema tiene configurada la capacidad máxima del vehículo de transporte

**When (Cuando):**
- El peso total calculado de todos los ítems del despacho supera la capacidad máxima configurada

**Then (Entonces):**
- El sistema emite una advertencia visible al operario indicando que la carga excede la capacidad del vehículo
- Permite al operario revisar y ajustar el despacho
- No bloquea la operación de forma definitiva, ya que la decisión final corresponde al operario responsable

---

## Resultado esperado (Then)

Ver sección **Then** en el extracto anterior del ERS. En automatización backend, el test asociado comprueba el contrato API/servicio equivalente o queda explícitamente marcado como pendiente si el criterio es solo UI, infraestructura o legalidad operativa fuera del alcance de pytest.

## Link directo al test

Ejecutar:

```bash
pytest tests/ers/test_gherkin_dynamic.py::test_RF006_S06 -v
```

Archivo de definición dinámica: [`tests/ers/test_gherkin_dynamic.py`](../../tests/ers/test_gherkin_dynamic.py)

Implementaciones concretas (cuando existan) pueden delegarse en módulos bajo `tests/ers/impl/`.

---

## Estado de automatización backend

Pendiente en backend: al ejecutar el test dinámico se aplicará `pytest.skip` con el motivo hasta que exista implementación.


<!-- file: RF006-S07.md -->

# Despacho cuando el lector de código de barras no está disponible

## Nombre del test

`tests/ers/test_gherkin_dynamic.py::test_RF006_S07`

## Propósito

Validar el criterio de aceptación Gherkin del ERS ICM para **RF006** — escenario 7.

## Requisito o caso de negocio asociado

- **Requisito:** `RF006` (ver `docs/requisitos/ERS_ICM_Requisitos.md`).
- **Fuente complementaria:** `docs/requisitos/ICM_Informe_Elicitacion_v2_plus.docx.md` (contexto de negocio y BR cuando aplica).

## Inputs (Given / When — extracto ERS)

**Given (Dado que):**
- El usuario autenticado tiene rol "Auxiliar de Despacho" o "Almacenista"
- El lector de código de barras no está conectado o no es reconocido

**When (Cuando):**
- El sistema detecta la ausencia del lector

**Then (Entonces):**
- Muestra una notificación visible pero no interrumpe el flujo de despacho
- Permite al operario identificar el producto ingresando manualmente el código de barras, el SKU, el código serial o buscando por nombre
- La validación cruzada se ejecuta igualmente usando el valor ingresado

## Resultado esperado (Then)

Ver sección **Then** en el extracto anterior del ERS. En automatización backend, el test asociado comprueba el contrato API/servicio equivalente o queda explícitamente marcado como pendiente si el criterio es solo UI, infraestructura o legalidad operativa fuera del alcance de pytest.

## Link directo al test

Ejecutar:

```bash
pytest tests/ers/test_gherkin_dynamic.py::test_RF006_S07 -v
```

Archivo de definición dinámica: [`tests/ers/test_gherkin_dynamic.py`](../../tests/ers/test_gherkin_dynamic.py)

Implementaciones concretas (cuando existan) pueden delegarse en módulos bajo `tests/ers/impl/`.

---

## Estado de automatización backend

Pendiente en backend: al ejecutar el test dinámico se aplicará `pytest.skip` con el motivo hasta que exista implementación.


<!-- file: RF007-S01.md -->

# Traslado exitoso de producto entre ubicaciones con stock suficiente

## Nombre del test

`tests/ers/test_gherkin_dynamic.py::test_RF007_S01`

## Propósito

Validar el criterio de aceptación Gherkin del ERS ICM para **RF007** — escenario 1.

## Requisito o caso de negocio asociado

- **Requisito:** `RF007` (ver `docs/requisitos/ERS_ICM_Requisitos.md`).
- **Fuente complementaria:** `docs/requisitos/ICM_Informe_Elicitacion_v2_plus.docx.md` (contexto de negocio y BR cuando aplica).

## Inputs (Given / When — extracto ERS)

**Given (Dado que):**
- El usuario autenticado tiene rol "Auxiliar de Despacho" o "Almacenista"
- El producto existe en el catálogo
- La ubicación de origen tiene stock suficiente para cubrir la cantidad a trasladar

**When (Cuando):**
- Selecciona el producto a trasladar
- Indica la cantidad, la ubicación de origen y la ubicación de destino
- Confirma el traslado

**Then (Entonces):**
- El sistema resta la cantidad indicada del stock en la ubicación de origen
- Suma esa misma cantidad al stock en la ubicación de destino
- El stock total global del producto permanece sin cambios
- Genera un movimiento inmutable con UserID, timestamp, producto, cantidad, ubicación de origen, ubicación de destino, stock previo y stock resultante por ubicación

---

## Resultado esperado (Then)

Ver sección **Then** en el extracto anterior del ERS. En automatización backend, el test asociado comprueba el contrato API/servicio equivalente o queda explícitamente marcado como pendiente si el criterio es solo UI, infraestructura o legalidad operativa fuera del alcance de pytest.

## Link directo al test

Ejecutar:

```bash
pytest tests/ers/test_gherkin_dynamic.py::test_RF007_S01 -v
```

Archivo de definición dinámica: [`tests/ers/test_gherkin_dynamic.py`](../../tests/ers/test_gherkin_dynamic.py)

Implementaciones concretas (cuando existan) pueden delegarse en módulos bajo `tests/ers/impl/`.

---

## Estado de automatización backend

Implementada en `tests/ers/gherkin_impl.py` (comprueba API/servicios equivalentes al Then del ERS).


<!-- file: RF007-S02.md -->

# Intento de traslado con stock insuficiente en la ubicación de origen

## Nombre del test

`tests/ers/test_gherkin_dynamic.py::test_RF007_S02`

## Propósito

Validar el criterio de aceptación Gherkin del ERS ICM para **RF007** — escenario 2.

## Requisito o caso de negocio asociado

- **Requisito:** `RF007` (ver `docs/requisitos/ERS_ICM_Requisitos.md`).
- **Fuente complementaria:** `docs/requisitos/ICM_Informe_Elicitacion_v2_plus.docx.md` (contexto de negocio y BR cuando aplica).

## Inputs (Given / When — extracto ERS)

**Given (Dado que):**
- El usuario autenticado tiene rol "Auxiliar de Despacho" o "Almacenista"
- El producto tiene 3 unidades disponibles en Bodega 1

**When (Cuando):**
- Intenta registrar un traslado de 5 unidades desde Bodega 1 hacia cualquier otra ubicación

**Then (Entonces):**
- El sistema bloquea la operación
- Muestra un mensaje indicando que el stock disponible en la ubicación de origen es insuficiente
- No genera ningún movimiento ni modifica el stock en ninguna ubicación

---

## Resultado esperado (Then)

Ver sección **Then** en el extracto anterior del ERS. En automatización backend, el test asociado comprueba el contrato API/servicio equivalente o queda explícitamente marcado como pendiente si el criterio es solo UI, infraestructura o legalidad operativa fuera del alcance de pytest.

## Link directo al test

Ejecutar:

```bash
pytest tests/ers/test_gherkin_dynamic.py::test_RF007_S02 -v
```

Archivo de definición dinámica: [`tests/ers/test_gherkin_dynamic.py`](../../tests/ers/test_gherkin_dynamic.py)

Implementaciones concretas (cuando existan) pueden delegarse en módulos bajo `tests/ers/impl/`.

---

## Estado de automatización backend

Implementada en `tests/ers/gherkin_impl.py` (comprueba API/servicios equivalentes al Then del ERS).


<!-- file: RF007-S03.md -->

# Intento de traslado hacia la misma ubicación de origen

## Nombre del test

`tests/ers/test_gherkin_dynamic.py::test_RF007_S03`

## Propósito

Validar el criterio de aceptación Gherkin del ERS ICM para **RF007** — escenario 3.

## Requisito o caso de negocio asociado

- **Requisito:** `RF007` (ver `docs/requisitos/ERS_ICM_Requisitos.md`).
- **Fuente complementaria:** `docs/requisitos/ICM_Informe_Elicitacion_v2_plus.docx.md` (contexto de negocio y BR cuando aplica).

## Inputs (Given / When — extracto ERS)

**Given (Dado que):**
- El usuario autenticado tiene rol "Auxiliar de Despacho" o "Almacenista"

**When (Cuando):**
- Selecciona la misma ubicación como origen y como destino del traslado

**Then (Entonces):**
- El sistema rechaza la operación
- Muestra un mensaje indicando que el origen y el destino no pueden ser la misma ubicación
- No genera ningún movimiento

---

## Resultado esperado (Then)

Ver sección **Then** en el extracto anterior del ERS. En automatización backend, el test asociado comprueba el contrato API/servicio equivalente o queda explícitamente marcado como pendiente si el criterio es solo UI, infraestructura o legalidad operativa fuera del alcance de pytest.

## Link directo al test

Ejecutar:

```bash
pytest tests/ers/test_gherkin_dynamic.py::test_RF007_S03 -v
```

Archivo de definición dinámica: [`tests/ers/test_gherkin_dynamic.py`](../../tests/ers/test_gherkin_dynamic.py)

Implementaciones concretas (cuando existan) pueden delegarse en módulos bajo `tests/ers/impl/`.

---

## Estado de automatización backend

Implementada en `tests/ers/gherkin_impl.py` (comprueba API/servicios equivalentes al Then del ERS).


<!-- file: RF007-S04.md -->

# Auxiliar corrige un traslado dentro de la misma franja horaria activa

## Nombre del test

`tests/ers/test_gherkin_dynamic.py::test_RF007_S04`

## Propósito

Validar el criterio de aceptación Gherkin del ERS ICM para **RF007** — escenario 4.

## Requisito o caso de negocio asociado

- **Requisito:** `RF007` (ver `docs/requisitos/ERS_ICM_Requisitos.md`).
- **Fuente complementaria:** `docs/requisitos/ICM_Informe_Elicitacion_v2_plus.docx.md` (contexto de negocio y BR cuando aplica).

## Inputs (Given / When — extracto ERS)

**Given (Dado que):**
- El usuario autenticado tiene rol "Auxiliar de Despacho"
- Registró un traslado durante la franja horaria activa actual
- La franja horaria aún no ha cerrado

**When (Cuando):**
- Detecta un error en el registro y accede a la opción de edición
- Corrige los datos incorrectos y confirma los cambios

**Then (Entonces):**
- El sistema permite la corrección
- Actualiza el registro reflejando los valores corregidos
- Deja constancia en el log de auditoría de que el registro fue editado, indicando el UserID del auxiliar y el timestamp de la corrección

---

## Resultado esperado (Then)

Ver sección **Then** en el extracto anterior del ERS. En automatización backend, el test asociado comprueba el contrato API/servicio equivalente o queda explícitamente marcado como pendiente si el criterio es solo UI, infraestructura o legalidad operativa fuera del alcance de pytest.

## Link directo al test

Ejecutar:

```bash
pytest tests/ers/test_gherkin_dynamic.py::test_RF007_S04 -v
```

Archivo de definición dinámica: [`tests/ers/test_gherkin_dynamic.py`](../../tests/ers/test_gherkin_dynamic.py)

Implementaciones concretas (cuando existan) pueden delegarse en módulos bajo `tests/ers/impl/`.

---

## Estado de automatización backend

Pendiente en backend: al ejecutar el test dinámico se aplicará `pytest.skip` con el motivo hasta que exista implementación.


<!-- file: RF007-S05.md -->

# Auxiliar intenta corregir un traslado después de cerrada la franja horaria

## Nombre del test

`tests/ers/test_gherkin_dynamic.py::test_RF007_S05`

## Propósito

Validar el criterio de aceptación Gherkin del ERS ICM para **RF007** — escenario 5.

## Requisito o caso de negocio asociado

- **Requisito:** `RF007` (ver `docs/requisitos/ERS_ICM_Requisitos.md`).
- **Fuente complementaria:** `docs/requisitos/ICM_Informe_Elicitacion_v2_plus.docx.md` (contexto de negocio y BR cuando aplica).

## Inputs (Given / When — extracto ERS)

**Given (Dado que):**
- El usuario autenticado tiene rol "Auxiliar de Despacho"
- Registró un traslado durante una franja horaria que ya cerró

**When (Cuando):**
- Intenta acceder a la opción de edición de ese registro

**Then (Entonces):**
- El sistema bloquea la edición
- Muestra un mensaje indicando que la ventana de corrección ha cerrado y que cualquier ajuste debe ser solicitado al Almacenista
- El registro original permanece inmutable

## Resultado esperado (Then)

Ver sección **Then** en el extracto anterior del ERS. En automatización backend, el test asociado comprueba el contrato API/servicio equivalente o queda explícitamente marcado como pendiente si el criterio es solo UI, infraestructura o legalidad operativa fuera del alcance de pytest.

## Link directo al test

Ejecutar:

```bash
pytest tests/ers/test_gherkin_dynamic.py::test_RF007_S05 -v
```

Archivo de definición dinámica: [`tests/ers/test_gherkin_dynamic.py`](../../tests/ers/test_gherkin_dynamic.py)

Implementaciones concretas (cuando existan) pueden delegarse en módulos bajo `tests/ers/impl/`.

---

## Estado de automatización backend

Pendiente en backend: al ejecutar el test dinámico se aplicará `pytest.skip` con el motivo hasta que exista implementación.


<!-- file: RF008-S01.md -->

# Registro exitoso de devolución de producto de Electroterapia

## Nombre del test

`tests/ers/test_gherkin_dynamic.py::test_RF008_S01`

## Propósito

Validar el criterio de aceptación Gherkin del ERS ICM para **RF008** — escenario 1.

## Requisito o caso de negocio asociado

- **Requisito:** `RF008` (ver `docs/requisitos/ERS_ICM_Requisitos.md`).
- **Fuente complementaria:** `docs/requisitos/ICM_Informe_Elicitacion_v2_plus.docx.md` (contexto de negocio y BR cuando aplica).

## Inputs (Given / When — extracto ERS)

**Given (Dado que):**
- El usuario autenticado tiene rol "Auxiliar de Despacho" o "Almacenista"
- El producto a devolver pertenece a la categoría "Electroterapia" o "Electrónicos"

**When (Cuando):**
- Inicia el registro de devolución
- Selecciona el producto por SKU o número de serie
- Registra el motivo declarado por el cliente
- Registra el estado físico del producto al momento de recibirlo
- Confirma la devolución

**Then (Entonces):**
- El sistema genera un log inmutable de la devolución con SKU, número de serie, motivo, estado del producto, UserID del operario y timestamp exacto
- El producto queda en estado "Pendiente de revisión" sin ser reincorporado al stock disponible todavía
- El Almacenista recibe una notificación de que hay una devolución pendiente de aprobación

---

## Resultado esperado (Then)

Ver sección **Then** en el extracto anterior del ERS. En automatización backend, el test asociado comprueba el contrato API/servicio equivalente o queda explícitamente marcado como pendiente si el criterio es solo UI, infraestructura o legalidad operativa fuera del alcance de pytest.

## Link directo al test

Ejecutar:

```bash
pytest tests/ers/test_gherkin_dynamic.py::test_RF008_S01 -v
```

Archivo de definición dinámica: [`tests/ers/test_gherkin_dynamic.py`](../../tests/ers/test_gherkin_dynamic.py)

Implementaciones concretas (cuando existan) pueden delegarse en módulos bajo `tests/ers/impl/`.

---

## Estado de automatización backend

Implementada en `tests/ers/gherkin_impl.py` (comprueba API/servicios equivalentes al Then del ERS).


<!-- file: RF008-S02.md -->

# Intento de devolución de producto que no es Electroterapia ni Electrónico

## Nombre del test

`tests/ers/test_gherkin_dynamic.py::test_RF008_S02`

## Propósito

Validar el criterio de aceptación Gherkin del ERS ICM para **RF008** — escenario 2.

## Requisito o caso de negocio asociado

- **Requisito:** `RF008` (ver `docs/requisitos/ERS_ICM_Requisitos.md`).
- **Fuente complementaria:** `docs/requisitos/ICM_Informe_Elicitacion_v2_plus.docx.md` (contexto de negocio y BR cuando aplica).

## Inputs (Given / When — extracto ERS)

**Given (Dado que):**
- El usuario autenticado tiene rol "Auxiliar de Despacho" o "Almacenista"
- El producto seleccionado pertenece a la categoría "Manoterapia" o "Mesas de Fisioterapia"

**When (Cuando):**
- Intenta iniciar el registro de una devolución para ese producto

**Then (Entonces):**
- El sistema bloquea la operación de forma inmediata
- Muestra un mensaje descriptivo indicando que ese tipo de producto no admite devoluciones según la política de ICM
- No genera ningún registro ni modifica el stock

---

## Resultado esperado (Then)

Ver sección **Then** en el extracto anterior del ERS. En automatización backend, el test asociado comprueba el contrato API/servicio equivalente o queda explícitamente marcado como pendiente si el criterio es solo UI, infraestructura o legalidad operativa fuera del alcance de pytest.

## Link directo al test

Ejecutar:

```bash
pytest tests/ers/test_gherkin_dynamic.py::test_RF008_S02 -v
```

Archivo de definición dinámica: [`tests/ers/test_gherkin_dynamic.py`](../../tests/ers/test_gherkin_dynamic.py)

Implementaciones concretas (cuando existan) pueden delegarse en módulos bajo `tests/ers/impl/`.

---

## Estado de automatización backend

Implementada en `tests/ers/gherkin_impl.py` (comprueba API/servicios equivalentes al Then del ERS).


<!-- file: RF008-S03.md -->

# Almacenista aprueba la reincorporación al stock de un producto devuelto

## Nombre del test

`tests/ers/test_gherkin_dynamic.py::test_RF008_S03`

## Propósito

Validar el criterio de aceptación Gherkin del ERS ICM para **RF008** — escenario 3.

## Requisito o caso de negocio asociado

- **Requisito:** `RF008` (ver `docs/requisitos/ERS_ICM_Requisitos.md`).
- **Fuente complementaria:** `docs/requisitos/ICM_Informe_Elicitacion_v2_plus.docx.md` (contexto de negocio y BR cuando aplica).

## Inputs (Given / When — extracto ERS)

**Given (Dado que):**
- El usuario autenticado tiene rol "Almacenista"
- Existe una devolución en estado "Pendiente de revisión"

**When (Cuando):**
- Accede al listado de devoluciones pendientes
- Revisa el log de la devolución incluyendo motivo y estado del producto
- Aprueba la reincorporación al stock
- Selecciona la ubicación de destino donde se reincorporará el producto

**Then (Entonces):**
- El sistema incrementa el stock del producto en la ubicación seleccionada
- Actualiza el estado de la devolución a "Reincorporado"
- Registra la aprobación en el log con el UserID del Almacenista y timestamp
- El movimiento de reincorporación queda vinculado al log original de la devolución

---

## Resultado esperado (Then)

Ver sección **Then** en el extracto anterior del ERS. En automatización backend, el test asociado comprueba el contrato API/servicio equivalente o queda explícitamente marcado como pendiente si el criterio es solo UI, infraestructura o legalidad operativa fuera del alcance de pytest.

## Link directo al test

Ejecutar:

```bash
pytest tests/ers/test_gherkin_dynamic.py::test_RF008_S03 -v
```

Archivo de definición dinámica: [`tests/ers/test_gherkin_dynamic.py`](../../tests/ers/test_gherkin_dynamic.py)

Implementaciones concretas (cuando existan) pueden delegarse en módulos bajo `tests/ers/impl/`.

---

## Estado de automatización backend

Pendiente en backend: al ejecutar el test dinámico se aplicará `pytest.skip` con el motivo hasta que exista implementación.


<!-- file: RF008-S04.md -->

# Almacenista rechaza la reincorporación de un producto devuelto

## Nombre del test

`tests/ers/test_gherkin_dynamic.py::test_RF008_S04`

## Propósito

Validar el criterio de aceptación Gherkin del ERS ICM para **RF008** — escenario 4.

## Requisito o caso de negocio asociado

- **Requisito:** `RF008` (ver `docs/requisitos/ERS_ICM_Requisitos.md`).
- **Fuente complementaria:** `docs/requisitos/ICM_Informe_Elicitacion_v2_plus.docx.md` (contexto de negocio y BR cuando aplica).

## Inputs (Given / When — extracto ERS)

**Given (Dado que):**
- El usuario autenticado tiene rol "Almacenista"
- Existe una devolución en estado "Pendiente de revisión"

**When (Cuando):**
- Revisa el log de la devolución
- Determina que el producto no está en condiciones de ser reincorporado
- Rechaza la reincorporación registrando el motivo del rechazo

**Then (Entonces):**
- El sistema actualiza el estado de la devolución a "Rechazada"
- No modifica el stock disponible en ninguna ubicación
- El motivo del rechazo queda vinculado al log original de la devolución
- El registro completo permanece inmutable para efectos de auditoría

---

## Resultado esperado (Then)

Ver sección **Then** en el extracto anterior del ERS. En automatización backend, el test asociado comprueba el contrato API/servicio equivalente o queda explícitamente marcado como pendiente si el criterio es solo UI, infraestructura o legalidad operativa fuera del alcance de pytest.

## Link directo al test

Ejecutar:

```bash
pytest tests/ers/test_gherkin_dynamic.py::test_RF008_S04 -v
```

Archivo de definición dinámica: [`tests/ers/test_gherkin_dynamic.py`](../../tests/ers/test_gherkin_dynamic.py)

Implementaciones concretas (cuando existan) pueden delegarse en módulos bajo `tests/ers/impl/`.

---

## Estado de automatización backend

Pendiente en backend: al ejecutar el test dinámico se aplicará `pytest.skip` con el motivo hasta que exista implementación.


<!-- file: RF008-S05.md -->

# Consulta del historial de devoluciones por el Almacenista

## Nombre del test

`tests/ers/test_gherkin_dynamic.py::test_RF008_S05`

## Propósito

Validar el criterio de aceptación Gherkin del ERS ICM para **RF008** — escenario 5.

## Requisito o caso de negocio asociado

- **Requisito:** `RF008` (ver `docs/requisitos/ERS_ICM_Requisitos.md`).
- **Fuente complementaria:** `docs/requisitos/ICM_Informe_Elicitacion_v2_plus.docx.md` (contexto de negocio y BR cuando aplica).

## Inputs (Given / When — extracto ERS)

**Given (Dado que):**
- El usuario autenticado tiene rol "Almacenista"

**When (Cuando):**
- Accede al historial de devoluciones

**Then (Entonces):**
- El sistema muestra todas las devoluciones registradas con su estado actual (Pendiente, Reincorporado o Rechazada)
- Permite filtrar por producto, período, operario o estado
- Cada registro del historial es de solo lectura e inmutable

## Resultado esperado (Then)

Ver sección **Then** en el extracto anterior del ERS. En automatización backend, el test asociado comprueba el contrato API/servicio equivalente o queda explícitamente marcado como pendiente si el criterio es solo UI, infraestructura o legalidad operativa fuera del alcance de pytest.

## Link directo al test

Ejecutar:

```bash
pytest tests/ers/test_gherkin_dynamic.py::test_RF008_S05 -v
```

Archivo de definición dinámica: [`tests/ers/test_gherkin_dynamic.py`](../../tests/ers/test_gherkin_dynamic.py)

Implementaciones concretas (cuando existan) pueden delegarse en módulos bajo `tests/ers/impl/`.

---

## Estado de automatización backend

Pendiente en backend: al ejecutar el test dinámico se aplicará `pytest.skip` con el motivo hasta que exista implementación.


<!-- file: RF009-S01.md -->

# Almacenista registra un ajuste de inventario con justificación

## Nombre del test

`tests/ers/test_gherkin_dynamic.py::test_RF009_S01`

## Propósito

Validar el criterio de aceptación Gherkin del ERS ICM para **RF009** — escenario 1.

## Requisito o caso de negocio asociado

- **Requisito:** `RF009` (ver `docs/requisitos/ERS_ICM_Requisitos.md`).
- **Fuente complementaria:** `docs/requisitos/ICM_Informe_Elicitacion_v2_plus.docx.md` (contexto de negocio y BR cuando aplica).

## Inputs (Given / When — extracto ERS)

**Given (Dado que):**
- El usuario autenticado tiene rol "Almacenista"
- Existe una discrepancia entre el stock físico real y el stock registrado en el sistema

**When (Cuando):**
- Accede al módulo de ajustes de inventario
- Selecciona el producto y la ubicación donde ocurre la discrepancia
- Ingresa el nuevo valor de stock correcto
- Registra una justificación obligatoria explicando la causa de la discrepancia
- Confirma el ajuste

**Then (Entonces):**
- El sistema actualiza el stock del producto en la ubicación indicada
- Genera un log inmutable del ajuste con UserID del Almacenista, timestamp, producto, ubicación, stock previo, stock ajustado, delta de la diferencia y justificación registrada
- Recalcula el stock total consolidado del producto

---

## Resultado esperado (Then)

Ver sección **Then** en el extracto anterior del ERS. En automatización backend, el test asociado comprueba el contrato API/servicio equivalente o queda explícitamente marcado como pendiente si el criterio es solo UI, infraestructura o legalidad operativa fuera del alcance de pytest.

## Link directo al test

Ejecutar:

```bash
pytest tests/ers/test_gherkin_dynamic.py::test_RF009_S01 -v
```

Archivo de definición dinámica: [`tests/ers/test_gherkin_dynamic.py`](../../tests/ers/test_gherkin_dynamic.py)

Implementaciones concretas (cuando existan) pueden delegarse en módulos bajo `tests/ers/impl/`.

---

## Estado de automatización backend

Implementada en `tests/ers/gherkin_impl.py` (comprueba API/servicios equivalentes al Then del ERS).


<!-- file: RF009-S02.md -->

# Intento de registrar un ajuste sin justificación

## Nombre del test

`tests/ers/test_gherkin_dynamic.py::test_RF009_S02`

## Propósito

Validar el criterio de aceptación Gherkin del ERS ICM para **RF009** — escenario 2.

## Requisito o caso de negocio asociado

- **Requisito:** `RF009` (ver `docs/requisitos/ERS_ICM_Requisitos.md`).
- **Fuente complementaria:** `docs/requisitos/ICM_Informe_Elicitacion_v2_plus.docx.md` (contexto de negocio y BR cuando aplica).

## Inputs (Given / When — extracto ERS)

**Given (Dado que):**
- El usuario autenticado tiene rol "Almacenista"

**When (Cuando):**
- Completa el formulario de ajuste dejando vacío el campo de justificación
- Intenta confirmar el ajuste

**Then (Entonces):**
- El sistema bloquea la operación
- Muestra un mensaje indicando que la justificación es un campo obligatorio
- No modifica el stock ni genera ningún registro

---

## Resultado esperado (Then)

Ver sección **Then** en el extracto anterior del ERS. En automatización backend, el test asociado comprueba el contrato API/servicio equivalente o queda explícitamente marcado como pendiente si el criterio es solo UI, infraestructura o legalidad operativa fuera del alcance de pytest.

## Link directo al test

Ejecutar:

```bash
pytest tests/ers/test_gherkin_dynamic.py::test_RF009_S02 -v
```

Archivo de definición dinámica: [`tests/ers/test_gherkin_dynamic.py`](../../tests/ers/test_gherkin_dynamic.py)

Implementaciones concretas (cuando existan) pueden delegarse en módulos bajo `tests/ers/impl/`.

---

## Estado de automatización backend

Implementada en `tests/ers/gherkin_impl.py` (comprueba API/servicios equivalentes al Then del ERS).


<!-- file: RF009-S03.md -->

# Auxiliar de Despacho intenta ejecutar un ajuste formal

## Nombre del test

`tests/ers/test_gherkin_dynamic.py::test_RF009_S03`

## Propósito

Validar el criterio de aceptación Gherkin del ERS ICM para **RF009** — escenario 3.

## Requisito o caso de negocio asociado

- **Requisito:** `RF009` (ver `docs/requisitos/ERS_ICM_Requisitos.md`).
- **Fuente complementaria:** `docs/requisitos/ICM_Informe_Elicitacion_v2_plus.docx.md` (contexto de negocio y BR cuando aplica).

## Inputs (Given / When — extracto ERS)

**Given (Dado que):**
- El usuario autenticado tiene rol "Auxiliar de Despacho"

**When (Cuando):**
- Intenta acceder al módulo de ajustes de inventario

**Then (Entonces):**
- El sistema bloquea el acceso
- Muestra un mensaje indicando que esta funcionalidad está reservada exclusivamente para el Almacenista
- No genera ningún cambio en el sistema

---

## Resultado esperado (Then)

Ver sección **Then** en el extracto anterior del ERS. En automatización backend, el test asociado comprueba el contrato API/servicio equivalente o queda explícitamente marcado como pendiente si el criterio es solo UI, infraestructura o legalidad operativa fuera del alcance de pytest.

## Link directo al test

Ejecutar:

```bash
pytest tests/ers/test_gherkin_dynamic.py::test_RF009_S03 -v
```

Archivo de definición dinámica: [`tests/ers/test_gherkin_dynamic.py`](../../tests/ers/test_gherkin_dynamic.py)

Implementaciones concretas (cuando existan) pueden delegarse en módulos bajo `tests/ers/impl/`.

---

## Estado de automatización backend

Implementada en `tests/ers/gherkin_impl.py` (comprueba API/servicios equivalentes al Then del ERS).


<!-- file: RF009-S04.md -->

# Corrección de un ajuste registrado incorrectamente

## Nombre del test

`tests/ers/test_gherkin_dynamic.py::test_RF009_S04`

## Propósito

Validar el criterio de aceptación Gherkin del ERS ICM para **RF009** — escenario 4.

## Requisito o caso de negocio asociado

- **Requisito:** `RF009` (ver `docs/requisitos/ERS_ICM_Requisitos.md`).
- **Fuente complementaria:** `docs/requisitos/ICM_Informe_Elicitacion_v2_plus.docx.md` (contexto de negocio y BR cuando aplica).

## Inputs (Given / When — extracto ERS)

**Given (Dado que):**
- El usuario autenticado tiene rol "Almacenista"
- Existe un ajuste previo registrado con valores incorrectos

**When (Cuando):**
- Determina que el ajuste anterior fue erróneo
- Registra un nuevo ajuste con los valores correctos
- Proporciona una justificación que referencia el ajuste anterior
- Confirma el nuevo ajuste

**Then (Entonces):**
- El sistema registra el nuevo ajuste como un movimiento independiente
- El ajuste anterior permanece inmutable en el historial
- Ambos registros quedan vinculados en el log de auditoría
- El stock refleja el valor correcto según el ajuste más reciente

---

## Resultado esperado (Then)

Ver sección **Then** en el extracto anterior del ERS. En automatización backend, el test asociado comprueba el contrato API/servicio equivalente o queda explícitamente marcado como pendiente si el criterio es solo UI, infraestructura o legalidad operativa fuera del alcance de pytest.

## Link directo al test

Ejecutar:

```bash
pytest tests/ers/test_gherkin_dynamic.py::test_RF009_S04 -v
```

Archivo de definición dinámica: [`tests/ers/test_gherkin_dynamic.py`](../../tests/ers/test_gherkin_dynamic.py)

Implementaciones concretas (cuando existan) pueden delegarse en módulos bajo `tests/ers/impl/`.

---

## Estado de automatización backend

Implementada en `tests/ers/gherkin_impl.py` (comprueba API/servicios equivalentes al Then del ERS).


<!-- file: RF009-S05.md -->

# Auxiliar corrige su propio movimiento dentro de la franja horaria activa

## Nombre del test

`tests/ers/test_gherkin_dynamic.py::test_RF009_S05`

## Propósito

Validar el criterio de aceptación Gherkin del ERS ICM para **RF009** — escenario 5.

## Requisito o caso de negocio asociado

- **Requisito:** `RF009` (ver `docs/requisitos/ERS_ICM_Requisitos.md`).
- **Fuente complementaria:** `docs/requisitos/ICM_Informe_Elicitacion_v2_plus.docx.md` (contexto de negocio y BR cuando aplica).

## Inputs (Given / When — extracto ERS)

**Given (Dado que):**
- El usuario autenticado tiene rol "Auxiliar de Despacho"
- Registró un movimiento durante la franja horaria activa actual
- La franja horaria aún no ha cerrado

**When (Cuando):**
- Detecta el error y accede a la opción de edición del movimiento
- Corrige los valores incorrectos y confirma el cambio

**Then (Entonces):**
- El sistema permite la corrección sin requerir intervención del Almacenista
- Registra en el log de auditoría que el movimiento fue editado con el UserID del auxiliar y el timestamp de la corrección
- El movimiento corregido refleja los valores actualizados

---

## Resultado esperado (Then)

Ver sección **Then** en el extracto anterior del ERS. En automatización backend, el test asociado comprueba el contrato API/servicio equivalente o queda explícitamente marcado como pendiente si el criterio es solo UI, infraestructura o legalidad operativa fuera del alcance de pytest.

## Link directo al test

Ejecutar:

```bash
pytest tests/ers/test_gherkin_dynamic.py::test_RF009_S05 -v
```

Archivo de definición dinámica: [`tests/ers/test_gherkin_dynamic.py`](../../tests/ers/test_gherkin_dynamic.py)

Implementaciones concretas (cuando existan) pueden delegarse en módulos bajo `tests/ers/impl/`.

---

## Estado de automatización backend

Pendiente en backend: al ejecutar el test dinámico se aplicará `pytest.skip` con el motivo hasta que exista implementación.


<!-- file: RF009-S06.md -->

# Consulta del historial completo de ajustes por el Almacenista

## Nombre del test

`tests/ers/test_gherkin_dynamic.py::test_RF009_S06`

## Propósito

Validar el criterio de aceptación Gherkin del ERS ICM para **RF009** — escenario 6.

## Requisito o caso de negocio asociado

- **Requisito:** `RF009` (ver `docs/requisitos/ERS_ICM_Requisitos.md`).
- **Fuente complementaria:** `docs/requisitos/ICM_Informe_Elicitacion_v2_plus.docx.md` (contexto de negocio y BR cuando aplica).

## Inputs (Given / When — extracto ERS)

**Given (Dado que):**
- El usuario autenticado tiene rol "Almacenista"

**When (Cuando):**
- Accede al historial de ajustes de inventario

**Then (Entonces):**
- El sistema muestra todos los ajustes registrados en orden cronológico
- Para cada ajuste despliega el producto, ubicación, stock previo, stock ajustado, delta, justificación, UserID y timestamp
- Permite filtrar por producto, período o usuario responsable
- Todos los registros son de solo lectura e inmutables

## Resultado esperado (Then)

Ver sección **Then** en el extracto anterior del ERS. En automatización backend, el test asociado comprueba el contrato API/servicio equivalente o queda explícitamente marcado como pendiente si el criterio es solo UI, infraestructura o legalidad operativa fuera del alcance de pytest.

## Link directo al test

Ejecutar:

```bash
pytest tests/ers/test_gherkin_dynamic.py::test_RF009_S06 -v
```

Archivo de definición dinámica: [`tests/ers/test_gherkin_dynamic.py`](../../tests/ers/test_gherkin_dynamic.py)

Implementaciones concretas (cuando existan) pueden delegarse en módulos bajo `tests/ers/impl/`.

---

## Estado de automatización backend

Implementada en `tests/ers/gherkin_impl.py` (comprueba API/servicios equivalentes al Then del ERS).


<!-- file: RF010-S01.md -->

# Almacenista consulta el reporte de ventas por período

## Nombre del test

`tests/ers/test_gherkin_dynamic.py::test_RF010_S01`

## Propósito

Validar el criterio de aceptación Gherkin del ERS ICM para **RF010** — escenario 1.

## Requisito o caso de negocio asociado

- **Requisito:** `RF010` (ver `docs/requisitos/ERS_ICM_Requisitos.md`).
- **Fuente complementaria:** `docs/requisitos/ICM_Informe_Elicitacion_v2_plus.docx.md` (contexto de negocio y BR cuando aplica).

## Inputs (Given / When — extracto ERS)

**Given (Dado que):**
- El usuario autenticado tiene rol "Almacenista"

**When (Cuando):**
- Accede al módulo de reportes
- Selecciona el tipo "Reporte de ventas"
- Define un rango de fechas (diario, semanal, mensual o rango personalizado)
- Aplica el filtro

**Then (Entonces):**
- El sistema muestra un reporte consolidado de todas las salidas clasificadas como venta dentro del período seleccionado
- Desglosa los resultados por tipo de salida (Venta al por Mayor, Venta al por Menor)
- El reporte es de solo lectura y no permite modificaciones

---

## Resultado esperado (Then)

Ver sección **Then** en el extracto anterior del ERS. En automatización backend, el test asociado comprueba el contrato API/servicio equivalente o queda explícitamente marcado como pendiente si el criterio es solo UI, infraestructura o legalidad operativa fuera del alcance de pytest.

## Link directo al test

Ejecutar:

```bash
pytest tests/ers/test_gherkin_dynamic.py::test_RF010_S01 -v
```

Archivo de definición dinámica: [`tests/ers/test_gherkin_dynamic.py`](../../tests/ers/test_gherkin_dynamic.py)

Implementaciones concretas (cuando existan) pueden delegarse en módulos bajo `tests/ers/impl/`.

---

## Estado de automatización backend

Implementada en `tests/ers/gherkin_impl.py` (comprueba API/servicios equivalentes al Then del ERS).


<!-- file: RF010-S02.md -->

# Administrador consulta el dashboard de KPIs operativos

## Nombre del test

`tests/ers/test_gherkin_dynamic.py::test_RF010_S02`

## Propósito

Validar el criterio de aceptación Gherkin del ERS ICM para **RF010** — escenario 2.

## Requisito o caso de negocio asociado

- **Requisito:** `RF010` (ver `docs/requisitos/ERS_ICM_Requisitos.md`).
- **Fuente complementaria:** `docs/requisitos/ICM_Informe_Elicitacion_v2_plus.docx.md` (contexto de negocio y BR cuando aplica).

## Inputs (Given / When — extracto ERS)

**Given (Dado que):**
- El usuario autenticado tiene rol "Administrador/Jefe"

**When (Cuando):**
- Accede al dashboard gerencial

**Then (Entonces):**
- El sistema presenta de forma visual e interactiva los siguientes indicadores:
  - Índice de rotación de inventario por categoría con gráficos de tendencia
  - Porcentaje de ocupación por zona de almacenamiento
  - Nivel de servicio expresado como porcentaje de pedidos despachados completos y a tiempo
  - Panel de alertas operativas activas (vencimientos, stock mínimo y pedidos pendientes)
- Ninguno de estos indicadores permite edición desde esta vista

---

## Resultado esperado (Then)

Ver sección **Then** en el extracto anterior del ERS. En automatización backend, el test asociado comprueba el contrato API/servicio equivalente o queda explícitamente marcado como pendiente si el criterio es solo UI, infraestructura o legalidad operativa fuera del alcance de pytest.

## Link directo al test

Ejecutar:

```bash
pytest tests/ers/test_gherkin_dynamic.py::test_RF010_S02 -v
```

Archivo de definición dinámica: [`tests/ers/test_gherkin_dynamic.py`](../../tests/ers/test_gherkin_dynamic.py)

Implementaciones concretas (cuando existan) pueden delegarse en módulos bajo `tests/ers/impl/`.

---

## Estado de automatización backend

Implementada en `tests/ers/gherkin_impl.py` (comprueba API/servicios equivalentes al Then del ERS).


<!-- file: RF010-S03.md -->

# Exportación de reporte en formato Excel o CSV

## Nombre del test

`tests/ers/test_gherkin_dynamic.py::test_RF010_S03`

## Propósito

Validar el criterio de aceptación Gherkin del ERS ICM para **RF010** — escenario 3.

## Requisito o caso de negocio asociado

- **Requisito:** `RF010` (ver `docs/requisitos/ERS_ICM_Requisitos.md`).
- **Fuente complementaria:** `docs/requisitos/ICM_Informe_Elicitacion_v2_plus.docx.md` (contexto de negocio y BR cuando aplica).

## Inputs (Given / When — extracto ERS)

**Given (Dado que):**
- El usuario autenticado tiene rol "Almacenista" o "Administrador/Jefe"
- Ha generado un reporte con los filtros deseados

**When (Cuando):**
- Selecciona la opción de exportar y elige el formato (Excel o CSV)

**Then (Entonces):**
- El sistema genera el archivo con los datos del reporte en el formato seleccionado
- Lo pone a disposición del usuario para su descarga inmediata
- El archivo exportado contiene exactamente los mismos datos visibles en pantalla

---

## Resultado esperado (Then)

Ver sección **Then** en el extracto anterior del ERS. En automatización backend, el test asociado comprueba el contrato API/servicio equivalente o queda explícitamente marcado como pendiente si el criterio es solo UI, infraestructura o legalidad operativa fuera del alcance de pytest.

## Link directo al test

Ejecutar:

```bash
pytest tests/ers/test_gherkin_dynamic.py::test_RF010_S03 -v
```

Archivo de definición dinámica: [`tests/ers/test_gherkin_dynamic.py`](../../tests/ers/test_gherkin_dynamic.py)

Implementaciones concretas (cuando existan) pueden delegarse en módulos bajo `tests/ers/impl/`.

---

## Estado de automatización backend

Pendiente en backend: al ejecutar el test dinámico se aplicará `pytest.skip` con el motivo hasta que exista implementación.


<!-- file: RF010-S04.md -->

# Consulta del historial de movimientos por operario

## Nombre del test

`tests/ers/test_gherkin_dynamic.py::test_RF010_S04`

## Propósito

Validar el criterio de aceptación Gherkin del ERS ICM para **RF010** — escenario 4.

## Requisito o caso de negocio asociado

- **Requisito:** `RF010` (ver `docs/requisitos/ERS_ICM_Requisitos.md`).
- **Fuente complementaria:** `docs/requisitos/ICM_Informe_Elicitacion_v2_plus.docx.md` (contexto de negocio y BR cuando aplica).

## Inputs (Given / When — extracto ERS)

**Given (Dado que):**
- El usuario autenticado tiene rol "Almacenista"

**When (Cuando):**
- Accede al reporte de historial de movimientos
- Filtra por un operario específico y un período de tiempo

**Then (Entonces):**
- El sistema muestra todos los movimientos registrados por ese operario en el período
- Para cada movimiento despliega tipo de transacción, producto, cantidad, ubicación, timestamp y stock resultante
- Permite exportar ese historial en Excel o CSV

---

## Resultado esperado (Then)

Ver sección **Then** en el extracto anterior del ERS. En automatización backend, el test asociado comprueba el contrato API/servicio equivalente o queda explícitamente marcado como pendiente si el criterio es solo UI, infraestructura o legalidad operativa fuera del alcance de pytest.

## Link directo al test

Ejecutar:

```bash
pytest tests/ers/test_gherkin_dynamic.py::test_RF010_S04 -v
```

Archivo de definición dinámica: [`tests/ers/test_gherkin_dynamic.py`](../../tests/ers/test_gherkin_dynamic.py)

Implementaciones concretas (cuando existan) pueden delegarse en módulos bajo `tests/ers/impl/`.

---

## Estado de automatización backend

Implementada en `tests/ers/gherkin_impl.py` (comprueba API/servicios equivalentes al Then del ERS).


<!-- file: RF010-S05.md -->

# Consulta del reporte de productos próximos a vencer

## Nombre del test

`tests/ers/test_gherkin_dynamic.py::test_RF010_S05`

## Propósito

Validar el criterio de aceptación Gherkin del ERS ICM para **RF010** — escenario 5.

## Requisito o caso de negocio asociado

- **Requisito:** `RF010` (ver `docs/requisitos/ERS_ICM_Requisitos.md`).
- **Fuente complementaria:** `docs/requisitos/ICM_Informe_Elicitacion_v2_plus.docx.md` (contexto de negocio y BR cuando aplica).

## Inputs (Given / When — extracto ERS)

**Given (Dado que):**
- El usuario autenticado tiene rol "Almacenista" o "Administrador/Jefe"

**When (Cuando):**
- Accede al reporte de vencimientos

**Then (Entonces):**
- El sistema lista todos los productos con fecha de vencimiento dentro de los próximos 60 días
- Los organiza por urgencia, mostrando primero los que vencen más pronto
- Para cada producto indica SKU, nombre, lote, fecha de vencimiento, stock disponible y ubicación

---

## Resultado esperado (Then)

Ver sección **Then** en el extracto anterior del ERS. En automatización backend, el test asociado comprueba el contrato API/servicio equivalente o queda explícitamente marcado como pendiente si el criterio es solo UI, infraestructura o legalidad operativa fuera del alcance de pytest.

## Link directo al test

Ejecutar:

```bash
pytest tests/ers/test_gherkin_dynamic.py::test_RF010_S05 -v
```

Archivo de definición dinámica: [`tests/ers/test_gherkin_dynamic.py`](../../tests/ers/test_gherkin_dynamic.py)

Implementaciones concretas (cuando existan) pueden delegarse en módulos bajo `tests/ers/impl/`.

---

## Estado de automatización backend

Implementada en `tests/ers/gherkin_impl.py` (comprueba API/servicios equivalentes al Then del ERS).


<!-- file: RF010-S06.md -->

# Consulta y descarga de factura individual desde el historial

## Nombre del test

`tests/ers/test_gherkin_dynamic.py::test_RF010_S06`

## Propósito

Validar el criterio de aceptación Gherkin del ERS ICM para **RF010** — escenario 6.

## Requisito o caso de negocio asociado

- **Requisito:** `RF010` (ver `docs/requisitos/ERS_ICM_Requisitos.md`).
- **Fuente complementaria:** `docs/requisitos/ICM_Informe_Elicitacion_v2_plus.docx.md` (contexto de negocio y BR cuando aplica).

## Inputs (Given / When — extracto ERS)

**Given (Dado que):**
- El usuario autenticado tiene rol "Almacenista" o "Administrador/Jefe"

**When (Cuando):**
- Accede al historial de facturas y remisiones
- Filtra por período, tipo de salida o cliente
- Selecciona una factura específica del listado

**Then (Entonces):**
- El sistema muestra los detalles completos de esa factura
- Permite su descarga individual en formato PDF
- El documento descargado es idéntico al generado en el momento del despacho

---

## Resultado esperado (Then)

Ver sección **Then** en el extracto anterior del ERS. En automatización backend, el test asociado comprueba el contrato API/servicio equivalente o queda explícitamente marcado como pendiente si el criterio es solo UI, infraestructura o legalidad operativa fuera del alcance de pytest.

## Link directo al test

Ejecutar:

```bash
pytest tests/ers/test_gherkin_dynamic.py::test_RF010_S06 -v
```

Archivo de definición dinámica: [`tests/ers/test_gherkin_dynamic.py`](../../tests/ers/test_gherkin_dynamic.py)

Implementaciones concretas (cuando existan) pueden delegarse en módulos bajo `tests/ers/impl/`.

---

## Estado de automatización backend

Pendiente en backend: al ejecutar el test dinámico se aplicará `pytest.skip` con el motivo hasta que exista implementación.


<!-- file: RF010-S07.md -->

# Usuario sin permisos intenta acceder al módulo de reportes

## Nombre del test

`tests/ers/test_gherkin_dynamic.py::test_RF010_S07`

## Propósito

Validar el criterio de aceptación Gherkin del ERS ICM para **RF010** — escenario 7.

## Requisito o caso de negocio asociado

- **Requisito:** `RF010` (ver `docs/requisitos/ERS_ICM_Requisitos.md`).
- **Fuente complementaria:** `docs/requisitos/ICM_Informe_Elicitacion_v2_plus.docx.md` (contexto de negocio y BR cuando aplica).

## Inputs (Given / When — extracto ERS)

**Given (Dado que):**
- El usuario autenticado tiene rol "Auxiliar de Despacho"

**When (Cuando):**
- Intenta acceder al módulo de reportes o al dashboard gerencial

**Then (Entonces):**
- El sistema bloquea el acceso
- Muestra un mensaje indicando que no tiene permisos para visualizar esta sección
- No expone ningún dato operativo ni indicador

## Resultado esperado (Then)

Ver sección **Then** en el extracto anterior del ERS. En automatización backend, el test asociado comprueba el contrato API/servicio equivalente o queda explícitamente marcado como pendiente si el criterio es solo UI, infraestructura o legalidad operativa fuera del alcance de pytest.

## Link directo al test

Ejecutar:

```bash
pytest tests/ers/test_gherkin_dynamic.py::test_RF010_S07 -v
```

Archivo de definición dinámica: [`tests/ers/test_gherkin_dynamic.py`](../../tests/ers/test_gherkin_dynamic.py)

Implementaciones concretas (cuando existan) pueden delegarse en módulos bajo `tests/ers/impl/`.

---

## Estado de automatización backend

Implementada en `tests/ers/gherkin_impl.py` (comprueba API/servicios equivalentes al Then del ERS).


<!-- file: RF011-S01.md -->

# Alerta de stock mínimo cuando el inventario cae bajo el punto de reorden

## Nombre del test

`tests/ers/test_gherkin_dynamic.py::test_RF011_S01`

## Propósito

Validar el criterio de aceptación Gherkin del ERS ICM para **RF011** — escenario 1.

## Requisito o caso de negocio asociado

- **Requisito:** `RF011` (ver `docs/requisitos/ERS_ICM_Requisitos.md`).
- **Fuente complementaria:** `docs/requisitos/ICM_Informe_Elicitacion_v2_plus.docx.md` (contexto de negocio y BR cuando aplica).

## Inputs (Given / When — extracto ERS)

**Given (Dado que):**
- Un producto tiene configurado un punto de reorden de 10 unidades
- El stock total del producto era de 12 unidades

**When (Cuando):**
- Se confirma un despacho que deja el stock total en 8 unidades

**Then (Entonces):**
- El sistema emite de forma automática una alerta de stock mínimo visible en el dashboard del Almacenista y del Administrador
- La alerta indica el SKU, nombre del producto, stock actual y punto de reorden
- La alerta permanece activa hasta que el stock supere nuevamente el umbral
- El evento de activación queda registrado en el log con timestamp

---

## Resultado esperado (Then)

Ver sección **Then** en el extracto anterior del ERS. En automatización backend, el test asociado comprueba el contrato API/servicio equivalente o queda explícitamente marcado como pendiente si el criterio es solo UI, infraestructura o legalidad operativa fuera del alcance de pytest.

## Link directo al test

Ejecutar:

```bash
pytest tests/ers/test_gherkin_dynamic.py::test_RF011_S01 -v
```

Archivo de definición dinámica: [`tests/ers/test_gherkin_dynamic.py`](../../tests/ers/test_gherkin_dynamic.py)

Implementaciones concretas (cuando existan) pueden delegarse en módulos bajo `tests/ers/impl/`.

---

## Estado de automatización backend

Implementada en `tests/ers/gherkin_impl.py` (comprueba API/servicios equivalentes al Then del ERS).


<!-- file: RF011-S02.md -->

# Alerta de vencimiento próximo a 60 días

## Nombre del test

`tests/ers/test_gherkin_dynamic.py::test_RF011_S02`

## Propósito

Validar el criterio de aceptación Gherkin del ERS ICM para **RF011** — escenario 2.

## Requisito o caso de negocio asociado

- **Requisito:** `RF011` (ver `docs/requisitos/ERS_ICM_Requisitos.md`).
- **Fuente complementaria:** `docs/requisitos/ICM_Informe_Elicitacion_v2_plus.docx.md` (contexto de negocio y BR cuando aplica).

## Inputs (Given / When — extracto ERS)

**Given (Dado que):**
- Existe un lote de producto registrado con fecha de vencimiento

**When (Cuando):**
- Faltan exactamente 60 días calendario para esa fecha de vencimiento

**Then (Entonces):**
- El sistema emite automáticamente una alerta de vencimiento visible en el dashboard y en el módulo de inventario
- La alerta indica SKU, nombre del producto, número de lote, fecha de vencimiento y stock disponible del lote afectado
- La alerta queda registrada en el log de auditoría con timestamp

---

## Resultado esperado (Then)

Ver sección **Then** en el extracto anterior del ERS. En automatización backend, el test asociado comprueba el contrato API/servicio equivalente o queda explícitamente marcado como pendiente si el criterio es solo UI, infraestructura o legalidad operativa fuera del alcance de pytest.

## Link directo al test

Ejecutar:

```bash
pytest tests/ers/test_gherkin_dynamic.py::test_RF011_S02 -v
```

Archivo de definición dinámica: [`tests/ers/test_gherkin_dynamic.py`](../../tests/ers/test_gherkin_dynamic.py)

Implementaciones concretas (cuando existan) pueden delegarse en módulos bajo `tests/ers/impl/`.

---

## Estado de automatización backend

Pendiente en backend: al ejecutar el test dinámico se aplicará `pytest.skip` con el motivo hasta que exista implementación.


<!-- file: RF011-S03.md -->

# Alerta de vencimiento próximo a 30 días

## Nombre del test

`tests/ers/test_gherkin_dynamic.py::test_RF011_S03`

## Propósito

Validar el criterio de aceptación Gherkin del ERS ICM para **RF011** — escenario 3.

## Requisito o caso de negocio asociado

- **Requisito:** `RF011` (ver `docs/requisitos/ERS_ICM_Requisitos.md`).
- **Fuente complementaria:** `docs/requisitos/ICM_Informe_Elicitacion_v2_plus.docx.md` (contexto de negocio y BR cuando aplica).

## Inputs (Given / When — extracto ERS)

**Given (Dado que):**
- Existe una alerta de vencimiento activa a 60 días
- Han transcurrido 30 días desde su activación

**When (Cuando):**
- El sistema detecta que ahora faltan 30 días para el vencimiento

**Then (Entonces):**
- El sistema escala la alerta existente a un nivel de urgencia mayor
- La alerta actualizada es visualmente diferenciada de la alerta a 60 días
- El escalamiento queda registrado en el log de auditoría

---

## Resultado esperado (Then)

Ver sección **Then** en el extracto anterior del ERS. En automatización backend, el test asociado comprueba el contrato API/servicio equivalente o queda explícitamente marcado como pendiente si el criterio es solo UI, infraestructura o legalidad operativa fuera del alcance de pytest.

## Link directo al test

Ejecutar:

```bash
pytest tests/ers/test_gherkin_dynamic.py::test_RF011_S03 -v
```

Archivo de definición dinámica: [`tests/ers/test_gherkin_dynamic.py`](../../tests/ers/test_gherkin_dynamic.py)

Implementaciones concretas (cuando existan) pueden delegarse en módulos bajo `tests/ers/impl/`.

---

## Estado de automatización backend

Pendiente en backend: al ejecutar el test dinámico se aplicará `pytest.skip` con el motivo hasta que exista implementación.


<!-- file: RF011-S04.md -->

# Alerta de cadena de frío al registrar movimiento de producto refrigerado

## Nombre del test

`tests/ers/test_gherkin_dynamic.py::test_RF011_S04`

## Propósito

Validar el criterio de aceptación Gherkin del ERS ICM para **RF011** — escenario 4.

## Requisito o caso de negocio asociado

- **Requisito:** `RF011` (ver `docs/requisitos/ERS_ICM_Requisitos.md`).
- **Fuente complementaria:** `docs/requisitos/ICM_Informe_Elicitacion_v2_plus.docx.md` (contexto de negocio y BR cuando aplica).

## Inputs (Given / When — extracto ERS)

**Given (Dado que):**
- Un producto tiene activado el indicador de cadena de frío

**When (Cuando):**
- Cualquier usuario registra un movimiento que involucra ese producto

**Then (Entonces):**
- El sistema despliega de forma inmediata una alerta visual persistente y de alta visibilidad en la pantalla activa del usuario
- El usuario debe reconocer la alerta antes de poder confirmar el movimiento
- El reconocimiento queda registrado en el log con UserID y timestamp

---

## Resultado esperado (Then)

Ver sección **Then** en el extracto anterior del ERS. En automatización backend, el test asociado comprueba el contrato API/servicio equivalente o queda explícitamente marcado como pendiente si el criterio es solo UI, infraestructura o legalidad operativa fuera del alcance de pytest.

## Link directo al test

Ejecutar:

```bash
pytest tests/ers/test_gherkin_dynamic.py::test_RF011_S04 -v
```

Archivo de definición dinámica: [`tests/ers/test_gherkin_dynamic.py`](../../tests/ers/test_gherkin_dynamic.py)

Implementaciones concretas (cuando existan) pueden delegarse en módulos bajo `tests/ers/impl/`.

---

## Estado de automatización backend

Pendiente en backend: al ejecutar el test dinámico se aplicará `pytest.skip` con el motivo hasta que exista implementación.


<!-- file: RF011-S05.md -->

# Alerta de seguridad eléctrica al registrar movimiento de equipo eléctrico

## Nombre del test

`tests/ers/test_gherkin_dynamic.py::test_RF011_S05`

## Propósito

Validar el criterio de aceptación Gherkin del ERS ICM para **RF011** — escenario 5.

## Requisito o caso de negocio asociado

- **Requisito:** `RF011` (ver `docs/requisitos/ERS_ICM_Requisitos.md`).
- **Fuente complementaria:** `docs/requisitos/ICM_Informe_Elicitacion_v2_plus.docx.md` (contexto de negocio y BR cuando aplica).

## Inputs (Given / When — extracto ERS)

**Given (Dado que):**
- Un producto pertenece a la categoría "Electroterapia"

**When (Cuando):**
- Cualquier usuario registra un movimiento que involucra ese producto

**Then (Entonces):**
- El sistema despliega una advertencia visual sobre los protocolos de manejo seguro
- La advertencia es visualmente distinguible de la alerta de cadena de frío
- El usuario debe reconocer la advertencia antes de confirmar el movimiento
- El reconocimiento queda registrado en el log con UserID y timestamp

---

## Resultado esperado (Then)

Ver sección **Then** en el extracto anterior del ERS. En automatización backend, el test asociado comprueba el contrato API/servicio equivalente o queda explícitamente marcado como pendiente si el criterio es solo UI, infraestructura o legalidad operativa fuera del alcance de pytest.

## Link directo al test

Ejecutar:

```bash
pytest tests/ers/test_gherkin_dynamic.py::test_RF011_S05 -v
```

Archivo de definición dinámica: [`tests/ers/test_gherkin_dynamic.py`](../../tests/ers/test_gherkin_dynamic.py)

Implementaciones concretas (cuando existan) pueden delegarse en módulos bajo `tests/ers/impl/`.

---

## Estado de automatización backend

Pendiente en backend: al ejecutar el test dinámico se aplicará `pytest.skip` con el motivo hasta que exista implementación.


<!-- file: RF011-S06.md -->

# Panel de alertas activas en el dashboard

## Nombre del test

`tests/ers/test_gherkin_dynamic.py::test_RF011_S06`

## Propósito

Validar el criterio de aceptación Gherkin del ERS ICM para **RF011** — escenario 6.

## Requisito o caso de negocio asociado

- **Requisito:** `RF011` (ver `docs/requisitos/ERS_ICM_Requisitos.md`).
- **Fuente complementaria:** `docs/requisitos/ICM_Informe_Elicitacion_v2_plus.docx.md` (contexto de negocio y BR cuando aplica).

## Inputs (Given / When — extracto ERS)

**Given (Dado que):**
- El usuario autenticado tiene rol "Almacenista" o "Administrador/Jefe"

**When (Cuando):**
- Accede al dashboard principal

**Then (Entonces):**
- El sistema presenta un panel consolidado con todas las alertas operativas activas, organizadas por tipo y urgencia
- Cada alerta en el panel es navegable hacia el producto o movimiento que la originó
- Las alertas a 30 días aparecen por encima de las alertas a 60 días en el panel

---

## Resultado esperado (Then)

Ver sección **Then** en el extracto anterior del ERS. En automatización backend, el test asociado comprueba el contrato API/servicio equivalente o queda explícitamente marcado como pendiente si el criterio es solo UI, infraestructura o legalidad operativa fuera del alcance de pytest.

## Link directo al test

Ejecutar:

```bash
pytest tests/ers/test_gherkin_dynamic.py::test_RF011_S06 -v
```

Archivo de definición dinámica: [`tests/ers/test_gherkin_dynamic.py`](../../tests/ers/test_gherkin_dynamic.py)

Implementaciones concretas (cuando existan) pueden delegarse en módulos bajo `tests/ers/impl/`.

---

## Estado de automatización backend

Pendiente en backend: al ejecutar el test dinámico se aplicará `pytest.skip` con el motivo hasta que exista implementación.


<!-- file: RF011-S07.md -->

# Resolución automática de una alerta de stock mínimo

## Nombre del test

`tests/ers/test_gherkin_dynamic.py::test_RF011_S07`

## Propósito

Validar el criterio de aceptación Gherkin del ERS ICM para **RF011** — escenario 7.

## Requisito o caso de negocio asociado

- **Requisito:** `RF011` (ver `docs/requisitos/ERS_ICM_Requisitos.md`).
- **Fuente complementaria:** `docs/requisitos/ICM_Informe_Elicitacion_v2_plus.docx.md` (contexto de negocio y BR cuando aplica).

## Inputs (Given / When — extracto ERS)

**Given (Dado que):**
- Existe una alerta de stock mínimo activa para un producto

**When (Cuando):**
- Se confirma una entrada de mercancía que eleva el stock total del producto por encima del punto de reorden

**Then (Entonces):**
- El sistema desactiva automáticamente la alerta de stock mínimo
- La elimina del panel de alertas activas
- Deja constancia en el log de auditoría de que la alerta fue resuelta, con el timestamp de resolución y el movimiento de entrada que la originó

## Resultado esperado (Then)

Ver sección **Then** en el extracto anterior del ERS. En automatización backend, el test asociado comprueba el contrato API/servicio equivalente o queda explícitamente marcado como pendiente si el criterio es solo UI, infraestructura o legalidad operativa fuera del alcance de pytest.

## Link directo al test

Ejecutar:

```bash
pytest tests/ers/test_gherkin_dynamic.py::test_RF011_S07 -v
```

Archivo de definición dinámica: [`tests/ers/test_gherkin_dynamic.py`](../../tests/ers/test_gherkin_dynamic.py)

Implementaciones concretas (cuando existan) pueden delegarse en módulos bajo `tests/ers/impl/`.

---

## Estado de automatización backend

Pendiente en backend: al ejecutar el test dinámico se aplicará `pytest.skip` con el motivo hasta que exista implementación.


<!-- file: RF012-S01.md -->

# El sistema genera automáticamente un registro de auditoría al confirmar cualquier movimiento de inventario

## Nombre del test

`tests/ers/test_gherkin_dynamic.py::test_RF012_S01`

## Propósito

Validar el criterio de aceptación Gherkin del ERS ICM para **RF012** — escenario 1.

## Requisito o caso de negocio asociado

- **Requisito:** `RF012` (ver `docs/requisitos/ERS_ICM_Requisitos.md`).
- **Fuente complementaria:** `docs/requisitos/ICM_Informe_Elicitacion_v2_plus.docx.md` (contexto de negocio y BR cuando aplica).

## Inputs (Given / When — extracto ERS)

**Given (Dado que):**
- Cualquier usuario autenticado confirma una operación que afecta el stock

**When (Cuando):**
- El sistema procesa y confirma la operación

**Then (Entonces):**
- El sistema genera de forma automática e inmediata un registro en el log que contiene:
  - Identificador único del movimiento
  - Timestamp con fecha y hora exacta
  - UserID del operario responsable
  - Tipo de transacción
  - SKU del producto involucrado
  - Código serial cuando aplique
  - Ubicación de origen y destino
  - Cantidad operada
  - Stock previo y stock resultante
  - Nota o justificación cuando la operación lo requiera
- Ese registro queda inmutable desde el momento de su creación

---

## Resultado esperado (Then)

Ver sección **Then** en el extracto anterior del ERS. En automatización backend, el test asociado comprueba el contrato API/servicio equivalente o queda explícitamente marcado como pendiente si el criterio es solo UI, infraestructura o legalidad operativa fuera del alcance de pytest.

## Link directo al test

Ejecutar:

```bash
pytest tests/ers/test_gherkin_dynamic.py::test_RF012_S01 -v
```

Archivo de definición dinámica: [`tests/ers/test_gherkin_dynamic.py`](../../tests/ers/test_gherkin_dynamic.py)

Implementaciones concretas (cuando existan) pueden delegarse en módulos bajo `tests/ers/impl/`.

---

## Estado de automatización backend

Implementada en `tests/ers/gherkin_impl.py` (comprueba API/servicios equivalentes al Then del ERS).


<!-- file: RF012-S02.md -->

# El sistema registra en el log los eventos de autenticación

## Nombre del test

`tests/ers/test_gherkin_dynamic.py::test_RF012_S02`

## Propósito

Validar el criterio de aceptación Gherkin del ERS ICM para **RF012** — escenario 2.

## Requisito o caso de negocio asociado

- **Requisito:** `RF012` (ver `docs/requisitos/ERS_ICM_Requisitos.md`).
- **Fuente complementaria:** `docs/requisitos/ICM_Informe_Elicitacion_v2_plus.docx.md` (contexto de negocio y BR cuando aplica).

## Inputs (Given / When — extracto ERS)

**Given (Dado que):**
- Cualquier usuario intenta iniciar o cerrar sesión en el sistema

**When (Cuando):**
- El intento de autenticación ocurre, sea exitoso o fallido

**Then (Entonces):**
- El sistema registra en el log el evento con timestamp, UserID o nombre de usuario intentado, resultado del intento (éxito o fallo) y dirección del dispositivo desde donde se realizó el intento
- Ese registro es inmutable y no puede ser eliminado

---

## Resultado esperado (Then)

Ver sección **Then** en el extracto anterior del ERS. En automatización backend, el test asociado comprueba el contrato API/servicio equivalente o queda explícitamente marcado como pendiente si el criterio es solo UI, infraestructura o legalidad operativa fuera del alcance de pytest.

## Link directo al test

Ejecutar:

```bash
pytest tests/ers/test_gherkin_dynamic.py::test_RF012_S02 -v
```

Archivo de definición dinámica: [`tests/ers/test_gherkin_dynamic.py`](../../tests/ers/test_gherkin_dynamic.py)

Implementaciones concretas (cuando existan) pueden delegarse en módulos bajo `tests/ers/impl/`.

---

## Estado de automatización backend

Implementada en `tests/ers/gherkin_impl.py` (comprueba API/servicios equivalentes al Then del ERS).


<!-- file: RF012-S03.md -->

# El sistema registra en el log los eventos de gestión de credenciales

## Nombre del test

`tests/ers/test_gherkin_dynamic.py::test_RF012_S03`

## Propósito

Validar el criterio de aceptación Gherkin del ERS ICM para **RF012** — escenario 3.

## Requisito o caso de negocio asociado

- **Requisito:** `RF012` (ver `docs/requisitos/ERS_ICM_Requisitos.md`).
- **Fuente complementaria:** `docs/requisitos/ICM_Informe_Elicitacion_v2_plus.docx.md` (contexto de negocio y BR cuando aplica).

## Inputs (Given / When — extracto ERS)

**Given (Dado que):**
- El Almacenista crea, modifica o deshabilita una cuenta de usuario

**When (Cuando):**
- Confirma cualquiera de esas acciones

**Then (Entonces):**
- El sistema registra en el log el evento con timestamp, UserID del Almacenista que ejecutó la acción, tipo de acción realizada (creación, modificación o deshabilitación) y UserID de la cuenta afectada
- El registro es inmutable desde su creación

---

## Resultado esperado (Then)

Ver sección **Then** en el extracto anterior del ERS. En automatización backend, el test asociado comprueba el contrato API/servicio equivalente o queda explícitamente marcado como pendiente si el criterio es solo UI, infraestructura o legalidad operativa fuera del alcance de pytest.

## Link directo al test

Ejecutar:

```bash
pytest tests/ers/test_gherkin_dynamic.py::test_RF012_S03 -v
```

Archivo de definición dinámica: [`tests/ers/test_gherkin_dynamic.py`](../../tests/ers/test_gherkin_dynamic.py)

Implementaciones concretas (cuando existan) pueden delegarse en módulos bajo `tests/ers/impl/`.

---

## Estado de automatización backend

Pendiente en backend: al ejecutar el test dinámico se aplicará `pytest.skip` con el motivo hasta que exista implementación.


<!-- file: RF012-S04.md -->

# El sistema registra el reconocimiento de alertas de cadena de frío y seguridad eléctrica

## Nombre del test

`tests/ers/test_gherkin_dynamic.py::test_RF012_S04`

## Propósito

Validar el criterio de aceptación Gherkin del ERS ICM para **RF012** — escenario 4.

## Requisito o caso de negocio asociado

- **Requisito:** `RF012` (ver `docs/requisitos/ERS_ICM_Requisitos.md`).
- **Fuente complementaria:** `docs/requisitos/ICM_Informe_Elicitacion_v2_plus.docx.md` (contexto de negocio y BR cuando aplica).

## Inputs (Given / When — extracto ERS)

**Given (Dado que):**
- Un usuario reconoce activamente una alerta de cadena de frío o de seguridad eléctrica antes de confirmar un movimiento

**When (Cuando):**
- Confirma el reconocimiento de la alerta

**Then (Entonces):**
- El sistema registra en el log ese reconocimiento con UserID, timestamp, tipo de alerta reconocida y SKU del producto involucrado
- Ese registro queda vinculado al movimiento que originó la alerta

---

## Resultado esperado (Then)

Ver sección **Then** en el extracto anterior del ERS. En automatización backend, el test asociado comprueba el contrato API/servicio equivalente o queda explícitamente marcado como pendiente si el criterio es solo UI, infraestructura o legalidad operativa fuera del alcance de pytest.

## Link directo al test

Ejecutar:

```bash
pytest tests/ers/test_gherkin_dynamic.py::test_RF012_S04 -v
```

Archivo de definición dinámica: [`tests/ers/test_gherkin_dynamic.py`](../../tests/ers/test_gherkin_dynamic.py)

Implementaciones concretas (cuando existan) pueden delegarse en módulos bajo `tests/ers/impl/`.

---

## Estado de automatización backend

Pendiente en backend: al ejecutar el test dinámico se aplicará `pytest.skip` con el motivo hasta que exista implementación.


<!-- file: RF012-S05.md -->

# Almacenista consulta el log completo de auditoría con filtros

## Nombre del test

`tests/ers/test_gherkin_dynamic.py::test_RF012_S05`

## Propósito

Validar el criterio de aceptación Gherkin del ERS ICM para **RF012** — escenario 5.

## Requisito o caso de negocio asociado

- **Requisito:** `RF012` (ver `docs/requisitos/ERS_ICM_Requisitos.md`).
- **Fuente complementaria:** `docs/requisitos/ICM_Informe_Elicitacion_v2_plus.docx.md` (contexto de negocio y BR cuando aplica).

## Inputs (Given / When — extracto ERS)

**Given (Dado que):**
- El usuario autenticado tiene rol "Almacenista"

**When (Cuando):**
- Accede al módulo de auditoría
- Aplica filtros por período, tipo de operación, operario o producto

**Then (Entonces):**
- El sistema muestra todos los registros que coinciden con los filtros en orden cronológico
- Cada registro es de solo lectura, sin opción de edición ni eliminación
- El Almacenista puede exportar el log filtrado en formato Excel o CSV

---

## Resultado esperado (Then)

Ver sección **Then** en el extracto anterior del ERS. En automatización backend, el test asociado comprueba el contrato API/servicio equivalente o queda explícitamente marcado como pendiente si el criterio es solo UI, infraestructura o legalidad operativa fuera del alcance de pytest.

## Link directo al test

Ejecutar:

```bash
pytest tests/ers/test_gherkin_dynamic.py::test_RF012_S05 -v
```

Archivo de definición dinámica: [`tests/ers/test_gherkin_dynamic.py`](../../tests/ers/test_gherkin_dynamic.py)

Implementaciones concretas (cuando existan) pueden delegarse en módulos bajo `tests/ers/impl/`.

---

## Estado de automatización backend

Implementada en `tests/ers/gherkin_impl.py` (comprueba API/servicios equivalentes al Then del ERS).


<!-- file: RF012-S06.md -->

# Auxiliar de Despacho intenta acceder al log de auditoría

## Nombre del test

`tests/ers/test_gherkin_dynamic.py::test_RF012_S06`

## Propósito

Validar el criterio de aceptación Gherkin del ERS ICM para **RF012** — escenario 6.

## Requisito o caso de negocio asociado

- **Requisito:** `RF012` (ver `docs/requisitos/ERS_ICM_Requisitos.md`).
- **Fuente complementaria:** `docs/requisitos/ICM_Informe_Elicitacion_v2_plus.docx.md` (contexto de negocio y BR cuando aplica).

## Inputs (Given / When — extracto ERS)

**Given (Dado que):**
- El usuario autenticado tiene rol "Auxiliar de Despacho"

**When (Cuando):**
- Intenta acceder al módulo de auditoría por cualquier vía

**Then (Entonces):**
- El sistema bloquea el acceso de forma inmediata
- Muestra un mensaje indicando que no tiene permisos para consultar el log
- No expone ningún registro del historial

---

## Resultado esperado (Then)

Ver sección **Then** en el extracto anterior del ERS. En automatización backend, el test asociado comprueba el contrato API/servicio equivalente o queda explícitamente marcado como pendiente si el criterio es solo UI, infraestructura o legalidad operativa fuera del alcance de pytest.

## Link directo al test

Ejecutar:

```bash
pytest tests/ers/test_gherkin_dynamic.py::test_RF012_S06 -v
```

Archivo de definición dinámica: [`tests/ers/test_gherkin_dynamic.py`](../../tests/ers/test_gherkin_dynamic.py)

Implementaciones concretas (cuando existan) pueden delegarse en módulos bajo `tests/ers/impl/`.

---

## Estado de automatización backend

Implementada en `tests/ers/gherkin_impl.py` (comprueba API/servicios equivalentes al Then del ERS).


<!-- file: RF012-S07.md -->

# El log registra tanto el movimiento original como la corrección del Auxiliar

## Nombre del test

`tests/ers/test_gherkin_dynamic.py::test_RF012_S07`

## Propósito

Validar el criterio de aceptación Gherkin del ERS ICM para **RF012** — escenario 7.

## Requisito o caso de negocio asociado

- **Requisito:** `RF012` (ver `docs/requisitos/ERS_ICM_Requisitos.md`).
- **Fuente complementaria:** `docs/requisitos/ICM_Informe_Elicitacion_v2_plus.docx.md` (contexto de negocio y BR cuando aplica).

## Inputs (Given / When — extracto ERS)

**Given (Dado que):**
- Un Auxiliar de Despacho registró un movimiento durante la franja activa
- Detecta un error y lo corrige antes de que cierre la franja

**When (Cuando):**
- Confirma la corrección

**Then (Entonces):**
- El sistema mantiene el registro original en el log con su timestamp de creación
- Agrega un segundo registro vinculado al primero indicando que fue corregido, con el UserID del auxiliar y el timestamp exacto de la corrección
- Ambos registros son inmutables e independientes

---

## Resultado esperado (Then)

Ver sección **Then** en el extracto anterior del ERS. En automatización backend, el test asociado comprueba el contrato API/servicio equivalente o queda explícitamente marcado como pendiente si el criterio es solo UI, infraestructura o legalidad operativa fuera del alcance de pytest.

## Link directo al test

Ejecutar:

```bash
pytest tests/ers/test_gherkin_dynamic.py::test_RF012_S07 -v
```

Archivo de definición dinámica: [`tests/ers/test_gherkin_dynamic.py`](../../tests/ers/test_gherkin_dynamic.py)

Implementaciones concretas (cuando existan) pueden delegarse en módulos bajo `tests/ers/impl/`.

---

## Estado de automatización backend

Pendiente en backend: al ejecutar el test dinámico se aplicará `pytest.skip` con el motivo hasta que exista implementación.


<!-- file: RF012-S08.md -->

# Intento de eliminación o modificación de un registro del log

## Nombre del test

`tests/ers/test_gherkin_dynamic.py::test_RF012_S08`

## Propósito

Validar el criterio de aceptación Gherkin del ERS ICM para **RF012** — escenario 8.

## Requisito o caso de negocio asociado

- **Requisito:** `RF012` (ver `docs/requisitos/ERS_ICM_Requisitos.md`).
- **Fuente complementaria:** `docs/requisitos/ICM_Informe_Elicitacion_v2_plus.docx.md` (contexto de negocio y BR cuando aplica).

## Inputs (Given / When — extracto ERS)

**Given (Dado que):**
- Cualquier usuario autenticado, independientemente de su rol, intenta modificar o eliminar un registro existente en el log

**When (Cuando):**
- Ejecuta esa acción por cualquier vía disponible en la interfaz

**Then (Entonces):**
- El sistema rechaza la operación de forma absoluta
- Muestra un mensaje indicando que los registros de auditoría son inmutables
- Registra en el propio log el intento fallido de modificación con UserID y timestamp

# **6. Requisitos No Funcionales**

Los requisitos no funcionales (RNF) definen los atributos de calidad que el sistema debe cumplir para ser operativamente viable en el contexto real de ICM. A diferencia de los requisitos funcionales, que describen qué hace el sistema, los requisitos no funcionales describen cómo debe hacerlo: con qué velocidad, con qué nivel de seguridad, con qué grado de disponibilidad. Estos requisitos son transversales a todos los módulos y deben ser considerados desde la fase de diseño arquitectónico, no como consideraciones tardías de optimización.

## Resultado esperado (Then)

Ver sección **Then** en el extracto anterior del ERS. En automatización backend, el test asociado comprueba el contrato API/servicio equivalente o queda explícitamente marcado como pendiente si el criterio es solo UI, infraestructura o legalidad operativa fuera del alcance de pytest.

## Link directo al test

Ejecutar:

```bash
pytest tests/ers/test_gherkin_dynamic.py::test_RF012_S08 -v
```

Archivo de definición dinámica: [`tests/ers/test_gherkin_dynamic.py`](../../tests/ers/test_gherkin_dynamic.py)

Implementaciones concretas (cuando existan) pueden delegarse en módulos bajo `tests/ers/impl/`.

---

## Estado de automatización backend

Pendiente en backend: al ejecutar el test dinámico se aplicará `pytest.skip` con el motivo hasta que exista implementación.


<!-- file: RNF001-S01.md -->

# Operario completa un flujo de despacho sin formación técnica previa

## Nombre del test

`tests/ers/test_gherkin_dynamic.py::test_RNF001_S01`

## Propósito

Validar el criterio de aceptación Gherkin del ERS ICM para **RNF001** — escenario 1.

## Requisito o caso de negocio asociado

- **Requisito:** `RNF001` (ver `docs/requisitos/ERS_ICM_Requisitos.md`).
- **Fuente complementaria:** `docs/requisitos/ICM_Informe_Elicitacion_v2_plus.docx.md` (contexto de negocio y BR cuando aplica).

## Inputs (Given / When — extracto ERS)

**Given (Dado que):**
- Un Auxiliar de Despacho accede al sistema por primera vez tras una inducción operativa básica de no más de 30 minutos

**When (Cuando):**
- Intenta registrar un despacho estándar de principio a fin

**Then (Entonces):**
- El operario completa el flujo sin necesidad de consultar documentación técnica ni solicitar asistencia
- El sistema guía al usuario paso a paso dentro del flujo sin ambigüedad sobre cuál es la siguiente acción requerida

---

## Resultado esperado (Then)

Ver sección **Then** en el extracto anterior del ERS. En automatización backend, el test asociado comprueba el contrato API/servicio equivalente o queda explícitamente marcado como pendiente si el criterio es solo UI, infraestructura o legalidad operativa fuera del alcance de pytest.

## Link directo al test

Ejecutar:

```bash
pytest tests/ers/test_gherkin_dynamic.py::test_RNF001_S01 -v
```

Archivo de definición dinámica: [`tests/ers/test_gherkin_dynamic.py`](../../tests/ers/test_gherkin_dynamic.py)

Implementaciones concretas (cuando existan) pueden delegarse en módulos bajo `tests/ers/impl/`.

---

## Estado de automatización backend

Pendiente en backend: al ejecutar el test dinámico se aplicará `pytest.skip` con el motivo hasta que exista implementación.


<!-- file: RNF001-S02.md -->

# La interfaz responde correctamente en dispositivos móviles y tabletas

## Nombre del test

`tests/ers/test_gherkin_dynamic.py::test_RNF001_S02`

## Propósito

Validar el criterio de aceptación Gherkin del ERS ICM para **RNF001** — escenario 2.

## Requisito o caso de negocio asociado

- **Requisito:** `RNF001` (ver `docs/requisitos/ERS_ICM_Requisitos.md`).
- **Fuente complementaria:** `docs/requisitos/ICM_Informe_Elicitacion_v2_plus.docx.md` (contexto de negocio y BR cuando aplica).

## Inputs (Given / When — extracto ERS)

**Given (Dado que):**
- Un operario accede al sistema desde una tableta o un teléfono inteligente

**When (Cuando):**
- Navega por cualquier módulo disponible para su rol

**Then (Entonces):**
- Todos los elementos de la interfaz se adaptan al tamaño de pantalla del dispositivo sin pérdida de funcionalidad
- Los botones y campos son suficientemente grandes para ser operados con precisión táctil
- Ningún elemento crítico queda oculto o inaccesible en resoluciones móviles

---

## Resultado esperado (Then)

Ver sección **Then** en el extracto anterior del ERS. En automatización backend, el test asociado comprueba el contrato API/servicio equivalente o queda explícitamente marcado como pendiente si el criterio es solo UI, infraestructura o legalidad operativa fuera del alcance de pytest.

## Link directo al test

Ejecutar:

```bash
pytest tests/ers/test_gherkin_dynamic.py::test_RNF001_S02 -v
```

Archivo de definición dinámica: [`tests/ers/test_gherkin_dynamic.py`](../../tests/ers/test_gherkin_dynamic.py)

Implementaciones concretas (cuando existan) pueden delegarse en módulos bajo `tests/ers/impl/`.

---

## Estado de automatización backend

Pendiente en backend: al ejecutar el test dinámico se aplicará `pytest.skip` con el motivo hasta que exista implementación.


<!-- file: RNF001-S03.md -->

# La búsqueda de productos es igualmente eficiente por cualquier vía

## Nombre del test

`tests/ers/test_gherkin_dynamic.py::test_RNF001_S03`

## Propósito

Validar el criterio de aceptación Gherkin del ERS ICM para **RNF001** — escenario 3.

## Requisito o caso de negocio asociado

- **Requisito:** `RNF001` (ver `docs/requisitos/ERS_ICM_Requisitos.md`).
- **Fuente complementaria:** `docs/requisitos/ICM_Informe_Elicitacion_v2_plus.docx.md` (contexto de negocio y BR cuando aplica).

## Inputs (Given / When — extracto ERS)

**Given (Dado que):**
- Un operario necesita localizar un producto durante la atención a un cliente

**When (Cuando):**
- Busca el producto ya sea por nombre, SKU o código de barras

**Then (Entonces):**
- El sistema devuelve resultados relevantes en menos de 2 segundos por cualquiera de las tres vías de búsqueda
- El operario puede identificar y seleccionar el producto correcto sin navegar por más de dos pantallas desde el punto de búsqueda

## Resultado esperado (Then)

Ver sección **Then** en el extracto anterior del ERS. En automatización backend, el test asociado comprueba el contrato API/servicio equivalente o queda explícitamente marcado como pendiente si el criterio es solo UI, infraestructura o legalidad operativa fuera del alcance de pytest.

## Link directo al test

Ejecutar:

```bash
pytest tests/ers/test_gherkin_dynamic.py::test_RNF001_S03 -v
```

Archivo de definición dinámica: [`tests/ers/test_gherkin_dynamic.py`](../../tests/ers/test_gherkin_dynamic.py)

Implementaciones concretas (cuando existan) pueden delegarse en módulos bajo `tests/ers/impl/`.

---

## Estado de automatización backend

Pendiente en backend: al ejecutar el test dinámico se aplicará `pytest.skip` con el motivo hasta que exista implementación.


<!-- file: RNF002-S01.md -->

# El sistema permanece disponible durante las franjas críticas de operación

## Nombre del test

`tests/ers/test_gherkin_dynamic.py::test_RNF002_S01`

## Propósito

Validar el criterio de aceptación Gherkin del ERS ICM para **RNF002** — escenario 1.

## Requisito o caso de negocio asociado

- **Requisito:** `RNF002` (ver `docs/requisitos/ERS_ICM_Requisitos.md`).
- **Fuente complementaria:** `docs/requisitos/ICM_Informe_Elicitacion_v2_plus.docx.md` (contexto de negocio y BR cuando aplica).

## Inputs (Given / When — extracto ERS)

**Given (Dado que):**
- El sistema está desplegado en el entorno de producción

**When (Cuando):**
- Un Auxiliar de Despacho intenta acceder al sistema dentro de su franja horaria

**Then (Entonces):**
- El sistema responde y permite el acceso sin interrupciones
- Cualquier operación iniciada dentro de la franja puede completarse sin que el sistema la interrumpa por inactividad o caída durante esa ventana

---

## Resultado esperado (Then)

Ver sección **Then** en el extracto anterior del ERS. En automatización backend, el test asociado comprueba el contrato API/servicio equivalente o queda explícitamente marcado como pendiente si el criterio es solo UI, infraestructura o legalidad operativa fuera del alcance de pytest.

## Link directo al test

Ejecutar:

```bash
pytest tests/ers/test_gherkin_dynamic.py::test_RNF002_S01 -v
```

Archivo de definición dinámica: [`tests/ers/test_gherkin_dynamic.py`](../../tests/ers/test_gherkin_dynamic.py)

Implementaciones concretas (cuando existan) pueden delegarse en módulos bajo `tests/ers/impl/`.

---

## Estado de automatización backend

Pendiente en backend: al ejecutar el test dinámico se aplicará `pytest.skip` con el motivo hasta que exista implementación.


<!-- file: RNF002-S02.md -->

# El Almacenista puede acceder al sistema en cualquier momento del día

## Nombre del test

`tests/ers/test_gherkin_dynamic.py::test_RNF002_S02`

## Propósito

Validar el criterio de aceptación Gherkin del ERS ICM para **RNF002** — escenario 2.

## Requisito o caso de negocio asociado

- **Requisito:** `RNF002` (ver `docs/requisitos/ERS_ICM_Requisitos.md`).
- **Fuente complementaria:** `docs/requisitos/ICM_Informe_Elicitacion_v2_plus.docx.md` (contexto de negocio y BR cuando aplica).

## Inputs (Given / When — extracto ERS)

**Given (Dado que):**
- El sistema está desplegado en producción

**When (Cuando):**
- El Almacenista intenta acceder al sistema fuera del horario laboral convencional

**Then (Entonces):**
- El sistema responde y otorga acceso completo sin restricciones horarias
- Todas las funcionalidades del rol Almacenista están disponibles

---

## Resultado esperado (Then)

Ver sección **Then** en el extracto anterior del ERS. En automatización backend, el test asociado comprueba el contrato API/servicio equivalente o queda explícitamente marcado como pendiente si el criterio es solo UI, infraestructura o legalidad operativa fuera del alcance de pytest.

## Link directo al test

Ejecutar:

```bash
pytest tests/ers/test_gherkin_dynamic.py::test_RNF002_S02 -v
```

Archivo de definición dinámica: [`tests/ers/test_gherkin_dynamic.py`](../../tests/ers/test_gherkin_dynamic.py)

Implementaciones concretas (cuando existan) pueden delegarse en módulos bajo `tests/ers/impl/`.

---

## Estado de automatización backend

Pendiente en backend: al ejecutar el test dinámico se aplicará `pytest.skip` con el motivo hasta que exista implementación.


<!-- file: RNF002-S03.md -->

# El sistema notifica adecuadamente ante una interrupción no planificada

## Nombre del test

`tests/ers/test_gherkin_dynamic.py::test_RNF002_S03`

## Propósito

Validar el criterio de aceptación Gherkin del ERS ICM para **RNF002** — escenario 3.

## Requisito o caso de negocio asociado

- **Requisito:** `RNF002` (ver `docs/requisitos/ERS_ICM_Requisitos.md`).
- **Fuente complementaria:** `docs/requisitos/ICM_Informe_Elicitacion_v2_plus.docx.md` (contexto de negocio y BR cuando aplica).

## Inputs (Given / When — extracto ERS)

**Given (Dado que):**
- Ocurre una interrupción no planificada del sistema

**When (Cuando):**
- Un usuario intenta acceder durante esa interrupción

**Then (Entonces):**
- El sistema muestra un mensaje claro indicando que el servicio no está disponible
- El mensaje no expone detalles técnicos internos del error al usuario final

## Resultado esperado (Then)

Ver sección **Then** en el extracto anterior del ERS. En automatización backend, el test asociado comprueba el contrato API/servicio equivalente o queda explícitamente marcado como pendiente si el criterio es solo UI, infraestructura o legalidad operativa fuera del alcance de pytest.

## Link directo al test

Ejecutar:

```bash
pytest tests/ers/test_gherkin_dynamic.py::test_RNF002_S03 -v
```

Archivo de definición dinámica: [`tests/ers/test_gherkin_dynamic.py`](../../tests/ers/test_gherkin_dynamic.py)

Implementaciones concretas (cuando existan) pueden delegarse en módulos bajo `tests/ers/impl/`.

---

## Estado de automatización backend

Pendiente en backend: al ejecutar el test dinámico se aplicará `pytest.skip` con el motivo hasta que exista implementación.


<!-- file: RNF003-S01.md -->

# Los datos sensibles viajan cifrados entre el cliente y el servidor

## Nombre del test

`tests/ers/test_gherkin_dynamic.py::test_RNF003_S01`

## Propósito

Validar el criterio de aceptación Gherkin del ERS ICM para **RNF003** — escenario 1.

## Requisito o caso de negocio asociado

- **Requisito:** `RNF003` (ver `docs/requisitos/ERS_ICM_Requisitos.md`).
- **Fuente complementaria:** `docs/requisitos/ICM_Informe_Elicitacion_v2_plus.docx.md` (contexto de negocio y BR cuando aplica).

## Inputs (Given / When — extracto ERS)

**Given (Dado que):**
- Cualquier usuario realiza una operación en el sistema que implica transmisión de datos

**When (Cuando):**
- Esa operación genera tráfico de red entre el frontend y el backend

**Then (Entonces):**
- Toda la comunicación ocurre exclusivamente sobre HTTPS
- Ningún dato sensible se transmite en texto plano bajo ninguna circunstancia

---

## Resultado esperado (Then)

Ver sección **Then** en el extracto anterior del ERS. En automatización backend, el test asociado comprueba el contrato API/servicio equivalente o queda explícitamente marcado como pendiente si el criterio es solo UI, infraestructura o legalidad operativa fuera del alcance de pytest.

## Link directo al test

Ejecutar:

```bash
pytest tests/ers/test_gherkin_dynamic.py::test_RNF003_S01 -v
```

Archivo de definición dinámica: [`tests/ers/test_gherkin_dynamic.py`](../../tests/ers/test_gherkin_dynamic.py)

Implementaciones concretas (cuando existan) pueden delegarse en módulos bajo `tests/ers/impl/`.

---

## Estado de automatización backend

Pendiente en backend: al ejecutar el test dinámico se aplicará `pytest.skip` con el motivo hasta que exista implementación.


<!-- file: RNF003-S02.md -->

# Un usuario no puede acceder a funcionalidades fuera de su rol

## Nombre del test

`tests/ers/test_gherkin_dynamic.py::test_RNF003_S02`

## Propósito

Validar el criterio de aceptación Gherkin del ERS ICM para **RNF003** — escenario 2.

## Requisito o caso de negocio asociado

- **Requisito:** `RNF003` (ver `docs/requisitos/ERS_ICM_Requisitos.md`).
- **Fuente complementaria:** `docs/requisitos/ICM_Informe_Elicitacion_v2_plus.docx.md` (contexto de negocio y BR cuando aplica).

## Inputs (Given / When — extracto ERS)

**Given (Dado que):**
- Cualquier usuario está autenticado en el sistema

**When (Cuando):**
- Intenta acceder a una ruta, vista o endpoint que corresponde a un rol distinto al suyo, ya sea manipulando la URL directamente o mediante cualquier otro mecanismo

**Then (Entonces):**
- El sistema rechaza la solicitud con un error de autorización
- No expone ningún dato ni funcionalidad del rol restringido
- El intento queda registrado en el log de auditoría

---

## Resultado esperado (Then)

Ver sección **Then** en el extracto anterior del ERS. En automatización backend, el test asociado comprueba el contrato API/servicio equivalente o queda explícitamente marcado como pendiente si el criterio es solo UI, infraestructura o legalidad operativa fuera del alcance de pytest.

## Link directo al test

Ejecutar:

```bash
pytest tests/ers/test_gherkin_dynamic.py::test_RNF003_S02 -v
```

Archivo de definición dinámica: [`tests/ers/test_gherkin_dynamic.py`](../../tests/ers/test_gherkin_dynamic.py)

Implementaciones concretas (cuando existan) pueden delegarse en módulos bajo `tests/ers/impl/`.

---

## Estado de automatización backend

Implementada en `tests/ers/gherkin_impl.py` (comprueba API/servicios equivalentes al Then del ERS).


<!-- file: RNF003-S03.md -->

# Las contraseñas de los usuarios se almacenan de forma segura

## Nombre del test

`tests/ers/test_gherkin_dynamic.py::test_RNF003_S03`

## Propósito

Validar el criterio de aceptación Gherkin del ERS ICM para **RNF003** — escenario 3.

## Requisito o caso de negocio asociado

- **Requisito:** `RNF003` (ver `docs/requisitos/ERS_ICM_Requisitos.md`).
- **Fuente complementaria:** `docs/requisitos/ICM_Informe_Elicitacion_v2_plus.docx.md` (contexto de negocio y BR cuando aplica).

## Inputs (Given / When — extracto ERS)

**Given (Dado que):**
- El Almacenista crea o modifica la contraseña de cualquier usuario

**When (Cuando):**
- El sistema procesa y almacena esa contraseña

**Then (Entonces):**
- La contraseña se almacena en la base de datos usando un algoritmo de hashing seguro con sal (por ejemplo bcrypt)
- En ningún punto del sistema la contraseña es almacenada ni transmitida en texto plano

---

## Resultado esperado (Then)

Ver sección **Then** en el extracto anterior del ERS. En automatización backend, el test asociado comprueba el contrato API/servicio equivalente o queda explícitamente marcado como pendiente si el criterio es solo UI, infraestructura o legalidad operativa fuera del alcance de pytest.

## Link directo al test

Ejecutar:

```bash
pytest tests/ers/test_gherkin_dynamic.py::test_RNF003_S03 -v
```

Archivo de definición dinámica: [`tests/ers/test_gherkin_dynamic.py`](../../tests/ers/test_gherkin_dynamic.py)

Implementaciones concretas (cuando existan) pueden delegarse en módulos bajo `tests/ers/impl/`.

---

## Estado de automatización backend

Implementada en `tests/ers/gherkin_impl.py` (comprueba API/servicios equivalentes al Then del ERS).


<!-- file: RNF003-S04.md -->

# Ningún usuario puede modificar ni eliminar un registro histórico

## Nombre del test

`tests/ers/test_gherkin_dynamic.py::test_RNF003_S04`

## Propósito

Validar el criterio de aceptación Gherkin del ERS ICM para **RNF003** — escenario 4.

## Requisito o caso de negocio asociado

- **Requisito:** `RNF003` (ver `docs/requisitos/ERS_ICM_Requisitos.md`).
- **Fuente complementaria:** `docs/requisitos/ICM_Informe_Elicitacion_v2_plus.docx.md` (contexto de negocio y BR cuando aplica).

## Inputs (Given / When — extracto ERS)

**Given (Dado que):**
- Cualquier usuario autenticado, independientemente de su rol, intenta modificar o eliminar un registro del log o un movimiento ya confirmado

**When (Cuando):**
- Ejecuta o intenta ejecutar esa acción

**Then (Entonces):**
- El sistema rechaza la operación de forma absoluta
- El registro original permanece intacto e inalterado
- El intento fallido queda registrado en el log con UserID y timestamp

## Resultado esperado (Then)

Ver sección **Then** en el extracto anterior del ERS. En automatización backend, el test asociado comprueba el contrato API/servicio equivalente o queda explícitamente marcado como pendiente si el criterio es solo UI, infraestructura o legalidad operativa fuera del alcance de pytest.

## Link directo al test

Ejecutar:

```bash
pytest tests/ers/test_gherkin_dynamic.py::test_RNF003_S04 -v
```

Archivo de definición dinámica: [`tests/ers/test_gherkin_dynamic.py`](../../tests/ers/test_gherkin_dynamic.py)

Implementaciones concretas (cuando existan) pueden delegarse en módulos bajo `tests/ers/impl/`.

---

## Estado de automatización backend

Pendiente en backend: al ejecutar el test dinámico se aplicará `pytest.skip` con el motivo hasta que exista implementación.


<!-- file: RNF004-S01.md -->

# Consulta de stock de un producto responde dentro del umbral definido

## Nombre del test

`tests/ers/test_gherkin_dynamic.py::test_RNF004_S01`

## Propósito

Validar el criterio de aceptación Gherkin del ERS ICM para **RNF004** — escenario 1.

## Requisito o caso de negocio asociado

- **Requisito:** `RNF004` (ver `docs/requisitos/ERS_ICM_Requisitos.md`).
- **Fuente complementaria:** `docs/requisitos/ICM_Informe_Elicitacion_v2_plus.docx.md` (contexto de negocio y BR cuando aplica).

## Inputs (Given / When — extracto ERS)

**Given (Dado que):**
- El sistema está operando bajo condiciones normales de uso
- El catálogo contiene entre 220 y 250 productos registrados

**When (Cuando):**
- Cualquier usuario realiza una consulta de stock por nombre, SKU o código de barras

**Then (Entonces):**
- El sistema devuelve el resultado con el stock por ubicación y el stock total consolidado en un tiempo no mayor a 2 segundos

---

## Resultado esperado (Then)

Ver sección **Then** en el extracto anterior del ERS. En automatización backend, el test asociado comprueba el contrato API/servicio equivalente o queda explícitamente marcado como pendiente si el criterio es solo UI, infraestructura o legalidad operativa fuera del alcance de pytest.

## Link directo al test

Ejecutar:

```bash
pytest tests/ers/test_gherkin_dynamic.py::test_RNF004_S01 -v
```

Archivo de definición dinámica: [`tests/ers/test_gherkin_dynamic.py`](../../tests/ers/test_gherkin_dynamic.py)

Implementaciones concretas (cuando existan) pueden delegarse en módulos bajo `tests/ers/impl/`.

---

## Estado de automatización backend

Implementada en `tests/ers/gherkin_impl.py` (comprueba API/servicios equivalentes al Then del ERS).


<!-- file: RNF004-S02.md -->

# El registro de un movimiento de inventario se confirma dentro de un tiempo razonable

## Nombre del test

`tests/ers/test_gherkin_dynamic.py::test_RNF004_S02`

## Propósito

Validar el criterio de aceptación Gherkin del ERS ICM para **RNF004** — escenario 2.

## Requisito o caso de negocio asociado

- **Requisito:** `RNF004` (ver `docs/requisitos/ERS_ICM_Requisitos.md`).
- **Fuente complementaria:** `docs/requisitos/ICM_Informe_Elicitacion_v2_plus.docx.md` (contexto de negocio y BR cuando aplica).

## Inputs (Given / When — extracto ERS)

**Given (Dado que):**
- Un operario completa y confirma un movimiento de inventario

**When (Cuando):**
- El sistema procesa la confirmación

**Then (Entonces):**
- El sistema actualiza el stock, genera el log de auditoría y muestra la confirmación al usuario en un tiempo no mayor a 3 segundos bajo condiciones normales de uso

---

## Resultado esperado (Then)

Ver sección **Then** en el extracto anterior del ERS. En automatización backend, el test asociado comprueba el contrato API/servicio equivalente o queda explícitamente marcado como pendiente si el criterio es solo UI, infraestructura o legalidad operativa fuera del alcance de pytest.

## Link directo al test

Ejecutar:

```bash
pytest tests/ers/test_gherkin_dynamic.py::test_RNF004_S02 -v
```

Archivo de definición dinámica: [`tests/ers/test_gherkin_dynamic.py`](../../tests/ers/test_gherkin_dynamic.py)

Implementaciones concretas (cuando existan) pueden delegarse en módulos bajo `tests/ers/impl/`.

---

## Estado de automatización backend

Pendiente en backend: al ejecutar el test dinámico se aplicará `pytest.skip` con el motivo hasta que exista implementación.


<!-- file: RNF004-S03.md -->

# El sistema mantiene el rendimiento bajo uso simultáneo de los tres roles

## Nombre del test

`tests/ers/test_gherkin_dynamic.py::test_RNF004_S03`

## Propósito

Validar el criterio de aceptación Gherkin del ERS ICM para **RNF004** — escenario 3.

## Requisito o caso de negocio asociado

- **Requisito:** `RNF004` (ver `docs/requisitos/ERS_ICM_Requisitos.md`).
- **Fuente complementaria:** `docs/requisitos/ICM_Informe_Elicitacion_v2_plus.docx.md` (contexto de negocio y BR cuando aplica).

## Inputs (Given / When — extracto ERS)

**Given (Dado que):**
- El Almacenista, un Auxiliar de Despacho y el Administrador están usando el sistema de forma simultánea

**When (Cuando):**
- Cada uno ejecuta operaciones propias de su rol al mismo tiempo

**Then (Entonces):**
- El tiempo de respuesta de cada operación no se degrada más allá de los umbrales definidos para cada tipo de consulta
- Ningún usuario experimenta bloqueos ni timeouts durante el uso concurrente normal

## Resultado esperado (Then)

Ver sección **Then** en el extracto anterior del ERS. En automatización backend, el test asociado comprueba el contrato API/servicio equivalente o queda explícitamente marcado como pendiente si el criterio es solo UI, infraestructura o legalidad operativa fuera del alcance de pytest.

## Link directo al test

Ejecutar:

```bash
pytest tests/ers/test_gherkin_dynamic.py::test_RNF004_S03 -v
```

Archivo de definición dinámica: [`tests/ers/test_gherkin_dynamic.py`](../../tests/ers/test_gherkin_dynamic.py)

Implementaciones concretas (cuando existan) pueden delegarse en módulos bajo `tests/ers/impl/`.

---

## Estado de automatización backend

Pendiente en backend: al ejecutar el test dinámico se aplicará `pytest.skip` con el motivo hasta que exista implementación.


<!-- file: RNF005-S01.md -->

# La arquitectura del sistema separa frontend y backend con APIs REST

## Nombre del test

`tests/ers/test_gherkin_dynamic.py::test_RNF005_S01`

## Propósito

Validar el criterio de aceptación Gherkin del ERS ICM para **RNF005** — escenario 1.

## Requisito o caso de negocio asociado

- **Requisito:** `RNF005` (ver `docs/requisitos/ERS_ICM_Requisitos.md`).
- **Fuente complementaria:** `docs/requisitos/ICM_Informe_Elicitacion_v2_plus.docx.md` (contexto de negocio y BR cuando aplica).

## Inputs (Given / When — extracto ERS)

**Given (Dado que):**
- El sistema está implementado y desplegado

**When (Cuando):**
- Se analiza la estructura del proyecto en el repositorio

**Then (Entonces):**
- Existe una separación clara entre el proyecto de frontend y el de backend como unidades independientes
- Toda la comunicación entre frontend y backend ocurre exclusivamente a través de endpoints REST documentados
- No existe lógica de negocio embebida directamente en el frontend

---

## Resultado esperado (Then)

Ver sección **Then** en el extracto anterior del ERS. En automatización backend, el test asociado comprueba el contrato API/servicio equivalente o queda explícitamente marcado como pendiente si el criterio es solo UI, infraestructura o legalidad operativa fuera del alcance de pytest.

## Link directo al test

Ejecutar:

```bash
pytest tests/ers/test_gherkin_dynamic.py::test_RNF005_S01 -v
```

Archivo de definición dinámica: [`tests/ers/test_gherkin_dynamic.py`](../../tests/ers/test_gherkin_dynamic.py)

Implementaciones concretas (cuando existan) pueden delegarse en módulos bajo `tests/ers/impl/`.

---

## Estado de automatización backend

Implementada en `tests/ers/gherkin_impl.py` (comprueba API/servicios equivalentes al Then del ERS).


<!-- file: RNF005-S02.md -->

# Los endpoints del backend están documentados con Swagger

## Nombre del test

`tests/ers/test_gherkin_dynamic.py::test_RNF005_S02`

## Propósito

Validar el criterio de aceptación Gherkin del ERS ICM para **RNF005** — escenario 2.

## Requisito o caso de negocio asociado

- **Requisito:** `RNF005` (ver `docs/requisitos/ERS_ICM_Requisitos.md`).
- **Fuente complementaria:** `docs/requisitos/ICM_Informe_Elicitacion_v2_plus.docx.md` (contexto de negocio y BR cuando aplica).

## Inputs (Given / When — extracto ERS)

**Given (Dado que):**
- El sistema está desplegado en el entorno de producción

**When (Cuando):**
- Se accede a la ruta de documentación Swagger del backend

**Then (Entonces):**
- Todos los endpoints disponibles están listados y documentados con su método HTTP, parámetros esperados, cuerpo de la solicitud y estructura de la respuesta
- La documentación refleja el estado actual del backend sin endpoints faltantes ni documentación desactualizada

---

## Resultado esperado (Then)

Ver sección **Then** en el extracto anterior del ERS. En automatización backend, el test asociado comprueba el contrato API/servicio equivalente o queda explícitamente marcado como pendiente si el criterio es solo UI, infraestructura o legalidad operativa fuera del alcance de pytest.

## Link directo al test

Ejecutar:

```bash
pytest tests/ers/test_gherkin_dynamic.py::test_RNF005_S02 -v
```

Archivo de definición dinámica: [`tests/ers/test_gherkin_dynamic.py`](../../tests/ers/test_gherkin_dynamic.py)

Implementaciones concretas (cuando existan) pueden delegarse en módulos bajo `tests/ers/impl/`.

---

## Estado de automatización backend

Pendiente en backend: al ejecutar el test dinámico se aplicará `pytest.skip` con el motivo hasta que exista implementación.


<!-- file: RNF005-S03.md -->

# El código cumple con los principios SOLID verificables

## Nombre del test

`tests/ers/test_gherkin_dynamic.py::test_RNF005_S03`

## Propósito

Validar el criterio de aceptación Gherkin del ERS ICM para **RNF005** — escenario 3.

## Requisito o caso de negocio asociado

- **Requisito:** `RNF005` (ver `docs/requisitos/ERS_ICM_Requisitos.md`).
- **Fuente complementaria:** `docs/requisitos/ICM_Informe_Elicitacion_v2_plus.docx.md` (contexto de negocio y BR cuando aplica).

## Inputs (Given / When — extracto ERS)

**Given (Dado que):**
- El equipo de Arquitectura de Software I realiza la evaluación formal del Corte 3

**When (Cuando):**
- Analiza la estructura de clases, servicios y módulos del backend

**Then (Entonces):**
- Cada clase o componente tiene una única responsabilidad claramente definida (SRP)
- Es posible extender el comportamiento del sistema sin modificar clases existentes (OCP)
- El sistema no presenta dependencias directas entre módulos de alto y bajo nivel (DIP)
- El informe de evaluación no identifica violaciones críticas no justificadas a ninguno de los cinco principios SOLID

## Resultado esperado (Then)

Ver sección **Then** en el extracto anterior del ERS. En automatización backend, el test asociado comprueba el contrato API/servicio equivalente o queda explícitamente marcado como pendiente si el criterio es solo UI, infraestructura o legalidad operativa fuera del alcance de pytest.

## Link directo al test

Ejecutar:

```bash
pytest tests/ers/test_gherkin_dynamic.py::test_RNF005_S03 -v
```

Archivo de definición dinámica: [`tests/ers/test_gherkin_dynamic.py`](../../tests/ers/test_gherkin_dynamic.py)

Implementaciones concretas (cuando existan) pueden delegarse en módulos bajo `tests/ers/impl/`.

---

## Estado de automatización backend

Pendiente en backend: al ejecutar el test dinámico se aplicará `pytest.skip` con el motivo hasta que exista implementación.


<!-- file: RNF006-S01.md -->

# El sistema captura datos personales de clientes mayoristas con aviso de privacidad

## Nombre del test

`tests/ers/test_gherkin_dynamic.py::test_RNF006_S01`

## Propósito

Validar el criterio de aceptación Gherkin del ERS ICM para **RNF006** — escenario 1.

## Requisito o caso de negocio asociado

- **Requisito:** `RNF006` (ver `docs/requisitos/ERS_ICM_Requisitos.md`).
- **Fuente complementaria:** `docs/requisitos/ICM_Informe_Elicitacion_v2_plus.docx.md` (contexto de negocio y BR cuando aplica).

## Inputs (Given / When — extracto ERS)

**Given (Dado que):**
- Un operario registra los datos de un cliente mayorista durante un despacho

**When (Cuando):**
- Completa el formulario con nombre, correo, teléfono y dirección

**Then (Entonces):**
- El sistema informa al operario, antes de guardar los datos, que esa información será tratada conforme a la política de privacidad de ICM bajo la Ley 1581 de 2012
- No almacena los datos del cliente sin que ese aviso haya sido presentado en el flujo

---

## Resultado esperado (Then)

Ver sección **Then** en el extracto anterior del ERS. En automatización backend, el test asociado comprueba el contrato API/servicio equivalente o queda explícitamente marcado como pendiente si el criterio es solo UI, infraestructura o legalidad operativa fuera del alcance de pytest.

## Link directo al test

Ejecutar:

```bash
pytest tests/ers/test_gherkin_dynamic.py::test_RNF006_S01 -v
```

Archivo de definición dinámica: [`tests/ers/test_gherkin_dynamic.py`](../../tests/ers/test_gherkin_dynamic.py)

Implementaciones concretas (cuando existan) pueden delegarse en módulos bajo `tests/ers/impl/`.

---

## Estado de automatización backend

Implementada en `tests/ers/gherkin_impl.py` (comprueba API/servicios equivalentes al Then del ERS).


<!-- file: RNF006-S02.md -->

# Los datos personales de clientes no son accesibles para el Auxiliar de Despacho fuera del contexto de su operación

## Nombre del test

`tests/ers/test_gherkin_dynamic.py::test_RNF006_S02`

## Propósito

Validar el criterio de aceptación Gherkin del ERS ICM para **RNF006** — escenario 2.

## Requisito o caso de negocio asociado

- **Requisito:** `RNF006` (ver `docs/requisitos/ERS_ICM_Requisitos.md`).
- **Fuente complementaria:** `docs/requisitos/ICM_Informe_Elicitacion_v2_plus.docx.md` (contexto de negocio y BR cuando aplica).

## Inputs (Given / When — extracto ERS)

**Given (Dado que):**
- El sistema tiene almacenados datos personales de clientes mayoristas

**When (Cuando):**
- Un Auxiliar de Despacho intenta consultar el historial de clientes fuera del contexto de un despacho activo

**Then (Entonces):**
- El sistema no expone listados de datos personales de clientes a ese rol
- El acceso a esa información está restringido al Almacenista y al Administrador dentro del módulo de reportes

---

## Resultado esperado (Then)

Ver sección **Then** en el extracto anterior del ERS. En automatización backend, el test asociado comprueba el contrato API/servicio equivalente o queda explícitamente marcado como pendiente si el criterio es solo UI, infraestructura o legalidad operativa fuera del alcance de pytest.

## Link directo al test

Ejecutar:

```bash
pytest tests/ers/test_gherkin_dynamic.py::test_RNF006_S02 -v
```

Archivo de definición dinámica: [`tests/ers/test_gherkin_dynamic.py`](../../tests/ers/test_gherkin_dynamic.py)

Implementaciones concretas (cuando existan) pueden delegarse en módulos bajo `tests/ers/impl/`.

---

## Estado de automatización backend

Pendiente en backend: al ejecutar el test dinámico se aplicará `pytest.skip` con el motivo hasta que exista implementación.


<!-- file: RNF006-S03.md -->

# El equipo documenta la autorización de ICM antes de usar datos reales en pruebas

## Nombre del test

`tests/ers/test_gherkin_dynamic.py::test_RNF006_S03`

## Propósito

Validar el criterio de aceptación Gherkin del ERS ICM para **RNF006** — escenario 3.

## Requisito o caso de negocio asociado

- **Requisito:** `RNF006` (ver `docs/requisitos/ERS_ICM_Requisitos.md`).
- **Fuente complementaria:** `docs/requisitos/ICM_Informe_Elicitacion_v2_plus.docx.md` (contexto de negocio y BR cuando aplica).

## Inputs (Given / When — extracto ERS)

**Given (Dado que):**
- El equipo de desarrollo va a ejecutar pruebas de aceptación usando datos operativos reales de ICM en el Corte 3

**When (Cuando):**
- Se planifica la fase de pruebas de aceptación

**Then (Entonces):**
- El equipo debe contar con un documento de autorización expresa firmado por ICM que permita el uso de sus datos operativos en el contexto académico del proyecto
- Las pruebas con datos reales no deben ejecutarse hasta que esa autorización esté formalmente obtenida

# **7. Resumen de Trazabilidad Requisitos — Módulos**

La siguiente tabla presenta un resumen de todos los requisitos especificados en este documento, con su módulo de pertenencia y las reglas de negocio que les aplican directamente. Esta tabla constituye el punto de partida para la Matriz de Trazabilidad Requisitos-Pruebas que debe ser elaborada por la asignatura de Pruebas de Software como entregable del Corte 1.

| **ID** | **Nombre** | **Módulo** | **Reglas de Negocio** |
| --- | --- | --- | --- |
| RF-001 | Inicio de Sesión con Credenciales Únicas | Autenticación | BR-01, BR-03 |
| RF-002 | Gestión de Credenciales de Usuario | Autenticación | BR-01, BR-02 |
| RF-003 | Registro de Producto en el Catálogo (SKU) | Gestión de Inventario | BR-04, BR-11, BR-12, BR-13 |
| RF-004 | Consulta y Búsqueda de Inventario en Tiempo Real | Gestión de Inventario | BR-11, BR-13 |
| RF-005 | Recepción de Mercancía | Recepción de Mercancía | BR-04, BR-09, BR-10, BR-11, BR-13 |
| RF-006 | Despacho y Salidas de Inventario | Despacho y Salidas | BR-08, BR-10, BR-11, BR-13 |
| RF-007 | Movimientos Internos entre Ubicaciones | Movimientos Internos | BR-06, BR-10, BR-11 |
| RF-008 | Registro de Devoluciones de Productos | Devoluciones | BR-02, BR-05, BR-10 |
| RF-009 | Ajustes de Inventario | Ajustes de Inventario | BR-06, BR-07, BR-10, BR-11 |
| RF-010 | Reportes e Indicadores Operativos | Reportes e Indicadores | BR-10, BR-11, BR-13 |
| RF-011 | Alertas Proactivas del Sistema | Alertas Proactivas | BR-04, BR-10, BR-11 |
| RF-012 | Log de Auditoría y Trazabilidad | Auditoría y Trazabilidad | BR-01, BR-06, BR-07, BR-10 |
| RNF-001 | Usabilidad e Interfaz Intuitiva | Transversal | — |
| RNF-002 | Disponibilidad del Sistema | Transversal | BR-03 |
| RNF-003 | Seguridad e Integridad de Datos | Transversal | BR-01, BR-02, BR-10 |
| RNF-004 | Rendimiento en Consultas y Operaciones | Transversal | — |
| RNF-005 | Mantenibilidad y Estándares Técnicos | Transversal | — |
| RNF-006 | Cumplimiento Legal: Ley 1581 de 2012 | Transversal | — |

# **8. Conclusiones**

El presente documento centraliza la especificación completa de dieciocho requisitos —doce funcionales y seis no funcionales— para el sistema de gestión de inventario y operaciones de Import Corporal Medical. Cada requisito ha sido elaborado a partir de la información recogida durante el proceso de elicitación con los responsables operativos de ICM y alineado con las condiciones académicas del Proyecto Nuclear 3.

Los requisitos funcionales cubren la totalidad de los módulos identificados en la elicitación: autenticación y gestión de credenciales, gestión de inventario, recepción de mercancía, despacho y salidas, movimientos internos, devoluciones, ajustes de inventario, reportes e indicadores, alertas proactivas y auditoría. Los requisitos no funcionales complementan esta especificación con atributos de calidad medibles en usabilidad, disponibilidad, seguridad, rendimiento, mantenibilidad y cumplimiento legal.

La redacción de los criterios de aceptación en formato Gherkin responde a una decisión deliberada orientada a facilitar el trabajo de la asignatura de Pruebas de Software: cada escenario puede ser convertido directamente en un caso de prueba sin necesidad de reinterpretación, lo que reduce el margen de error entre lo que el sistema debe hacer y lo que efectivamente se verifica en las fases de prueba.

Este documento debe ser considerado un artefacto vivo durante el desarrollo del proyecto: cualquier cambio …

## Resultado esperado (Then)

Ver sección **Then** en el extracto anterior del ERS. En automatización backend, el test asociado comprueba el contrato API/servicio equivalente o queda explícitamente marcado como pendiente si el criterio es solo UI, infraestructura o legalidad operativa fuera del alcance de pytest.

## Link directo al test

Ejecutar:

```bash
pytest tests/ers/test_gherkin_dynamic.py::test_RNF006_S03 -v
```

Archivo de definición dinámica: [`tests/ers/test_gherkin_dynamic.py`](../../tests/ers/test_gherkin_dynamic.py)

Implementaciones concretas (cuando existan) pueden delegarse en módulos bajo `tests/ers/impl/`.

---

## Estado de automatización backend

Pendiente en backend: al ejecutar el test dinámico se aplicará `pytest.skip` con el motivo hasta que exista implementación.
