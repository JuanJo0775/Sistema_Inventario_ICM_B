#!/usr/bin/env python3
"""
Genera y sincroniza la sección arquitectónica del README principal.

El script inspecciona la estructura real del proyecto Django, construye un árbol
legible con comentarios solo en nodos relevantes y reemplaza de forma idempotente
el bloque de la sección "3. Estructura del Proyecto" en `docs/README_ARQUITECTURA.md`.

Uso:
    python scripts/generate_project_structure.py

Opcionalmente acepta un archivo JSON externo con overrides de exclusiones,
comentarios y profundidad.
"""

from __future__ import annotations

import argparse
import json
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Iterable

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_README = ROOT / "docs" / "README_ARQUITECTURA.md"
SECTION_ANCHOR = "## 3. Estructura del Proyecto\n\nEstructura de Directorios del Proyecto:"

DEFAULT_EXCLUDED_DIRS = {
    ".git",
    ".cursor",
    ".github",
    "venv",
    ".venv",
    "__pycache__",
    ".pytest_cache",
    "node_modules",
    "staticfiles",
    "media",
    "dist",
    "build",
    ".mypy_cache",
    ".ruff_cache",
    ".idea",
    ".vscode",
    "coverage",
    "migrations",
}

DEFAULT_EXCLUDED_SUFFIXES = {".pyc", ".log", ".sqlite3"}
DEFAULT_EXCLUDED_NAMES = {".DS_Store"}
DEFAULT_EXCLUDED_NAMES.add("__init__.py")

ROOT_FILES = {
    "manage.py",
    "pytest.ini",
    "README.md",
    "schema.yml",
    "docker-compose.yml",
    "docker-compose.prod.yml",
}

COMMENT_COLUMN_WIDTH = 62

ROOT_DIR_ORDER = ["config", "apps", "shared", "tests", "docs", "scripts", "requirements", "docker"]
APP_ORDER = ["authentication", "catalog", "inventory", "movements", "reports", "alerts", "audit"]
APP_CHILD_ORDER = [
    "models.py",
    "serializers.py",
    "views.py",
    "urls.py",
    "services.py",
    "selectors.py",
    "permissions.py",
    "exceptions.py",
    "signals.py",
    "admin.py",
    "tests",
]
CONFIG_ORDER = ["settings", "urls.py", "wsgi.py", "asgi.py"]
SETTINGS_ORDER = ["base.py", "development.py", "production.py", "test.py"]
SHARED_ORDER = ["models.py", "permissions.py", "exceptions.py", "mixins.py", "pagination.py", "openapi.py", "utils"]
DOCS_ORDER = ["README_ARQUITECTURA.md", "api", "requisitos", "test", "calidad_restricciones", "architecture", "adr"]
SCRIPTS_ORDER = [
    "README_SCRIPTS.md",
    "generate_project_structure.py",
    "parse_ers_gherkin.py",
    "generate_docs",
]
GENERATED_DOC_FILES = ["README_API.md", "README_PERMISOS.md", "README_TEST.md", "TRAZABILIDAD_ERS_GHERKIN.md"]
REQUIREMENTS_ORDER = ["base.txt", "development.txt", "production.txt"]
DOCKER_ORDER = ["Dockerfile", "entrypoint.sh"]
TESTS_ORDER = ["conftest.py", "factories.py", "ers", "integration"]

