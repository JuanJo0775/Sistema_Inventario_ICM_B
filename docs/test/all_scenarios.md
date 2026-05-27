<!-- file: index.md -->

# Ãndice de escenarios Gherkin
| CÃ³digo | Escenario | Estado | Archivo |
|---|---|---|---|
| RNF006-S03 | El equipo documenta la autorizaciÃ³n de ICM antes de usar datos reales en pruebas | Implementado | [RNF006-S03.md](./RNF006-S03.md) |


<!-- file: RF001-S01.md -->

# Inicio de sesiÃ³n exitoso como Almacenista

## Nombre del test

`tests/ers/test_gherkin_dynamic.py::test_RF001_S01`

## PropÃ³sito

Validar el criterio de aceptaciÃ³n Gherkin del ERS ICM para **RF001** â€” escenario 1.

## Requisito o caso de negocio asociado

- **Requisito:** `RF001` (ver `docs/requisitos/ERS_ICM_Requisitos.md`).

## Inputs (Given / When â€” extracto ERS)

**Given (Dado que):**
- El usuario tiene un rol de "Almacenista"
- Sus credenciales estÃ¡n activas en el sistema

**When (Cuando):**
- Ingresa su nombre de usuario y contraseÃ±a correctos
- Hace clic en "Iniciar sesiÃ³n"

**Then (Entonces):**
- El sistema autentica al usuario correctamente
- Lo redirige al dashboard del Almacenista
- Registra el evento de inicio de sesiÃ³n con el UserID y timestamp exacto

---

## Resultado esperado (Then)

Ver secciÃ³n **Then** en el extracto anterior del ERS. En automatizaciÃ³n backend, el test asociado comprueba el contrato API/servicio equivalente o queda explÃ­citamente marcado como pendiente si el criterio es solo UI, infraestructura o legalidad operativa fuera del alcance de pytest.

## Link directo al test

Ejecutar:

```bash
pytest tests/ers/test_gherkin_dynamic.py::test_RF001_S01 -v
```

Archivo de definiciÃ³n dinÃ¡mica: [`tests/ers/test_gherkin_dynamic.py`](../../tests/ers/test_gherkin_dynamic.py)

---

## Estado de automatizaciÃ³n backend

Implementada en `tests/ers/gherkin_impl.py` (comprueba API/servicios equivalentes al Then del ERS).


<!-- file: RF001-S02.md -->

# Inicio de sesiÃ³n exitoso como Auxiliar de Despacho dentro del horario permitido

## Nombre del test

`tests/ers/test_gherkin_dynamic.py::test_RF001_S02`

## PropÃ³sito

Validar el criterio de aceptaciÃ³n Gherkin del ERS ICM para **RF001** â€” escenario 2.

## Requisito o caso de negocio asociado

- **Requisito:** `RF001` (ver `docs/requisitos/ERS_ICM_Requisitos.md`).

## Inputs (Given / When â€” extracto ERS)

**Given (Dado que):**
- El usuario tiene rol "Auxiliar de Despacho"
- La hora actual estÃ¡ dentro de la franja 07:00â€“12:00 o 14:00â€“17:00
- Sus credenciales estÃ¡n activas

**When (Cuando):**
- Ingresa sus credenciales correctas y hace clic en "Iniciar sesiÃ³n"

**Then (Entonces):**
- El sistema lo autentica y redirige a la vista del Auxiliar de Despacho

---

## Resultado esperado (Then)

Ver secciÃ³n **Then** en el extracto anterior del ERS. En automatizaciÃ³n backend, el test asociado comprueba el contrato API/servicio equivalente o queda explÃ­citamente marcado como pendiente si el criterio es solo UI, infraestructura o legalidad operativa fuera del alcance de pytest.

## Link directo al test

Ejecutar:

```bash
pytest tests/ers/test_gherkin_dynamic.py::test_RF001_S02 -v
```

Archivo de definiciÃ³n dinÃ¡mica: [`tests/ers/test_gherkin_dynamic.py`](../../tests/ers/test_gherkin_dynamic.py)

---

## Estado de automatizaciÃ³n backend

Implementada en `tests/ers/gherkin_impl.py` (comprueba API/servicios equivalentes al Then del ERS).


<!-- file: RF001-S03.md -->

# Intento de inicio de sesiÃ³n de Auxiliar fuera del horario permitido

## Nombre del test

`tests/ers/test_gherkin_dynamic.py::test_RF001_S03`

## PropÃ³sito

Validar el criterio de aceptaciÃ³n Gherkin del ERS ICM para **RF001** â€” escenario 3.

## Requisito o caso de negocio asociado

- **Requisito:** `RF001` (ver `docs/requisitos/ERS_ICM_Requisitos.md`).

## Inputs (Given / When â€” extracto ERS)

**Given (Dado que):**
- El usuario tiene rol "Auxiliar de Despacho"
- La hora actual estÃ¡ fuera de las franjas 07:00â€“12:00 y 14:00â€“17:00

**When (Cuando):**
- Ingresa sus credenciales correctas y hace clic en "Iniciar sesiÃ³n"

**Then (Entonces):**
- El sistema bloquea el acceso
- Muestra un mensaje indicando que su horario de acceso no estÃ¡ activo
- No genera sesiÃ³n ni redirige a ninguna vista

---

## Resultado esperado (Then)

Ver secciÃ³n **Then** en el extracto anterior del ERS. En automatizaciÃ³n backend, el test asociado comprueba el contrato API/servicio equivalente o queda explÃ­citamente marcado como pendiente si el criterio es solo UI, infraestructura o legalidad operativa fuera del alcance de pytest.

## Link directo al test

Ejecutar:

```bash
pytest tests/ers/test_gherkin_dynamic.py::test_RF001_S03 -v
```

Archivo de definiciÃ³n dinÃ¡mica: [`tests/ers/test_gherkin_dynamic.py`](../../tests/ers/test_gherkin_dynamic.py)

---

## Estado de automatizaciÃ³n backend

Implementada en `tests/ers/gherkin_impl.py` (comprueba API/servicios equivalentes al Then del ERS).


<!-- file: RF001-S04.md -->

# Intento de inicio de sesiÃ³n con credenciales incorrectas

## Nombre del test

`tests/ers/test_gherkin_dynamic.py::test_RF001_S04`

## PropÃ³sito

Validar el criterio de aceptaciÃ³n Gherkin del ERS ICM para **RF001** â€” escenario 4.

## Requisito o caso de negocio asociado

- **Requisito:** `RF001` (ver `docs/requisitos/ERS_ICM_Requisitos.md`).

## Inputs (Given / When â€” extracto ERS)

**Given (Dado que):**
- Existe un usuario registrado en el sistema

**When (Cuando):**
- Ingresa una contraseÃ±a o nombre de usuario incorrecto

**Then (Entonces):**
- El sistema rechaza el acceso
- Muestra un mensaje de error genÃ©rico sin revelar si el fallo fue en usuario o contraseÃ±a
- No genera sesiÃ³n activa

---

## Resultado esperado (Then)

Ver secciÃ³n **Then** en el extracto anterior del ERS. En automatizaciÃ³n backend, el test asociado comprueba el contrato API/servicio equivalente o queda explÃ­citamente marcado como pendiente si el criterio es solo UI, infraestructura o legalidad operativa fuera del alcance de pytest.

## Link directo al test

Ejecutar:

```bash
pytest tests/ers/test_gherkin_dynamic.py::test_RF001_S04 -v
```

Archivo de definiciÃ³n dinÃ¡mica: [`tests/ers/test_gherkin_dynamic.py`](../../tests/ers/test_gherkin_dynamic.py)

---

## Estado de automatizaciÃ³n backend

Implementada en `tests/ers/gherkin_impl.py` (comprueba API/servicios equivalentes al Then del ERS).


<!-- file: RF001-S05.md -->

# Inicio de sesiÃ³n como Administrador fuera del horario laboral

## Nombre del test

`tests/ers/test_gherkin_dynamic.py::test_RF001_S05`

## PropÃ³sito

Validar el criterio de aceptaciÃ³n Gherkin del ERS ICM para **RF001** â€” escenario 5.

## Requisito o caso de negocio asociado

- **Requisito:** `RF001` (ver `docs/requisitos/ERS_ICM_Requisitos.md`).

## Inputs (Given / When â€” extracto ERS)

**Given (Dado que):**
- El usuario tiene rol "Administrador/Jefe"
- La hora actual es fuera del horario laboral convencional

**When (Cuando):**
- Ingresa sus credenciales correctas

**Then (Entonces):**
- El sistema lo autentica sin restricciÃ³n horaria
- Lo redirige al dashboard gerencial de solo lectura

## Resultado esperado (Then)

Ver secciÃ³n **Then** en el extracto anterior del ERS. En automatizaciÃ³n backend, el test asociado comprueba el contrato API/servicio equivalente o queda explÃ­citamente marcado como pendiente si el criterio es solo UI, infraestructura o legalidad operativa fuera del alcance de pytest.

## Link directo al test

Ejecutar:

```bash
pytest tests/ers/test_gherkin_dynamic.py::test_RF001_S05 -v
```

Archivo de definiciÃ³n dinÃ¡mica: [`tests/ers/test_gherkin_dynamic.py`](../../tests/ers/test_gherkin_dynamic.py)

---

## Estado de automatizaciÃ³n backend

Implementada en `tests/ers/gherkin_impl.py` (comprueba API/servicios equivalentes al Then del ERS).


<!-- file: RF002-S01.md -->

# Almacenista crea una nueva cuenta de usuario

## Nombre del test

`tests/ers/test_gherkin_dynamic.py::test_RF002_S01`

## PropÃ³sito

Validar el criterio de aceptaciÃ³n Gherkin del ERS ICM para **RF002** â€” escenario 1.

## Requisito o caso de negocio asociado

- **Requisito:** `RF002` (ver `docs/requisitos/ERS_ICM_Requisitos.md`).

## Inputs (Given / When â€” extracto ERS)

**Given (Dado que):**
- El usuario autenticado tiene rol "Almacenista"

**When (Cuando):**
- Accede al mÃ³dulo de gestiÃ³n de credenciales
- Completa el formulario con nombre de usuario, contraseÃ±a temporal y rol asignado
- Hace clic en "Crear usuario"

**Then (Entonces):**
- El sistema crea la cuenta con un UserID Ãºnico e irrepetible
- La cuenta queda activa y asociada al rol seleccionado
- El evento de creaciÃ³n queda registrado en el log de auditorÃ­a con el UserID del Almacenista y el timestamp

---

## Resultado esperado (Then)

Ver secciÃ³n **Then** en el extracto anterior del ERS. En automatizaciÃ³n backend, el test asociado comprueba el contrato API/servicio equivalente o queda explÃ­citamente marcado como pendiente si el criterio es solo UI, infraestructura o legalidad operativa fuera del alcance de pytest.

## Link directo al test

Ejecutar:

```bash
pytest tests/ers/test_gherkin_dynamic.py::test_RF002_S01 -v
```

Archivo de definiciÃ³n dinÃ¡mica: [`tests/ers/test_gherkin_dynamic.py`](../../tests/ers/test_gherkin_dynamic.py)

---

## Estado de automatizaciÃ³n backend

Implementada en `tests/ers/gherkin_impl.py` (comprueba API/servicios equivalentes al Then del ERS).


<!-- file: RF002-S02.md -->

# Almacenista modifica la contraseÃ±a de un usuario existente

## Nombre del test

`tests/ers/test_gherkin_dynamic.py::test_RF002_S02`

## PropÃ³sito

Validar el criterio de aceptaciÃ³n Gherkin del ERS ICM para **RF002** â€” escenario 2.

## Requisito o caso de negocio asociado

- **Requisito:** `RF002` (ver `docs/requisitos/ERS_ICM_Requisitos.md`).

## Inputs (Given / When â€” extracto ERS)

**Given (Dado que):**
- El usuario autenticado tiene rol "Almacenista"
- Existe una cuenta activa en el sistema

**When (Cuando):**
- Selecciona la cuenta y elige la opciÃ³n "Modificar contraseÃ±a"
- Ingresa la nueva contraseÃ±a y confirma la acciÃ³n

**Then (Entonces):**
- El sistema actualiza la contraseÃ±a de la cuenta seleccionada
- El cambio queda registrado en el log de auditorÃ­a con UserID del Almacenista y timestamp

---

## Resultado esperado (Then)

Ver secciÃ³n **Then** en el extracto anterior del ERS. En automatizaciÃ³n backend, el test asociado comprueba el contrato API/servicio equivalente o queda explÃ­citamente marcado como pendiente si el criterio es solo UI, infraestructura o legalidad operativa fuera del alcance de pytest.

## Link directo al test

Ejecutar:

```bash
pytest tests/ers/test_gherkin_dynamic.py::test_RF002_S02 -v
```

Archivo de definiciÃ³n dinÃ¡mica: [`tests/ers/test_gherkin_dynamic.py`](../../tests/ers/test_gherkin_dynamic.py)

---

## Estado de automatizaciÃ³n backend

Implementada en `tests/ers/gherkin_impl.py` (comprueba API/servicios equivalentes al Then del ERS).


<!-- file: RF002-S03.md -->

# Almacenista deshabilita una cuenta activa

## Nombre del test

`tests/ers/test_gherkin_dynamic.py::test_RF002_S03`

## PropÃ³sito

Validar el criterio de aceptaciÃ³n Gherkin del ERS ICM para **RF002** â€” escenario 3.

## Requisito o caso de negocio asociado

- **Requisito:** `RF002` (ver `docs/requisitos/ERS_ICM_Requisitos.md`).

## Inputs (Given / When â€” extracto ERS)

**Given (Dado que):**
- El usuario autenticado tiene rol "Almacenista"
- Existe una cuenta de usuario activa en el sistema

**When (Cuando):**
- Selecciona la cuenta y elige la opciÃ³n "Deshabilitar"
- Confirma la acciÃ³n

**Then (Entonces):**
- El sistema deshabilita la cuenta inmediatamente
- Si el usuario tenÃ­a una sesiÃ³n activa, Ã©sta se termina en ese momento
- El usuario deshabilitado no puede iniciar sesiÃ³n hasta que el Almacenista reactive la cuenta
- El evento queda registrado en el log de auditorÃ­a

---

## Resultado esperado (Then)

Ver secciÃ³n **Then** en el extracto anterior del ERS. En automatizaciÃ³n backend, el test asociado comprueba el contrato API/servicio equivalente o queda explÃ­citamente marcado como pendiente si el criterio es solo UI, infraestructura o legalidad operativa fuera del alcance de pytest.

## Link directo al test

Ejecutar:

```bash
pytest tests/ers/test_gherkin_dynamic.py::test_RF002_S03 -v
```

Archivo de definiciÃ³n dinÃ¡mica: [`tests/ers/test_gherkin_dynamic.py`](../../tests/ers/test_gherkin_dynamic.py)

---

## Estado de automatizaciÃ³n backend

Implementada en `tests/ers/gherkin_impl.py` (comprueba API/servicios equivalentes al Then del ERS).


<!-- file: RF002-S04.md -->

# Auxiliar de Despacho intenta modificar su propio perfil

## Nombre del test

`tests/ers/test_gherkin_dynamic.py::test_RF002_S04`

## PropÃ³sito

Validar el criterio de aceptaciÃ³n Gherkin del ERS ICM para **RF002** â€” escenario 4.

## Requisito o caso de negocio asociado

- **Requisito:** `RF002` (ver `docs/requisitos/ERS_ICM_Requisitos.md`).

## Inputs (Given / When â€” extracto ERS)

**Given (Dado que):**
- El usuario autenticado tiene rol "Auxiliar de Despacho"

**When (Cuando):**
- Intenta acceder a cualquier opciÃ³n de ediciÃ³n de credenciales propias o ajenas

**Then (Entonces):**
- El sistema bloquea la acciÃ³n
- Muestra un mensaje indicando que no tiene permisos para realizar esa operaciÃ³n
- No realiza ningÃºn cambio en el sistema

---

## Resultado esperado (Then)

Ver secciÃ³n **Then** en el extracto anterior del ERS. En automatizaciÃ³n backend, el test asociado comprueba el contrato API/servicio equivalente o queda explÃ­citamente marcado como pendiente si el criterio es solo UI, infraestructura o legalidad operativa fuera del alcance de pytest.

## Link directo al test

Ejecutar:

```bash
pytest tests/ers/test_gherkin_dynamic.py::test_RF002_S04 -v
```

Archivo de definiciÃ³n dinÃ¡mica: [`tests/ers/test_gherkin_dynamic.py`](../../tests/ers/test_gherkin_dynamic.py)

---

## Estado de automatizaciÃ³n backend

Implementada en `tests/ers/gherkin_impl.py` (comprueba API/servicios equivalentes al Then del ERS).


<!-- file: RF002-S05.md -->

# Intento de crear una cuenta con un nombre de usuario ya existente

## Nombre del test

`tests/ers/test_gherkin_dynamic.py::test_RF002_S05`

## PropÃ³sito

Validar el criterio de aceptaciÃ³n Gherkin del ERS ICM para **RF002** â€” escenario 5.

## Requisito o caso de negocio asociado

- **Requisito:** `RF002` (ver `docs/requisitos/ERS_ICM_Requisitos.md`).

## Inputs (Given / When â€” extracto ERS)

**Given (Dado que):**
- El usuario autenticado tiene rol "Almacenista"
- Ya existe una cuenta con el nombre de usuario "auxiliar01" en el sistema

**When (Cuando):**
- Intenta crear una nueva cuenta con el mismo nombre de usuario "auxiliar01"

**Then (Entonces):**
- El sistema rechaza la creaciÃ³n
- Muestra un mensaje indicando que el nombre de usuario ya estÃ¡ en uso
- No genera ninguna cuenta duplicada

## Resultado esperado (Then)

Ver secciÃ³n **Then** en el extracto anterior del ERS. En automatizaciÃ³n backend, el test asociado comprueba el contrato API/servicio equivalente o queda explÃ­citamente marcado como pendiente si el criterio es solo UI, infraestructura o legalidad operativa fuera del alcance de pytest.

## Link directo al test

Ejecutar:

```bash
pytest tests/ers/test_gherkin_dynamic.py::test_RF002_S05 -v
```

Archivo de definiciÃ³n dinÃ¡mica: [`tests/ers/test_gherkin_dynamic.py`](../../tests/ers/test_gherkin_dynamic.py)

---

## Estado de automatizaciÃ³n backend

Implementada en `tests/ers/gherkin_impl.py` (comprueba API/servicios equivalentes al Then del ERS).


<!-- file: RF003-S01.md -->

# Almacenista registra un producto nuevo con todos los atributos obligatorios

## Nombre del test

`tests/ers/test_gherkin_dynamic.py::test_RF003_S01`

## PropÃ³sito

Validar el criterio de aceptaciÃ³n Gherkin del ERS ICM para **RF003** â€” escenario 1.

## Requisito o caso de negocio asociado

- **Requisito:** `RF003` (ver `docs/requisitos/ERS_ICM_Requisitos.md`).

## Inputs (Given / When â€” extracto ERS)

**Given (Dado que):**
- El usuario autenticado tiene rol "Almacenista"

**When (Cuando):**
- Accede al formulario de creaciÃ³n de producto
- Completa todos los campos obligatorios: nombre, categorÃ­a, subcategorÃ­a, cÃ³digo de barras, fecha de vencimiento, peso unitario y punto de reorden
- Hace clic en "Guardar producto"

**Then (Entonces):**
- El sistema crea el producto con un SKU Ãºnico
- Lo registra en el catÃ¡logo con stock inicial en cero para cada ubicaciÃ³n
- El evento de creaciÃ³n queda en el log de auditorÃ­a con UserID y timestamp

---

## Resultado esperado (Then)

Ver secciÃ³n **Then** en el extracto anterior del ERS. En automatizaciÃ³n backend, el test asociado comprueba el contrato API/servicio equivalente o queda explÃ­citamente marcado como pendiente si el criterio es solo UI, infraestructura o legalidad operativa fuera del alcance de pytest.

## Link directo al test

Ejecutar:

```bash
pytest tests/ers/test_gherkin_dynamic.py::test_RF003_S01 -v
```

Archivo de definiciÃ³n dinÃ¡mica: [`tests/ers/test_gherkin_dynamic.py`](../../tests/ers/test_gherkin_dynamic.py)

---

## Estado de automatizaciÃ³n backend

Implementada en `tests/ers/gherkin_impl.py` (comprueba API/servicios equivalentes al Then del ERS).


<!-- file: RF003-S02.md -->

# Registro de producto de marca propia "Can"

## Nombre del test

`tests/ers/test_gherkin_dynamic.py::test_RF003_S02`

## PropÃ³sito

Validar el criterio de aceptaciÃ³n Gherkin del ERS ICM para **RF003** â€” escenario 2.

## Requisito o caso de negocio asociado

- **Requisito:** `RF003` (ver `docs/requisitos/ERS_ICM_Requisitos.md`).

## Inputs (Given / When â€” extracto ERS)

**Given (Dado que):**
- El usuario autenticado tiene rol "Almacenista"

**When (Cuando):**
- Registra un producto indicando que pertenece a la marca propia "Can"

**Then (Entonces):**
- El sistema acepta el SKU proporcionado por el usuario siempre que cumpla el patrÃ³n 1â€“4 letras, un guion y 1â€“4 dÃ­gitos
- No permite guardar el producto si el SKU no cumple el formato requerido

---

## Resultado esperado (Then)

Ver secciÃ³n **Then** en el extracto anterior del ERS. En automatizaciÃ³n backend, el test asociado comprueba el contrato API/servicio equivalente o queda explÃ­citamente marcado como pendiente si el criterio es solo UI, infraestructura o legalidad operativa fuera del alcance de pytest.

## Link directo al test

Ejecutar:

```bash
pytest tests/ers/test_gherkin_dynamic.py::test_RF003_S02 -v
```

Archivo de definiciÃ³n dinÃ¡mica: [`tests/ers/test_gherkin_dynamic.py`](../../tests/ers/test_gherkin_dynamic.py)

---

## Estado de automatizaciÃ³n backend

Implementada en `tests/ers/gherkin_impl.py` (comprueba API/servicios equivalentes al Then del ERS).


<!-- file: RF003-S03.md -->

# Registro de producto de categorÃ­a Electroterapia

## Nombre del test

`tests/ers/test_gherkin_dynamic.py::test_RF003_S03`

## PropÃ³sito

Validar el criterio de aceptaciÃ³n Gherkin del ERS ICM para **RF003** â€” escenario 3.

## Requisito o caso de negocio asociado

- **Requisito:** `RF003` (ver `docs/requisitos/ERS_ICM_Requisitos.md`).

## Inputs (Given / When â€” extracto ERS)

**Given (Dado que):**
- El usuario autenticado tiene rol "Almacenista"

**When (Cuando):**
- Registra un producto con categorÃ­a "Electroterapia"

