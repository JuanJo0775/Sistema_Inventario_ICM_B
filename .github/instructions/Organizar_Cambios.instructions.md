---
description: Instrucciones para la gestión de ramas, commits y flujo de trabajo senior en Git
applyTo: ".*"
---

Actúa como un desarrollador senior encargado de organizar cambios en un repositorio usando buenas prácticas de Git.
Tu tarea es analizar los cambios actuales y gestionarlos correctamente siguiendo estas reglas:

### Análisis previo
* Revisar si ya existen ramas relacionadas antes de crear nuevas.
* Reutilizar ramas existentes cuando correspondan al contexto del cambio.
* Crear nuevas ramas solo si aporta claridad y organización.

### Commits
* Cada commit debe representar un cambio lógico claro y específico.
* No mezclar cambios no relacionados.
* Evitar commits demasiado grandes o demasiado pequeños sin sentido.
* Dividir los cambios cuando mejore la claridad del historial.

### Nomenclatura de commits (obligatorio)
Usar formato tipo Conventional Commits:
`tipo(scope): descripcion breve`

**Tipos permitidos:**
feat, fix, refactor, chore, docs, style, test

**Reglas:**
* Usar inglés
* Descripción en minúsculas
* Ser específico y directo
* El scope debe reflejar el módulo, componente o contexto afectado

**Ejemplos:**
* feat(auth): implement login with jwt
* fix(reservations): correct date validation bug
* refactor(inventory): simplify stock calculation logic

### Manejo de ramas
* Usar una rama principal de trabajo como base.
* Clasificar los cambios según su naturaleza.
* Si múltiples commits pertenecen a una misma funcionalidad o refactor relevante: Agruparlos en una rama dedicada.

### Creación de nuevas ramas
Crear ramas cuando:
* Hay múltiples cambios relacionados
* El cambio tiene suficiente entidad propia

Usar nomenclatura clara y consistente:
`tipo-descripcion-corta`

**Ejemplos:**
* feature-auth-system
* refactor-inventory-logic
* fix-reservation-validation

### Trabajo con remoto
* Toda rama creada debe ser publicada en el repositorio remoto.
* Asegurar sincronización entre local y remoto.
* No dejar ramas relevantes solo en local.

### Pull Requests
* Abrir un PR cuando el cambio lógico esté completo, la rama ya esté publicada y los tests relevantes hayan pasado.
* Usar un PR por cambio funcional o refactor relevante; evitar agrupar temas no relacionados.
* Elegir como base la rama principal de integración del flujo actual del repositorio y como head la rama publicada del trabajo.
* Antes de crear el PR, revisar si ya existe uno abierto para la misma rama o tema y reutilizarlo si corresponde.
* Describir en el PR qué cambió, por qué cambió y cómo se validó, con referencia al alcance afectado.

### Integración
* Integrar las ramas secundarias hacia la rama principal de trabajo.
* Mantener la rama principal:
    * Actualizada
    * Consistente
    * Con historial limpio

### Resultado esperado
* Commits claros, específicos y bien nombrados
* Uso correcto de Conventional Commits
* Ramas bien organizadas y coherentes
* Ramas publicadas en remoto
* Historial limpio, entendible y mantenible

### Sincronización con reglas de agentes
Antes de modificar reglas de negocio, APIs o tests, consulta la guía de agentes y asistentes de código para asegurar consistencia de políticas y referencias:

- Instrucción canonical para agentes: [`.github/instructions/Agents.instructions.md`](.github/instructions/Agents.instructions.md)
- Documento legible en la raíz: [AGENTS.md](AGENTS.md)
- Runbook operativo CI/CD: [docs/CI-CD/README_CICD.md](../../docs/CI-CD/README_CICD.md)

Mantén estas guías sincronizadas: cuando actualices políticas que afecten el flujo de trabajo (nomenclatura de ramas, convención de commits, pruebas obligatorias), actualiza ambos archivos y referencia los RF/BR/RNF afectados en la descripción del PR.