IMPORTANT_COMMENT_PATHS = {
    "config": "Configuración central del proyecto Django",
    "config/settings": "Configuración compartida y sobreescrituras por entorno",
    "config/settings/base.py": "Configuración base compartida",
    "config/settings/development.py": "Sobreescrituras para desarrollo local",
    "config/settings/production.py": "Sobreescrituras para producción",
    "config/settings/test.py": "Configuración aislada para la suite de pruebas",
    "config/urls.py": "URL root con inclusión por módulo",
    "config/wsgi.py": "Punto de entrada WSGI",
    "config/asgi.py": "Punto de entrada ASGI",
    "apps": "Todas las apps del dominio del backend",
    "apps/authentication": "RF-001, RF-002 — JWT, RBAC, restricción horaria",
    "apps/catalog": "RF-003 — Productos, SKUs, categorías y validadores",
    "apps/inventory": "RF-004 — Consulta de stock en tiempo real",
    "apps/movements": "RF-005 a RF-009 — Ledger central e invariantes de inventario",
    "apps/reports": "RF-010 — Reportes e indicadores operativos",
    "apps/alerts": "RF-011 — Alertas proactivas del sistema",
    "apps/audit": "RF-012 — Log de auditoría y trazabilidad",
    "shared": "Código compartido entre apps sin lógica de dominio",
    "shared/models.py": "BaseModel con timestamps y metadatos comunes",
    "shared/permissions.py": "Permisos RBAC base",
    "shared/exceptions.py": "Excepciones base del sistema",
    "shared/mixins.py": "Mixins reutilizables para views",
    "shared/pagination.py": "Configuración de paginación",
    "shared/openapi.py": "Tags OpenAPI y contratos compartidos",
    "shared/utils": "Utilidades transversales",
    "shared/utils/validators.py": "Validadores reutilizables",
    "tests": "Tests de integración cross-módulo",
    "tests/factories.py": "Factories de datos de prueba",
    "tests/ers": "Suite Gherkin dinámica alineada al ERS",
    "tests/integration": "Pruebas HTTP/API de integración",
    "docs": "Documentación técnica viva del proyecto",
    "docs/README_ARQUITECTURA.md": "Documento vivo de arquitectura",
    "docs/api": "Contratos OpenAPI, seguridad y permisos",
    "docs/requisitos": "Requisitos funcionales y contexto de negocio",
    "docs/test": "Trazabilidad y documentación de pruebas",
    "docs/calidad_restricciones": "Atributos de calidad y restricciones",
    "docs/architecture": "Síntesis arquitectónica: drivers, Utility Tree y relaciones con ADRs",
    "docs/architecture/architecture_drivers.md": "Drivers arquitectónicos priorizados basados en el código y requisitos",
    "docs/architecture/utility_tree.md": "Utility Tree: escenarios, métricas y trade-offs",
    "docs/architecture/architectural_constraints.md": "Restricciones arquitectónicas y riesgos",
    "docs/architecture/adr_relationships.md": "Trazabilidad entre drivers y ADRs",
    "docs/adr": "Architecture Decision Records",
    "scripts": "Automatizaciones reutilizables del repositorio",
    "scripts/README_SCRIPTS.md": "Indice y contexto de las automatizaciones",
    "scripts/generate_docs": "Generadores compartidos de documentación",
    "requirements": "Dependencias por entorno",
    "docker": "Infraestructura de contenedores y arranque",
    "manage.py": "Punto de entrada de comandos Django",
    "pytest.ini": "Configuración de pytest",
    "schema.yml": "Esquema OpenAPI consolidado",
    "docker-compose.yml": "Orquestación local del stack",
    "docker-compose.prod.yml": "Orquestación de producción",
    "README.md": "Resumen general del repositorio",
}

APP_FILE_COMMENTS = {
    "models.py": "Entidades y constraints de persistencia",
    "serializers.py": "Validación y transformación de entrada/salida",
    "views.py": "Adaptador HTTP sin reglas de negocio",
    "urls.py": "Rutas del módulo",
    "services.py": "Lógica de negocio y transacciones",
    "selectors.py": "Consultas de lectura sin efectos secundarios",
    "permissions.py": "Reglas de acceso y RBAC",
    "exceptions.py": "Excepciones de dominio",
    "signals.py": "Eventos de dominio y sincronización",
    "admin.py": "Registro administrativo del módulo",
}