**Then (Entonces):**
- El sistema habilita y marca como obligatorio el campo "NÃºmero de Serie"
- No permite guardar el producto si ese campo estÃ¡ vacÃ­o

---

## Resultado esperado (Then)

Ver secciÃ³n **Then** en el extracto anterior del ERS. En automatizaciÃ³n backend, el test asociado comprueba el contrato API/servicio equivalente o queda explÃ­citamente marcado como pendiente si el criterio es solo UI, infraestructura o legalidad operativa fuera del alcance de pytest.

## Link directo al test

Ejecutar:

```bash
pytest tests/ers/test_gherkin_dynamic.py::test_RF003_S03 -v
```

Archivo de definiciÃ³n dinÃ¡mica: [`tests/ers/test_gherkin_dynamic.py`](../../tests/ers/test_gherkin_dynamic.py)

---

## Estado de automatizaciÃ³n backend

Implementada en `tests/ers/gherkin_impl.py` (comprueba API/servicios equivalentes al Then del ERS).


<!-- file: RF003-S04.md -->

# Registro de producto con cÃ³digo de barras como alias de escaneo

## Nombre del test

`tests/ers/test_gherkin_dynamic.py::test_RF003_S04`

## PropÃ³sito

Validar el criterio de aceptaciÃ³n Gherkin del ERS ICM para **RF003** â€” escenario 4.

## Requisito o caso de negocio asociado

- **Requisito:** `RF003` (ver `docs/requisitos/ERS_ICM_Requisitos.md`).

## Inputs (Given / When â€” extracto ERS)

**Given (Dado que):**
- El usuario autenticado tiene rol "Almacenista"

**When (Cuando):**
- Registra un producto e ingresa un cÃ³digo de barras en el campo correspondiente

**Then (Entonces):**
- El sistema almacena el cÃ³digo como atributo adicional del producto
- Lo vincula internamente al SKU sin reemplazarlo
- Cuando ese cÃ³digo sea escaneado o ingresado manualmente en cualquier mÃ³dulo, el sistema resuelve la correspondencia al SKU correcto

---

## Resultado esperado (Then)

Ver secciÃ³n **Then** en el extracto anterior del ERS. En automatizaciÃ³n backend, el test asociado comprueba el contrato API/servicio equivalente o queda explÃ­citamente marcado como pendiente si el criterio es solo UI, infraestructura o legalidad operativa fuera del alcance de pytest.

## Link directo al test

Ejecutar:

```bash
pytest tests/ers/test_gherkin_dynamic.py::test_RF003_S04 -v
```

Archivo de definiciÃ³n dinÃ¡mica: [`tests/ers/test_gherkin_dynamic.py`](../../tests/ers/test_gherkin_dynamic.py)

---

## Estado de automatizaciÃ³n backend

Implementada en `tests/ers/gherkin_impl.py` (comprueba API/servicios equivalentes al Then del ERS).


<!-- file: RF003-S05.md -->

# Registro de producto que requiere cadena de frÃ­o

## Nombre del test

`tests/ers/test_gherkin_dynamic.py::test_RF003_S05`

## PropÃ³sito

Validar el criterio de aceptaciÃ³n Gherkin del ERS ICM para **RF003** â€” escenario 5.

## Requisito o caso de negocio asociado

- **Requisito:** `RF003` (ver `docs/requisitos/ERS_ICM_Requisitos.md`).

## Inputs (Given / When â€” extracto ERS)

**Given (Dado que):**
- El usuario autenticado tiene rol "Almacenista"

**When (Cuando):**
- Registra un producto y activa el indicador de "Cadena de frÃ­o"

**Then (Entonces):**
- El sistema almacena esa condiciÃ³n especial en la ficha del producto
- DesplegarÃ¡ una alerta visual persistente en cualquier mÃ³dulo donde ese producto sea manipulado

---

## Resultado esperado (Then)

Ver secciÃ³n **Then** en el extracto anterior del ERS. En automatizaciÃ³n backend, el test asociado comprueba el contrato API/servicio equivalente o queda explÃ­citamente marcado como pendiente si el criterio es solo UI, infraestructura o legalidad operativa fuera del alcance de pytest.

## Link directo al test

Ejecutar:

```bash
pytest tests/ers/test_gherkin_dynamic.py::test_RF003_S05 -v
```

Archivo de definiciÃ³n dinÃ¡mica: [`tests/ers/test_gherkin_dynamic.py`](../../tests/ers/test_gherkin_dynamic.py)

---

## Estado de automatizaciÃ³n backend

Implementada en `tests/ers/gherkin_impl.py` (comprueba API/servicios equivalentes al Then del ERS).


<!-- file: RF003-S06.md -->

# CreaciÃ³n de un Combo o Kit con mÃºltiples SKUs

## Nombre del test

`tests/ers/test_gherkin_dynamic.py::test_RF003_S06`

## PropÃ³sito

Validar el criterio de aceptaciÃ³n Gherkin del ERS ICM para **RF003** â€” escenario 6.

## Requisito o caso de negocio asociado

- **Requisito:** `RF003` (ver `docs/requisitos/ERS_ICM_Requisitos.md`).

## Inputs (Given / When â€” extracto ERS)

**Given (Dado que):**
- El usuario autenticado tiene rol "Almacenista"
- Existen al menos dos productos registrados en el catÃ¡logo

**When (Cuando):**
- Crea un nuevo Ã­tem de tipo "Combo" y asocia dos o mÃ¡s SKUs existentes

**Then (Entonces):**
- El sistema registra el Combo con un identificador propio
- Permite despacharlo como una sola unidad de salida
- Al confirmar un despacho de ese Combo, descuenta el stock de cada SKU componente en sus respectivas ubicaciones

---

## Resultado esperado (Then)

Ver secciÃ³n **Then** en el extracto anterior del ERS. En automatizaciÃ³n backend, el test asociado comprueba el contrato API/servicio equivalente o queda explÃ­citamente marcado como pendiente si el criterio es solo UI, infraestructura o legalidad operativa fuera del alcance de pytest.

## Link directo al test

Ejecutar:

```bash
pytest tests/ers/test_gherkin_dynamic.py::test_RF003_S06 -v
```

Archivo de definiciÃ³n dinÃ¡mica: [`tests/ers/test_gherkin_dynamic.py`](../../tests/ers/test_gherkin_dynamic.py)

---

## Estado de automatizaciÃ³n backend

Implementada en `tests/ers/gherkin_impl.py` (comprueba API/servicios equivalentes al Then del ERS).


<!-- file: RF003-S07.md -->

# Intento de guardar un producto sin completar campos obligatorios

## Nombre del test

`tests/ers/test_gherkin_dynamic.py::test_RF003_S07`

## PropÃ³sito

Validar el criterio de aceptaciÃ³n Gherkin del ERS ICM para **RF003** â€” escenario 7.

## Requisito o caso de negocio asociado

- **Requisito:** `RF003` (ver `docs/requisitos/ERS_ICM_Requisitos.md`).

## Inputs (Given / When â€” extracto ERS)

**Given (Dado que):**
- El usuario autenticado tiene rol "Almacenista"

**When (Cuando):**
- Intenta guardar un producto dejando uno o mÃ¡s campos obligatorios vacÃ­os

**Then (Entonces):**
- El sistema rechaza el guardado
- SeÃ±ala visualmente los campos faltantes
- No crea ningÃºn registro parcial en el catÃ¡logo

## Resultado esperado (Then)

Ver secciÃ³n **Then** en el extracto anterior del ERS. En automatizaciÃ³n backend, el test asociado comprueba el contrato API/servicio equivalente o queda explÃ­citamente marcado como pendiente si el criterio es solo UI, infraestructura o legalidad operativa fuera del alcance de pytest.

## Link directo al test

Ejecutar:

```bash
pytest tests/ers/test_gherkin_dynamic.py::test_RF003_S07 -v
```

Archivo de definiciÃ³n dinÃ¡mica: [`tests/ers/test_gherkin_dynamic.py`](../../tests/ers/test_gherkin_dynamic.py)

---

## Estado de automatizaciÃ³n backend

Implementada en `tests/ers/gherkin_impl.py` (comprueba API/servicios equivalentes al Then del ERS).


<!-- file: RF004-S01.md -->

# Consulta de stock navegando por filtros multinivel

## Nombre del test

`tests/ers/test_gherkin_dynamic.py::test_RF004_S01`

## PropÃ³sito

Validar el criterio de aceptaciÃ³n Gherkin del ERS ICM para **RF004** â€” escenario 1.

## Requisito o caso de negocio asociado

- **Requisito:** `RF004` (ver `docs/requisitos/ERS_ICM_Requisitos.md`).

## Inputs (Given / When â€” extracto ERS)

**Given (Dado que):**
- El usuario estÃ¡ autenticado con cualquier rol

**When (Cuando):**
- Selecciona una categorÃ­a (por ejemplo "Electroterapia")
- Luego selecciona una subcategorÃ­a (por ejemplo "Agujas de PunciÃ³n Seca")

**Then (Entonces):**
- El sistema muestra Ãºnicamente los productos que corresponden a esa combinaciÃ³n de categorÃ­a y subcategorÃ­a
- Para cada producto despliega el stock disponible en Vitrina, Bodega 1, Bodega 2 y el total consolidado

---

## Resultado esperado (Then)

Ver secciÃ³n **Then** en el extracto anterior del ERS. En automatizaciÃ³n backend, el test asociado comprueba el contrato API/servicio equivalente o queda explÃ­citamente marcado como pendiente si el criterio es solo UI, infraestructura o legalidad operativa fuera del alcance de pytest.

## Link directo al test

Ejecutar:

```bash
pytest tests/ers/test_gherkin_dynamic.py::test_RF004_S01 -v
```

Archivo de definiciÃ³n dinÃ¡mica: [`tests/ers/test_gherkin_dynamic.py`](../../tests/ers/test_gherkin_dynamic.py)

---

## Estado de automatizaciÃ³n backend

Implementada en `tests/ers/gherkin_impl.py` (comprueba API/servicios equivalentes al Then del ERS).


<!-- file: RF004-S02.md -->

# BÃºsqueda de producto por nombre con autocompletado

## Nombre del test

`tests/ers/test_gherkin_dynamic.py::test_RF004_S02`

## PropÃ³sito

Validar el criterio de aceptaciÃ³n Gherkin del ERS ICM para **RF004** â€” escenario 2.

## Requisito o caso de negocio asociado

- **Requisito:** `RF004` (ver `docs/requisitos/ERS_ICM_Requisitos.md`).

## Inputs (Given / When â€” extracto ERS)

**Given (Dado que):**
- El usuario estÃ¡ autenticado con cualquier rol

**When (Cuando):**
- Escribe al menos tres caracteres del nombre de un producto en el campo de bÃºsqueda

**Then (Entonces):**
- El sistema despliega en tiempo real una lista de sugerencias que coinciden con los caracteres ingresados
- Al seleccionar un producto de la lista, muestra su ficha con el stock por ubicaciÃ³n y el total consolidado

---

## Resultado esperado (Then)

Ver secciÃ³n **Then** en el extracto anterior del ERS. En automatizaciÃ³n backend, el test asociado comprueba el contrato API/servicio equivalente o queda explÃ­citamente marcado como pendiente si el criterio es solo UI, infraestructura o legalidad operativa fuera del alcance de pytest.

## Link directo al test

Ejecutar:

```bash
pytest tests/ers/test_gherkin_dynamic.py::test_RF004_S02 -v
```

Archivo de definiciÃ³n dinÃ¡mica: [`tests/ers/test_gherkin_dynamic.py`](../../tests/ers/test_gherkin_dynamic.py)

---

## Estado de automatizaciÃ³n backend

Implementada en `tests/ers/gherkin_impl.py` (comprueba API/servicios equivalentes al Then del ERS).


<!-- file: RF004-S03.md -->

# BÃºsqueda de producto por cÃ³digo de barras escaneado

## Nombre del test

`tests/ers/test_gherkin_dynamic.py::test_RF004_S03`

## PropÃ³sito

Validar el criterio de aceptaciÃ³n Gherkin del ERS ICM para **RF004** â€” escenario 3.

## Requisito o caso de negocio asociado

- **Requisito:** `RF004` (ver `docs/requisitos/ERS_ICM_Requisitos.md`).

## Inputs (Given / When â€” extracto ERS)

**Given (Dado que):**
- El usuario estÃ¡ autenticado con cualquier rol
- Hay un lector de cÃ³digo de barras conectado en modo HID

**When (Cuando):**
- Escanea el cÃ³digo de barras impreso en el empaque de un producto

**Then (Entonces):**
- El sistema resuelve el cÃ³digo al SKU interno correspondiente
- Muestra la ficha del producto con su stock por ubicaciÃ³n y el total consolidado en menos de 2 segundos

---

## Resultado esperado (Then)

Ver secciÃ³n **Then** en el extracto anterior del ERS. En automatizaciÃ³n backend, el test asociado comprueba el contrato API/servicio equivalente o queda explÃ­citamente marcado como pendiente si el criterio es solo UI, infraestructura o legalidad operativa fuera del alcance de pytest.

## Link directo al test

Ejecutar:

```bash
pytest tests/ers/test_gherkin_dynamic.py::test_RF004_S03 -v
```

Archivo de definiciÃ³n dinÃ¡mica: [`tests/ers/test_gherkin_dynamic.py`](../../tests/ers/test_gherkin_dynamic.py)

---

## Estado de automatizaciÃ³n backend

Implementada en `tests/ers/gherkin_impl.py` (comprueba API/servicios equivalentes al Then del ERS).


<!-- file: RF004-S04.md -->

# BÃºsqueda de producto por cÃ³digo de barras ingresado manualmente

## Nombre del test

`tests/ers/test_gherkin_dynamic.py::test_RF004_S04`

## PropÃ³sito

Validar el criterio de aceptaciÃ³n Gherkin del ERS ICM para **RF004** â€” escenario 4.

## Requisito o caso de negocio asociado

- **Requisito:** `RF004` (ver `docs/requisitos/ERS_ICM_Requisitos.md`).

## Inputs (Given / When â€” extracto ERS)

**Given (Dado que):**
- El usuario estÃ¡ autenticado con cualquier rol
- No hay un lector de cÃ³digo de barras disponible

**When (Cuando):**
- Escribe manualmente el cÃ³digo de barras en el campo de bÃºsqueda

**Then (Entonces):**
- El sistema resuelve el cÃ³digo al SKU interno correspondiente
- Muestra la misma ficha y resultado que si hubiera sido escaneado

---

## Resultado esperado (Then)

Ver secciÃ³n **Then** en el extracto anterior del ERS. En automatizaciÃ³n backend, el test asociado comprueba el contrato API/servicio equivalente o queda explÃ­citamente marcado como pendiente si el criterio es solo UI, infraestructura o legalidad operativa fuera del alcance de pytest.

## Link directo al test

Ejecutar:

```bash
pytest tests/ers/test_gherkin_dynamic.py::test_RF004_S04 -v
```

Archivo de definiciÃ³n dinÃ¡mica: [`tests/ers/test_gherkin_dynamic.py`](../../tests/ers/test_gherkin_dynamic.py)

---

## Estado de automatizaciÃ³n backend

Implementada en `tests/ers/gherkin_impl.py` (comprueba API/servicios equivalentes al Then del ERS).


<!-- file: RF004-S05.md -->

# Consulta de producto con alerta de cadena de frÃ­o

## Nombre del test

`tests/ers/test_gherkin_dynamic.py::test_RF004_S05`

## PropÃ³sito

Validar el criterio de aceptaciÃ³n Gherkin del ERS ICM para **RF004** â€” escenario 5.

## Requisito o caso de negocio asociado

- **Requisito:** `RF004` (ver `docs/requisitos/ERS_ICM_Requisitos.md`).

## Inputs (Given / When â€” extracto ERS)

**Given (Dado que):**
- El usuario estÃ¡ autenticado con cualquier rol

**When (Cuando):**
- Consulta un producto que tiene activado el indicador de cadena de frÃ­o

**Then (Entonces):**
- El sistema despliega una alerta visual persistente y de alta visibilidad junto a la ficha del producto
- Recuerda las condiciones especiales de manejo

---

## Resultado esperado (Then)

Ver secciÃ³n **Then** en el extracto anterior del ERS. En automatizaciÃ³n backend, el test asociado comprueba el contrato API/servicio equivalente o queda explÃ­citamente marcado como pendiente si el criterio es solo UI, infraestructura o legalidad operativa fuera del alcance de pytest.

## Link directo al test

Ejecutar:

```bash
pytest tests/ers/test_gherkin_dynamic.py::test_RF004_S05 -v
```

Archivo de definiciÃ³n dinÃ¡mica: [`tests/ers/test_gherkin_dynamic.py`](../../tests/ers/test_gherkin_dynamic.py)

---

## Estado de automatizaciÃ³n backend

Implementada en `tests/ers/gherkin_impl.py` (comprueba API/servicios equivalentes al Then del ERS).


<!-- file: RF004-S06.md -->

# Consulta de producto con alerta de seguridad elÃ©ctrica

## Nombre del test

`tests/ers/test_gherkin_dynamic.py::test_RF004_S06`

## PropÃ³sito

Validar el criterio de aceptaciÃ³n Gherkin del ERS ICM para **RF004** â€” escenario 6.

## Requisito o caso de negocio asociado

- **Requisito:** `RF004` (ver `docs/requisitos/ERS_ICM_Requisitos.md`).

## Inputs (Given / When â€” extracto ERS)

**Given (Dado que):**
- El usuario estÃ¡ autenticado con cualquier rol

**When (Cuando):**
- Consulta un producto de la categorÃ­a Electroterapia

**Then (Entonces):**
- El sistema despliega una advertencia visual sobre los protocolos de manejo seguro aplicables a equipos elÃ©ctricos

---

## Resultado esperado (Then)

Ver secciÃ³n **Then** en el extracto anterior del ERS. En automatizaciÃ³n backend, el test asociado comprueba el contrato API/servicio equivalente o queda explÃ­citamente marcado como pendiente si el criterio es solo UI, infraestructura o legalidad operativa fuera del alcance de pytest.

## Link directo al test

Ejecutar:

```bash
pytest tests/ers/test_gherkin_dynamic.py::test_RF004_S06 -v
```

Archivo de definiciÃ³n dinÃ¡mica: [`tests/ers/test_gherkin_dynamic.py`](../../tests/ers/test_gherkin_dynamic.py)

---

## Estado de automatizaciÃ³n backend

Implementada en `tests/ers/gherkin_impl.py` (comprueba API/servicios equivalentes al Then del ERS).


<!-- file: RF004-S07.md -->

# BÃºsqueda de un producto inexistente en el catÃ¡logo

## Nombre del test

`tests/ers/test_gherkin_dynamic.py::test_RF004_S07`

## PropÃ³sito

Validar el criterio de aceptaciÃ³n Gherkin del ERS ICM para **RF004** â€” escenario 7.

## Requisito o caso de negocio asociado

- **Requisito:** `RF004` (ver `docs/requisitos/ERS_ICM_Requisitos.md`).

## Inputs (Given / When â€” extracto ERS)

**Given (Dado que):**
- El usuario estÃ¡ autenticado con cualquier rol

**When (Cuando):**
- Realiza una bÃºsqueda por nombre, SKU o cÃ³digo de barras que no corresponde a ningÃºn producto registrado

**Then (Entonces):**
- El sistema muestra un mensaje claro indicando que no se encontraron resultados para ese criterio de bÃºsqueda
- No genera ningÃºn error ni interrupciÃ³n en la interfaz

## Resultado esperado (Then)

Ver secciÃ³n **Then** en el extracto anterior del ERS. En automatizaciÃ³n backend, el test asociado comprueba el contrato API/servicio equivalente o queda explÃ­citamente marcado como pendiente si el criterio es solo UI, infraestructura o legalidad operativa fuera del alcance de pytest.

## Link directo al test

Ejecutar:

```bash
pytest tests/ers/test_gherkin_dynamic.py::test_RF004_S07 -v
```

Archivo de definiciÃ³n dinÃ¡mica: [`tests/ers/test_gherkin_dynamic.py`](../../tests/ers/test_gherkin_dynamic.py)

---

## Estado de automatizaciÃ³n backend

Implementada en `tests/ers/gherkin_impl.py` (comprueba API/servicios equivalentes al Then del ERS).


<!-- file: RF005-S01.md -->

# RecepciÃ³n exitosa de producto estÃ¡ndar sin discrepancia

## Nombre del test

`tests/ers/test_gherkin_dynamic.py::test_RF005_S01`

## PropÃ³sito

Validar el criterio de aceptaciÃ³n Gherkin del ERS ICM para **RF005** â€” escenario 1.

## Requisito o caso de negocio asociado

- **Requisito:** `RF005` (ver `docs/requisitos/ERS_ICM_Requisitos.md`).

## Inputs (Given / When â€” extracto ERS)

**Given (Dado que):**
- El usuario autenticado tiene rol "Auxiliar de Despacho" o "Almacenista"
- El producto existe en el catÃ¡logo
- La hora actual estÃ¡ dentro de la franja horaria permitida

**When (Cuando):**
- Inicia un registro de entrada
- Selecciona el producto por escaneo de cÃ³digo de barras o bÃºsqueda por nombre
- Ingresa la cantidad recibida igual a la cantidad facturada
- Selecciona la ubicaciÃ³n de destino (Vitrina, Bodega 1 o Bodega 2)
- Confirma la entrada

**Then (Entonces):**
- El sistema incrementa el stock del producto en la ubicaciÃ³n seleccionada
- Recalcula el stock total consolidado
- Genera un movimiento de entrada inmutable con UserID, timestamp, ubicaciÃ³n de destino, cantidad, stock previo y stock resultante

---

## Resultado esperado (Then)

Ver secciÃ³n **Then** en el extracto anterior del ERS. En automatizaciÃ³n backend, el test asociado comprueba el contrato API/servicio equivalente o queda explÃ­citamente marcado como pendiente si el criterio es solo UI, infraestructura o legalidad operativa fuera del alcance de pytest.

## Link directo al test

Ejecutar:

```bash
pytest tests/ers/test_gherkin_dynamic.py::test_RF005_S01 -v
```

Archivo de definiciÃ³n dinÃ¡mica: [`tests/ers/test_gherkin_dynamic.py`](../../tests/ers/test_gherkin_dynamic.py)

---

## Estado de automatizaciÃ³n backend

Implementada en `tests/ers/gherkin_impl.py` (comprueba API/servicios equivalentes al Then del ERS).


<!-- file: RF005-S02.md -->

# RecepciÃ³n con discrepancia entre cantidad recibida y facturada

## Nombre del test

`tests/ers/test_gherkin_dynamic.py::test_RF005_S02`

## PropÃ³sito

Validar el criterio de aceptaciÃ³n Gherkin del ERS ICM para **RF005** â€” escenario 2.

## Requisito o caso de negocio asociado

