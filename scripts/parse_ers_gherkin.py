#!/usr/bin/env python3
"""
Parsea docs/ERS_ICM_Requisitos.md y genera:
- docs/test/gherkin_scenarios.json (metadatos por escenario)
- docs/test/scenarios/<ID>.md (uno por escenario, formato ICM)

Ejecutar desde la raíz del repo:
    python scripts/parse_ers_gherkin.py
"""

from __future__ import annotations

import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ERS_PATH = ROOT / "docs" / "ERS_ICM_Requisitos.md"
OUT_JSON = ROOT / "docs" / "test" / "gherkin_scenarios.json"
OUT_DIR = ROOT / "docs" / "test" / "scenarios"

# IDs con implementación en tests/ers/gherkin_impl.py (sincronizar al añadir escenarios)
_IMPL_IDS = {
    "RF001-S01",
    "RF001-S02",
    "RF001-S03",
    "RF001-S04",
    "RF001-S05",
    "RF002-S01",
    "RF002-S02",
    "RF002-S03",
    "RF002-S04",
    "RF002-S05",
    "RF003-S01",
    "RF003-S02",
    "RF003-S03",
    "RF003-S04",
    "RF003-S05",
    "RF003-S06",
    "RF003-S07",
    "RF004-S01",
    "RF004-S02",
    "RF004-S03",
    "RF004-S04",
    "RF004-S05",
    "RF004-S06",
    "RF004-S07",
    "RF005-S01",
    "RF005-S02",
    "RF005-S03",
    "RF005-S04",
    "RF005-S05",
    "RF005-S06",
    "RF005-S07",
    "RF006-S01",
    "RF006-S02",
    "RF006-S03",
    "RF006-S04",
    "RF006-S05",
    "RF007-S01",
    "RF007-S02",
    "RF007-S03",
    "RF008-S01",
    "RF008-S02",
    "RF009-S01",
    "RF009-S02",
    "RF009-S03",
    "RF009-S04",
    "RF009-S06",
    "RF010-S01",
    "RF010-S02",
    "RF010-S04",
    "RF010-S05",
    "RF010-S07",
    "RF011-S01",
    "RF012-S01",
    "RF012-S02",
    "RF012-S05",
    "RF012-S06",
    "RNF003-S02",
    "RNF003-S03",
    "RNF004-S01",
    "RNF005-S01",
    "RNF006-S01",
}


def _slug_id(rf: str, num: int) -> str:
    return f"{rf.upper()}-S{num:02d}"


def parse_ers() -> list[dict]:
    text = ERS_PATH.read_text(encoding="utf-8")
    lines = text.splitlines()
    current_rf: str | None = None
    scenarios: list[dict] = []

    i = 0
    while i < len(lines):
        line = lines[i]
        m_rf = re.match(r"^## \*\*(RF|RNF)-(\d+)", line)
        if m_rf:
            kind, num = m_rf.group(1), m_rf.group(2)
            current_rf = f"{kind}{int(num):03d}"
            i += 1
            continue
        m_sc = re.match(r"^### Scenario (\d+):\s*(.+)\s*$", line)
        if m_sc and current_rf:
            sn = int(m_sc.group(1))
            title = m_sc.group(2).strip()
            sid = _slug_id(current_rf, sn)
            body_lines: list[str] = []
            i += 1
            while i < len(lines):
                nxt = lines[i]
                if re.match(r"^### Scenario \d+:", nxt) or re.match(r"^## \*\*", nxt):
                    break
                body_lines.append(nxt)
                i += 1
            body = "\n".join(body_lines).strip()
            given = when = then = ""
            if "**Given" in body or "**Given (Dado que):**" in body:
                parts = re.split(r"\*\*When|\*\*Then", body, flags=re.I)
                given = parts[0].strip() if parts else ""
                rest = body[len(parts[0]) :] if parts else body
                m_when = re.search(r"\*\*When[^*]*\*\*.*?(?=\*\*Then|\Z)", rest, re.S | re.I)
                m_then = re.search(r"\*\*Then[^*]*\*\*.*", rest, re.S | re.I)
                if m_when:
                    when = m_when.group(0).strip()
                if m_then:
                    then = m_then.group(0).strip()
            scenarios.append(
                {
                    "id": sid,
                    "rf": current_rf,
                    "scenario_number": sn,
                    "title": title,
                    "given_when_then": body,
                    "given": given or body[:500],
                    "when": when,
                    "then": then or "",
                    "source": "docs/ERS_ICM_Requisitos.md",
                }
            )
            continue
        i += 1
    return scenarios


def write_markdown(sc: dict) -> None:
    sid = sc["id"]
    pytest_node = f"tests/ers/test_gherkin_dynamic.py::test_{sid.replace('-', '_')}"
    auto = sid in _IMPL_IDS
    auto_txt = (
        "Implementada en `tests/ers/gherkin_impl.py` (comprueba API/servicios equivalentes al Then del ERS)."
        if auto
        else "Pendiente en backend: al ejecutar el test dinámico se aplicará `pytest.skip` con el motivo hasta que exista implementación."
    )
    md = f"""# {sc["title"]}

## Nombre del test

`{pytest_node}`

## Propósito

Validar el criterio de aceptación Gherkin del ERS ICM para **{sc["rf"]}** — escenario {sc["scenario_number"]}.

## Requisito o caso de negocio asociado

- **Requisito:** `{sc["rf"]}` (ver `docs/ERS_ICM_Requisitos.md`).
- **Fuente complementaria:** `docs/ICM_Informe_Elicitacion_v2_plus.docx.md` (contexto de negocio y BR cuando aplica).

## Inputs (Given / When — extracto ERS)

{sc["given_when_then"][:4000]}{"…" if len(sc["given_when_then"]) > 4000 else ""}

## Resultado esperado (Then)

Ver sección **Then** en el extracto anterior del ERS. En automatización backend, el test asociado comprueba el contrato API/servicio equivalente o queda explícitamente marcado como pendiente si el criterio es solo UI, infraestructura o legalidad operativa fuera del alcance de pytest.

## Link directo al test

Ejecutar:

```bash
pytest {pytest_node} -v
```

Archivo de definición dinámica: [`tests/ers/test_gherkin_dynamic.py`](../../tests/ers/test_gherkin_dynamic.py)

Implementaciones concretas (cuando existan) pueden delegarse en módulos bajo `tests/ers/impl/`.

---

## Estado de automatización backend

{auto_txt}
"""
    (OUT_DIR / f"{sid}.md").write_text(md, encoding="utf-8")


def main() -> None:
    scenarios = parse_ers()
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    OUT_JSON.write_text(json.dumps(scenarios, ensure_ascii=False, indent=2), encoding="utf-8")
    for sc in scenarios:
        write_markdown(sc)
    print(f"Escenarios: {len(scenarios)}")
    print(f"JSON: {OUT_JSON}")
    print(f"Markdown: {OUT_DIR}/*.md")


if __name__ == "__main__":
    main()