APP_EXTRA_COMMENTS = {
    "authentication": {
        "services.py": "Autenticación JWT, RBAC y restricción horaria",
        "signals.py": "Sincronización de eventos de identidad",
    },
    "catalog": {
        "services.py": "Catálogo, SKUs definidos por usuario y validación de productos",
    },
    "inventory": {
        "selectors.py": "Lecturas de stock por ubicación",
    },
    "movements": {
        "services.py": "Ledger inmutable, validaciones BR-04 a BR-13 y atomicidad",
        "selectors.py": "Lecturas del ledger y stock derivado",
        "exceptions.py": "Errores de inventario y consistencia",
    },
    "reports": {
        "selectors.py": "Consultas agregadas para reportes y KPIs",
    },
    "alerts": {
        "services.py": "Generación de alertas operativas",
    },
    "audit": {
        "services.py": "Trazabilidad e inmutabilidad de eventos",
        "selectors.py": "Consultas de auditoría",
    },
}

DOCS_CHILDREN = {
    "api": ["README_API.md", "README_MATRIZ_PERMISOS.md"],
    "requisitos": ["ERS_ICM_Requisitos.md", "ICM_Informe_Elicitacion_v2_plus.docx.md"],
    "test": [
        "README_TEST.md",
        "TRAZABILIDAD_ERS_GHERKIN.md",
        "gherkin_scenarios.json",
        "gherkin_out_of_scope.json",
        "all_unit.md",
        "all_integration.md",
        "all_scenarios.md",
        "unit",
        "integration",
        "scenarios",
    ],
    "calidad_restricciones": ["README_ATRIBUTOS_CALIDAD.md", "README_RESTRICCIONES.md"],
    "architecture": [
        "architecture_drivers.md",
        "utility_tree.md",
        "architectural_constraints.md",
        "adr_relationships.md",
    ],
    "adr": [],
}

@dataclass(frozen=True)
class TreeConfig:
    root_label: str
    excluded_dirs: set[str] = field(default_factory=set)
    excluded_suffixes: set[str] = field(default_factory=set)
    excluded_names: set[str] = field(default_factory=set)
    max_depth: int = 4
    doc_paths: tuple[Path, ...] = ()


@dataclass(frozen=True)
class ArchitectureContext:
    root_label: str
    keywords: tuple[str, ...]
    existing_comments: dict[str, str]
    source_files: tuple[Path, ...]


def load_json_config(config_path: Path | None) -> dict:
    if not config_path:
        return {}
    if not config_path.exists():
        raise FileNotFoundError(f"No existe el archivo de configuración: {config_path}")
    raw = json.loads(config_path.read_text(encoding="utf-8"))
    if not isinstance(raw, dict):
        raise ValueError("La configuración externa debe ser un objeto JSON")
    return raw


def discover_reference_docs(root: Path) -> tuple[Path, ...]:
    candidates = [
        root / "docs" / "README_ARQUITECTURA.md",
        root / "docs" / "api" / "README_API.md",
        root / "docs" / "api" / "README_PERMISOS.md",
        root / "docs" / "test" / "README_TEST.md",
        root / "docs" / "test" / "TRAZABILIDAD_ERS_GHERKIN.md",
        root / "docs" / "requisitos" / "ERS_ICM_Requisitos.md",
        root / "docs" / "requisitos" / "ICM_Informe_Elicitacion_v2_plus.docx.md",
        root / "docs" / "calidad_restricciones" / "README_ATRIBUTOS_CALIDAD.md",
        root / "docs" / "calidad_restricciones" / "README_RESTRICCIONES.md",
    ]
    return tuple(path for path in candidates if path.exists())