- **Requisito:** `RF005` (ver `docs/requisitos/ERS_ICM_Requisitos.md`).

## Inputs (Given / When â€” extracto ERS)

**Given (Dado que):**
- El usuario autenticado tiene rol "Auxiliar de Despacho" o "Almacenista"
- El producto existe en el catÃ¡logo

**When (Cuando):**
- Ingresa una cantidad recibida diferente a la cantidad facturada o esperada
- Intenta confirmar la entrada sin registrar una nota de discrepancia

**Then (Entonces):**
- El sistema bloquea la confirmaciÃ³n
- Muestra un mensaje indicando que es obligatorio registrar una nota que explique la diferencia
- No genera ningÃºn movimiento hasta que la nota sea completada

---

## Resultado esperado (Then)

Ver secciÃ³n **Then** en el extracto anterior del ERS. En automatizaciÃ³n backend, el test asociado comprueba el contrato API/servicio equivalente o queda explÃ­citamente marcado como pendiente si el criterio es solo UI, infraestructura o legalidad operativa fuera del alcance de pytest.

## Link directo al test

Ejecutar:

```bash
pytest tests/ers/test_gherkin_dynamic.py::test_RF005_S02 -v
```

Archivo de definiciÃ³n dinÃ¡mica: [`tests/ers/test_gherkin_dynamic.py`](../../tests/ers/test_gherkin_dynamic.py)

---

## Estado de automatizaciÃ³n backend

Implementada en `tests/ers/gherkin_impl.py` (comprueba API/servicios equivalentes al Then del ERS).


<!-- file: RF005-S03.md -->

# RecepciÃ³n exitosa con discrepancia documentada

## Nombre del test

`tests/ers/test_gherkin_dynamic.py::test_RF005_S03`

## PropÃ³sito

Validar el criterio de aceptaciÃ³n Gherkin del ERS ICM para **RF005** â€” escenario 3.

## Requisito o caso de negocio asociado

- **Requisito:** `RF005` (ver `docs/requisitos/ERS_ICM_Requisitos.md`).

## Inputs (Given / When â€” extracto ERS)

**Given (Dado que):**
- El usuario autenticado tiene rol "Auxiliar de Despacho" o "Almacenista"
- La cantidad recibida difiere de la facturada

**When (Cuando):**
- Registra la nota de discrepancia obligatoria
- Confirma la entrada

**Then (Entonces):**
- El sistema acepta la operaciÃ³n
- Genera el movimiento de entrada vinculando la nota de discrepancia al registro
- El movimiento queda inmutable con todos los atributos de trazabilidad

---

## Resultado esperado (Then)

Ver secciÃ³n **Then** en el extracto anterior del ERS. En automatizaciÃ³n backend, el test asociado comprueba el contrato API/servicio equivalente o queda explÃ­citamente marcado como pendiente si el criterio es solo UI, infraestructura o legalidad operativa fuera del alcance de pytest.

## Link directo al test

Ejecutar:

```bash
pytest tests/ers/test_gherkin_dynamic.py::test_RF005_S03 -v
```

Archivo de definiciÃ³n dinÃ¡mica: [`tests/ers/test_gherkin_dynamic.py`](../../tests/ers/test_gherkin_dynamic.py)

---

## Estado de automatizaciÃ³n backend

Implementada en `tests/ers/gherkin_impl.py` (comprueba API/servicios equivalentes al Then del ERS).


<!-- file: RF005-S04.md -->

# RecepciÃ³n de producto de categorÃ­a Electroterapia sin nÃºmero de serie

## Nombre del test

`tests/ers/test_gherkin_dynamic.py::test_RF005_S04`

## PropÃ³sito

Validar el criterio de aceptaciÃ³n Gherkin del ERS ICM para **RF005** â€” escenario 4.

## Requisito o caso de negocio asociado

- **Requisito:** `RF005` (ver `docs/requisitos/ERS_ICM_Requisitos.md`).

## Inputs (Given / When â€” extracto ERS)

**Given (Dado que):**
- El usuario autenticado tiene rol "Auxiliar de Despacho" o "Almacenista"
- El producto seleccionado pertenece a la categorÃ­a "Electroterapia"

**When (Cuando):**
- Completa el formulario de entrada dejando vacÃ­o el campo "NÃºmero de Serie"
- Intenta confirmar la entrada

**Then (Entonces):**
- El sistema bloquea la confirmaciÃ³n
- Muestra un mensaje indicando que el nÃºmero de serie es obligatorio para productos de Electroterapia
- No genera ningÃºn movimiento ni actualizaciÃ³n de stock

---

## Resultado esperado (Then)

Ver secciÃ³n **Then** en el extracto anterior del ERS. En automatizaciÃ³n backend, el test asociado comprueba el contrato API/servicio equivalente o queda explÃ­citamente marcado como pendiente si el criterio es solo UI, infraestructura o legalidad operativa fuera del alcance de pytest.

## Link directo al test

Ejecutar:

```bash
pytest tests/ers/test_gherkin_dynamic.py::test_RF005_S04 -v
```

Archivo de definiciÃ³n dinÃ¡mica: [`tests/ers/test_gherkin_dynamic.py`](../../tests/ers/test_gherkin_dynamic.py)

---

## Estado de automatizaciÃ³n backend

Implementada en `tests/ers/gherkin_impl.py` (comprueba API/servicios equivalentes al Then del ERS).


<!-- file: RF005-S05.md -->

# RecepciÃ³n exitosa de producto de Electroterapia con nÃºmero de serie

## Nombre del test

`tests/ers/test_gherkin_dynamic.py::test_RF005_S05`

## PropÃ³sito

Validar el criterio de aceptaciÃ³n Gherkin del ERS ICM para **RF005** â€” escenario 5.

## Requisito o caso de negocio asociado

- **Requisito:** `RF005` (ver `docs/requisitos/ERS_ICM_Requisitos.md`).

## Inputs (Given / When â€” extracto ERS)

**Given (Dado que):**
- El usuario autenticado tiene rol "Auxiliar de Despacho" o "Almacenista"
- El producto pertenece a la categorÃ­a "Electroterapia"

**When (Cuando):**
- Ingresa el nÃºmero de serie de cada unidad recibida
- Completa los demÃ¡s campos obligatorios y confirma la entrada

**Then (Entonces):**
- El sistema registra cada unidad vinculada a su nÃºmero de serie individual
- Actualiza el stock en la ubicaciÃ³n de destino seleccionada
- Genera el movimiento con trazabilidad completa incluyendo los seriales

---

## Resultado esperado (Then)

Ver secciÃ³n **Then** en el extracto anterior del ERS. En automatizaciÃ³n backend, el test asociado comprueba el contrato API/servicio equivalente o queda explÃ­citamente marcado como pendiente si el criterio es solo UI, infraestructura o legalidad operativa fuera del alcance de pytest.

## Link directo al test

Ejecutar:

```bash
pytest tests/ers/test_gherkin_dynamic.py::test_RF005_S05 -v
```

Archivo de definiciÃ³n dinÃ¡mica: [`tests/ers/test_gherkin_dynamic.py`](../../tests/ers/test_gherkin_dynamic.py)

---

## Estado de automatizaciÃ³n backend

Implementada en `tests/ers/gherkin_impl.py` (comprueba API/servicios equivalentes al Then del ERS).


<!-- file: RF005-S06.md -->

# IdentificaciÃ³n del producto por cÃ³digo de barras escaneado durante recepciÃ³n

## Nombre del test

`tests/ers/test_gherkin_dynamic.py::test_RF005_S06`

## PropÃ³sito

Validar el criterio de aceptaciÃ³n Gherkin del ERS ICM para **RF005** â€” escenario 6.

## Requisito o caso de negocio asociado

- **Requisito:** `RF005` (ver `docs/requisitos/ERS_ICM_Requisitos.md`).

## Inputs (Given / When â€” extracto ERS)

**Given (Dado que):**
- El usuario autenticado tiene rol "Auxiliar de Despacho" o "Almacenista"
- Hay un lector de cÃ³digo de barras conectado en modo HID

**When (Cuando):**
- Escanea el cÃ³digo de barras del producto a recepcionar

**Then (Entonces):**
- El sistema resuelve el cÃ³digo al SKU interno
- Autocompleta el formulario con el nombre, categorÃ­a y demÃ¡s atributos del producto
- El operario solo debe completar cantidad, ubicaciÃ³n y los campos variables de esa entrada

---

## Resultado esperado (Then)

Ver secciÃ³n **Then** en el extracto anterior del ERS. En automatizaciÃ³n backend, el test asociado comprueba el contrato API/servicio equivalente o queda explÃ­citamente marcado como pendiente si el criterio es solo UI, infraestructura o legalidad operativa fuera del alcance de pytest.

## Link directo al test

Ejecutar:

```bash
pytest tests/ers/test_gherkin_dynamic.py::test_RF005_S06 -v
```

Archivo de definiciÃ³n dinÃ¡mica: [`tests/ers/test_gherkin_dynamic.py`](../../tests/ers/test_gherkin_dynamic.py)

---

## Estado de automatizaciÃ³n backend

Implementada en `tests/ers/gherkin_impl.py` (comprueba API/servicios equivalentes al Then del ERS).


<!-- file: RF005-S07.md -->

# RecepciÃ³n cuando el lector de cÃ³digo de barras no estÃ¡ disponible

## Nombre del test

`tests/ers/test_gherkin_dynamic.py::test_RF005_S07`

## PropÃ³sito

Validar el criterio de aceptaciÃ³n Gherkin del ERS ICM para **RF005** â€” escenario 7.

## Requisito o caso de negocio asociado

- **Requisito:** `RF005` (ver `docs/requisitos/ERS_ICM_Requisitos.md`).

## Inputs (Given / When â€” extracto ERS)

**Given (Dado que):**
- El usuario autenticado tiene rol "Auxiliar de Despacho" o "Almacenista"
- El lector de cÃ³digo de barras no estÃ¡ conectado o no es reconocido

**When (Cuando):**
- El sistema detecta la ausencia del lector

**Then (Entonces):**
- Muestra una notificaciÃ³n visible informando que el lector no estÃ¡ disponible
- Permite continuar el flujo de recepciÃ³n mediante bÃºsqueda por nombre, ingreso manual del cÃ³digo de barras o ingreso directo del SKU
- No interrumpe ni bloquea el proceso de entrada bajo ninguna circunstancia

## Resultado esperado (Then)

Ver secciÃ³n **Then** en el extracto anterior del ERS. En automatizaciÃ³n backend, el test asociado comprueba el contrato API/servicio equivalente o queda explÃ­citamente marcado como pendiente si el criterio es solo UI, infraestructura o legalidad operativa fuera del alcance de pytest.

## Link directo al test

Ejecutar:

```bash
pytest tests/ers/test_gherkin_dynamic.py::test_RF005_S07 -v
```

Archivo de definiciÃ³n dinÃ¡mica: [`tests/ers/test_gherkin_dynamic.py`](../../tests/ers/test_gherkin_dynamic.py)

---

## Estado de automatizaciÃ³n backend

Implementada en `tests/ers/gherkin_impl.py` (comprueba API/servicios equivalentes al Then del ERS).


<!-- file: RF006-S01.md -->

# Despacho exitoso de venta al por mayor con validaciÃ³n cruzada

## Nombre del test

`tests/ers/test_gherkin_dynamic.py::test_RF006_S01`

## PropÃ³sito

Validar el criterio de aceptaciÃ³n Gherkin del ERS ICM para **RF006** â€” escenario 1.

## Requisito o caso de negocio asociado

- **Requisito:** `RF006` (ver `docs/requisitos/ERS_ICM_Requisitos.md`).

## Inputs (Given / When â€” extracto ERS)

**Given (Dado que):**
- El usuario autenticado tiene rol "Auxiliar de Despacho" o "Almacenista"
- Existe una orden de despacho con uno o mÃ¡s productos
- El stock disponible en la ubicaciÃ³n de origen es suficiente

**When (Cuando):**
- Selecciona el tipo de salida "Venta al por Mayor"
- Registra los datos completos del cliente receptor (nombre o razÃ³n social, correo, telÃ©fono, direcciÃ³n)
- Escanea o ingresa el cÃ³digo del producto a despachar
- El cÃ³digo coincide con el SKU de la orden
- Confirma el despacho

**Then (Entonces):**
- El sistema descuenta el stock del producto en la ubicaciÃ³n de origen
- Recalcula el stock total consolidado
- Genera un movimiento de salida inmutable con UserID, timestamp, tipo de salida, cliente, SKU, cantidad, ubicaciÃ³n de origen, stock previo y stock resultante
- Genera automÃ¡ticamente una factura digital en PDF con numeraciÃ³n secuencial que incluye todos los datos del despacho
- La factura queda almacenada de forma persistente en el historial

---

## Resultado esperado (Then)

Ver secciÃ³n **Then** en el extracto anterior del ERS. En automatizaciÃ³n backend, el test asociado comprueba el contrato API/servicio equivalente o queda explÃ­citamente marcado como pendiente si el criterio es solo UI, infraestructura o legalidad operativa fuera del alcance de pytest.

## Link directo al test

Ejecutar:

```bash
pytest tests/ers/test_gherkin_dynamic.py::test_RF006_S01 -v
```

Archivo de definiciÃ³n dinÃ¡mica: [`tests/ers/test_gherkin_dynamic.py`](../../tests/ers/test_gherkin_dynamic.py)

---

## Estado de automatizaciÃ³n backend

Implementada en `tests/ers/gherkin_impl.py` (comprueba API/servicios equivalentes al Then del ERS).


<!-- file: RF006-S02.md -->

# ValidaciÃ³n cruzada falla por cÃ³digo escaneado incorrecto

## Nombre del test

`tests/ers/test_gherkin_dynamic.py::test_RF006_S02`

## PropÃ³sito

Validar el criterio de aceptaciÃ³n Gherkin del ERS ICM para **RF006** â€” escenario 2.

## Requisito o caso de negocio asociado

- **Requisito:** `RF006` (ver `docs/requisitos/ERS_ICM_Requisitos.md`).

## Inputs (Given / When â€” extracto ERS)

**Given (Dado que):**
- El usuario autenticado tiene rol "Auxiliar de Despacho" o "Almacenista"
- Existe una orden de despacho para el SKU "ELEC-0001"

**When (Cuando):**
- Escanea fÃ­sicamente un producto cuyo cÃ³digo corresponde a un SKU diferente

**Then (Entonces):**
- El sistema bloquea la confirmaciÃ³n del despacho
- Muestra un mensaje de error descriptivo indicando que el producto escaneado no corresponde al producto de la orden
- No genera ningÃºn movimiento ni descuento de stock
- No genera factura hasta que la validaciÃ³n sea superada

---

## Resultado esperado (Then)

Ver secciÃ³n **Then** en el extracto anterior del ERS. En automatizaciÃ³n backend, el test asociado comprueba el contrato API/servicio equivalente o queda explÃ­citamente marcado como pendiente si el criterio es solo UI, infraestructura o legalidad operativa fuera del alcance de pytest.

## Link directo al test

Ejecutar:

```bash
pytest tests/ers/test_gherkin_dynamic.py::test_RF006_S02 -v
```

Archivo de definiciÃ³n dinÃ¡mica: [`tests/ers/test_gherkin_dynamic.py`](../../tests/ers/test_gherkin_dynamic.py)

---

## Estado de automatizaciÃ³n backend

Implementada en `tests/ers/gherkin_impl.py` (comprueba API/servicios equivalentes al Then del ERS).


<!-- file: RF006-S03.md -->

# Despacho de venta al por menor sin registro obligatorio de cliente

## Nombre del test

`tests/ers/test_gherkin_dynamic.py::test_RF006_S03`

## PropÃ³sito

Validar el criterio de aceptaciÃ³n Gherkin del ERS ICM para **RF006** â€” escenario 3.

## Requisito o caso de negocio asociado

- **Requisito:** `RF006` (ver `docs/requisitos/ERS_ICM_Requisitos.md`).

## Inputs (Given / When â€” extracto ERS)

**Given (Dado que):**
- El usuario autenticado tiene rol "Auxiliar de Despacho" o "Almacenista"

**When (Cuando):**
- Selecciona el tipo de salida "Venta al por Menor"
- Completa el formulario sin registrar datos del cliente
- La validaciÃ³n cruzada del producto es exitosa
- Confirma el despacho

**Then (Entonces):**
- El sistema acepta la operaciÃ³n sin exigir datos del cliente
- Genera el movimiento de salida con trazabilidad completa
- Genera la factura o remisiÃ³n digital en PDF

---

## Resultado esperado (Then)

Ver secciÃ³n **Then** en el extracto anterior del ERS. En automatizaciÃ³n backend, el test asociado comprueba el contrato API/servicio equivalente o queda explÃ­citamente marcado como pendiente si el criterio es solo UI, infraestructura o legalidad operativa fuera del alcance de pytest.

## Link directo al test

Ejecutar:

```bash
pytest tests/ers/test_gherkin_dynamic.py::test_RF006_S03 -v
```

Archivo de definiciÃ³n dinÃ¡mica: [`tests/ers/test_gherkin_dynamic.py`](../../tests/ers/test_gherkin_dynamic.py)

---

## Estado de automatizaciÃ³n backend

Implementada en `tests/ers/gherkin_impl.py` (comprueba API/servicios equivalentes al Then del ERS).


<!-- file: RF006-S04.md -->

# Registro de baja por daÃ±o

## Nombre del test

`tests/ers/test_gherkin_dynamic.py::test_RF006_S04`

## PropÃ³sito

Validar el criterio de aceptaciÃ³n Gherkin del ERS ICM para **RF006** â€” escenario 4.

## Requisito o caso de negocio asociado

- **Requisito:** `RF006` (ver `docs/requisitos/ERS_ICM_Requisitos.md`).

## Inputs (Given / When â€” extracto ERS)

**Given (Dado que):**
- El usuario autenticado tiene rol "Auxiliar de Despacho" o "Almacenista"

**When (Cuando):**
- Selecciona el tipo de salida "DaÃ±o"
- Ingresa el nÃºmero de unidades afectadas
- Registra una nota descriptiva del daÃ±o detectado
- Confirma la operaciÃ³n

**Then (Entonces):**
- El sistema descuenta las unidades del stock en la ubicaciÃ³n correspondiente
- Registra el movimiento como "baja por daÃ±o", no como venta
- La nota descriptiva queda vinculada de forma inmutable al movimiento
- Genera el documento de remisiÃ³n en PDF reflejando el tipo de baja

---

## Resultado esperado (Then)

Ver secciÃ³n **Then** en el extracto anterior del ERS. En automatizaciÃ³n backend, el test asociado comprueba el contrato API/servicio equivalente o queda explÃ­citamente marcado como pendiente si el criterio es solo UI, infraestructura o legalidad operativa fuera del alcance de pytest.

## Link directo al test

Ejecutar:

```bash
pytest tests/ers/test_gherkin_dynamic.py::test_RF006_S04 -v
```

Archivo de definiciÃ³n dinÃ¡mica: [`tests/ers/test_gherkin_dynamic.py`](../../tests/ers/test_gherkin_dynamic.py)

---

## Estado de automatizaciÃ³n backend

Implementada en `tests/ers/gherkin_impl.py` (comprueba API/servicios equivalentes al Then del ERS).


<!-- file: RF006-S05.md -->

# Registro de baja por vencimiento

## Nombre del test

`tests/ers/test_gherkin_dynamic.py::test_RF006_S05`

## PropÃ³sito

Validar el criterio de aceptaciÃ³n Gherkin del ERS ICM para **RF006** â€” escenario 5.

## Requisito o caso de negocio asociado

- **Requisito:** `RF006` (ver `docs/requisitos/ERS_ICM_Requisitos.md`).

## Inputs (Given / When â€” extracto ERS)

**Given (Dado que):**
- El usuario autenticado tiene rol "Auxiliar de Despacho" o "Almacenista"
- Existen productos con alertas de vencimiento activas

**When (Cuando):**
- Selecciona el tipo de salida "Vencimiento"
- Selecciona el producto y el lote afectado
- Confirma la operaciÃ³n

**Then (Entonces):**
- El sistema descuenta las unidades del stock en la ubicaciÃ³n correspondiente
- Registra el movimiento como "baja por vencimiento"
- Vincula la fecha de vencimiento del lote al registro del movimiento
- El movimiento queda inmutable con trazabilidad completa

---

## Resultado esperado (Then)

Ver secciÃ³n **Then** en el extracto anterior del ERS. En automatizaciÃ³n backend, el test asociado comprueba el contrato API/servicio equivalente o queda explÃ­citamente marcado como pendiente si el criterio es solo UI, infraestructura o legalidad operativa fuera del alcance de pytest.

## Link directo al test

Ejecutar:

```bash
pytest tests/ers/test_gherkin_dynamic.py::test_RF006_S05 -v
```

Archivo de definiciÃ³n dinÃ¡mica: [`tests/ers/test_gherkin_dynamic.py`](../../tests/ers/test_gherkin_dynamic.py)

---

## Estado de automatizaciÃ³n backend

Implementada en `tests/ers/gherkin_impl.py` (comprueba API/servicios equivalentes al Then del ERS).


<!-- file: RF006-S06.md -->

# Advertencia por peso total del despacho excede capacidad del vehÃ­culo

## Nombre del test

`tests/ers/test_gherkin_dynamic.py::test_RF006_S06`

## PropÃ³sito

Validar el criterio de aceptaciÃ³n Gherkin del ERS ICM para **RF006** â€” escenario 6.

## Requisito o caso de negocio asociado

- **Requisito:** `RF006` (ver `docs/requisitos/ERS_ICM_Requisitos.md`).

## Inputs (Given / When â€” extracto ERS)

**Given (Dado que):**
- El usuario autenticado tiene rol "Auxiliar de Despacho" o "Almacenista"
- El tipo de salida es "Venta al por Mayor"
- El sistema tiene configurada la capacidad mÃ¡xima del vehÃ­culo de transporte

**When (Cuando):**
- El peso total calculado de todos los Ã­tems del despacho supera la capacidad mÃ¡xima configurada

**Then (Entonces):**
- El sistema emite una advertencia visible al operario indicando que la carga excede la capacidad del vehÃ­culo
- Permite al operario revisar y ajustar el despacho
- No bloquea la operaciÃ³n de forma definitiva, ya que la decisiÃ³n final corresponde al operario responsable

---

## Resultado esperado (Then)

Ver secciÃ³n **Then** en el extracto anterior del ERS. En automatizaciÃ³n backend, el test asociado comprueba el contrato API/servicio equivalente o queda explÃ­citamente marcado como pendiente si el criterio es solo UI, infraestructura o legalidad operativa fuera del alcance de pytest.

## Link directo al test

Ejecutar:

```bash
pytest tests/ers/test_gherkin_dynamic.py::test_RF006_S06 -v
```

Archivo de definiciÃ³n dinÃ¡mica: [`tests/ers/test_gherkin_dynamic.py`](../../tests/ers/test_gherkin_dynamic.py)

---

## Estado de automatizaciÃ³n backend

Implementada en `tests/ers/gherkin_impl.py` (comprueba API/servicios equivalentes al Then del ERS).


<!-- file: RF006-S07.md -->

# Despacho cuando el lector de cÃ³digo de barras no estÃ¡ disponible

## Nombre del test

`tests/ers/test_gherkin_dynamic.py::test_RF006_S07`

## PropÃ³sito

Validar el criterio de aceptaciÃ³n Gherkin del ERS ICM para **RF006** â€” escenario 7.

## Requisito o caso de negocio asociado

- **Requisito:** `RF006` (ver `docs/requisitos/ERS_ICM_Requisitos.md`).

## Inputs (Given / When â€” extracto ERS)

**Given (Dado que):**
- El usuario autenticado tiene rol "Auxiliar de Despacho" o "Almacenista"
- El lector de cÃ³digo de barras no estÃ¡ conectado o no es reconocido

**When (Cuando):**
- El sistema detecta la ausencia del lector

**Then (Entonces):**
- Muestra una notificaciÃ³n visible pero no interrumpe el flujo de despacho
- Permite al operario identificar el producto ingresando manualmente el cÃ³digo de barras, el SKU, el cÃ³digo serial o buscando por nombre
- La validaciÃ³n cruzada se ejecuta igualmente usando el valor ingresado

## Resultado esperado (Then)

Ver secciÃ³n **Then** en el extracto anterior del ERS. En automatizaciÃ³n backend, el test asociado comprueba el contrato API/servicio equivalente o queda explÃ­citamente marcado como pendiente si el criterio es solo UI, infraestructura o legalidad operativa fuera del alcance de pytest.

## Link directo al test

Ejecutar:

```bash
pytest tests/ers/test_gherkin_dynamic.py::test_RF006_S07 -v
```

Archivo de definiciÃ³n dinÃ¡mica: [`tests/ers/test_gherkin_dynamic.py`](../../tests/ers/test_gherkin_dynamic.py)

---

## Estado de automatizaciÃ³n backend

Implementada en `tests/ers/gherkin_impl.py` (comprueba API/servicios equivalentes al Then del ERS).


<!-- file: RF007-S01.md -->

# Traslado exitoso de producto entre ubicaciones con stock suficiente

## Nombre del test

`tests/ers/test_gherkin_dynamic.py::test_RF007_S01`

## PropÃ³sito

Validar el criterio de aceptaciÃ³n Gherkin del ERS ICM para **RF007** â€” escenario 1.

## Requisito o caso de negocio asociado

- **Requisito:** `RF007` (ver `docs/requisitos/ERS_ICM_Requisitos.md`).

## Inputs (Given / When â€” extracto ERS)

**Given (Dado que):**
- El usuario autenticado tiene rol "Auxiliar de Despacho" o "Almacenista"
- El producto existe en el catÃ¡logo
- La ubicaciÃ³n de origen tiene stock suficiente para cubrir la cantidad a trasladar

**When (Cuando):**
- Selecciona el producto a trasladar
- Indica la cantidad, la ubicaciÃ³n de origen y la ubicaciÃ³n de destino
- Confirma el traslado

**Then (Entonces):**
- El sistema resta la cantidad indicada del stock en la ubicaciÃ³n de origen
- Suma esa misma cantidad al stock en la ubicaciÃ³n de destino
- El stock total global del producto permanece sin cambios
- Genera un movimiento inmutable con UserID, timestamp, producto, cantidad, ubicaciÃ³n de origen, ubicaciÃ³n de destino, stock previo y stock resultante por ubicaciÃ³n

---

## Resultado esperado (Then)

Ver secciÃ³n **Then** en el extracto anterior del ERS. En automatizaciÃ³n backend, el test asociado comprueba el contrato API/servicio equivalente o queda explÃ­citamente marcado como pendiente si el criterio es solo UI, infraestructura o legalidad operativa fuera del alcance de pytest.

## Link directo al test

Ejecutar:

```bash
pytest tests/ers/test_gherkin_dynamic.py::test_RF007_S01 -v
```

Archivo de definiciÃ³n dinÃ¡mica: [`tests/ers/test_gherkin_dynamic.py`](../../tests/ers/test_gherkin_dynamic.py)

---

## Estado de automatizaciÃ³n backend

Implementada en `tests/ers/gherkin_impl.py` (comprueba API/servicios equivalentes al Then del ERS).


<!-- file: RF007-S02.md -->

# Intento de traslado con stock insuficiente en la ubicaciÃ³n de origen

## Nombre del test

`tests/ers/test_gherkin_dynamic.py::test_RF007_S02`

## PropÃ³sito

Validar el criterio de aceptaciÃ³n Gherkin del ERS ICM para **RF007** â€” escenario 2.

## Requisito o caso de negocio asociado

- **Requisito:** `RF007` (ver `docs/requisitos/ERS_ICM_Requisitos.md`).

## Inputs (Given / When â€” extracto ERS)

**Given (Dado que):**
- El usuario autenticado tiene rol "Auxiliar de Despacho" o "Almacenista"
- El producto tiene 3 unidades disponibles en Bodega 1

**When (Cuando):**
- Intenta registrar un traslado de 5 unidades desde Bodega 1 hacia cualquier otra ubicaciÃ³n

**Then (Entonces):**
- El sistema bloquea la operaciÃ³n
- Muestra un mensaje indicando que el stock disponible en la ubicaciÃ³n de origen es insuficiente
- No genera ningÃºn movimiento ni modifica el stock en ninguna ubicaciÃ³n

---

## Resultado esperado (Then)

Ver secciÃ³n **Then** en el extracto anterior del ERS. En automatizaciÃ³n backend, el test asociado comprueba el contrato API/servicio equivalente o queda explÃ­citamente marcado como pendiente si el criterio es solo UI, infraestructura o legalidad operativa fuera del alcance de pytest.

## Link directo al test

Ejecutar:

```bash
pytest tests/ers/test_gherkin_dynamic.py::test_RF007_S02 -v
```

Archivo de definiciÃ³n dinÃ¡mica: [`tests/ers/test_gherkin_dynamic.py`](../../tests/ers/test_gherkin_dynamic.py)

---

## Estado de automatizaciÃ³n backend

Implementada en `tests/ers/gherkin_impl.py` (comprueba API/servicios equivalentes al Then del ERS).


<!-- file: RF007-S03.md -->

# Intento de traslado hacia la misma ubicaciÃ³n de origen

## Nombre del test

`tests/ers/test_gherkin_dynamic.py::test_RF007_S03`

## PropÃ³sito

Validar el criterio de aceptaciÃ³n Gherkin del ERS ICM para **RF007** â€” escenario 3.

## Requisito o caso de negocio asociado

- **Requisito:** `RF007` (ver `docs/requisitos/ERS_ICM_Requisitos.md`).

## Inputs (Given / When â€” extracto ERS)

**Given (Dado que):**
- El usuario autenticado tiene rol "Auxiliar de Despacho" o "Almacenista"

**When (Cuando):**
- Selecciona la misma ubicaciÃ³n como origen y como destino del traslado

**Then (Entonces):**
- El sistema rechaza la operaciÃ³n
- Muestra un mensaje indicando que el origen y el destino no pueden ser la misma ubicaciÃ³n
- No genera ningÃºn movimiento

---

## Resultado esperado (Then)

Ver secciÃ³n **Then** en el extracto anterior del ERS. En automatizaciÃ³n backend, el test asociado comprueba el contrato API/servicio equivalente o queda explÃ­citamente marcado como pendiente si el criterio es solo UI, infraestructura o legalidad operativa fuera del alcance de pytest.

## Link directo al test

Ejecutar:

```bash
pytest tests/ers/test_gherkin_dynamic.py::test_RF007_S03 -v
```

Archivo de definiciÃ³n dinÃ¡mica: [`tests/ers/test_gherkin_dynamic.py`](../../tests/ers/test_gherkin_dynamic.py)

---

## Estado de automatizaciÃ³n backend

Implementada en `tests/ers/gherkin_impl.py` (comprueba API/servicios equivalentes al Then del ERS).


<!-- file: RF007-S04.md -->

# Auxiliar corrige un traslado dentro de la misma franja horaria activa

## Nombre del test

`tests/ers/test_gherkin_dynamic.py::test_RF007_S04`

## PropÃ³sito

Validar el criterio de aceptaciÃ³n Gherkin del ERS ICM para **RF007** â€” escenario 4.

## Requisito o caso de negocio asociado

- **Requisito:** `RF007` (ver `docs/requisitos/ERS_ICM_Requisitos.md`).

## Inputs (Given / When â€” extracto ERS)

**Given (Dado que):**
- El usuario autenticado tiene rol "Auxiliar de Despacho"
- RegistrÃ³ un traslado durante la franja horaria activa actual
- La franja horaria aÃºn no ha cerrado

**When (Cuando):**
- Detecta un error en el registro y accede a la opciÃ³n de ediciÃ³n
- Corrige los datos incorrectos y confirma los cambios

**Then (Entonces):**
- El sistema permite la correcciÃ³n
- Actualiza el registro reflejando los valores corregidos
- Deja constancia en el log de auditorÃ­a de que el registro fue editado, indicando el UserID del auxiliar y el timestamp de la correcciÃ³n

---

## Resultado esperado (Then)

Ver secciÃ³n **Then** en el extracto anterior del ERS. En automatizaciÃ³n backend, el test asociado comprueba el contrato API/servicio equivalente o queda explÃ­citamente marcado como pendiente si el criterio es solo UI, infraestructura o legalidad operativa fuera del alcance de pytest.

## Link directo al test

Ejecutar:

```bash
pytest tests/ers/test_gherkin_dynamic.py::test_RF007_S04 -v
```

Archivo de definiciÃ³n dinÃ¡mica: [`tests/ers/test_gherkin_dynamic.py`](../../tests/ers/test_gherkin_dynamic.py)

---

## Estado de automatizaciÃ³n backend

Implementada en `tests/ers/gherkin_impl.py` (comprueba API/servicios equivalentes al Then del ERS).


<!-- file: RF007-S05.md -->

# Auxiliar intenta corregir un traslado despuÃ©s de cerrada la franja horaria

## Nombre del test

`tests/ers/test_gherkin_dynamic.py::test_RF007_S05`

## PropÃ³sito

Validar el criterio de aceptaciÃ³n Gherkin del ERS ICM para **RF007** â€” escenario 5.

## Requisito o caso de negocio asociado

- **Requisito:** `RF007` (ver `docs/requisitos/ERS_ICM_Requisitos.md`).

## Inputs (Given / When â€” extracto ERS)

**Given (Dado que):**
- El usuario autenticado tiene rol "Auxiliar de Despacho"
- RegistrÃ³ un traslado durante una franja horaria que ya cerrÃ³

**When (Cuando):**
- Intenta acceder a la opciÃ³n de ediciÃ³n de ese registro

**Then (Entonces):**
- El sistema bloquea la ediciÃ³n
- Muestra un mensaje indicando que la ventana de correcciÃ³n ha cerrado y que cualquier ajuste debe ser solicitado al Almacenista
- El registro original permanece inmutable

## Resultado esperado (Then)

Ver secciÃ³n **Then** en el extracto anterior del ERS. En automatizaciÃ³n backend, el test asociado comprueba el contrato API/servicio equivalente o queda explÃ­citamente marcado como pendiente si el criterio es solo UI, infraestructura o legalidad operativa fuera del alcance de pytest.

## Link directo al test

Ejecutar:

```bash
pytest tests/ers/test_gherkin_dynamic.py::test_RF007_S05 -v
```

Archivo de definiciÃ³n dinÃ¡mica: [`tests/ers/test_gherkin_dynamic.py`](../../tests/ers/test_gherkin_dynamic.py)

---

## Estado de automatizaciÃ³n backend

Implementada en `tests/ers/gherkin_impl.py` (comprueba API/servicios equivalentes al Then del ERS).


<!-- file: RF008-S01.md -->

# Registro exitoso de devoluciÃ³n de producto de Electroterapia

## Nombre del test

`tests/ers/test_gherkin_dynamic.py::test_RF008_S01`

## PropÃ³sito

Validar el criterio de aceptaciÃ³n Gherkin del ERS ICM para **RF008** â€” escenario 1.

## Requisito o caso de negocio asociado

- **Requisito:** `RF008` (ver `docs/requisitos/ERS_ICM_Requisitos.md`).

## Inputs (Given / When â€” extracto ERS)

**Given (Dado que):**
- El usuario autenticado tiene rol "Auxiliar de Despacho" o "Almacenista"
- El producto a devolver pertenece a la categorÃ­a "Electroterapia" o "ElectrÃ³nicos"

**When (Cuando):**
- Inicia el registro de devoluciÃ³n
- Selecciona el producto por SKU o nÃºmero de serie
- Registra el motivo declarado por el cliente
- Registra el estado fÃ­sico del producto al momento de recibirlo
- Confirma la devoluciÃ³n

**Then (Entonces):**
- El sistema genera un log inmutable de la devoluciÃ³n con SKU, nÃºmero de serie, motivo, estado del producto, UserID del operario y timestamp exacto
- El producto queda en estado "Pendiente de revisiÃ³n" sin ser reincorporado al stock disponible todavÃ­a
- El Almacenista recibe una notificaciÃ³n de que hay una devoluciÃ³n pendiente de aprobaciÃ³n

---

## Resultado esperado (Then)

Ver secciÃ³n **Then** en el extracto anterior del ERS. En automatizaciÃ³n backend, el test asociado comprueba el contrato API/servicio equivalente o queda explÃ­citamente marcado como pendiente si el criterio es solo UI, infraestructura o legalidad operativa fuera del alcance de pytest.

## Link directo al test

Ejecutar:

```bash
pytest tests/ers/test_gherkin_dynamic.py::test_RF008_S01 -v
```

Archivo de definiciÃ³n dinÃ¡mica: [`tests/ers/test_gherkin_dynamic.py`](../../tests/ers/test_gherkin_dynamic.py)

---

## Estado de automatizaciÃ³n backend

Implementada en `tests/ers/gherkin_impl.py` (comprueba API/servicios equivalentes al Then del ERS).


<!-- file: RF008-S02.md -->

# Intento de devoluciÃ³n de producto que no es Electroterapia ni ElectrÃ³nico

## Nombre del test

`tests/ers/test_gherkin_dynamic.py::test_RF008_S02`

## PropÃ³sito

Validar el criterio de aceptaciÃ³n Gherkin del ERS ICM para **RF008** â€” escenario 2.

## Requisito o caso de negocio asociado

- **Requisito:** `RF008` (ver `docs/requisitos/ERS_ICM_Requisitos.md`).

## Inputs (Given / When â€” extracto ERS)

**Given (Dado que):**
- El usuario autenticado tiene rol "Auxiliar de Despacho" o "Almacenista"
- El producto seleccionado pertenece a la categorÃ­a "Manoterapia" o "Mesas de Fisioterapia"

**When (Cuando):**
- Intenta iniciar el registro de una devoluciÃ³n para ese producto

**Then (Entonces):**
- El sistema bloquea la operaciÃ³n de forma inmediata
- Muestra un mensaje descriptivo indicando que ese tipo de producto no admite devoluciones segÃºn la polÃ­tica de ICM
- No genera ningÃºn registro ni modifica el stock

---

## Resultado esperado (Then)

Ver secciÃ³n **Then** en el extracto anterior del ERS. En automatizaciÃ³n backend, el test asociado comprueba el contrato API/servicio equivalente o queda explÃ­citamente marcado como pendiente si el criterio es solo UI, infraestructura o legalidad operativa fuera del alcance de pytest.

## Link directo al test

Ejecutar:

```bash
pytest tests/ers/test_gherkin_dynamic.py::test_RF008_S02 -v
```

Archivo de definiciÃ³n dinÃ¡mica: [`tests/ers/test_gherkin_dynamic.py`](../../tests/ers/test_gherkin_dynamic.py)

---

## Estado de automatizaciÃ³n backend

Implementada en `tests/ers/gherkin_impl.py` (comprueba API/servicios equivalentes al Then del ERS).


<!-- file: RF008-S03.md -->

# Almacenista aprueba la reincorporaciÃ³n al stock de un producto devuelto

## Nombre del test

`tests/ers/test_gherkin_dynamic.py::test_RF008_S03`

## PropÃ³sito

Validar el criterio de aceptaciÃ³n Gherkin del ERS ICM para **RF008** â€” escenario 3.

## Requisito o caso de negocio asociado

- **Requisito:** `RF008` (ver `docs/requisitos/ERS_ICM_Requisitos.md`).

## Inputs (Given / When â€” extracto ERS)

**Given (Dado que):**
- El usuario autenticado tiene rol "Almacenista"
- Existe una devoluciÃ³n en estado "Pendiente de revisiÃ³n"

**When (Cuando):**
- Accede al listado de devoluciones pendientes
- Revisa el log de la devoluciÃ³n incluyendo motivo y estado del producto
- Aprueba la reincorporaciÃ³n al stock
- Selecciona la ubicaciÃ³n de destino donde se reincorporarÃ¡ el producto

**Then (Entonces):**
- El sistema incrementa el stock del producto en la ubicaciÃ³n seleccionada
- Actualiza el estado de la devoluciÃ³n a "Reincorporado"
- Registra la aprobaciÃ³n en el log con el UserID del Almacenista y timestamp
- El movimiento de reincorporaciÃ³n queda vinculado al log original de la devoluciÃ³n

---

## Resultado esperado (Then)

Ver secciÃ³n **Then** en el extracto anterior del ERS. En automatizaciÃ³n backend, el test asociado comprueba el contrato API/servicio equivalente o queda explÃ­citamente marcado como pendiente si el criterio es solo UI, infraestructura o legalidad operativa fuera del alcance de pytest.

## Link directo al test

Ejecutar:

```bash
pytest tests/ers/test_gherkin_dynamic.py::test_RF008_S03 -v
```

Archivo de definiciÃ³n dinÃ¡mica: [`tests/ers/test_gherkin_dynamic.py`](../../tests/ers/test_gherkin_dynamic.py)

---

## Estado de automatizaciÃ³n backend

Implementada en `tests/ers/gherkin_impl.py` (comprueba API/servicios equivalentes al Then del ERS).


<!-- file: RF008-S04.md -->

# Almacenista rechaza la reincorporaciÃ³n de un producto devuelto

## Nombre del test

`tests/ers/test_gherkin_dynamic.py::test_RF008_S04`

## PropÃ³sito

Validar el criterio de aceptaciÃ³n Gherkin del ERS ICM para **RF008** â€” escenario 4.

## Requisito o caso de negocio asociado

- **Requisito:** `RF008` (ver `docs/requisitos/ERS_ICM_Requisitos.md`).

## Inputs (Given / When â€” extracto ERS)

**Given (Dado que):**
- El usuario autenticado tiene rol "Almacenista"
- Existe una devoluciÃ³n en estado "Pendiente de revisiÃ³n"

**When (Cuando):**
- Revisa el log de la devoluciÃ³n
- Determina que el producto no estÃ¡ en condiciones de ser reincorporado
- Rechaza la reincorporaciÃ³n registrando el motivo del rechazo

**Then (Entonces):**
- El sistema actualiza el estado de la devoluciÃ³n a "Rechazada"
- No modifica el stock disponible en ninguna ubicaciÃ³n
- El motivo del rechazo queda vinculado al log original de la devoluciÃ³n
- El registro completo permanece inmutable para efectos de auditorÃ­a

---

## Resultado esperado (Then)

Ver secciÃ³n **Then** en el extracto anterior del ERS. En automatizaciÃ³n backend, el test asociado comprueba el contrato API/servicio equivalente o queda explÃ­citamente marcado como pendiente si el criterio es solo UI, infraestructura o legalidad operativa fuera del alcance de pytest.

## Link directo al test

Ejecutar:

```bash
pytest tests/ers/test_gherkin_dynamic.py::test_RF008_S04 -v
```

Archivo de definiciÃ³n dinÃ¡mica: [`tests/ers/test_gherkin_dynamic.py`](../../tests/ers/test_gherkin_dynamic.py)

---

## Estado de automatizaciÃ³n backend

Implementada en `tests/ers/gherkin_impl.py` (comprueba API/servicios equivalentes al Then del ERS).


<!-- file: RF008-S05.md -->

# Consulta del historial de devoluciones por el Almacenista

## Nombre del test

`tests/ers/test_gherkin_dynamic.py::test_RF008_S05`

## PropÃ³sito

Validar el criterio de aceptaciÃ³n Gherkin del ERS ICM para **RF008** â€” escenario 5.

## Requisito o caso de negocio asociado

- **Requisito:** `RF008` (ver `docs/requisitos/ERS_ICM_Requisitos.md`).

## Inputs (Given / When â€” extracto ERS)

**Given (Dado que):**
- El usuario autenticado tiene rol "Almacenista"

**When (Cuando):**
- Accede al historial de devoluciones

**Then (Entonces):**
- El sistema muestra todas las devoluciones registradas con su estado actual (Pendiente, Reincorporado o Rechazada)
- Permite filtrar por producto, perÃ­odo, operario o estado
- Cada registro del historial es de solo lectura e inmutable

## Resultado esperado (Then)

Ver secciÃ³n **Then** en el extracto anterior del ERS. En automatizaciÃ³n backend, el test asociado comprueba el contrato API/servicio equivalente o queda explÃ­citamente marcado como pendiente si el criterio es solo UI, infraestructura o legalidad operativa fuera del alcance de pytest.

## Link directo al test

Ejecutar:

```bash
pytest tests/ers/test_gherkin_dynamic.py::test_RF008_S05 -v
```

Archivo de definiciÃ³n dinÃ¡mica: [`tests/ers/test_gherkin_dynamic.py`](../../tests/ers/test_gherkin_dynamic.py)

---

## Estado de automatizaciÃ³n backend

Implementada en `tests/ers/gherkin_impl.py` (comprueba API/servicios equivalentes al Then del ERS).


<!-- file: RF009-S01.md -->

# Almacenista registra un ajuste de inventario con justificaciÃ³n

## Nombre del test

`tests/ers/test_gherkin_dynamic.py::test_RF009_S01`

## PropÃ³sito

Validar el criterio de aceptaciÃ³n Gherkin del ERS ICM para **RF009** â€” escenario 1.

## Requisito o caso de negocio asociado

- **Requisito:** `RF009` (ver `docs/requisitos/ERS_ICM_Requisitos.md`).

## Inputs (Given / When â€” extracto ERS)

**Given (Dado que):**
- El usuario autenticado tiene rol "Almacenista"
- Existe una discrepancia entre el stock fÃ­sico real y el stock registrado en el sistema