def extract_text(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8")
    except OSError:
        return ""


def extract_keywords(texts: Iterable[str]) -> tuple[str, ...]:
    patterns = [
        r"RF-\d{3}",
        r"BR-\d{2}",
        r"RNF-\d{3}",
        r"JWT",
        r"RBAC",
        r"OpenAPI",
        r"Swagger",
        r"services\.py",
        r"selectors\.py",
        r"ledger",
        r"StockByLocation",
        r"America/Bogota",
        r"select_for_update",
        r"transaction\.atomic",
    ]
    detected: set[str] = set()
    for text in texts:
        for pattern in patterns:
            if re.search(pattern, text, flags=re.IGNORECASE):
                detected.add(pattern.replace(r"\\", "").replace("\\.", "."))
    return tuple(sorted(detected))


def extract_existing_tree_block(readme_text: str) -> str:
    anchor_index = readme_text.find(SECTION_ANCHOR)
    if anchor_index < 0:
        return ""
    block_start = readme_text.find("```", anchor_index)
    if block_start < 0:
        return ""
    block_start = readme_text.find("\n", block_start)
    if block_start < 0:
        return ""
    block_end = readme_text.find("\n```", block_start + 1)
    if block_end < 0:
        block_end = readme_text.find("```", block_start + 1)
        if block_end < 0:
            return ""
    return readme_text[block_start + 1 : block_end].strip()


def parse_existing_comments(tree_block: str) -> dict[str, str]:
    comments: dict[str, str] = {}
    for line in tree_block.splitlines():
        if "#" not in line:
            continue
        head, tail = line.split("#", 1)
        label = re.sub(r"^[\s│├└─]+", "", head).strip()
        label = label.rstrip("/")
        if not label:
            continue
        comments.setdefault(label.lower(), tail.strip())
    return comments


def load_existing_architecture_context(root: Path, readme_path: Path, doc_paths: tuple[Path, ...]) -> ArchitectureContext:
    texts = [extract_text(readme_path)]
    texts.extend(extract_text(path) for path in doc_paths)
    tree_block = extract_existing_tree_block(texts[0])
    existing_comments = parse_existing_comments(tree_block)
    root_label = root.name
    if tree_block:
        first_line = tree_block.splitlines()[0].strip()
        if first_line.endswith("/"):
            root_label = first_line.rstrip("/")
    return ArchitectureContext(
        root_label=root_label,
        keywords=extract_keywords(texts),
        existing_comments=existing_comments,
        source_files=tuple([readme_path, *doc_paths]),
    )


def load_tree_config(root: Path, readme_path: Path, config_path: Path | None = None) -> TreeConfig:
    external = load_json_config(config_path)
    excluded_dirs = set(DEFAULT_EXCLUDED_DIRS)
    excluded_dirs.update(str(item) for item in external.get("excluded_dirs", []))
    excluded_suffixes = set(DEFAULT_EXCLUDED_SUFFIXES)
    excluded_suffixes.update(str(item) for item in external.get("excluded_suffixes", []))
    excluded_names = set(DEFAULT_EXCLUDED_NAMES)
    excluded_names.update(str(item) for item in external.get("excluded_names", []))
    root_label = str(external.get("root_label") or readme_path.parent.parent.name or root.name)
    max_depth = int(external.get("max_depth", 4))
    return TreeConfig(
        root_label=root_label,
        excluded_dirs=excluded_dirs,
        excluded_suffixes=excluded_suffixes,
        excluded_names=excluded_names,
        max_depth=max_depth,
        doc_paths=discover_reference_docs(root),
    )


def is_excluded(path: Path, config: TreeConfig) -> bool:
    if path.name in config.excluded_names:
        return True
    if path.suffix in config.excluded_suffixes:
        return True
    return any(part in config.excluded_dirs for part in path.parts)


def rel_key(path: Path, root: Path) -> str:
    rel = path.relative_to(root).as_posix()
    return rel[:-1] if rel.endswith("/") else rel


def matches_any_prefix(value: str, prefixes: Iterable[str]) -> bool:
    return any(value == prefix or value.startswith(f"{prefix}/") for prefix in prefixes)


def allowed_root_child(path: Path) -> bool:
    if path.name in ROOT_FILES:
        return True
    return path.is_dir()


def sort_key_for_children(parent_key: str, child: Path) -> tuple[int, int, str]:
    name = child.name.lower()
    if parent_key == "":
        order = ROOT_DIR_ORDER + [file_name for file_name in sorted(ROOT_FILES)]
    elif parent_key == "config":
        order = CONFIG_ORDER
    elif parent_key == "config/settings":
        order = SETTINGS_ORDER
    elif parent_key == "shared":
        order = SHARED_ORDER
    elif parent_key == "docs":
        order = DOCS_ORDER
    elif parent_key.startswith("docs/") and parent_key.count("/") == 1:
        order = DOCS_CHILDREN.get(child.name, [])
    elif parent_key == "scripts":
        order = SCRIPTS_ORDER
    elif parent_key == "requirements":
        order = REQUIREMENTS_ORDER
    elif parent_key == "docker":
        order = DOCKER_ORDER
    elif parent_key == "tests":
        order = TESTS_ORDER
    elif parent_key == "apps":
        order = APP_ORDER
    elif parent_key.startswith("apps/"):
        order = APP_CHILD_ORDER
    else:
        order = []
    try:
        return (0 if child.is_dir() else 1, order.index(child.name), name)
    except ValueError:
        return (0 if child.is_dir() else 1, len(order), name)


def should_render_dir(path: Path, root: Path, config: TreeConfig, depth: int) -> bool:
    if is_excluded(path, config):
        return False
    rel = rel_key(path, root)
    if depth == 0:
        return True
    if matches_any_prefix(rel, {"apps", "config", "shared", "tests", "docs", "scripts", "requirements", "docker"}):
        return True
    return depth < config.max_depth


def should_render_file(path: Path, root: Path, config: TreeConfig, depth: int) -> bool:
    if is_excluded(path, config):
        return False
    rel = rel_key(path, root)
    if depth == 0:
        return path.name in ROOT_FILES
    if rel.startswith("apps/"):
        app_parts = path.relative_to(root).parts
        if len(app_parts) >= 3 and app_parts[2] == "tests":
            return path.name in {"__init__.py", "conftest.py", "factories.py"}
        return path.name in set(APP_FILE_COMMENTS) or path.name in {"__init__.py"}
    if rel.startswith("config/settings"):
        return path.name in SETTINGS_ORDER
    if rel.startswith("config"):
        return path.name in {"urls.py", "wsgi.py", "asgi.py", "__init__.py"}
    if rel.startswith("shared/utils"):
        return path.name == "validators.py" or path.name == "__init__.py"
    if rel.startswith("shared"):
        return path.name in set(SHARED_ORDER) or path.name == "__init__.py"
    if rel.startswith("docs/"):
        if path.parent.name in DOCS_CHILDREN:
            return path.name in set(DOCS_CHILDREN[path.parent.name])
        return path.name.startswith("README") or path.name.endswith(".md")
    if rel.startswith("scripts/generate_docs"):
        return path.name in {"menu.py", "utils.py", "__init__.py", "__main__.py"}
    if rel.startswith("scripts"):
        return path.suffix == ".py" or path.name == "README_SCRIPTS.md"
    if rel.startswith("requirements"):
        return path.suffix == ".txt"
    if rel.startswith("docker"):
        return path.name in DOCKER_ORDER
    if rel.startswith("tests"):
        if path.parent.name == "tests":
            return path.name in {"conftest.py", "factories.py"}
        if len(path.relative_to(root).parts) >= 3 and path.relative_to(root).parts[1] in {"ers", "integration"}:
            return path.name in {"gherkin_impl.py", "test_gherkin_dynamic.py"}
        return False
    return path.suffix in {".py", ".md", ".txt", ".yml", ".yaml", ".sh"} or path.name in {"Dockerfile"}


def resolve_comment_for_path(path: Path, root: Path, context: ArchitectureContext) -> str | None:
    rel = rel_key(path, root)
    exact = IMPORTANT_COMMENT_PATHS.get(rel)
    if exact:
        return exact

    if path.is_dir():
        if rel == "apps":
            return IMPORTANT_COMMENT_PATHS["apps"]
        if rel.startswith("apps/") and len(path.relative_to(root).parts) == 2:
            return IMPORTANT_COMMENT_PATHS.get(rel)
        if rel.startswith("docs/") and len(path.relative_to(root).parts) == 2:
            return IMPORTANT_COMMENT_PATHS.get(rel)
        if rel.startswith("scripts/") and len(path.relative_to(root).parts) == 2:
            return IMPORTANT_COMMENT_PATHS.get(rel)
        return IMPORTANT_COMMENT_PATHS.get(rel)

    label = path.name.lower()
    if label in context.existing_comments:
        return context.existing_comments[label]

    if path.parent == root and label in context.existing_comments:
        return context.existing_comments[label]

    parent_rel = rel_key(path.parent, root)
    if parent_rel.startswith("apps/"):
        app_name = path.parent.name if path.parent.parent.name == "apps" else path.parent.parent.name
        app_comment = APP_EXTRA_COMMENTS.get(app_name, {}).get(path.name)
        if app_comment:
            return app_comment
        if path.name in APP_FILE_COMMENTS:
            base = APP_FILE_COMMENTS[path.name]
            extra = APP_EXTRA_COMMENTS.get(app_name, {}).get(path.name)
            return extra or base

    if parent_rel == "config/settings" and path.name in SETTINGS_ORDER:
        return IMPORTANT_COMMENT_PATHS.get(f"config/settings/{path.name}")

    if parent_rel == "shared/utils" and path.name == "validators.py":
        return IMPORTANT_COMMENT_PATHS.get("shared/utils/validators.py")

    if parent_rel.startswith("docs/") and path.name in GENERATED_DOC_FILES:
        return context.existing_comments.get(path.name.lower()) or IMPORTANT_COMMENT_PATHS.get(parent_rel)

    if parent_rel == "scripts/generate_docs":
        base = {
            "utils.py": "Utilidades compartidas para generación documental",
            "__main__.py": "Entry point oficial de documentación de tests",
        }.get(path.name)
        if base:
            return base

    if path.name == "manage.py":
        return IMPORTANT_COMMENT_PATHS["manage.py"]
    if path.name == "Dockerfile":
        return "Imagen base del contenedor de despliegue"
    if path.name == "entrypoint.sh":
        return "Inicialización del contenedor y arranque"

    return None


def render_entry(path: Path, root: Path, context: ArchitectureContext, config: TreeConfig, prefix: str, is_last: bool, depth: int) -> list[str]:
    branch = "└── " if is_last else "├── "
    label = path.name + ("/" if path.is_dir() else "")
    comment = resolve_comment_for_path(path, root, context)
    tree_text = f"{prefix}{branch}{label}"
    if comment:
        display = f"{tree_text:<{COMMENT_COLUMN_WIDTH}}  # {comment}"
    else:
        display = tree_text
    lines = [display.rstrip()]
    if path.is_dir() and rel_key(path, root) in {"docs/test/unit", "docs/test/integration", "docs/test/scenarios"}:
        return lines
    if path.is_dir():
        children = list(iter_visible_children(path, root, config, depth + 1))
        next_prefix = prefix + ("    " if is_last else "│   ")
        for index, child in enumerate(children):
            lines.extend(render_entry(child, root, context, config, next_prefix, index == len(children) - 1, depth + 1))
    return lines


def iter_visible_children(dir_path: Path, root: Path, config: TreeConfig, depth: int) -> Iterable[Path]:
    if depth > config.max_depth and not matches_any_prefix(rel_key(dir_path, root), {"apps", "config", "shared", "tests", "docs", "scripts"}):
        return []

    children: list[Path] = []
    if rel_key(dir_path, root) == "docs":
        for name in DOCS_ORDER:
            candidate = dir_path / name
            if candidate.exists() and not is_excluded(candidate, config):
                children.append(candidate)
        return children

    if rel_key(dir_path, root) == "scripts":
        for name in SCRIPTS_ORDER:
            candidate = dir_path / name
            if candidate.exists() and not is_excluded(candidate, config):
                children.append(candidate)
        # Include any extra helper scripts that match the general policy.
        for candidate in sorted(dir_path.iterdir(), key=lambda p: sort_key_for_children("scripts", p)):
            if candidate in children or is_excluded(candidate, config):
                continue
            if candidate.is_dir() or candidate.suffix == ".py":
                children.append(candidate)
        return children

    if rel_key(dir_path, root) == "requirements":
        for name in REQUIREMENTS_ORDER:
            candidate = dir_path / name
            if candidate.exists() and not is_excluded(candidate, config):
                children.append(candidate)
        return children

    if rel_key(dir_path, root) == "docker":
        for name in DOCKER_ORDER:
            candidate = dir_path / name
            if candidate.exists() and not is_excluded(candidate, config):
                children.append(candidate)
        return children

    if rel_key(dir_path, root) == "config":
        for name in CONFIG_ORDER:
            candidate = dir_path / name
            if candidate.exists() and not is_excluded(candidate, config):
                children.append(candidate)
        return children

    if rel_key(dir_path, root) == "config/settings":
        for name in SETTINGS_ORDER:
            candidate = dir_path / name
            if candidate.exists() and not is_excluded(candidate, config):
                children.append(candidate)
        return children

    if rel_key(dir_path, root) == "shared":
        for name in SHARED_ORDER:
            candidate = dir_path / name
            if candidate.exists() and not is_excluded(candidate, config):
                children.append(candidate)
        return children

    if rel_key(dir_path, root) == "shared/utils":
        candidate = dir_path / "validators.py"
        if candidate.exists() and not is_excluded(candidate, config):
            return [candidate]
        return []

    if rel_key(dir_path, root) == "tests":
        for name in TESTS_ORDER:
            candidate = dir_path / name
            if candidate.exists() and not is_excluded(candidate, config):
                children.append(candidate)
        for candidate in sorted(dir_path.iterdir(), key=lambda p: sort_key_for_children("tests", p)):
            if candidate in children or is_excluded(candidate, config):
                continue
            if candidate.is_dir() or candidate.name in {"factories.py", "conftest.py"}:
                children.append(candidate)
        return children

    if rel_key(dir_path, root) == "apps":
        for name in APP_ORDER:
            candidate = dir_path / name
            if candidate.exists() and candidate.is_dir() and not is_excluded(candidate, config):
                children.append(candidate)
        return children

    if rel_key(dir_path, root).startswith("docs/") and dir_path.parent == root / "docs":
        key = dir_path.name
        if key in DOCS_CHILDREN and DOCS_CHILDREN[key]:
            for name in DOCS_CHILDREN[key]:
                candidate = dir_path / name
                if candidate.exists() and not is_excluded(candidate, config):
                    children.append(candidate)
            return children
        if key in DOCS_CHILDREN and not DOCS_CHILDREN[key]:
            return []

    if rel_key(dir_path, root).startswith("apps/"):
        for candidate in sorted(dir_path.iterdir(), key=lambda p: sort_key_for_children(rel_key(dir_path, root), p)):
            if is_excluded(candidate, config):
                continue
            if candidate.is_dir():
                if candidate.name == "tests":
                    children.append(candidate)
                    continue
                if candidate.name == "migrations":
                    continue
                children.append(candidate)
                continue
            if should_render_file(candidate, root, config, depth):
                children.append(candidate)
        return children

    for candidate in sorted(dir_path.iterdir(), key=lambda p: sort_key_for_children(rel_key(dir_path, root), p)):
        if is_excluded(candidate, config):
            continue
        if candidate.is_dir():
            if should_render_dir(candidate, root, config, depth):
                children.append(candidate)
        elif should_render_file(candidate, root, config, depth):
            children.append(candidate)
    return children


def build_tree(root: Path, context: ArchitectureContext, config: TreeConfig) -> str:
    lines = [f"{context.root_label}/"]
    children = list(iter_visible_children(root, root, config, 0))
    for index, child in enumerate(children):
        lines.extend(render_entry(child, root, context, config, "", index == len(children) - 1, 0))
    return "\n".join(lines)


def replace_architecture_section(readme_text: str, tree_text: str) -> str:
    anchor_index = readme_text.find(SECTION_ANCHOR)
    if anchor_index < 0:
        raise RuntimeError("No se encontró la sección arquitectónica objetivo en el README")

    block_start = readme_text.find("```", anchor_index)
    if block_start < 0:
        raise RuntimeError("No se encontró el bloque de árbol dentro de la sección arquitectónica")

    block_end = readme_text.find("\n```", block_start + 3)
    if block_end < 0:
        raise RuntimeError("No se encontró el cierre del bloque de árbol en el README")

    return (
        readme_text[:block_start]
        + f"```text\n{tree_text}\n```"
        + readme_text[block_end + 4 :]
    )


def update_readme_section(readme_path: Path, tree_text: str) -> None:
    try:
        original = readme_path.read_text(encoding="utf-8")
    except FileNotFoundError as exc:
        raise FileNotFoundError(f"No existe el README de arquitectura: {readme_path}") from exc
    updated = replace_architecture_section(original, tree_text)
    readme_path.write_text(updated, encoding="utf-8")


def build_external_config(config: TreeConfig, external: dict) -> TreeConfig:
    excluded_dirs = set(config.excluded_dirs)
    excluded_dirs.update(str(item) for item in external.get("excluded_dirs", []))
    excluded_suffixes = set(config.excluded_suffixes)
    excluded_suffixes.update(str(item) for item in external.get("excluded_suffixes", []))
    excluded_names = set(config.excluded_names)
    excluded_names.update(str(item) for item in external.get("excluded_names", []))
    root_label = str(external.get("root_label", config.root_label))
    max_depth = int(external.get("max_depth", config.max_depth))
    return TreeConfig(
        root_label=root_label,
        excluded_dirs=excluded_dirs,
        excluded_suffixes=excluded_suffixes,
        excluded_names=excluded_names,
        max_depth=max_depth,
        doc_paths=config.doc_paths,
    )


def main() -> None:
    parser = argparse.ArgumentParser(description="Genera la estructura del proyecto y sincroniza el README arquitectónico.")
    parser.add_argument("--root", type=Path, default=ROOT, help="Raíz del proyecto a analizar")
    parser.add_argument("--readme", type=Path, default=DEFAULT_README, help="Archivo README de arquitectura a actualizar")
    parser.add_argument("--config", type=Path, default=None, help="Configuración externa JSON opcional")
    parser.add_argument("--dry-run", action="store_true", help="Imprime el árbol sin modificar archivos")
    args = parser.parse_args()

    root = args.root.resolve()
    readme_path = args.readme.resolve()
    tree_config = load_tree_config(root, readme_path, args.config)
    external = load_json_config(args.config)
    if external:
        tree_config = build_external_config(tree_config, external)

    context = load_existing_architecture_context(root, readme_path, tree_config.doc_paths)
    tree_text = build_tree(root, context, tree_config)

    if args.dry_run:
        print(tree_text)
        return

    update_readme_section(readme_path, tree_text)
    print(f"Estructura arquitectónica actualizada en {readme_path}")


if __name__ == "__main__":
    main()