**When (Cuando):**
- Accede al mÃ³dulo de ajustes de inventario
- Selecciona el producto y la ubicaciÃ³n donde ocurre la discrepancia
- Ingresa el nuevo valor de stock correcto
- Registra una justificaciÃ³n obligatoria explicando la causa de la discrepancia
- Confirma el ajuste

**Then (Entonces):**
- El sistema actualiza el stock del producto en la ubicaciÃ³n indicada
- Genera un log inmutable del ajuste con UserID del Almacenista, timestamp, producto, ubicaciÃ³n, stock previo, stock ajustado, delta de la diferencia y justificaciÃ³n registrada
- Recalcula el stock total consolidado del producto

---

## Resultado esperado (Then)

Ver secciÃ³n **Then** en el extracto anterior del ERS. En automatizaciÃ³n backend, el test asociado comprueba el contrato API/servicio equivalente o queda explÃ­citamente marcado como pendiente si el criterio es solo UI, infraestructura o legalidad operativa fuera del alcance de pytest.

## Link directo al test

Ejecutar:

```bash
pytest tests/ers/test_gherkin_dynamic.py::test_RF009_S01 -v
```

Archivo de definiciÃ³n dinÃ¡mica: [`tests/ers/test_gherkin_dynamic.py`](../../tests/ers/test_gherkin_dynamic.py)

---

## Estado de automatizaciÃ³n backend

Implementada en `tests/ers/gherkin_impl.py` (comprueba API/servicios equivalentes al Then del ERS).


<!-- file: RF009-S02.md -->

# Intento de registrar un ajuste sin justificaciÃ³n

## Nombre del test

`tests/ers/test_gherkin_dynamic.py::test_RF009_S02`

## PropÃ³sito

Validar el criterio de aceptaciÃ³n Gherkin del ERS ICM para **RF009** â€” escenario 2.

## Requisito o caso de negocio asociado

- **Requisito:** `RF009` (ver `docs/requisitos/ERS_ICM_Requisitos.md`).

## Inputs (Given / When â€” extracto ERS)

**Given (Dado que):**
- El usuario autenticado tiene rol "Almacenista"

**When (Cuando):**
- Completa el formulario de ajuste dejando vacÃ­o el campo de justificaciÃ³n
- Intenta confirmar el ajuste

**Then (Entonces):**
- El sistema bloquea la operaciÃ³n
- Muestra un mensaje indicando que la justificaciÃ³n es un campo obligatorio
- No modifica el stock ni genera ningÃºn registro

---

## Resultado esperado (Then)

Ver secciÃ³n **Then** en el extracto anterior del ERS. En automatizaciÃ³n backend, el test asociado comprueba el contrato API/servicio equivalente o queda explÃ­citamente marcado como pendiente si el criterio es solo UI, infraestructura o legalidad operativa fuera del alcance de pytest.

## Link directo al test

Ejecutar:

```bash
pytest tests/ers/test_gherkin_dynamic.py::test_RF009_S02 -v
```

Archivo de definiciÃ³n dinÃ¡mica: [`tests/ers/test_gherkin_dynamic.py`](../../tests/ers/test_gherkin_dynamic.py)

---

## Estado de automatizaciÃ³n backend

Implementada en `tests/ers/gherkin_impl.py` (comprueba API/servicios equivalentes al Then del ERS).


<!-- file: RF009-S03.md -->

# Auxiliar de Despacho intenta ejecutar un ajuste formal

## Nombre del test

`tests/ers/test_gherkin_dynamic.py::test_RF009_S03`

## PropÃ³sito

Validar el criterio de aceptaciÃ³n Gherkin del ERS ICM para **RF009** â€” escenario 3.

## Requisito o caso de negocio asociado

- **Requisito:** `RF009` (ver `docs/requisitos/ERS_ICM_Requisitos.md`).

## Inputs (Given / When â€” extracto ERS)

**Given (Dado que):**
- El usuario autenticado tiene rol "Auxiliar de Despacho"

**When (Cuando):**
- Intenta acceder al mÃ³dulo de ajustes de inventario

**Then (Entonces):**
- El sistema bloquea el acceso
- Muestra un mensaje indicando que esta funcionalidad estÃ¡ reservada exclusivamente para el Almacenista
- No genera ningÃºn cambio en el sistema

---

## Resultado esperado (Then)

Ver secciÃ³n **Then** en el extracto anterior del ERS. En automatizaciÃ³n backend, el test asociado comprueba el contrato API/servicio equivalente o queda explÃ­citamente marcado como pendiente si el criterio es solo UI, infraestructura o legalidad operativa fuera del alcance de pytest.

## Link directo al test

Ejecutar:

```bash
pytest tests/ers/test_gherkin_dynamic.py::test_RF009_S03 -v
```

Archivo de definiciÃ³n dinÃ¡mica: [`tests/ers/test_gherkin_dynamic.py`](../../tests/ers/test_gherkin_dynamic.py)

---

## Estado de automatizaciÃ³n backend

Implementada en `tests/ers/gherkin_impl.py` (comprueba API/servicios equivalentes al Then del ERS).


<!-- file: RF009-S04.md -->

# CorrecciÃ³n de un ajuste registrado incorrectamente

## Nombre del test

`tests/ers/test_gherkin_dynamic.py::test_RF009_S04`

## PropÃ³sito

Validar el criterio de aceptaciÃ³n Gherkin del ERS ICM para **RF009** â€” escenario 4.

## Requisito o caso de negocio asociado

- **Requisito:** `RF009` (ver `docs/requisitos/ERS_ICM_Requisitos.md`).

## Inputs (Given / When â€” extracto ERS)

**Given (Dado que):**
- El usuario autenticado tiene rol "Almacenista"
- Existe un ajuste previo registrado con valores incorrectos

**When (Cuando):**
- Determina que el ajuste anterior fue errÃ³neo
- Registra un nuevo ajuste con los valores correctos
- Proporciona una justificaciÃ³n que referencia el ajuste anterior
- Confirma el nuevo ajuste

**Then (Entonces):**
- El sistema registra el nuevo ajuste como un movimiento independiente
- El ajuste anterior permanece inmutable en el historial
- Ambos registros quedan vinculados en el log de auditorÃ­a
- El stock refleja el valor correcto segÃºn el ajuste mÃ¡s reciente

---

## Resultado esperado (Then)

Ver secciÃ³n **Then** en el extracto anterior del ERS. En automatizaciÃ³n backend, el test asociado comprueba el contrato API/servicio equivalente o queda explÃ­citamente marcado como pendiente si el criterio es solo UI, infraestructura o legalidad operativa fuera del alcance de pytest.

## Link directo al test

Ejecutar:

```bash
pytest tests/ers/test_gherkin_dynamic.py::test_RF009_S04 -v
```

Archivo de definiciÃ³n dinÃ¡mica: [`tests/ers/test_gherkin_dynamic.py`](../../tests/ers/test_gherkin_dynamic.py)

---

## Estado de automatizaciÃ³n backend

Implementada en `tests/ers/gherkin_impl.py` (comprueba API/servicios equivalentes al Then del ERS).


<!-- file: RF009-S05.md -->

# Auxiliar corrige su propio movimiento dentro de la franja horaria activa

## Nombre del test

`tests/ers/test_gherkin_dynamic.py::test_RF009_S05`

## PropÃ³sito

Validar el criterio de aceptaciÃ³n Gherkin del ERS ICM para **RF009** â€” escenario 5.

## Requisito o caso de negocio asociado

- **Requisito:** `RF009` (ver `docs/requisitos/ERS_ICM_Requisitos.md`).

## Inputs (Given / When â€” extracto ERS)

**Given (Dado que):**
- El usuario autenticado tiene rol "Auxiliar de Despacho"
- RegistrÃ³ un movimiento durante la franja horaria activa actual
- La franja horaria aÃºn no ha cerrado

**When (Cuando):**
- Detecta el error y accede a la opciÃ³n de ediciÃ³n del movimiento
- Corrige los valores incorrectos y confirma el cambio

**Then (Entonces):**
- El sistema permite la correcciÃ³n sin requerir intervenciÃ³n del Almacenista
- Registra en el log de auditorÃ­a que el movimiento fue editado con el UserID del auxiliar y el timestamp de la correcciÃ³n
- El movimiento corregido refleja los valores actualizados

---

## Resultado esperado (Then)

Ver secciÃ³n **Then** en el extracto anterior del ERS. En automatizaciÃ³n backend, el test asociado comprueba el contrato API/servicio equivalente o queda explÃ­citamente marcado como pendiente si el criterio es solo UI, infraestructura o legalidad operativa fuera del alcance de pytest.

## Link directo al test

Ejecutar:

```bash
pytest tests/ers/test_gherkin_dynamic.py::test_RF009_S05 -v
```

Archivo de definiciÃ³n dinÃ¡mica: [`tests/ers/test_gherkin_dynamic.py`](../../tests/ers/test_gherkin_dynamic.py)

---

## Estado de automatizaciÃ³n backend

Implementada en `tests/ers/gherkin_impl.py` (comprueba API/servicios equivalentes al Then del ERS).


<!-- file: RF009-S06.md -->

# Consulta del historial completo de ajustes por el Almacenista

## Nombre del test

`tests/ers/test_gherkin_dynamic.py::test_RF009_S06`

## PropÃ³sito

Validar el criterio de aceptaciÃ³n Gherkin del ERS ICM para **RF009** â€” escenario 6.

## Requisito o caso de negocio asociado

- **Requisito:** `RF009` (ver `docs/requisitos/ERS_ICM_Requisitos.md`).

## Inputs (Given / When â€” extracto ERS)

**Given (Dado que):**
- El usuario autenticado tiene rol "Almacenista"

**When (Cuando):**
- Accede al historial de ajustes de inventario

**Then (Entonces):**
- El sistema muestra todos los ajustes registrados en orden cronolÃ³gico
- Para cada ajuste despliega el producto, ubicaciÃ³n, stock previo, stock ajustado, delta, justificaciÃ³n, UserID y timestamp
- Permite filtrar por producto, perÃ­odo o usuario responsable
- Todos los registros son de solo lectura e inmutables

## Resultado esperado (Then)

Ver secciÃ³n **Then** en el extracto anterior del ERS. En automatizaciÃ³n backend, el test asociado comprueba el contrato API/servicio equivalente o queda explÃ­citamente marcado como pendiente si el criterio es solo UI, infraestructura o legalidad operativa fuera del alcance de pytest.

## Link directo al test

Ejecutar:

```bash
pytest tests/ers/test_gherkin_dynamic.py::test_RF009_S06 -v
```

Archivo de definiciÃ³n dinÃ¡mica: [`tests/ers/test_gherkin_dynamic.py`](../../tests/ers/test_gherkin_dynamic.py)

---

## Estado de automatizaciÃ³n backend

Implementada en `tests/ers/gherkin_impl.py` (comprueba API/servicios equivalentes al Then del ERS).


<!-- file: RF010-S01.md -->

# Almacenista consulta el reporte de ventas por perÃ­odo

## Nombre del test

`tests/ers/test_gherkin_dynamic.py::test_RF010_S01`

## PropÃ³sito

Validar el criterio de aceptaciÃ³n Gherkin del ERS ICM para **RF010** â€” escenario 1.

## Requisito o caso de negocio asociado

- **Requisito:** `RF010` (ver `docs/requisitos/ERS_ICM_Requisitos.md`).

## Inputs (Given / When â€” extracto ERS)

**Given (Dado que):**
- El usuario autenticado tiene rol "Almacenista"

**When (Cuando):**
- Accede al mÃ³dulo de reportes
- Selecciona el tipo "Reporte de ventas"
- Define un rango de fechas (diario, semanal, mensual o rango personalizado)
- Aplica el filtro

**Then (Entonces):**
- El sistema muestra un reporte consolidado de todas las salidas clasificadas como venta dentro del perÃ­odo seleccionado
- Desglosa los resultados por tipo de salida (Venta al por Mayor, Venta al por Menor)
- El reporte es de solo lectura y no permite modificaciones

---

## Resultado esperado (Then)

Ver secciÃ³n **Then** en el extracto anterior del ERS. En automatizaciÃ³n backend, el test asociado comprueba el contrato API/servicio equivalente o queda explÃ­citamente marcado como pendiente si el criterio es solo UI, infraestructura o legalidad operativa fuera del alcance de pytest.

## Link directo al test

Ejecutar:

```bash
pytest tests/ers/test_gherkin_dynamic.py::test_RF010_S01 -v
```

Archivo de definiciÃ³n dinÃ¡mica: [`tests/ers/test_gherkin_dynamic.py`](../../tests/ers/test_gherkin_dynamic.py)

---

## Estado de automatizaciÃ³n backend

Implementada en `tests/ers/gherkin_impl.py` (comprueba API/servicios equivalentes al Then del ERS).


<!-- file: RF010-S02.md -->

# Administrador consulta el dashboard de KPIs operativos

## Nombre del test

`tests/ers/test_gherkin_dynamic.py::test_RF010_S02`

## PropÃ³sito

Validar el criterio de aceptaciÃ³n Gherkin del ERS ICM para **RF010** â€” escenario 2.

## Requisito o caso de negocio asociado

- **Requisito:** `RF010` (ver `docs/requisitos/ERS_ICM_Requisitos.md`).

## Inputs (Given / When â€” extracto ERS)

**Given (Dado que):**
- El usuario autenticado tiene rol "Administrador/Jefe"

**When (Cuando):**
- Accede al dashboard gerencial

**Then (Entonces):**
- El sistema presenta de forma visual e interactiva los siguientes indicadores:
  - Ãndice de rotaciÃ³n de inventario por categorÃ­a con grÃ¡ficos de tendencia
  - Porcentaje de ocupaciÃ³n por zona de almacenamiento
  - Nivel de servicio expresado como porcentaje de pedidos despachados completos y a tiempo
  - Panel de alertas operativas activas (vencimientos, stock mÃ­nimo y pedidos pendientes)
- Ninguno de estos indicadores permite ediciÃ³n desde esta vista

---

## Resultado esperado (Then)

Ver secciÃ³n **Then** en el extracto anterior del ERS. En automatizaciÃ³n backend, el test asociado comprueba el contrato API/servicio equivalente o queda explÃ­citamente marcado como pendiente si el criterio es solo UI, infraestructura o legalidad operativa fuera del alcance de pytest.

## Link directo al test

Ejecutar:

```bash
pytest tests/ers/test_gherkin_dynamic.py::test_RF010_S02 -v
```

Archivo de definiciÃ³n dinÃ¡mica: [`tests/ers/test_gherkin_dynamic.py`](../../tests/ers/test_gherkin_dynamic.py)

---

## Estado de automatizaciÃ³n backend

Implementada en `tests/ers/gherkin_impl.py` (comprueba API/servicios equivalentes al Then del ERS).


<!-- file: RF010-S03.md -->

# ExportaciÃ³n de reporte en formato Excel o CSV

## Nombre del test

`tests/ers/test_gherkin_dynamic.py::test_RF010_S03`

## PropÃ³sito

Validar el criterio de aceptaciÃ³n Gherkin del ERS ICM para **RF010** â€” escenario 3.

## Requisito o caso de negocio asociado

- **Requisito:** `RF010` (ver `docs/requisitos/ERS_ICM_Requisitos.md`).

## Inputs (Given / When â€” extracto ERS)

**Given (Dado que):**
- El usuario autenticado tiene rol "Almacenista" o "Administrador/Jefe"
- Ha generado un reporte con los filtros deseados

**When (Cuando):**
- Selecciona la opciÃ³n de exportar y elige el formato (Excel o CSV)

**Then (Entonces):**
- El sistema genera el archivo con los datos del reporte en el formato seleccionado
- Lo pone a disposiciÃ³n del usuario para su descarga inmediata
- El archivo exportado contiene exactamente los mismos datos visibles en pantalla

---

## Resultado esperado (Then)

Ver secciÃ³n **Then** en el extracto anterior del ERS. En automatizaciÃ³n backend, el test asociado comprueba el contrato API/servicio equivalente o queda explÃ­citamente marcado como pendiente si el criterio es solo UI, infraestructura o legalidad operativa fuera del alcance de pytest.

## Link directo al test

Ejecutar:

```bash
pytest tests/ers/test_gherkin_dynamic.py::test_RF010_S03 -v
```

Archivo de definiciÃ³n dinÃ¡mica: [`tests/ers/test_gherkin_dynamic.py`](../../tests/ers/test_gherkin_dynamic.py)

---

## Estado de automatizaciÃ³n backend

Implementada en `tests/ers/gherkin_impl.py` (comprueba API/servicios equivalentes al Then del ERS).


<!-- file: RF010-S04.md -->

# Consulta del historial de movimientos por operario

## Nombre del test

`tests/ers/test_gherkin_dynamic.py::test_RF010_S04`

## PropÃ³sito

Validar el criterio de aceptaciÃ³n Gherkin del ERS ICM para **RF010** â€” escenario 4.

## Requisito o caso de negocio asociado

- **Requisito:** `RF010` (ver `docs/requisitos/ERS_ICM_Requisitos.md`).

## Inputs (Given / When â€” extracto ERS)

**Given (Dado que):**
- El usuario autenticado tiene rol "Almacenista"

**When (Cuando):**
- Accede al reporte de historial de movimientos
- Filtra por un operario especÃ­fico y un perÃ­odo de tiempo

**Then (Entonces):**
- El sistema muestra todos los movimientos registrados por ese operario en el perÃ­odo
- Para cada movimiento despliega tipo de transacciÃ³n, producto, cantidad, ubicaciÃ³n, timestamp y stock resultante
- Permite exportar ese historial en Excel o CSV

---

## Resultado esperado (Then)

Ver secciÃ³n **Then** en el extracto anterior del ERS. En automatizaciÃ³n backend, el test asociado comprueba el contrato API/servicio equivalente o queda explÃ­citamente marcado como pendiente si el criterio es solo UI, infraestructura o legalidad operativa fuera del alcance de pytest.

## Link directo al test

Ejecutar:

```bash
pytest tests/ers/test_gherkin_dynamic.py::test_RF010_S04 -v
```

Archivo de definiciÃ³n dinÃ¡mica: [`tests/ers/test_gherkin_dynamic.py`](../../tests/ers/test_gherkin_dynamic.py)

---

## Estado de automatizaciÃ³n backend

Implementada en `tests/ers/gherkin_impl.py` (comprueba API/servicios equivalentes al Then del ERS).


<!-- file: RF010-S05.md -->

# Consulta del reporte de productos prÃ³ximos a vencer

## Nombre del test

`tests/ers/test_gherkin_dynamic.py::test_RF010_S05`

## PropÃ³sito

Validar el criterio de aceptaciÃ³n Gherkin del ERS ICM para **RF010** â€” escenario 5.

## Requisito o caso de negocio asociado

- **Requisito:** `RF010` (ver `docs/requisitos/ERS_ICM_Requisitos.md`).

## Inputs (Given / When â€” extracto ERS)

**Given (Dado que):**
- El usuario autenticado tiene rol "Almacenista" o "Administrador/Jefe"

**When (Cuando):**
- Accede al reporte de vencimientos

**Then (Entonces):**
- El sistema lista todos los productos con fecha de vencimiento dentro de los prÃ³ximos 60 dÃ­as
- Los organiza por urgencia, mostrando primero los que vencen mÃ¡s pronto
- Para cada producto indica SKU, nombre, lote, fecha de vencimiento, stock disponible y ubicaciÃ³n

---

## Resultado esperado (Then)

Ver secciÃ³n **Then** en el extracto anterior del ERS. En automatizaciÃ³n backend, el test asociado comprueba el contrato API/servicio equivalente o queda explÃ­citamente marcado como pendiente si el criterio es solo UI, infraestructura o legalidad operativa fuera del alcance de pytest.

## Link directo al test

Ejecutar:

```bash
pytest tests/ers/test_gherkin_dynamic.py::test_RF010_S05 -v
```

Archivo de definiciÃ³n dinÃ¡mica: [`tests/ers/test_gherkin_dynamic.py`](../../tests/ers/test_gherkin_dynamic.py)

---

## Estado de automatizaciÃ³n backend

Implementada en `tests/ers/gherkin_impl.py` (comprueba API/servicios equivalentes al Then del ERS).


<!-- file: RF010-S06.md -->

# Consulta y descarga de factura individual desde el historial

## Nombre del test

`tests/ers/test_gherkin_dynamic.py::test_RF010_S06`

## PropÃ³sito

Validar el criterio de aceptaciÃ³n Gherkin del ERS ICM para **RF010** â€” escenario 6.

## Requisito o caso de negocio asociado

- **Requisito:** `RF010` (ver `docs/requisitos/ERS_ICM_Requisitos.md`).

## Inputs (Given / When â€” extracto ERS)

**Given (Dado que):**
- El usuario autenticado tiene rol "Almacenista" o "Administrador/Jefe"

**When (Cuando):**
- Accede al historial de facturas y remisiones
- Filtra por perÃ­odo, tipo de salida o cliente
- Selecciona una factura especÃ­fica del listado

**Then (Entonces):**
- El sistema muestra los detalles completos de esa factura
- Permite su descarga individual en formato PDF
- El documento descargado es idÃ©ntico al generado en el momento del despacho

---

## Resultado esperado (Then)

Ver secciÃ³n **Then** en el extracto anterior del ERS. En automatizaciÃ³n backend, el test asociado comprueba el contrato API/servicio equivalente o queda explÃ­citamente marcado como pendiente si el criterio es solo UI, infraestructura o legalidad operativa fuera del alcance de pytest.

## Link directo al test

Ejecutar:

```bash
pytest tests/ers/test_gherkin_dynamic.py::test_RF010_S06 -v
```

Archivo de definiciÃ³n dinÃ¡mica: [`tests/ers/test_gherkin_dynamic.py`](../../tests/ers/test_gherkin_dynamic.py)

---

## Estado de automatizaciÃ³n backend

Implementada en `tests/ers/gherkin_impl.py` (comprueba API/servicios equivalentes al Then del ERS).


<!-- file: RF010-S07.md -->

# Usuario sin permisos intenta acceder al mÃ³dulo de reportes

## Nombre del test

`tests/ers/test_gherkin_dynamic.py::test_RF010_S07`

## PropÃ³sito

Validar el criterio de aceptaciÃ³n Gherkin del ERS ICM para **RF010** â€” escenario 7.

## Requisito o caso de negocio asociado

- **Requisito:** `RF010` (ver `docs/requisitos/ERS_ICM_Requisitos.md`).

## Inputs (Given / When â€” extracto ERS)

**Given (Dado que):**
- El usuario autenticado tiene rol "Auxiliar de Despacho"

**When (Cuando):**
- Intenta acceder al mÃ³dulo de reportes o al dashboard gerencial

**Then (Entonces):**
- El sistema bloquea el acceso
- Muestra un mensaje indicando que no tiene permisos para visualizar esta secciÃ³n
- No expone ningÃºn dato operativo ni indicador

## Resultado esperado (Then)

Ver secciÃ³n **Then** en el extracto anterior del ERS. En automatizaciÃ³n backend, el test asociado comprueba el contrato API/servicio equivalente o queda explÃ­citamente marcado como pendiente si el criterio es solo UI, infraestructura o legalidad operativa fuera del alcance de pytest.

## Link directo al test

Ejecutar:

```bash
pytest tests/ers/test_gherkin_dynamic.py::test_RF010_S07 -v
```

Archivo de definiciÃ³n dinÃ¡mica: [`tests/ers/test_gherkin_dynamic.py`](../../tests/ers/test_gherkin_dynamic.py)

---

## Estado de automatizaciÃ³n backend

Implementada en `tests/ers/gherkin_impl.py` (comprueba API/servicios equivalentes al Then del ERS).


<!-- file: RF011-S01.md -->

# Alerta de stock mÃ­nimo cuando el inventario cae bajo el punto de reorden

## Nombre del test

`tests/ers/test_gherkin_dynamic.py::test_RF011_S01`

## PropÃ³sito

Validar el criterio de aceptaciÃ³n Gherkin del ERS ICM para **RF011** â€” escenario 1.

## Requisito o caso de negocio asociado

- **Requisito:** `RF011` (ver `docs/requisitos/ERS_ICM_Requisitos.md`).

## Inputs (Given / When â€” extracto ERS)

**Given (Dado que):**
- Un producto tiene configurado un punto de reorden de 10 unidades
- El stock total del producto era de 12 unidades

**When (Cuando):**
- Se confirma un despacho que deja el stock total en 8 unidades

**Then (Entonces):**
- El sistema emite de forma automÃ¡tica una alerta de stock mÃ­nimo visible en el dashboard del Almacenista y del Administrador
- La alerta indica el SKU, nombre del producto, stock actual y punto de reorden
- La alerta permanece activa hasta que el stock supere nuevamente el umbral
- El evento de activaciÃ³n queda registrado en el log con timestamp

---

## Resultado esperado (Then)

Ver secciÃ³n **Then** en el extracto anterior del ERS. En automatizaciÃ³n backend, el test asociado comprueba el contrato API/servicio equivalente o queda explÃ­citamente marcado como pendiente si el criterio es solo UI, infraestructura o legalidad operativa fuera del alcance de pytest.

## Link directo al test

Ejecutar:

```bash
pytest tests/ers/test_gherkin_dynamic.py::test_RF011_S01 -v
```

Archivo de definiciÃ³n dinÃ¡mica: [`tests/ers/test_gherkin_dynamic.py`](../../tests/ers/test_gherkin_dynamic.py)

---

## Estado de automatizaciÃ³n backend

Implementada en `tests/ers/gherkin_impl.py` (comprueba API/servicios equivalentes al Then del ERS).


<!-- file: RF011-S02.md -->

# Alerta de vencimiento prÃ³ximo a 60 dÃ­as

## Nombre del test

`tests/ers/test_gherkin_dynamic.py::test_RF011_S02`

## PropÃ³sito

Validar el criterio de aceptaciÃ³n Gherkin del ERS ICM para **RF011** â€” escenario 2.

## Requisito o caso de negocio asociado

- **Requisito:** `RF011` (ver `docs/requisitos/ERS_ICM_Requisitos.md`).

## Inputs (Given / When â€” extracto ERS)

**Given (Dado que):**
- Existe un lote de producto registrado con fecha de vencimiento

**When (Cuando):**
- Faltan exactamente 60 dÃ­as calendario para esa fecha de vencimiento

**Then (Entonces):**
- El sistema emite automÃ¡ticamente una alerta de vencimiento visible en el dashboard y en el mÃ³dulo de inventario
- La alerta indica SKU, nombre del producto, nÃºmero de lote, fecha de vencimiento y stock disponible del lote afectado
- La alerta queda registrada en el log de auditorÃ­a con timestamp

---

## Resultado esperado (Then)

Ver secciÃ³n **Then** en el extracto anterior del ERS. En automatizaciÃ³n backend, el test asociado comprueba el contrato API/servicio equivalente o queda explÃ­citamente marcado como pendiente si el criterio es solo UI, infraestructura o legalidad operativa fuera del alcance de pytest.

## Link directo al test

Ejecutar:

```bash
pytest tests/ers/test_gherkin_dynamic.py::test_RF011_S02 -v
```

Archivo de definiciÃ³n dinÃ¡mica: [`tests/ers/test_gherkin_dynamic.py`](../../tests/ers/test_gherkin_dynamic.py)

---

## Estado de automatizaciÃ³n backend

Implementada en `tests/ers/gherkin_impl.py` (comprueba API/servicios equivalentes al Then del ERS).


<!-- file: RF011-S03.md -->

# Alerta de vencimiento prÃ³ximo a 30 dÃ­as

## Nombre del test

`tests/ers/test_gherkin_dynamic.py::test_RF011_S03`

## PropÃ³sito

Validar el criterio de aceptaciÃ³n Gherkin del ERS ICM para **RF011** â€” escenario 3.

## Requisito o caso de negocio asociado

- **Requisito:** `RF011` (ver `docs/requisitos/ERS_ICM_Requisitos.md`).

## Inputs (Given / When â€” extracto ERS)

**Given (Dado que):**
- Existe una alerta de vencimiento activa a 60 dÃ­as
- Han transcurrido 30 dÃ­as desde su activaciÃ³n

**When (Cuando):**
- El sistema detecta que ahora faltan 30 dÃ­as para el vencimiento

**Then (Entonces):**
- El sistema escala la alerta existente a un nivel de urgencia mayor
- La alerta actualizada es visualmente diferenciada de la alerta a 60 dÃ­as
- El escalamiento queda registrado en el log de auditorÃ­a

---

## Resultado esperado (Then)

Ver secciÃ³n **Then** en el extracto anterior del ERS. En automatizaciÃ³n backend, el test asociado comprueba el contrato API/servicio equivalente o queda explÃ­citamente marcado como pendiente si el criterio es solo UI, infraestructura o legalidad operativa fuera del alcance de pytest.

## Link directo al test

Ejecutar:

```bash
pytest tests/ers/test_gherkin_dynamic.py::test_RF011_S03 -v
```

Archivo de definiciÃ³n dinÃ¡mica: [`tests/ers/test_gherkin_dynamic.py`](../../tests/ers/test_gherkin_dynamic.py)

---

## Estado de automatizaciÃ³n backend

Implementada en `tests/ers/gherkin_impl.py` (comprueba API/servicios equivalentes al Then del ERS).


<!-- file: RF011-S04.md -->

# Alerta de cadena de frÃ­o al registrar movimiento de producto refrigerado

## Nombre del test

`tests/ers/test_gherkin_dynamic.py::test_RF011_S04`

## PropÃ³sito

Validar el criterio de aceptaciÃ³n Gherkin del ERS ICM para **RF011** â€” escenario 4.

## Requisito o caso de negocio asociado

- **Requisito:** `RF011` (ver `docs/requisitos/ERS_ICM_Requisitos.md`).

## Inputs (Given / When â€” extracto ERS)

**Given (Dado que):**
- Un producto tiene activado el indicador de cadena de frÃ­o

**When (Cuando):**
- Cualquier usuario registra un movimiento que involucra ese producto

**Then (Entonces):**
- El sistema despliega de forma inmediata una alerta visual persistente y de alta visibilidad en la pantalla activa del usuario
- El usuario debe reconocer la alerta antes de poder confirmar el movimiento
- El reconocimiento queda registrado en el log con UserID y timestamp

---

## Resultado esperado (Then)

Ver secciÃ³n **Then** en el extracto anterior del ERS. En automatizaciÃ³n backend, el test asociado comprueba el contrato API/servicio equivalente o queda explÃ­citamente marcado como pendiente si el criterio es solo UI, infraestructura o legalidad operativa fuera del alcance de pytest.

## Link directo al test

Ejecutar:

```bash
pytest tests/ers/test_gherkin_dynamic.py::test_RF011_S04 -v
```

Archivo de definiciÃ³n dinÃ¡mica: [`tests/ers/test_gherkin_dynamic.py`](../../tests/ers/test_gherkin_dynamic.py)

---

## Estado de automatizaciÃ³n backend

Implementada en `tests/ers/gherkin_impl.py` (comprueba API/servicios equivalentes al Then del ERS).


<!-- file: RF011-S05.md -->

# Alerta de seguridad elÃ©ctrica al registrar movimiento de equipo elÃ©ctrico

## Nombre del test

`tests/ers/test_gherkin_dynamic.py::test_RF011_S05`

## PropÃ³sito

Validar el criterio de aceptaciÃ³n Gherkin del ERS ICM para **RF011** â€” escenario 5.

## Requisito o caso de negocio asociado

- **Requisito:** `RF011` (ver `docs/requisitos/ERS_ICM_Requisitos.md`).

## Inputs (Given / When â€” extracto ERS)

**Given (Dado que):**
- Un producto pertenece a la categorÃ­a "Electroterapia"

**When (Cuando):**
- Cualquier usuario registra un movimiento que involucra ese producto

**Then (Entonces):**
- El sistema despliega una advertencia visual sobre los protocolos de manejo seguro
- La advertencia es visualmente distinguible de la alerta de cadena de frÃ­o
- El usuario debe reconocer la advertencia antes de confirmar el movimiento
- El reconocimiento queda registrado en el log con UserID y timestamp

---

## Resultado esperado (Then)

Ver secciÃ³n **Then** en el extracto anterior del ERS. En automatizaciÃ³n backend, el test asociado comprueba el contrato API/servicio equivalente o queda explÃ­citamente marcado como pendiente si el criterio es solo UI, infraestructura o legalidad operativa fuera del alcance de pytest.

## Link directo al test

Ejecutar:

```bash
pytest tests/ers/test_gherkin_dynamic.py::test_RF011_S05 -v
```

Archivo de definiciÃ³n dinÃ¡mica: [`tests/ers/test_gherkin_dynamic.py`](../../tests/ers/test_gherkin_dynamic.py)

---

## Estado de automatizaciÃ³n backend

Implementada en `tests/ers/gherkin_impl.py` (comprueba API/servicios equivalentes al Then del ERS).


<!-- file: RF011-S06.md -->

# Panel de alertas activas en el dashboard

## Nombre del test

`tests/ers/test_gherkin_dynamic.py::test_RF011_S06`

## PropÃ³sito

Validar el criterio de aceptaciÃ³n Gherkin del ERS ICM para **RF011** â€” escenario 6.

## Requisito o caso de negocio asociado

- **Requisito:** `RF011` (ver `docs/requisitos/ERS_ICM_Requisitos.md`).

## Inputs (Given / When â€” extracto ERS)

**Given (Dado que):**
- El usuario autenticado tiene rol "Almacenista" o "Administrador/Jefe"

**When (Cuando):**
- Accede al dashboard principal

**Then (Entonces):**
- El sistema presenta un panel consolidado con todas las alertas operativas activas, organizadas por tipo y urgencia
- Cada alerta en el panel es navegable hacia el producto o movimiento que la originÃ³
- Las alertas a 30 dÃ­as aparecen por encima de las alertas a 60 dÃ­as en el panel

---

## Resultado esperado (Then)

Ver secciÃ³n **Then** en el extracto anterior del ERS. En automatizaciÃ³n backend, el test asociado comprueba el contrato API/servicio equivalente o queda explÃ­citamente marcado como pendiente si el criterio es solo UI, infraestructura o legalidad operativa fuera del alcance de pytest.

## Link directo al test

Ejecutar:

```bash
pytest tests/ers/test_gherkin_dynamic.py::test_RF011_S06 -v
```

Archivo de definiciÃ³n dinÃ¡mica: [`tests/ers/test_gherkin_dynamic.py`](../../tests/ers/test_gherkin_dynamic.py)

---

## Estado de automatizaciÃ³n backend

Implementada en `tests/ers/gherkin_impl.py` (comprueba API/servicios equivalentes al Then del ERS).


<!-- file: RF011-S07.md -->

# ResoluciÃ³n automÃ¡tica de una alerta de stock mÃ­nimo

## Nombre del test

`tests/ers/test_gherkin_dynamic.py::test_RF011_S07`

## PropÃ³sito

Validar el criterio de aceptaciÃ³n Gherkin del ERS ICM para **RF011** â€” escenario 7.

## Requisito o caso de negocio asociado

- **Requisito:** `RF011` (ver `docs/requisitos/ERS_ICM_Requisitos.md`).

## Inputs (Given / When â€” extracto ERS)

**Given (Dado que):**
- Existe una alerta de stock mÃ­nimo activa para un producto

**When (Cuando):**
- Se confirma una entrada de mercancÃ­a que eleva el stock total del producto por encima del punto de reorden

**Then (Entonces):**
- El sistema desactiva automÃ¡ticamente la alerta de stock mÃ­nimo
- La elimina del panel de alertas activas
- Deja constancia en el log de auditorÃ­a de que la alerta fue resuelta, con el timestamp de resoluciÃ³n y el movimiento de entrada que la originÃ³

## Resultado esperado (Then)

Ver secciÃ³n **Then** en el extracto anterior del ERS. En automatizaciÃ³n backend, el test asociado comprueba el contrato API/servicio equivalente o queda explÃ­citamente marcado como pendiente si el criterio es solo UI, infraestructura o legalidad operativa fuera del alcance de pytest.

## Link directo al test

Ejecutar:

```bash
pytest tests/ers/test_gherkin_dynamic.py::test_RF011_S07 -v
```

Archivo de definiciÃ³n dinÃ¡mica: [`tests/ers/test_gherkin_dynamic.py`](../../tests/ers/test_gherkin_dynamic.py)

---

## Estado de automatizaciÃ³n backend

Implementada en `tests/ers/gherkin_impl.py` (comprueba API/servicios equivalentes al Then del ERS).


<!-- file: RF012-S01.md -->

# El sistema genera automÃ¡ticamente un registro de auditorÃ­a al confirmar cualquier movimiento de inventario

## Nombre del test

`tests/ers/test_gherkin_dynamic.py::test_RF012_S01`

## PropÃ³sito

Validar el criterio de aceptaciÃ³n Gherkin del ERS ICM para **RF012** â€” escenario 1.

## Requisito o caso de negocio asociado

- **Requisito:** `RF012` (ver `docs/requisitos/ERS_ICM_Requisitos.md`).

## Inputs (Given / When â€” extracto ERS)

**Given (Dado que):**
- Cualquier usuario autenticado confirma una operaciÃ³n que afecta el stock

**When (Cuando):**
- El sistema procesa y confirma la operaciÃ³n

**Then (Entonces):**
- El sistema genera de forma automÃ¡tica e inmediata un registro en el log que contiene:
  - Identificador Ãºnico del movimiento
  - Timestamp con fecha y hora exacta
  - UserID del operario responsable
  - Tipo de transacciÃ³n
  - SKU del producto involucrado
  - CÃ³digo serial cuando aplique
  - UbicaciÃ³n de origen y destino
  - Cantidad operada
  - Stock previo y stock resultante
  - Nota o justificaciÃ³n cuando la operaciÃ³n lo requiera
- Ese registro queda inmutable desde el momento de su creaciÃ³n

---

## Resultado esperado (Then)

Ver secciÃ³n **Then** en el extracto anterior del ERS. En automatizaciÃ³n backend, el test asociado comprueba el contrato API/servicio equivalente o queda explÃ­citamente marcado como pendiente si el criterio es solo UI, infraestructura o legalidad operativa fuera del alcance de pytest.

## Link directo al test

Ejecutar:

```bash
pytest tests/ers/test_gherkin_dynamic.py::test_RF012_S01 -v
```

Archivo de definiciÃ³n dinÃ¡mica: [`tests/ers/test_gherkin_dynamic.py`](../../tests/ers/test_gherkin_dynamic.py)

---

## Estado de automatizaciÃ³n backend

Implementada en `tests/ers/gherkin_impl.py` (comprueba API/servicios equivalentes al Then del ERS).


<!-- file: RF012-S02.md -->

# El sistema registra en el log los eventos de autenticaciÃ³n

## Nombre del test

`tests/ers/test_gherkin_dynamic.py::test_RF012_S02`

## PropÃ³sito

Validar el criterio de aceptaciÃ³n Gherkin del ERS ICM para **RF012** â€” escenario 2.

## Requisito o caso de negocio asociado

- **Requisito:** `RF012` (ver `docs/requisitos/ERS_ICM_Requisitos.md`).

## Inputs (Given / When â€” extracto ERS)

**Given (Dado que):**
- Cualquier usuario intenta iniciar o cerrar sesiÃ³n en el sistema

**When (Cuando):**
- El intento de autenticaciÃ³n ocurre, sea exitoso o fallido

**Then (Entonces):**
- El sistema registra en el log el evento con timestamp, UserID o nombre de usuario intentado, resultado del intento (Ã©xito o fallo) y direcciÃ³n del dispositivo desde donde se realizÃ³ el intento
- Ese registro es inmutable y no puede ser eliminado

---

## Resultado esperado (Then)

Ver secciÃ³n **Then** en el extracto anterior del ERS. En automatizaciÃ³n backend, el test asociado comprueba el contrato API/servicio equivalente o queda explÃ­citamente marcado como pendiente si el criterio es solo UI, infraestructura o legalidad operativa fuera del alcance de pytest.

## Link directo al test

Ejecutar:

```bash
pytest tests/ers/test_gherkin_dynamic.py::test_RF012_S02 -v
```

Archivo de definiciÃ³n dinÃ¡mica: [`tests/ers/test_gherkin_dynamic.py`](../../tests/ers/test_gherkin_dynamic.py)

---

## Estado de automatizaciÃ³n backend

Implementada en `tests/ers/gherkin_impl.py` (comprueba API/servicios equivalentes al Then del ERS).


<!-- file: RF012-S03.md -->

# El sistema registra en el log los eventos de gestiÃ³n de credenciales

## Nombre del test

`tests/ers/test_gherkin_dynamic.py::test_RF012_S03`

## PropÃ³sito

Validar el criterio de aceptaciÃ³n Gherkin del ERS ICM para **RF012** â€” escenario 3.

## Requisito o caso de negocio asociado

- **Requisito:** `RF012` (ver `docs/requisitos/ERS_ICM_Requisitos.md`).

## Inputs (Given / When â€” extracto ERS)

**Given (Dado que):**
- El Almacenista crea, modifica o deshabilita una cuenta de usuario

**When (Cuando):**
- Confirma cualquiera de esas acciones

**Then (Entonces):**
- El sistema registra en el log el evento con timestamp, UserID del Almacenista que ejecutÃ³ la acciÃ³n, tipo de acciÃ³n realizada (creaciÃ³n, modificaciÃ³n o deshabilitaciÃ³n) y UserID de la cuenta afectada
- El registro es inmutable desde su creaciÃ³n

---

## Resultado esperado (Then)

Ver secciÃ³n **Then** en el extracto anterior del ERS. En automatizaciÃ³n backend, el test asociado comprueba el contrato API/servicio equivalente o queda explÃ­citamente marcado como pendiente si el criterio es solo UI, infraestructura o legalidad operativa fuera del alcance de pytest.

## Link directo al test

Ejecutar:

```bash
pytest tests/ers/test_gherkin_dynamic.py::test_RF012_S03 -v
```

Archivo de definiciÃ³n dinÃ¡mica: [`tests/ers/test_gherkin_dynamic.py`](../../tests/ers/test_gherkin_dynamic.py)

---

## Estado de automatizaciÃ³n backend

Implementada en `tests/ers/gherkin_impl.py` (comprueba API/servicios equivalentes al Then del ERS).


<!-- file: RF012-S04.md -->

# El sistema registra el reconocimiento de alertas de cadena de frÃ­o y seguridad elÃ©ctrica

## Nombre del test

`tests/ers/test_gherkin_dynamic.py::test_RF012_S04`

## PropÃ³sito

Validar el criterio de aceptaciÃ³n Gherkin del ERS ICM para **RF012** â€” escenario 4.

## Requisito o caso de negocio asociado

- **Requisito:** `RF012` (ver `docs/requisitos/ERS_ICM_Requisitos.md`).

## Inputs (Given / When â€” extracto ERS)

**Given (Dado que):**
- Un usuario reconoce activamente una alerta de cadena de frÃ­o o de seguridad elÃ©ctrica antes de confirmar un movimiento

**When (Cuando):**
- Confirma el reconocimiento de la alerta

**Then (Entonces):**
- El sistema registra en el log ese reconocimiento con UserID, timestamp, tipo de alerta reconocida y SKU del producto involucrado
- Ese registro queda vinculado al movimiento que originÃ³ la alerta

---

## Resultado esperado (Then)

Ver secciÃ³n **Then** en el extracto anterior del ERS. En automatizaciÃ³n backend, el test asociado comprueba el contrato API/servicio equivalente o queda explÃ­citamente marcado como pendiente si el criterio es solo UI, infraestructura o legalidad operativa fuera del alcance de pytest.

## Link directo al test

Ejecutar:

```bash
pytest tests/ers/test_gherkin_dynamic.py::test_RF012_S04 -v
```

Archivo de definiciÃ³n dinÃ¡mica: [`tests/ers/test_gherkin_dynamic.py`](../../tests/ers/test_gherkin_dynamic.py)

---

## Estado de automatizaciÃ³n backend

Implementada en `tests/ers/gherkin_impl.py` (comprueba API/servicios equivalentes al Then del ERS).


<!-- file: RF012-S05.md -->

# Almacenista consulta el log completo de auditorÃ­a con filtros

## Nombre del test

`tests/ers/test_gherkin_dynamic.py::test_RF012_S05`

## PropÃ³sito

Validar el criterio de aceptaciÃ³n Gherkin del ERS ICM para **RF012** â€” escenario 5.

## Requisito o caso de negocio asociado

- **Requisito:** `RF012` (ver `docs/requisitos/ERS_ICM_Requisitos.md`).

## Inputs (Given / When â€” extracto ERS)

**Given (Dado que):**
- El usuario autenticado tiene rol "Almacenista"

**When (Cuando):**
- Accede al mÃ³dulo de auditorÃ­a
- Aplica filtros por perÃ­odo, tipo de operaciÃ³n, operario o producto

**Then (Entonces):**
- El sistema muestra todos los registros que coinciden con los filtros en orden cronolÃ³gico
- Cada registro es de solo lectura, sin opciÃ³n de ediciÃ³n ni eliminaciÃ³n
- El Almacenista puede exportar el log filtrado en formato Excel o CSV

---

## Resultado esperado (Then)

Ver secciÃ³n **Then** en el extracto anterior del ERS. En automatizaciÃ³n backend, el test asociado comprueba el contrato API/servicio equivalente o queda explÃ­citamente marcado como pendiente si el criterio es solo UI, infraestructura o legalidad operativa fuera del alcance de pytest.

## Link directo al test

Ejecutar:

```bash
pytest tests/ers/test_gherkin_dynamic.py::test_RF012_S05 -v
```

Archivo de definiciÃ³n dinÃ¡mica: [`tests/ers/test_gherkin_dynamic.py`](../../tests/ers/test_gherkin_dynamic.py)

---

## Estado de automatizaciÃ³n backend

Implementada en `tests/ers/gherkin_impl.py` (comprueba API/servicios equivalentes al Then del ERS).


<!-- file: RF012-S06.md -->

# Auxiliar de Despacho intenta acceder al log de auditorÃ­a

## Nombre del test

`tests/ers/test_gherkin_dynamic.py::test_RF012_S06`

## PropÃ³sito

Validar el criterio de aceptaciÃ³n Gherkin del ERS ICM para **RF012** â€” escenario 6.

## Requisito o caso de negocio asociado

- **Requisito:** `RF012` (ver `docs/requisitos/ERS_ICM_Requisitos.md`).

## Inputs (Given / When â€” extracto ERS)

**Given (Dado que):**
- El usuario autenticado tiene rol "Auxiliar de Despacho"

**When (Cuando):**
- Intenta acceder al mÃ³dulo de auditorÃ­a por cualquier vÃ­a

**Then (Entonces):**
- El sistema bloquea el acceso de forma inmediata
- Muestra un mensaje indicando que no tiene permisos para consultar el log
- No expone ningÃºn registro del historial

---

## Resultado esperado (Then)

Ver secciÃ³n **Then** en el extracto anterior del ERS. En automatizaciÃ³n backend, el test asociado comprueba el contrato API/servicio equivalente o queda explÃ­citamente marcado como pendiente si el criterio es solo UI, infraestructura o legalidad operativa fuera del alcance de pytest.

## Link directo al test

Ejecutar:

```bash
pytest tests/ers/test_gherkin_dynamic.py::test_RF012_S06 -v
```

Archivo de definiciÃ³n dinÃ¡mica: [`tests/ers/test_gherkin_dynamic.py`](../../tests/ers/test_gherkin_dynamic.py)

---

## Estado de automatizaciÃ³n backend

Implementada en `tests/ers/gherkin_impl.py` (comprueba API/servicios equivalentes al Then del ERS).


<!-- file: RF012-S07.md -->

# El log registra tanto el movimiento original como la correcciÃ³n del Auxiliar

## Nombre del test

`tests/ers/test_gherkin_dynamic.py::test_RF012_S07`

## PropÃ³sito

Validar el criterio de aceptaciÃ³n Gherkin del ERS ICM para **RF012** â€” escenario 7.

## Requisito o caso de negocio asociado

- **Requisito:** `RF012` (ver `docs/requisitos/ERS_ICM_Requisitos.md`).

## Inputs (Given / When â€” extracto ERS)

**Given (Dado que):**
- Un Auxiliar de Despacho registrÃ³ un movimiento durante la franja activa
- Detecta un error y lo corrige antes de que cierre la franja

**When (Cuando):**
- Confirma la correcciÃ³n

**Then (Entonces):**
- El sistema mantiene el registro original en el log con su timestamp de creaciÃ³n
- Agrega un segundo registro vinculado al primero indicando que fue corregido, con el UserID del auxiliar y el timestamp exacto de la correcciÃ³n
- Ambos registros son inmutables e independientes

---

## Resultado esperado (Then)

Ver secciÃ³n **Then** en el extracto anterior del ERS. En automatizaciÃ³n backend, el test asociado comprueba el contrato API/servicio equivalente o queda explÃ­citamente marcado como pendiente si el criterio es solo UI, infraestructura o legalidad operativa fuera del alcance de pytest.

## Link directo al test

Ejecutar:

```bash
pytest tests/ers/test_gherkin_dynamic.py::test_RF012_S07 -v
```

Archivo de definiciÃ³n dinÃ¡mica: [`tests/ers/test_gherkin_dynamic.py`](../../tests/ers/test_gherkin_dynamic.py)

---

## Estado de automatizaciÃ³n backend

Implementada en `tests/ers/gherkin_impl.py` (comprueba API/servicios equivalentes al Then del ERS).


<!-- file: RF012-S08.md -->

# Intento de eliminaciÃ³n o modificaciÃ³n de un registro del log

## Nombre del test

`tests/ers/test_gherkin_dynamic.py::test_RF012_S08`

## PropÃ³sito

Validar el criterio de aceptaciÃ³n Gherkin del ERS ICM para **RF012** â€” escenario 8.

## Requisito o caso de negocio asociado

- **Requisito:** `RF012` (ver `docs/requisitos/ERS_ICM_Requisitos.md`).

## Inputs (Given / When â€” extracto ERS)

**Given (Dado que):**
- Cualquier usuario autenticado, independientemente de su rol, intenta modificar o eliminar un registro existente en el log

**When (Cuando):**
- Ejecuta esa acciÃ³n por cualquier vÃ­a disponible en la interfaz

**Then (Entonces):**
- El sistema rechaza la operaciÃ³n de forma absoluta
- Muestra un mensaje indicando que los registros de auditorÃ­a son inmutables
- Registra en el propio log el intento fallido de modificaciÃ³n con UserID y timestamp

# **6. Requisitos No Funcionales**

Los requisitos no funcionales (RNF) definen los atributos de calidad que el sistema debe cumplir para ser operativamente viable en el contexto real de ICM. A diferencia de los requisitos funcionales, que describen quÃ© hace el sistema, los requisitos no funcionales describen cÃ³mo debe hacerlo: con quÃ© velocidad, con quÃ© nivel de seguridad, con quÃ© grado de disponibilidad. Estos requisitos son transversales a todos los mÃ³dulos y deben ser considerados desde la fase de diseÃ±o arquitectÃ³nico, no como consideraciones tardÃ­as de optimizaciÃ³n.

## Resultado esperado (Then)

Ver secciÃ³n **Then** en el extracto anterior del ERS. En automatizaciÃ³n backend, el test asociado comprueba el contrato API/servicio equivalente o queda explÃ­citamente marcado como pendiente si el criterio es solo UI, infraestructura o legalidad operativa fuera del alcance de pytest.

## Link directo al test

Ejecutar:

```bash
pytest tests/ers/test_gherkin_dynamic.py::test_RF012_S08 -v
```

Archivo de definiciÃ³n dinÃ¡mica: [`tests/ers/test_gherkin_dynamic.py`](../../tests/ers/test_gherkin_dynamic.py)

---

## Estado de automatizaciÃ³n backend

Implementada en `tests/ers/gherkin_impl.py` (comprueba API/servicios equivalentes al Then del ERS).


<!-- file: RNF001-S01.md -->

# Operario completa un flujo de despacho sin formaciÃ³n tÃ©cnica previa

## Nombre del test

`tests/ers/test_gherkin_dynamic.py::test_RNF001_S01`

## PropÃ³sito

Validar el criterio de aceptaciÃ³n Gherkin del ERS ICM para **RNF001** â€” escenario 1.

## Requisito o caso de negocio asociado

- **Requisito:** `RNF001` (ver `docs/requisitos/ERS_ICM_Requisitos.md`).

## Inputs (Given / When â€” extracto ERS)

**Given (Dado que):**
- Un Auxiliar de Despacho accede al sistema por primera vez tras una inducciÃ³n operativa bÃ¡sica de no mÃ¡s de 30 minutos

**When (Cuando):**
- Intenta registrar un despacho estÃ¡ndar de principio a fin

**Then (Entonces):**
- El operario completa el flujo sin necesidad de consultar documentaciÃ³n tÃ©cnica ni solicitar asistencia
- El sistema guÃ­a al usuario paso a paso dentro del flujo sin ambigÃ¼edad sobre cuÃ¡l es la siguiente acciÃ³n requerida

---

## Resultado esperado (Then)

Ver secciÃ³n **Then** en el extracto anterior del ERS. En automatizaciÃ³n backend, el test asociado comprueba el contrato API/servicio equivalente o queda explÃ­citamente marcado como pendiente si el criterio es solo UI, infraestructura o legalidad operativa fuera del alcance de pytest.

## Link directo al test

Ejecutar:

```bash
pytest tests/ers/test_gherkin_dynamic.py::test_RNF001_S01 -v
```

Archivo de definiciÃ³n dinÃ¡mica: [`tests/ers/test_gherkin_dynamic.py`](../../tests/ers/test_gherkin_dynamic.py)

---

## Estado de automatizaciÃ³n backend

Fuera de alcance del backend/pytest; debe validarse en frontend o E2E. Motivo: describe el flujo visual y la facilidad de uso de la interfaz; no es verificable con pytest backend


<!-- file: RNF001-S02.md -->

# La interfaz responde correctamente en dispositivos mÃ³viles y tabletas

## Nombre del test

`tests/ers/test_gherkin_dynamic.py::test_RNF001_S02`

## PropÃ³sito

Validar el criterio de aceptaciÃ³n Gherkin del ERS ICM para **RNF001** â€” escenario 2.

## Requisito o caso de negocio asociado

- **Requisito:** `RNF001` (ver `docs/requisitos/ERS_ICM_Requisitos.md`).

## Inputs (Given / When â€” extracto ERS)

**Given (Dado que):**
- Un operario accede al sistema desde una tableta o un telÃ©fono inteligente

**When (Cuando):**
- Navega por cualquier mÃ³dulo disponible para su rol

**Then (Entonces):**
- Todos los elementos de la interfaz se adaptan al tamaÃ±o de pantalla del dispositivo sin pÃ©rdida de funcionalidad
- Los botones y campos son suficientemente grandes para ser operados con precisiÃ³n tÃ¡ctil
- NingÃºn elemento crÃ­tico queda oculto o inaccesible en resoluciones mÃ³viles

---

## Resultado esperado (Then)

Ver secciÃ³n **Then** en el extracto anterior del ERS. En automatizaciÃ³n backend, el test asociado comprueba el contrato API/servicio equivalente o queda explÃ­citamente marcado como pendiente si el criterio es solo UI, infraestructura o legalidad operativa fuera del alcance de pytest.

## Link directo al test

Ejecutar:

```bash
pytest tests/ers/test_gherkin_dynamic.py::test_RNF001_S02 -v
```

Archivo de definiciÃ³n dinÃ¡mica: [`tests/ers/test_gherkin_dynamic.py`](../../tests/ers/test_gherkin_dynamic.py)

---

## Estado de automatizaciÃ³n backend

Fuera de alcance del backend/pytest; debe validarse en frontend o E2E. Motivo: depende de responsividad y adaptacion visual en dispositivos moviles/tabletas


<!-- file: RNF001-S03.md -->

# La bÃºsqueda de productos es igualmente eficiente por cualquier vÃ­a

## Nombre del test

`tests/ers/test_gherkin_dynamic.py::test_RNF001_S03`

## PropÃ³sito

Validar el criterio de aceptaciÃ³n Gherkin del ERS ICM para **RNF001** â€” escenario 3.

## Requisito o caso de negocio asociado

- **Requisito:** `RNF001` (ver `docs/requisitos/ERS_ICM_Requisitos.md`).

## Inputs (Given / When â€” extracto ERS)

**Given (Dado que):**
- Un operario necesita localizar un producto durante la atenciÃ³n a un cliente

**When (Cuando):**
- Busca el producto ya sea por nombre, SKU o cÃ³digo de barras

**Then (Entonces):**
- El sistema devuelve resultados relevantes en menos de 2 segundos por cualquiera de las tres vÃ­as de bÃºsqueda
- El operario puede identificar y seleccionar el producto correcto sin navegar por mÃ¡s de dos pantallas desde el punto de bÃºsqueda

## Resultado esperado (Then)

Ver secciÃ³n **Then** en el extracto anterior del ERS. En automatizaciÃ³n backend, el test asociado comprueba el contrato API/servicio equivalente o queda explÃ­citamente marcado como pendiente si el criterio es solo UI, infraestructura o legalidad operativa fuera del alcance de pytest.

## Link directo al test

Ejecutar:

```bash
pytest tests/ers/test_gherkin_dynamic.py::test_RNF001_S03 -v
```

Archivo de definiciÃ³n dinÃ¡mica: [`tests/ers/test_gherkin_dynamic.py`](../../tests/ers/test_gherkin_dynamic.py)

---

## Estado de automatizaciÃ³n backend

Fuera de alcance del backend/pytest; debe validarse en frontend o E2E. Motivo: depende de tiempos percibidos y navegacion de interfaz, no de una respuesta backend aislada


<!-- file: RNF002-S01.md -->

# El sistema permanece disponible durante las franjas crÃ­ticas de operaciÃ³n

## Nombre del test

`tests/ers/test_gherkin_dynamic.py::test_RNF002_S01`

## PropÃ³sito

Validar el criterio de aceptaciÃ³n Gherkin del ERS ICM para **RNF002** â€” escenario 1.

## Requisito o caso de negocio asociado

- **Requisito:** `RNF002` (ver `docs/requisitos/ERS_ICM_Requisitos.md`).

## Inputs (Given / When â€” extracto ERS)

**Given (Dado que):**
- El sistema estÃ¡ desplegado en el entorno de producciÃ³n

**When (Cuando):**
- Un Auxiliar de Despacho intenta acceder al sistema dentro de su franja horaria

**Then (Entonces):**
- El sistema responde y permite el acceso sin interrupciones
- Cualquier operaciÃ³n iniciada dentro de la franja puede completarse sin que el sistema la interrumpa por inactividad o caÃ­da durante esa ventana

---

## Resultado esperado (Then)

Ver secciÃ³n **Then** en el extracto anterior del ERS. En automatizaciÃ³n backend, el test asociado comprueba el contrato API/servicio equivalente o queda explÃ­citamente marcado como pendiente si el criterio es solo UI, infraestructura o legalidad operativa fuera del alcance de pytest.

## Link directo al test

Ejecutar:

```bash
pytest tests/ers/test_gherkin_dynamic.py::test_RNF002_S01 -v
```

Archivo de definiciÃ³n dinÃ¡mica: [`tests/ers/test_gherkin_dynamic.py`](../../tests/ers/test_gherkin_dynamic.py)

---

## Estado de automatizaciÃ³n backend

Fuera de alcance del backend/pytest; debe validarse en frontend o E2E. Motivo: describe continuidad de servicio y disponibilidad en produccion; requiere verificacion de despliegue/infraestructura


<!-- file: RNF002-S02.md -->

# El Almacenista puede acceder al sistema en cualquier momento del dÃ­a

## Nombre del test

`tests/ers/test_gherkin_dynamic.py::test_RNF002_S02`

## PropÃ³sito

Validar el criterio de aceptaciÃ³n Gherkin del ERS ICM para **RNF002** â€” escenario 2.

## Requisito o caso de negocio asociado

- **Requisito:** `RNF002` (ver `docs/requisitos/ERS_ICM_Requisitos.md`).

## Inputs (Given / When â€” extracto ERS)

**Given (Dado que):**
- El sistema estÃ¡ desplegado en producciÃ³n

**When (Cuando):**
- El Almacenista intenta acceder al sistema fuera del horario laboral convencional

**Then (Entonces):**
- El sistema responde y otorga acceso completo sin restricciones horarias
- Todas las funcionalidades del rol Almacenista estÃ¡n disponibles

---

## Resultado esperado (Then)

Ver secciÃ³n **Then** en el extracto anterior del ERS. En automatizaciÃ³n backend, el test asociado comprueba el contrato API/servicio equivalente o queda explÃ­citamente marcado como pendiente si el criterio es solo UI, infraestructura o legalidad operativa fuera del alcance de pytest.

## Link directo al test

Ejecutar:

```bash
pytest tests/ers/test_gherkin_dynamic.py::test_RNF002_S02 -v
```

Archivo de definiciÃ³n dinÃ¡mica: [`tests/ers/test_gherkin_dynamic.py`](../../tests/ers/test_gherkin_dynamic.py)

---

## Estado de automatizaciÃ³n backend

Fuera de alcance del backend/pytest; debe validarse en frontend o E2E. Motivo: depende de disponibilidad 24/7 en produccion y no de un contrato de API aislado


<!-- file: RNF002-S03.md -->

# El sistema notifica adecuadamente ante una interrupciÃ³n no planificada

## Nombre del test

`tests/ers/test_gherkin_dynamic.py::test_RNF002_S03`

## PropÃ³sito

Validar el criterio de aceptaciÃ³n Gherkin del ERS ICM para **RNF002** â€” escenario 3.

## Requisito o caso de negocio asociado

- **Requisito:** `RNF002` (ver `docs/requisitos/ERS_ICM_Requisitos.md`).

## Inputs (Given / When â€” extracto ERS)

**Given (Dado que):**
- Ocurre una interrupciÃ³n no planificada del sistema

**When (Cuando):**
- Un usuario intenta acceder durante esa interrupciÃ³n

**Then (Entonces):**
- El sistema muestra un mensaje claro indicando que el servicio no estÃ¡ disponible
- El mensaje no expone detalles tÃ©cnicos internos del error al usuario final

## Resultado esperado (Then)

Ver secciÃ³n **Then** en el extracto anterior del ERS. En automatizaciÃ³n backend, el test asociado comprueba el contrato API/servicio equivalente o queda explÃ­citamente marcado como pendiente si el criterio es solo UI, infraestructura o legalidad operativa fuera del alcance de pytest.

## Link directo al test

Ejecutar:

```bash
pytest tests/ers/test_gherkin_dynamic.py::test_RNF002_S03 -v
```

Archivo de definiciÃ³n dinÃ¡mica: [`tests/ers/test_gherkin_dynamic.py`](../../tests/ers/test_gherkin_dynamic.py)

---

## Estado de automatizaciÃ³n backend

Fuera de alcance del backend/pytest; debe validarse en frontend o E2E. Motivo: depende del comportamiento de error y mensajeria en capa de presentacion o gateways


<!-- file: RNF003-S01.md -->

# Los datos sensibles viajan cifrados entre el cliente y el servidor

## Nombre del test

`tests/ers/test_gherkin_dynamic.py::test_RNF003_S01`

## PropÃ³sito

Validar el criterio de aceptaciÃ³n Gherkin del ERS ICM para **RNF003** â€” escenario 1.

## Requisito o caso de negocio asociado

- **Requisito:** `RNF003` (ver `docs/requisitos/ERS_ICM_Requisitos.md`).

## Inputs (Given / When â€” extracto ERS)

**Given (Dado que):**
- Cualquier usuario realiza una operaciÃ³n en el sistema que implica transmisiÃ³n de datos

**When (Cuando):**
- Esa operaciÃ³n genera trÃ¡fico de red entre el frontend y el backend

**Then (Entonces):**
- Toda la comunicaciÃ³n ocurre exclusivamente sobre HTTPS
- NingÃºn dato sensible se transmite en texto plano bajo ninguna circunstancia

---

## Resultado esperado (Then)

Ver secciÃ³n **Then** en el extracto anterior del ERS. En automatizaciÃ³n backend, el test asociado comprueba el contrato API/servicio equivalente o queda explÃ­citamente marcado como pendiente si el criterio es solo UI, infraestructura o legalidad operativa fuera del alcance de pytest.

## Link directo al test

Ejecutar:

```bash
pytest tests/ers/test_gherkin_dynamic.py::test_RNF003_S01 -v
```

Archivo de definiciÃ³n dinÃ¡mica: [`tests/ers/test_gherkin_dynamic.py`](../../tests/ers/test_gherkin_dynamic.py)

---

## Estado de automatizaciÃ³n backend

Implementada en `tests/ers/gherkin_impl.py` (comprueba API/servicios equivalentes al Then del ERS).


<!-- file: RNF003-S02.md -->

# Un usuario no puede acceder a funcionalidades fuera de su rol

## Nombre del test

`tests/ers/test_gherkin_dynamic.py::test_RNF003_S02`

## PropÃ³sito

Validar el criterio de aceptaciÃ³n Gherkin del ERS ICM para **RNF003** â€” escenario 2.

## Requisito o caso de negocio asociado

- **Requisito:** `RNF003` (ver `docs/requisitos/ERS_ICM_Requisitos.md`).

## Inputs (Given / When â€” extracto ERS)

**Given (Dado que):**
- Cualquier usuario estÃ¡ autenticado en el sistema

**When (Cuando):**
- Intenta acceder a una ruta, vista o endpoint que corresponde a un rol distinto al suyo, ya sea manipulando la URL directamente o mediante cualquier otro mecanismo

**Then (Entonces):**
- El sistema rechaza la solicitud con un error de autorizaciÃ³n
- No expone ningÃºn dato ni funcionalidad del rol restringido
- El intento queda registrado en el log de auditorÃ­a

---

## Resultado esperado (Then)

Ver secciÃ³n **Then** en el extracto anterior del ERS. En automatizaciÃ³n backend, el test asociado comprueba el contrato API/servicio equivalente o queda explÃ­citamente marcado como pendiente si el criterio es solo UI, infraestructura o legalidad operativa fuera del alcance de pytest.

## Link directo al test

Ejecutar:

```bash
pytest tests/ers/test_gherkin_dynamic.py::test_RNF003_S02 -v
```

Archivo de definiciÃ³n dinÃ¡mica: [`tests/ers/test_gherkin_dynamic.py`](../../tests/ers/test_gherkin_dynamic.py)

---

## Estado de automatizaciÃ³n backend

Implementada en `tests/ers/gherkin_impl.py` (comprueba API/servicios equivalentes al Then del ERS).


<!-- file: RNF003-S03.md -->

# Las contraseÃ±as de los usuarios se almacenan de forma segura

## Nombre del test

`tests/ers/test_gherkin_dynamic.py::test_RNF003_S03`

## PropÃ³sito

Validar el criterio de aceptaciÃ³n Gherkin del ERS ICM para **RNF003** â€” escenario 3.

## Requisito o caso de negocio asociado

- **Requisito:** `RNF003` (ver `docs/requisitos/ERS_ICM_Requisitos.md`).

## Inputs (Given / When â€” extracto ERS)

**Given (Dado que):**
- El Almacenista crea o modifica la contraseÃ±a de cualquier usuario

**When (Cuando):**
- El sistema procesa y almacena esa contraseÃ±a

**Then (Entonces):**
- La contraseÃ±a se almacena en la base de datos usando un algoritmo de hashing seguro con sal (por ejemplo bcrypt)
- En ningÃºn punto del sistema la contraseÃ±a es almacenada ni transmitida en texto plano

---

## Resultado esperado (Then)

Ver secciÃ³n **Then** en el extracto anterior del ERS. En automatizaciÃ³n backend, el test asociado comprueba el contrato API/servicio equivalente o queda explÃ­citamente marcado como pendiente si el criterio es solo UI, infraestructura o legalidad operativa fuera del alcance de pytest.

## Link directo al test

Ejecutar:

```bash
pytest tests/ers/test_gherkin_dynamic.py::test_RNF003_S03 -v
```

Archivo de definiciÃ³n dinÃ¡mica: [`tests/ers/test_gherkin_dynamic.py`](../../tests/ers/test_gherkin_dynamic.py)

---

## Estado de automatizaciÃ³n backend

Implementada en `tests/ers/gherkin_impl.py` (comprueba API/servicios equivalentes al Then del ERS).


<!-- file: RNF003-S04.md -->

# NingÃºn usuario puede modificar ni eliminar un registro histÃ³rico

## Nombre del test

`tests/ers/test_gherkin_dynamic.py::test_RNF003_S04`

## PropÃ³sito

Validar el criterio de aceptaciÃ³n Gherkin del ERS ICM para **RNF003** â€” escenario 4.

## Requisito o caso de negocio asociado

- **Requisito:** `RNF003` (ver `docs/requisitos/ERS_ICM_Requisitos.md`).

## Inputs (Given / When â€” extracto ERS)

**Given (Dado que):**
- Cualquier usuario autenticado, independientemente de su rol, intenta modificar o eliminar un registro del log o un movimiento ya confirmado

**When (Cuando):**
- Ejecuta o intenta ejecutar esa acciÃ³n

**Then (Entonces):**
- El sistema rechaza la operaciÃ³n de forma absoluta
- El registro original permanece intacto e inalterado
- El intento fallido queda registrado en el log con UserID y timestamp

## Resultado esperado (Then)

Ver secciÃ³n **Then** en el extracto anterior del ERS. En automatizaciÃ³n backend, el test asociado comprueba el contrato API/servicio equivalente o queda explÃ­citamente marcado como pendiente si el criterio es solo UI, infraestructura o legalidad operativa fuera del alcance de pytest.

## Link directo al test

Ejecutar:

```bash
pytest tests/ers/test_gherkin_dynamic.py::test_RNF003_S04 -v
```

Archivo de definiciÃ³n dinÃ¡mica: [`tests/ers/test_gherkin_dynamic.py`](../../tests/ers/test_gherkin_dynamic.py)

---

## Estado de automatizaciÃ³n backend

Implementada en `tests/ers/gherkin_impl.py` (comprueba API/servicios equivalentes al Then del ERS).


<!-- file: RNF004-S01.md -->

# Consulta de stock de un producto responde dentro del umbral definido

## Nombre del test

`tests/ers/test_gherkin_dynamic.py::test_RNF004_S01`

## PropÃ³sito

Validar el criterio de aceptaciÃ³n Gherkin del ERS ICM para **RNF004** â€” escenario 1.

## Requisito o caso de negocio asociado

- **Requisito:** `RNF004` (ver `docs/requisitos/ERS_ICM_Requisitos.md`).

## Inputs (Given / When â€” extracto ERS)

**Given (Dado que):**
- El sistema estÃ¡ operando bajo condiciones normales de uso
- El catÃ¡logo contiene entre 220 y 250 productos registrados

**When (Cuando):**
- Cualquier usuario realiza una consulta de stock por nombre, SKU o cÃ³digo de barras

**Then (Entonces):**
- El sistema devuelve el resultado con el stock por ubicaciÃ³n y el stock total consolidado en un tiempo no mayor a 2 segundos

---

## Resultado esperado (Then)

Ver secciÃ³n **Then** en el extracto anterior del ERS. En automatizaciÃ³n backend, el test asociado comprueba el contrato API/servicio equivalente o queda explÃ­citamente marcado como pendiente si el criterio es solo UI, infraestructura o legalidad operativa fuera del alcance de pytest.

## Link directo al test

Ejecutar:

```bash
pytest tests/ers/test_gherkin_dynamic.py::test_RNF004_S01 -v
```

Archivo de definiciÃ³n dinÃ¡mica: [`tests/ers/test_gherkin_dynamic.py`](../../tests/ers/test_gherkin_dynamic.py)

---

## Estado de automatizaciÃ³n backend

Implementada en `tests/ers/gherkin_impl.py` (comprueba API/servicios equivalentes al Then del ERS).


<!-- file: RNF004-S02.md -->

# El registro de un movimiento de inventario se confirma dentro de un tiempo razonable

## Nombre del test

`tests/ers/test_gherkin_dynamic.py::test_RNF004_S02`

## PropÃ³sito

Validar el criterio de aceptaciÃ³n Gherkin del ERS ICM para **RNF004** â€” escenario 2.

## Requisito o caso de negocio asociado

- **Requisito:** `RNF004` (ver `docs/requisitos/ERS_ICM_Requisitos.md`).

## Inputs (Given / When â€” extracto ERS)

**Given (Dado que):**
- Un operario completa y confirma un movimiento de inventario

**When (Cuando):**
- El sistema procesa la confirmaciÃ³n

**Then (Entonces):**
- El sistema actualiza el stock, genera el log de auditorÃ­a y muestra la confirmaciÃ³n al usuario en un tiempo no mayor a 3 segundos bajo condiciones normales de uso

---

## Resultado esperado (Then)

Ver secciÃ³n **Then** en el extracto anterior del ERS. En automatizaciÃ³n backend, el test asociado comprueba el contrato API/servicio equivalente o queda explÃ­citamente marcado como pendiente si el criterio es solo UI, infraestructura o legalidad operativa fuera del alcance de pytest.

## Link directo al test

Ejecutar:

```bash
pytest tests/ers/test_gherkin_dynamic.py::test_RNF004_S02 -v
```

Archivo de definiciÃ³n dinÃ¡mica: [`tests/ers/test_gherkin_dynamic.py`](../../tests/ers/test_gherkin_dynamic.py)

---

## Estado de automatizaciÃ³n backend

Implementada en `tests/ers/gherkin_impl.py` (comprueba API/servicios equivalentes al Then del ERS).


<!-- file: RNF004-S03.md -->

# El sistema mantiene el rendimiento bajo uso simultÃ¡neo de los tres roles

## Nombre del test

`tests/ers/test_gherkin_dynamic.py::test_RNF004_S03`

## PropÃ³sito

Validar el criterio de aceptaciÃ³n Gherkin del ERS ICM para **RNF004** â€” escenario 3.

## Requisito o caso de negocio asociado

- **Requisito:** `RNF004` (ver `docs/requisitos/ERS_ICM_Requisitos.md`).

## Inputs (Given / When â€” extracto ERS)

**Given (Dado que):**
- El Almacenista, un Auxiliar de Despacho y el Administrador estÃ¡n usando el sistema de forma simultÃ¡nea

**When (Cuando):**
- Cada uno ejecuta operaciones propias de su rol al mismo tiempo

**Then (Entonces):**
- El tiempo de respuesta de cada operaciÃ³n no se degrada mÃ¡s allÃ¡ de los umbrales definidos para cada tipo de consulta
- NingÃºn usuario experimenta bloqueos ni timeouts durante el uso concurrente normal

## Resultado esperado (Then)

Ver secciÃ³n **Then** en el extracto anterior del ERS. En automatizaciÃ³n backend, el test asociado comprueba el contrato API/servicio equivalente o queda explÃ­citamente marcado como pendiente si el criterio es solo UI, infraestructura o legalidad operativa fuera del alcance de pytest.

## Link directo al test

Ejecutar:

```bash
pytest tests/ers/test_gherkin_dynamic.py::test_RNF004_S03 -v
```

Archivo de definiciÃ³n dinÃ¡mica: [`tests/ers/test_gherkin_dynamic.py`](../../tests/ers/test_gherkin_dynamic.py)

---

## Estado de automatizaciÃ³n backend

Implementada en `tests/ers/gherkin_impl.py` (comprueba API/servicios equivalentes al Then del ERS).


<!-- file: RNF005-S01.md -->

# La arquitectura del sistema separa frontend y backend con APIs REST

## Nombre del test

`tests/ers/test_gherkin_dynamic.py::test_RNF005_S01`

## PropÃ³sito

Validar el criterio de aceptaciÃ³n Gherkin del ERS ICM para **RNF005** â€” escenario 1.

## Requisito o caso de negocio asociado

- **Requisito:** `RNF005` (ver `docs/requisitos/ERS_ICM_Requisitos.md`).

## Inputs (Given / When â€” extracto ERS)

**Given (Dado que):**
- El sistema estÃ¡ implementado y desplegado

**When (Cuando):**
- Se analiza la estructura del proyecto en el repositorio

**Then (Entonces):**
- Existe una separaciÃ³n clara entre el proyecto de frontend y el de backend como unidades independientes
- Toda la comunicaciÃ³n entre frontend y backend ocurre exclusivamente a travÃ©s de endpoints REST documentados
- No existe lÃ³gica de negocio embebida directamente en el frontend

---

## Resultado esperado (Then)

Ver secciÃ³n **Then** en el extracto anterior del ERS. En automatizaciÃ³n backend, el test asociado comprueba el contrato API/servicio equivalente o queda explÃ­citamente marcado como pendiente si el criterio es solo UI, infraestructura o legalidad operativa fuera del alcance de pytest.

## Link directo al test

Ejecutar:

```bash
pytest tests/ers/test_gherkin_dynamic.py::test_RNF005_S01 -v
```

Archivo de definiciÃ³n dinÃ¡mica: [`tests/ers/test_gherkin_dynamic.py`](../../tests/ers/test_gherkin_dynamic.py)

---

## Estado de automatizaciÃ³n backend

Implementada en `tests/ers/gherkin_impl.py` (comprueba API/servicios equivalentes al Then del ERS).


<!-- file: RNF005-S02.md -->

# Los endpoints del backend estÃ¡n documentados con Swagger

## Nombre del test

`tests/ers/test_gherkin_dynamic.py::test_RNF005_S02`

## PropÃ³sito

Validar el criterio de aceptaciÃ³n Gherkin del ERS ICM para **RNF005** â€” escenario 2.

## Requisito o caso de negocio asociado

- **Requisito:** `RNF005` (ver `docs/requisitos/ERS_ICM_Requisitos.md`).

## Inputs (Given / When â€” extracto ERS)

**Given (Dado que):**
- El sistema estÃ¡ desplegado en el entorno de producciÃ³n

**When (Cuando):**
- Se accede a la ruta de documentaciÃ³n Swagger del backend

**Then (Entonces):**
- Todos los endpoints disponibles estÃ¡n listados y documentados con su mÃ©todo HTTP, parÃ¡metros esperados, cuerpo de la solicitud y estructura de la respuesta
- La documentaciÃ³n refleja el estado actual del backend sin endpoints faltantes ni documentaciÃ³n desactualizada

---

## Resultado esperado (Then)

Ver secciÃ³n **Then** en el extracto anterior del ERS. En automatizaciÃ³n backend, el test asociado comprueba el contrato API/servicio equivalente o queda explÃ­citamente marcado como pendiente si el criterio es solo UI, infraestructura o legalidad operativa fuera del alcance de pytest.

## Link directo al test

Ejecutar:

```bash
pytest tests/ers/test_gherkin_dynamic.py::test_RNF005_S02 -v
```

Archivo de definiciÃ³n dinÃ¡mica: [`tests/ers/test_gherkin_dynamic.py`](../../tests/ers/test_gherkin_dynamic.py)

---

## Estado de automatizaciÃ³n backend

Implementada en `tests/ers/gherkin_impl.py` (comprueba API/servicios equivalentes al Then del ERS).


<!-- file: RNF005-S03.md -->

# El cÃ³digo cumple con los principios SOLID verificables

## Nombre del test

`tests/ers/test_gherkin_dynamic.py::test_RNF005_S03`

## PropÃ³sito

Validar el criterio de aceptaciÃ³n Gherkin del ERS ICM para **RNF005** â€” escenario 3.

## Requisito o caso de negocio asociado

- **Requisito:** `RNF005` (ver `docs/requisitos/ERS_ICM_Requisitos.md`).

## Inputs (Given / When â€” extracto ERS)

**Given (Dado que):**
- El equipo de Arquitectura de Software I realiza la evaluaciÃ³n formal del Corte 3

**When (Cuando):**
- Analiza la estructura de clases, servicios y mÃ³dulos del backend

**Then (Entonces):**
- Cada clase o componente tiene una Ãºnica responsabilidad claramente definida (SRP)
- Es posible extender el comportamiento del sistema sin modificar clases existentes (OCP)
- El sistema no presenta dependencias directas entre mÃ³dulos de alto y bajo nivel (DIP)
- El informe de evaluaciÃ³n no identifica violaciones crÃ­ticas no justificadas a ninguno de los cinco principios SOLID

## Resultado esperado (Then)

Ver secciÃ³n **Then** en el extracto anterior del ERS. En automatizaciÃ³n backend, el test asociado comprueba el contrato API/servicio equivalente o queda explÃ­citamente marcado como pendiente si el criterio es solo UI, infraestructura o legalidad operativa fuera del alcance de pytest.

## Link directo al test

Ejecutar:

```bash
pytest tests/ers/test_gherkin_dynamic.py::test_RNF005_S03 -v
```

Archivo de definiciÃ³n dinÃ¡mica: [`tests/ers/test_gherkin_dynamic.py`](../../tests/ers/test_gherkin_dynamic.py)

---

## Estado de automatizaciÃ³n backend

Implementada en `tests/ers/gherkin_impl.py` (comprueba API/servicios equivalentes al Then del ERS).


<!-- file: RNF006-S01.md -->

# El sistema captura datos personales de clientes mayoristas con aviso de privacidad

## Nombre del test

`tests/ers/test_gherkin_dynamic.py::test_RNF006_S01`

## PropÃ³sito

Validar el criterio de aceptaciÃ³n Gherkin del ERS ICM para **RNF006** â€” escenario 1.

## Requisito o caso de negocio asociado

- **Requisito:** `RNF006` (ver `docs/requisitos/ERS_ICM_Requisitos.md`).

## Inputs (Given / When â€” extracto ERS)

**Given (Dado que):**
- Un operario registra los datos de un cliente mayorista durante un despacho

**When (Cuando):**
- Completa el formulario con nombre, correo, telÃ©fono y direcciÃ³n

**Then (Entonces):**
- El sistema informa al operario, antes de guardar los datos, que esa informaciÃ³n serÃ¡ tratada conforme a la polÃ­tica de privacidad de ICM bajo la Ley 1581 de 2012
- No almacena los datos del cliente sin que ese aviso haya sido presentado en el flujo

---

## Resultado esperado (Then)

Ver secciÃ³n **Then** en el extracto anterior del ERS. En automatizaciÃ³n backend, el test asociado comprueba el contrato API/servicio equivalente o queda explÃ­citamente marcado como pendiente si el criterio es solo UI, infraestructura o legalidad operativa fuera del alcance de pytest.

## Link directo al test

Ejecutar:

```bash
pytest tests/ers/test_gherkin_dynamic.py::test_RNF006_S01 -v
```

Archivo de definiciÃ³n dinÃ¡mica: [`tests/ers/test_gherkin_dynamic.py`](../../tests/ers/test_gherkin_dynamic.py)

---

## Estado de automatizaciÃ³n backend

Implementada en `tests/ers/gherkin_impl.py` (comprueba API/servicios equivalentes al Then del ERS).


<!-- file: RNF006-S02.md -->

# Los datos personales de clientes no son accesibles para el Auxiliar de Despacho fuera del contexto de su operaciÃ³n

## Nombre del test

`tests/ers/test_gherkin_dynamic.py::test_RNF006_S02`

## PropÃ³sito

Validar el criterio de aceptaciÃ³n Gherkin del ERS ICM para **RNF006** â€” escenario 2.

## Requisito o caso de negocio asociado

- **Requisito:** `RNF006` (ver `docs/requisitos/ERS_ICM_Requisitos.md`).

## Inputs (Given / When â€” extracto ERS)

**Given (Dado que):**
- El sistema tiene almacenados datos personales de clientes mayoristas

**When (Cuando):**
- Un Auxiliar de Despacho intenta consultar el historial de clientes fuera del contexto de un despacho activo

**Then (Entonces):**
- El sistema no expone listados de datos personales de clientes a ese rol
- El acceso a esa informaciÃ³n estÃ¡ restringido al Almacenista y al Administrador dentro del mÃ³dulo de reportes

---

## Resultado esperado (Then)

Ver secciÃ³n **Then** en el extracto anterior del ERS. En automatizaciÃ³n backend, el test asociado comprueba el contrato API/servicio equivalente o queda explÃ­citamente marcado como pendiente si el criterio es solo UI, infraestructura o legalidad operativa fuera del alcance de pytest.

## Link directo al test

Ejecutar:

```bash
pytest tests/ers/test_gherkin_dynamic.py::test_RNF006_S02 -v
```

Archivo de definiciÃ³n dinÃ¡mica: [`tests/ers/test_gherkin_dynamic.py`](../../tests/ers/test_gherkin_dynamic.py)

---

## Estado de automatizaciÃ³n backend

Implementada en `tests/ers/gherkin_impl.py` (comprueba API/servicios equivalentes al Then del ERS).


<!-- file: RNF006-S03.md -->

# El equipo documenta la autorizaciÃ³n de ICM antes de usar datos reales en pruebas

## Nombre del test

`tests/ers/test_gherkin_dynamic.py::test_RNF006_S03`

## PropÃ³sito

Validar el criterio de aceptaciÃ³n Gherkin del ERS ICM para **RNF006** â€” escenario 3.

## Requisito o caso de negocio asociado

- **Requisito:** `RNF006` (ver `docs/requisitos/ERS_ICM_Requisitos.md`).

## Inputs (Given / When â€” extracto ERS)

**Given (Dado que):**
- El equipo de desarrollo va a ejecutar pruebas de aceptaciÃ³n usando datos operativos reales de ICM en el Corte 3

**When (Cuando):**
- Se planifica la fase de pruebas de aceptaciÃ³n

**Then (Entonces):**
- El equipo debe contar con un documento de autorizaciÃ³n expresa firmado por ICM que permita el uso de sus datos operativos en el contexto acadÃ©mico del proyecto
- Las pruebas con datos reales no deben ejecutarse hasta que esa autorizaciÃ³n estÃ© formalmente obtenida

# **7. Resumen de Trazabilidad Requisitos â€” MÃ³dulos**

La siguiente tabla presenta un resumen de todos los requisitos especificados en este documento, con su mÃ³dulo de pertenencia y las reglas de negocio que les aplican directamente. Esta tabla constituye el punto de partida para la Matriz de Trazabilidad Requisitos-Pruebas que debe ser elaborada por la asignatura de Pruebas de Software como entregable del Corte 1.

| **ID** | **Nombre** | **MÃ³dulo** | **Reglas de Negocio** |
| --- | --- | --- | --- |
| RF-001 | Inicio de SesiÃ³n con Credenciales Ãšnicas | AutenticaciÃ³n | BR-01, BR-03 |
| RF-002 | GestiÃ³n de Credenciales de Usuario | AutenticaciÃ³n | BR-01, BR-02 |
| RF-003 | Registro de Producto en el CatÃ¡logo (SKU) | GestiÃ³n de Inventario | BR-04, BR-11, BR-12, BR-13 |
| RF-004 | Consulta y BÃºsqueda de Inventario en Tiempo Real | GestiÃ³n de Inventario | BR-11, BR-13 |
| RF-005 | RecepciÃ³n de MercancÃ­a | RecepciÃ³n de MercancÃ­a | BR-04, BR-09, BR-10, BR-11, BR-13 |
| RF-006 | Despacho y Salidas de Inventario | Despacho y Salidas | BR-08, BR-10, BR-11, BR-13 |
| RF-007 | Movimientos Internos entre Ubicaciones | Movimientos Internos | BR-06, BR-10, BR-11 |
| RF-008 | Registro de Devoluciones de Productos | Devoluciones | BR-02, BR-05, BR-10 |
| RF-009 | Ajustes de Inventario | Ajustes de Inventario | BR-06, BR-07, BR-10, BR-11 |
| RF-010 | Reportes e Indicadores Operativos | Reportes e Indicadores | BR-10, BR-11, BR-13 |
| RF-011 | Alertas Proactivas del Sistema | Alertas Proactivas | BR-04, BR-10, BR-11 |
| RF-012 | Log de AuditorÃ­a y Trazabilidad | AuditorÃ­a y Trazabilidad | BR-01, BR-06, BR-07, BR-10 |
| RNF-001 | Usabilidad e Interfaz Intuitiva | Transversal | â€” |
| RNF-002 | Disponibilidad del Sistema | Transversal | BR-03 |
| RNF-003 | Seguridad e Integridad de Datos | Transversal | BR-01, BR-02, BR-10 |
| RNF-004 | Rendimiento en Consultas y Operaciones | Transversal | â€” |
| RNF-005 | Mantenibilidad y EstÃ¡ndares TÃ©cnicos | Transversal | â€” |
| RNF-006 | Cumplimiento Legal: Ley 1581 de 2012 | Transversal | â€” |

# **8. Conclusiones**

El presente documento centraliza la especificaciÃ³n completa de dieciocho requisitos â€”doce funcionales y seis no funcionalesâ€” para el sistema de gestiÃ³n de inventario y operaciones de Import Corporal Medical. Cada requisito ha sido elaborado a partir de la informaciÃ³n recogida durante el proceso de elicitaciÃ³n con los responsables operativos de ICM y alineado con las condiciones acadÃ©micas del Proyecto Nuclear 3.

Los requisitos funcionales cubren la totalidad de los mÃ³dulos identificados en la elicitaciÃ³n: autenticaciÃ³n y gestiÃ³n de credenciales, gestiÃ³n de inventario, recepciÃ³n de mercancÃ­a, despacho y salidas, movimientos internos, devoluciones, ajustes de inventario, reportes e indicadores, alertas proactivas y auditorÃ­a. Los requisitos no funcionales complementan esta especificaciÃ³n con atributos de calidad medibles en usabilidad, disponibilidad, seguridad, rendimiento, mantenibilidad y cumplimiento legal.

La redacciÃ³n de los criterios de aceptaciÃ³n en formato Gherkin responde a una decisiÃ³n deliberada orientada a facilitar el trabajo de la asignatura de Pruebas de Software: cada escenario puede ser convertido directamente en un caso de prueba sin necesidad de reinterpretaciÃ³n, lo que reduce el margen de error entre lo que el sistema debe hacer y lo que efectivamente se verifica en las fases de prueba.

Este documento debe ser considerado un artefacto vivo durante el desarrollo del proyecto: cualquier cambio â€¦

## Resultado esperado (Then)

Ver secciÃ³n **Then** en el extracto anterior del ERS. En automatizaciÃ³n backend, el test asociado comprueba el contrato API/servicio equivalente o queda explÃ­citamente marcado como pendiente si el criterio es solo UI, infraestructura o legalidad operativa fuera del alcance de pytest.

## Link directo al test

Ejecutar:

```bash
pytest tests/ers/test_gherkin_dynamic.py::test_RNF006_S03 -v
```

Archivo de definiciÃ³n dinÃ¡mica: [`tests/ers/test_gherkin_dynamic.py`](../../tests/ers/test_gherkin_dynamic.py)

---

## Estado de automatizaciÃ³n backend

Implementada en `tests/ers/gherkin_impl.py` (comprueba API/servicios equivalentes al Then del ERS).
