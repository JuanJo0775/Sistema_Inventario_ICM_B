#!/usr/bin/env python3
"""Generate a semantic architectural tree and keep docs/README_ARQUITECTURA.md in sync.

The script inspects the repository, keeps only architecture-relevant nodes,
annotates them with concise semantic comments, updates the architecture block in
`docs/README_ARQUITECTURA.md`, and writes a compact auxiliary report with the
relevant structural deltas.
"""

from __future__ import annotations

import argparse
import ast
import json
import re
from collections import defaultdict
from dataclasses import dataclass, field
from pathlib import Path
from typing import Iterable, Iterator, Sequence

ROOT = Path(__file__).resolve().parents[2]
DEFAULT_README = ROOT / "docs" / "README_ARQUITECTURA.md"
DEFAULT_REPORT = ROOT / "scripts" / "project_structure" / "project_structure_report.md"
SECTION_ANCHOR = (
    "## 3. Estructura del Proyecto\n\nEstructura de Directorios del Proyecto:"
)
DERIVED_REPORT_REL = "scripts/project_structure/project_structure_report.md"

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
DEFAULT_EXCLUDED_NAMES = {".DS_Store", "__init__.py"}
ROOT_FILES = {
    "manage.py",
    "pytest.ini",
    "README.md",
    "schema.yml",
    "docker-compose.yml",
    "docker-compose.prod.yml",
}

ROOT_DIR_ORDER = [
    "config",
    "apps",
    "shared",
    "tests",
    "docs",
    "scripts",
    "requirements",
    "docker",
]
APP_ORDER = [
    "authentication",
    "catalog",
    "inventory",
    "movements",
    "reports",
    "alerts",
    "audit",
]
APP_FILE_ORDER = [
    "models.py",
    "serializers.py",
    "views.py",
    "urls.py",
    "services.py",
    "selectors.py",
    "permissions.py",
    "exceptions.py",
    "signals.py",
    "tasks.py",
    "middleware.py",
    "admin.py",
    "tests",
]
CONFIG_ORDER = ["settings", "urls.py", "middleware.py", "wsgi.py", "asgi.py"]
SETTINGS_ORDER = ["base.py", "development.py", "production.py", "test.py"]
SHARED_ORDER = [
    "models.py",
    "permissions.py",
    "exceptions.py",
    "mixins.py",
    "pagination.py",
    "openapi.py",
    "email_service.py",
    "utils",
]
DOCS_ORDER = [
    "README_ARQUITECTURA.md",
    "api",
    "requisitos",
    "test",
    "calidad_restricciones",
    "architecture",
    "adr",
    "guias",
    "CI",
]
SCRIPTS_ORDER = [
    "README_SCRIPTS.md",
    "project_structure",
    "parse_ers_gherkin.py",
    "generate_docs",
]
REQUIREMENTS_ORDER = ["base.txt", "development.txt", "production.txt"]
DOCKER_ORDER = ["Dockerfile", "entrypoint.sh"]
TESTS_ORDER = ["conftest.py", "factories.py", "ers", "integration"]
DOCS_CHILDREN = {
    "api": ["README_API.md", "README_MATRIZ_PERMISOS.md", "REFERENCIA_ENDPOINTS.md"],
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
    "calidad_restricciones": [
        "README_ATRIBUTOS_CALIDAD.md",
        "README_RESTRICCIONES.md",
        "INFORME_COMPLETITUD_PRINCIPIOS_Y_CALIDAD.md",
    ],
    "architecture": [
        "architecture_drivers.md",
        "utility_tree.md",
        "architectural_constraints.md",
        "adr_relationships.md",
    ],
    "adr": [],
    "guias": ["ENV_GUIDE.md", "SEED_DB.md"],
    "CI": ["README_CICD.md"],
}

IMPORTANT_COMMENT_PATHS = {
    "config": "Configuración central del proyecto Django",
    "config/settings": "Configuración compartida y sobreescrituras por entorno",
    "config/settings/base.py": "Configuración base compartida",
    "config/settings/development.py": "Sobreescrituras para desarrollo local",
    "config/settings/production.py": "Sobreescrituras para producción",
    "config/settings/test.py": "Configuración aislada para la suite de pruebas",
    "config/urls.py": "Composición de rutas y puntos de entrada HTTP",
    "config/middleware.py": "Cadena transversal del ciclo de request",
    "config/wsgi.py": "Punto de entrada WSGI",
    "config/asgi.py": "Punto de entrada ASGI",
    "apps": "Dominios Django del backend",
    "shared": "Código transversal reutilizable",
    "shared/models.py": "BaseModel y metadatos comunes",
    "shared/permissions.py": "Permisos base y reutilizables",
    "shared/exceptions.py": "Excepciones tipadas del sistema",
    "shared/mixins.py": "Mixins transversales para vistas",
    "shared/pagination.py": "Paginación reutilizable",
    "shared/openapi.py": "Tags OpenAPI y contratos compartidos",
    "shared/email_service.py": "Servicio de email desacoplado (porta-adaptador SMTP)",
    "shared/utils": "Utilidades transversales",
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
    "docs/architecture": "Síntesis arquitectónica: drivers, Utility Tree y ADRs",
    "docs/architecture/architecture_drivers.md": "Drivers arquitectónicos priorizados",
    "docs/architecture/utility_tree.md": "Utility Tree con escenarios y trade-offs",
    "docs/architecture/architectural_constraints.md": "Restricciones arquitectónicas y riesgos",
    "docs/architecture/adr_relationships.md": "Trazabilidad entre drivers y ADRs",
    "docs/guias": "Guías operativas del proyecto",
    "docs/guias/ENV_GUIDE.md": "Guía completa de variables de entorno",
    "docs/guias/SEED_DB.md": "Guía de carga de datos semilla",
    "docs/CI": "Runbook operativo de CI/CD",
    "docs/CI/README_CICD.md": "Runbook CI/CD: pipelines, despliegue, backups y rollback",
    "docs/api/README_API.md": "Especificación de la API: endpoints, contratos y estándares",
    "docs/api/README_MATRIZ_PERMISOS.md": "Matriz de permisos por rol para todos los endpoints",
    "docs/api/REFERENCIA_ENDPOINTS.md": "Referencia completa de endpoints con ejemplos request/response",
    "scripts": "Automatizaciones reutilizables del repositorio",
    "scripts/README_SCRIPTS.md": "Índice y contexto de las automatizaciones",
    "scripts/project_structure": "Generador semántico de la estructura arquitectónica",
    "scripts/project_structure/generate_project_structure.py": "Generador semántico de la estructura arquitectónica",
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

APP_OVERVIEW_COMMENT = {
    "authentication": "Autenticación JWT, RBAC, gestión de usuarios y recuperación de contraseña",
    "catalog": "Catálogo, SKUs definidos por usuario y validación de productos",
    "inventory": "Consulta de stock en tiempo real",
    "movements": "Ledger inmutable y consistencia de inventario",
    "reports": "Reportes e indicadores operativos",
    "alerts": "Alertas operativas y monitoreo preventivo",
    "audit": "Trazabilidad e histórico de eventos",
}

APP_FILE_COMMENTS = {
    "models.py": "Entidades y constraints de persistencia",
    "serializers.py": "Validación y adaptación del contrato de entrada/salida",
    "views.py": "Capa HTTP del módulo; delega la lógica a services.py",
    "urls.py": "Rutas del módulo y composición de endpoints",
    "services.py": "Reglas de negocio y transacciones del dominio",
    "selectors.py": "Consultas de lectura sin efectos secundarios",
    "permissions.py": "Política de acceso y restricciones de rol",
    "exceptions.py": "Excepciones de dominio y validación",
    "signals.py": "Eventos de sincronización entre módulos",
    "tasks.py": "Tareas asíncronas o diferidas del módulo",
    "middleware.py": "Interceptores transversales del ciclo de request",
    "admin.py": "Registro administrativo y soporte operacional",
}

APP_ROLE_EXTRA = {
    "authentication": {
        "models.py": "User (UUID, role, RBAC), UserSchedule, TemporaryAccessPermit, PasswordResetToken",
        "serializers.py": "UserSerializer (created_by_username, is_active read-only), password serializers",
        "views.py": "17 endpoints: JWT, CRUD usuarios, horarios, permisos temporales, change/forgot/reset-password",
        "services.py": "Autenticación JWT, RBAC, gestión de usuarios, change_own_password, forgot/reset-password",
        "selectors.py": "get_all_users (filtros role/search/inactive), check_user_access, get_user_by_id",
        "signals.py": "Sincronización de eventos de identidad",
        "test_password.py": "Flujo completo de cambio y recuperación de contraseña",
        "test_services.py": "Política de acceso y restricciones de rol",
        "test_permissions_api.py": "Cobertura de permisos por rol y endpoint",
        "test_permissions_reorganization.py": "Cobertura de reorganización de permisos",
        "test_user_enable.py": "Ciclo de vida: deshabilitar y rehabilitar usuarios",
    },
    "catalog": {
        "services.py": "Catálogo, SKU definido por usuario y validación de producto",
    },
    "inventory": {
        "selectors.py": "Lecturas de stock por ubicación",
    },
    "movements": {
        "services.py": "Ledger inmutable, atomicidad y actualización del stock derivado",
        "selectors.py": "Lecturas del ledger y del stock derivado",
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

ROLE_PATTERNS = [
    ("command", re.compile(r"\bBaseCommand\b|class\s+Command\b|add_arguments\(")),
    ("task", re.compile(r"@shared_task\b|\bcelery\b|\bCelery\b")),
    ("router", re.compile(r"\burlpatterns\b|\bpath\(|\bre_path\(|\binclude\(")),
    ("serializer", re.compile(r"\b(ModelSerializer|Serializer)\b")),
    (
        "view",
        re.compile(
            r"\b(APIView|ViewSet|GenericViewSet)\b|@extend_schema\b|\bResponse\("
        ),
    ),
    ("model", re.compile(r"\bmodels\.Model\b|\bAbstractUser\b|\bForeignKey\(")),
    (
        "permission",
        re.compile(r"\bBasePermission\b|\bhas_permission\b|\bhas_object_permission\b"),
    ),
    (
        "middleware",
        re.compile(r"\bMiddlewareMixin\b|\bprocess_request\b|\bprocess_response\b"),
    ),
    ("selector", re.compile(r"\bselect_related\b|\bprefetch_related\b|\bannotate\(")),
    (
        "service",
        re.compile(
            r"\btransaction\.atomic\b|\bselect_for_update\b|\bMovement\b|\bStockByLocation\b|\bledger\b",
            re.IGNORECASE,
        ),
    ),
]

TREE_LINE_RE = re.compile(
    r"^(?P<prefix>(?:│   |    )*)(?P<branch>├── |└── )(?P<label>.+?)(?:\s+#.*)?$"
)


@dataclass
class TreeConfig:
    root_label: str
    excluded_dirs: set[str] = field(default_factory=set)
    excluded_suffixes: set[str] = field(default_factory=set)
    excluded_names: set[str] = field(default_factory=set)
    forced_includes: set[str] = field(default_factory=set)
    max_depth: int = 5
    manual_comments: dict[str, str] = field(default_factory=dict)
    doc_paths: tuple[Path, ...] = ()


@dataclass(frozen=True)
class AnalysisContext:
    root_label: str
    existing_comments: dict[str, str]
    existing_paths: tuple[str, ...]


@dataclass
class TreeNode:
    path: Path
    rel: str
    is_dir: bool
    kind: str
    comment: str | None
    children: list["TreeNode"] = field(default_factory=list)

    @property
    def label(self) -> str:
        return f"{self.path.name}/" if self.is_dir else self.path.name


@dataclass(frozen=True)
class TreeModel:
    root_label: str
    children: tuple[TreeNode, ...]


@dataclass(frozen=True)
class TreeSnapshot:
    root_label: str
    paths: tuple[str, ...]


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
        root / "docs" / "architecture" / "architecture_drivers.md",
        root / "docs" / "architecture" / "utility_tree.md",
        root / "docs" / "architecture" / "architectural_constraints.md",
        root / "docs" / "architecture" / "adr_relationships.md",
    ]
    return tuple(path for path in candidates if path.exists())


def extract_text(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8")
    except OSError:
        return ""


def _normalize_config_list(values: object) -> set[str]:
    if not isinstance(values, list):
        return set()
    return {str(value) for value in values}


def _normalize_comment_map(values: object) -> dict[str, str]:
    if not isinstance(values, dict):
        return {}
    return {str(key): str(value) for key, value in values.items()}


def load_tree_config(
    root: Path, readme_path: Path, config_path: Path | None = None
) -> TreeConfig:
    external = load_json_config(config_path)
    excluded_dirs = set(DEFAULT_EXCLUDED_DIRS)
    excluded_dirs.update(_normalize_config_list(external.get("excluded_dirs")))
    excluded_suffixes = set(DEFAULT_EXCLUDED_SUFFIXES)
    excluded_suffixes.update(_normalize_config_list(external.get("excluded_suffixes")))
    excluded_names = set(DEFAULT_EXCLUDED_NAMES)
    excluded_names.update(_normalize_config_list(external.get("excluded_names")))
    forced_includes = _normalize_config_list(external.get("forced_includes"))
    manual_comments = _normalize_comment_map(
        external.get("manual_comments") or external.get("comments")
    )
    root_label = str(
        external.get("root_label") or readme_path.parent.parent.name or root.name
    )
    max_depth = int(external.get("max_depth", 5))
    return TreeConfig(
        root_label=root_label,
        excluded_dirs=excluded_dirs,
        excluded_suffixes=excluded_suffixes,
        excluded_names=excluded_names,
        forced_includes=forced_includes,
        max_depth=max_depth,
        manual_comments=manual_comments,
        doc_paths=discover_reference_docs(root),
    )


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
        label = re.sub(r"^[\s│├└─]+", "", head).strip().rstrip("/")
        if not label:
            continue
        comments.setdefault(label.lower(), tail.strip())
    return comments


def parse_rendered_tree_snapshot(tree_block: str) -> TreeSnapshot:
    lines = [line.rstrip() for line in tree_block.splitlines() if line.strip()]
    if not lines:
        return TreeSnapshot(root_label="", paths=())
    root_label = lines[0].rstrip("/").strip()
    stack: list[str] = []
    paths: list[str] = []
    for line in lines[1:]:
        match = TREE_LINE_RE.match(line)
        if not match:
            continue
        prefix = match.group("prefix")
        depth = len(prefix) // 4
        label = match.group("label").strip()
        is_dir = label.endswith("/")
        label = label.rstrip("/")
        stack = stack[:depth]
        stack.append(label)
        rel = "/".join(stack)
        if is_dir:
            rel = f"{rel}/"
        paths.append(rel)
    return TreeSnapshot(root_label=root_label, paths=tuple(paths))


def load_existing_architecture_context(
    root: Path, readme_path: Path, doc_paths: tuple[Path, ...]
) -> AnalysisContext:
    texts = [extract_text(readme_path)]
    texts.extend(extract_text(path) for path in doc_paths)
    tree_block = extract_existing_tree_block(texts[0])
    existing_comments = parse_existing_comments(tree_block)
    snapshot = parse_rendered_tree_snapshot(tree_block)
    root_label = root.name
    if tree_block:
        first_line = tree_block.splitlines()[0].strip()
        if first_line.endswith("/"):
            root_label = first_line.rstrip("/")
    return AnalysisContext(
        root_label=root_label,
        existing_comments=existing_comments,
        existing_paths=snapshot.paths,
    )


def rel_key(path: Path, root: Path) -> str:
    return path.relative_to(root).as_posix()


def forced_include(path: Path, root: Path, config: TreeConfig) -> bool:
    rel = rel_key(path, root)
    if rel in config.forced_includes:
        return True
    return any(
        rel == forced or rel.startswith(f"{forced.rstrip('/')}/")
        for forced in config.forced_includes
    )


def is_excluded(path: Path, root: Path, config: TreeConfig) -> bool:
    if forced_include(path, root, config):
        return False
    if path.name in config.excluded_names:
        return True
    if path.suffix in config.excluded_suffixes:
        return True
    return any(part in config.excluded_dirs for part in path.parts)


def classify_python_role(path: Path, text: str) -> str | None:
    lowered = text.lower()
    for role, pattern in ROLE_PATTERNS:
        if pattern.search(text):
            return role
    if path.name == "services.py":
        return "service"
    if path.name == "selectors.py":
        return "selector"
    if path.name == "views.py":
        return "view"
    if path.name == "urls.py":
        return "router"
    if path.name == "models.py":
        return "model"
    if path.name == "serializers.py":
        return "serializer"
    if path.name == "permissions.py":
        return "permission"
    if path.name == "signals.py":
        return "signal"
    if path.name == "tasks.py":
        return "task"
    if path.name == "middleware.py":
        return "middleware"
    if path.name == "admin.py":
        return "admin"
    if path.name == "conftest.py" or path.name.startswith("test_"):
        return "test"
    if "pytest" in lowered or "unittest" in lowered:
        return "test"
    return None


def classify_path(
    path: Path, root: Path, text: str = ""
) -> tuple[str | None, str | None]:
    rel = rel_key(path, root)
    if rel == DERIVED_REPORT_REL:
        return None, None
    if path.is_dir():
        if rel == "apps":
            return "apps-root", IMPORTANT_COMMENT_PATHS["apps"]
        if rel.startswith("apps/") and len(path.relative_to(root).parts) == 2:
            app_name = path.name
            return "app", APP_OVERVIEW_COMMENT.get(
                app_name, "Aplicación Django detectada automáticamente"
            )
        if rel == "config":
            return "config-root", IMPORTANT_COMMENT_PATHS["config"]
        if rel == "config/settings":
            return "settings-root", IMPORTANT_COMMENT_PATHS["config/settings"]
        if rel == "shared":
            return "shared-root", IMPORTANT_COMMENT_PATHS["shared"]
        if rel == "docs":
            return "docs-root", IMPORTANT_COMMENT_PATHS["docs"]
        if rel.startswith("docs/") and len(path.relative_to(root).parts) == 2:
            return "docs-section", IMPORTANT_COMMENT_PATHS.get(
                rel, "Documento arquitectónico relevante"
            )
        if rel == "scripts":
            return "scripts-root", IMPORTANT_COMMENT_PATHS["scripts"]
        if rel == "requirements":
            return "requirements-root", IMPORTANT_COMMENT_PATHS["requirements"]
        if rel == "docker":
            return "docker-root", IMPORTANT_COMMENT_PATHS["docker"]
        if rel == "tests":
            return "tests-root", IMPORTANT_COMMENT_PATHS["tests"]
        if rel.startswith("apps/") and rel.endswith("/tests"):
            return "tests-dir", "Pruebas del subdominio"
        if rel.startswith("apps/") and "/management/commands" in rel:
            return "commands-dir", "Comandos administrativos del módulo"
        return "directory", None

    if rel.startswith("docs/"):
        return "doc", IMPORTANT_COMMENT_PATHS.get(rel, "Documento técnico relevante")
    if rel.startswith("requirements/"):
        return "dependency", "Dependencia del entorno"
    if rel.startswith("docker"):
        return "infra", IMPORTANT_COMMENT_PATHS.get(
            rel, "Infraestructura de despliegue"
        )
    if rel == "manage.py":
        return "entrypoint", IMPORTANT_COMMENT_PATHS["manage.py"]
    if rel == "pytest.ini":
        return "config-file", IMPORTANT_COMMENT_PATHS["pytest.ini"]
    if rel == "schema.yml":
        return "schema", IMPORTANT_COMMENT_PATHS["schema.yml"]
    if rel in {"docker-compose.yml", "docker-compose.prod.yml", "README.md"}:
        return "root-file", IMPORTANT_COMMENT_PATHS[rel]
    if rel.startswith("config/"):
        if path.name == "settings":
            return "settings-root", IMPORTANT_COMMENT_PATHS["config/settings"]
        if path.suffix == ".py":
            role = classify_python_role(path, text)
            if role:
                return role, None
        return "config", IMPORTANT_COMMENT_PATHS.get(rel, "Configuración del proyecto")
    if rel.startswith("shared/"):
        if path.suffix == ".py":
            role = classify_python_role(path, text)
            if role:
                return role, None
        return "shared", IMPORTANT_COMMENT_PATHS.get(rel, "Código compartido")
    if rel.startswith("tests/"):
        if path.suffix == ".py":
            role = classify_python_role(path, text)
            if role:
                return role, None
        if path.suffix in {".json", ".md"}:
            return "doc", "Artefacto de pruebas y trazabilidad"
        return "test", None
    if rel.startswith("scripts/"):
        if path.suffix == ".py":
            role = classify_python_role(path, text)
            if role:
                return role, None
        return "script", IMPORTANT_COMMENT_PATHS.get(
            rel, "Automatización del repositorio"
        )
    if rel.startswith("apps/"):
        if path.name == "__init__.py":
            return None, None
        if path.suffix == ".py":
            role = classify_python_role(path, text)
            if role:
                return role, None
        if path.suffix in {".md", ".json", ".yml", ".yaml", ".sh"}:
            return "doc", "Artefacto relevante del módulo"
        return None, None
    return None, None


def file_text_for_analysis(path: Path) -> str:
    if path.suffix not in {".py", ".md", ".json", ".yml", ".yaml", ".txt", ".sh"}:
        return ""
    return extract_text(path)


def should_include_file(path: Path, root: Path, config: TreeConfig) -> bool:
    if is_excluded(path, root, config):
        return False
    rel = rel_key(path, root)
    if rel == "scripts/project_structure/generate_project_structure.py":
        return False
    if rel == DERIVED_REPORT_REL:
        return False
    if path.name in ROOT_FILES:
        return True
    if rel.startswith("docs/"):
        if path.parent.name in DOCS_CHILDREN:
            return path.name in set(DOCS_CHILDREN[path.parent.name])
        # Excluir archivos MD auto-generados de la estructura de tests (UNIT-, INT-, RFxxx-Sxx)
        if rel.startswith("docs/test") and path.suffix == ".md":
            # patrones: UNIT-0001.md, INT-0001.md, RF001-S01.md, RNF001-S01.md, etc.
            if re.match(r"^(UNIT|INT)-\d{4}\.md$", path.name) or re.match(
                r"^(?:RNF|RF)\d{3}(-S\d{2})?\.md$", path.name
            ):
                return False
        return path.suffix in {".md", ".json", ".yml", ".yaml"} or path.name.startswith(
            "README"
        )
    if rel.startswith("requirements/"):
        return path.suffix == ".txt"
    if rel.startswith("docker"):
        return path.name in DOCKER_ORDER or path.name.endswith(".sh")
    if rel.startswith("config/"):
        if rel.startswith("config/settings/"):
            return path.name in set(SETTINGS_ORDER)
        return path.suffix == ".py" and path.name != "__init__.py"
    if rel.startswith("shared/"):
        if rel.startswith("shared/utils/"):
            return path.name == "validators.py"
        return path.suffix == ".py" and path.name != "__init__.py"
    if rel.startswith("tests/"):
        if path.parent.name == "tests":
            return path.name in {"conftest.py", "factories.py"}
        if path.suffix == ".py":
            if "/ers/" in rel:
                return path.name == "test_gherkin_dynamic.py"
            if "/integration/" in rel:
                return path.name.startswith("test_") or path.name == "conftest.py"
            return path.name.startswith("test_") or path.name in {
                "conftest.py",
                "factories.py",
            }
        return False
    if rel.startswith("scripts/"):
        return path.suffix == ".py" or path.name == "README_SCRIPTS.md"
    if rel.startswith("apps/"):
        if path.name in {
            "models.py",
            "serializers.py",
            "views.py",
            "urls.py",
            "services.py",
            "selectors.py",
            "permissions.py",
            "exceptions.py",
            "signals.py",
            "tasks.py",
            "middleware.py",
            "admin.py",
        }:
            return True
        if path.parent.name == "tests" and path.suffix == ".py":
            return path.name.startswith("test_") or path.name in {
                "conftest.py",
                "factories.py",
            }
        if (
            "/management/commands/" in rel
            and path.suffix == ".py"
            and path.name != "__init__.py"
        ):
            return True
        role = classify_python_role(path, file_text_for_analysis(path))
        return role is not None
    return False


def child_sort_key(parent_rel: str, child: Path) -> tuple[int, int, str]:
    name = child.name.lower()
    if parent_rel == "":
        order = ROOT_DIR_ORDER + [file_name for file_name in sorted(ROOT_FILES)]
    elif parent_rel == "config":
        order = CONFIG_ORDER
    elif parent_rel == "config/settings":
        order = SETTINGS_ORDER
    elif parent_rel == "shared":
        order = SHARED_ORDER
    elif parent_rel == "docs":
        order = DOCS_ORDER
    elif parent_rel.startswith("docs/") and parent_rel.count("/") == 1:
        order = DOCS_CHILDREN.get(child.name, [])
    elif parent_rel == "scripts":
        order = SCRIPTS_ORDER
    elif parent_rel == "requirements":
        order = REQUIREMENTS_ORDER
    elif parent_rel == "docker":
        order = DOCKER_ORDER
    elif parent_rel == "tests":
        order = TESTS_ORDER
    elif parent_rel == "apps":
        order = APP_ORDER
    elif parent_rel.startswith("apps/"):
        order = APP_FILE_ORDER
    else:
        order = []
    try:
        return (0 if child.is_dir() else 1, order.index(child.name), name)
    except ValueError:
        return (0 if child.is_dir() else 1, len(order), name)


def visible_children(dir_path: Path, root: Path, config: TreeConfig) -> list[Path]:
    rel = rel_key(dir_path, root)
    if rel == "docs":
        result: list[Path] = []
        for name in DOCS_ORDER:
            candidate = dir_path / name
            if candidate.exists() and not is_excluded(candidate, root, config):
                result.append(candidate)
        for candidate in sorted(
            dir_path.iterdir(), key=lambda item: child_sort_key(rel, item)
        ):
            if candidate in result or is_excluded(candidate, root, config):
                continue
            if candidate.is_dir() or candidate.suffix in {
                ".md",
                ".json",
                ".yml",
                ".yaml",
            }:
                result.append(candidate)
        return result
    if rel == "scripts":
        result = []
        for name in SCRIPTS_ORDER:
            candidate = dir_path / name
            if candidate.exists() and not is_excluded(candidate, root, config):
                result.append(candidate)
        for candidate in sorted(
            dir_path.iterdir(), key=lambda item: child_sort_key(rel, item)
        ):
            if candidate in result or is_excluded(candidate, root, config):
                continue
            if candidate.is_dir() or candidate.suffix == ".py":
                result.append(candidate)
        return result
    if rel == "requirements":
        return [
            candidate
            for candidate in (dir_path / name for name in REQUIREMENTS_ORDER)
            if candidate.exists() and not is_excluded(candidate, root, config)
        ]
    if rel == "docker":
        return [
            candidate
            for candidate in (dir_path / name for name in DOCKER_ORDER)
            if candidate.exists() and not is_excluded(candidate, root, config)
        ]
    if rel == "config":
        return [
            candidate
            for candidate in (dir_path / name for name in CONFIG_ORDER)
            if candidate.exists() and not is_excluded(candidate, root, config)
        ]
    if rel == "config/settings":
        return [
            candidate
            for candidate in (dir_path / name for name in SETTINGS_ORDER)
            if candidate.exists() and not is_excluded(candidate, root, config)
        ]
    if rel == "shared":
        result = []
        for name in SHARED_ORDER:
            candidate = dir_path / name
            if candidate.exists() and not is_excluded(candidate, root, config):
                result.append(candidate)
        for candidate in sorted(
            dir_path.iterdir(), key=lambda item: child_sort_key(rel, item)
        ):
            if candidate in result or is_excluded(candidate, root, config):
                continue
            if candidate.is_dir() or candidate.suffix == ".py":
                result.append(candidate)
        return result
    if rel == "shared/utils":
        candidate = dir_path / "validators.py"
        return (
            [candidate]
            if candidate.exists() and not is_excluded(candidate, root, config)
            else []
        )
    if rel == "tests":
        result = []
        for name in TESTS_ORDER:
            candidate = dir_path / name
            if candidate.exists() and not is_excluded(candidate, root, config):
                result.append(candidate)
        for candidate in sorted(
            dir_path.iterdir(), key=lambda item: child_sort_key(rel, item)
        ):
            if candidate in result or is_excluded(candidate, root, config):
                continue
            if (
                candidate.is_dir()
                or candidate.name in {"conftest.py", "factories.py"}
                or candidate.name.startswith("test_")
            ):
                result.append(candidate)
        return result
    if rel == "apps":
        result = []
        for name in APP_ORDER:
            candidate = dir_path / name
            if (
                candidate.exists()
                and candidate.is_dir()
                and not is_excluded(candidate, root, config)
            ):
                result.append(candidate)
        for candidate in sorted(
            dir_path.iterdir(), key=lambda item: child_sort_key(rel, item)
        ):
            if candidate in result or is_excluded(candidate, root, config):
                continue
            if candidate.is_dir():
                result.append(candidate)
        return result
    if rel.startswith("docs/") and dir_path.parent == root / "docs":
        key = dir_path.name
        if key in DOCS_CHILDREN:
            result = []
            for name in DOCS_CHILDREN[key]:
                candidate = dir_path / name
                if candidate.exists() and not is_excluded(candidate, root, config):
                    result.append(candidate)
            # fallback: include any remaining .md files not in the explicit list
            listed = {c.name for c in result}
            for candidate in sorted(dir_path.iterdir()):
                if candidate.name in listed or is_excluded(candidate, root, config):
                    continue
                if candidate.suffix in {".md", ".json", ".yml", ".yaml"}:
                    result.append(candidate)
            return result
    if rel.startswith("apps/"):
        result = []
        for candidate in sorted(
            dir_path.iterdir(), key=lambda item: child_sort_key(rel, item)
        ):
            if is_excluded(candidate, root, config):
                continue
            if candidate.is_dir():
                if candidate.name == "migrations":
                    continue
                result.append(candidate)
                continue
            if should_include_file(candidate, root, config):
                result.append(candidate)
        return result
    result = []
    for candidate in sorted(
        dir_path.iterdir(), key=lambda item: child_sort_key(rel, item)
    ):
        if is_excluded(candidate, root, config):
            continue
        if candidate.is_dir():
            result.append(candidate)
        elif should_include_file(candidate, root, config):
            result.append(candidate)
    return result


def _generic_dir_comment(rel: str) -> str | None:
    if rel.startswith("apps/") and rel.count("/") == 1:
        return APP_OVERVIEW_COMMENT.get(rel.split("/")[-1])
    if rel.startswith("apps/") and rel.endswith("/tests"):
        return "Pruebas del subdominio"
    if "/management/commands" in rel:
        return "Comandos administrativos del módulo"
    if rel == "docs/architecture":
        return IMPORTANT_COMMENT_PATHS["docs/architecture"]
    return None


def semantic_comment_for_file(path: Path, root: Path, text: str) -> str | None:
    rel = rel_key(path, root)
    app_name = (
        path.relative_to(root).parts[1]
        if rel.startswith("apps/") and len(path.relative_to(root).parts) >= 2
        else ""
    )
    if rel in IMPORTANT_COMMENT_PATHS:
        return IMPORTANT_COMMENT_PATHS[rel]
    if rel.startswith("apps/"):
        if app_name and rel.count("/") == 1:
            return APP_OVERVIEW_COMMENT.get(app_name)
        if app_name in APP_ROLE_EXTRA and path.name in APP_ROLE_EXTRA[app_name]:
            return APP_ROLE_EXTRA[app_name][path.name]
        if path.name in APP_FILE_COMMENTS:
            if path.name == "services.py" and text:
                lowered = text.lower()
                if "transaction.atomic" in lowered or "select_for_update" in lowered:
                    if "stockbylocation" in lowered or "movement" in lowered:
                        return "Reglas de negocio del ledger y actualización transaccional del stock"
                    return "Reglas de negocio y transacciones del dominio"
            if (
                path.name == "selectors.py"
                and text
                and any(
                    token in text.lower()
                    for token in ("select_related", "prefetch_related", "annotate")
                )
            ):
                return "Consultas de lectura y agregaciones del módulo"
            if (
                path.name == "views.py"
                and text
                and ("extend_schema" in text or "APIView" in text or "ViewSet" in text)
            ):
                return "Endpoints HTTP del módulo y orquestación de requests"
            if path.name == "urls.py":
                return "Ruteo HTTP y composición de endpoints"
            return APP_FILE_COMMENTS[path.name]
        if "/management/commands/" in rel:
            return "Comando Django para automatización operativa"
        role = classify_python_role(path, text)
        if role == "command":
            return "Comando Django para automatización operativa"
        if role == "task":
            return "Tarea asíncrona o diferida del módulo"
        if role == "router":
            return "Ruteo HTTP y composición de endpoints"
        if role == "middleware":
            return "Interceptores transversales del ciclo de request"
        if role == "permission":
            return "Política de acceso y restricciones de rol"
        if role == "model":
            return "Entidades y constraints de persistencia"
        if role == "serializer":
            return "Validación y adaptación del contrato de entrada/salida"
        if role == "view":
            return "Capa HTTP del módulo; delega la lógica a services.py"
        if role == "selector":
            return "Consultas de lectura sin efectos secundarios"
        if role == "service":
            return "Reglas de negocio y transacciones del dominio"
        if role == "test":
            return "Cobertura crítica del módulo"
    if rel.startswith("config/"):
        if path.name == "urls.py":
            return "Composición de rutas y puntos de entrada HTTP"
        if path.name == "middleware.py":
            return "Cadena transversal del ciclo de request"
        if path.name in {"base.py", "development.py", "production.py", "test.py"}:
            return IMPORTANT_COMMENT_PATHS.get(f"config/settings/{path.name}")
    if rel.startswith("shared/"):
        if path.name in APP_FILE_COMMENTS:
            return APP_FILE_COMMENTS[path.name]
    if rel.startswith("docs/"):
        return IMPORTANT_COMMENT_PATHS.get(rel) or "Documento técnico relevante"
    if rel.startswith("scripts/"):
        if path.name == "generate_docs":
            return "Generadores compartidos de documentación"
        if path.name == "README_SCRIPTS.md":
            return "Índice y contexto de automatizaciones"
        if path.name == "generate_project_structure.py":
            return "Generador semántico de la estructura arquitectónica"
    if rel.startswith("tests/"):
        if "/ers/" in rel:
            return "Escenarios Gherkin y trazabilidad al ERS"
        if "/integration/" in rel:
            return "Pruebas de integración HTTP/API"
        if path.name == "conftest.py":
            return "Fixtures globales de la suite"
        if path.name == "factories.py":
            return "Factories reutilizables para pruebas"
        if path.name.startswith("test_"):
            return "Cobertura crítica del módulo"
    if path.name == "Dockerfile":
        return "Imagen base del contenedor de despliegue"
    if path.name == "entrypoint.sh":
        return "Inicialización del contenedor y arranque"
    return None


def semantic_comment_for_dir(path: Path, root: Path) -> str | None:
    rel = rel_key(path, root)
    if rel in IMPORTANT_COMMENT_PATHS:
        return IMPORTANT_COMMENT_PATHS[rel]
    if rel.startswith("apps/") and len(path.relative_to(root).parts) == 2:
        return APP_OVERVIEW_COMMENT.get(
            path.name, "Aplicación Django detectada automáticamente"
        )
    if rel.startswith("apps/") and rel.endswith("/tests"):
        return "Pruebas del subdominio"
    if "/management/commands" in rel:
        return "Comandos administrativos del módulo"
    if rel.startswith("docs/") and len(path.relative_to(root).parts) == 2:
        return IMPORTANT_COMMENT_PATHS.get(rel, "Documento arquitectónico relevante")
    return _generic_dir_comment(rel)


def resolve_comment_for_path(
    path: Path, root: Path, context: AnalysisContext, config: TreeConfig, text: str = ""
) -> str | None:
    rel = rel_key(path, root)
    if rel in config.manual_comments:
        return config.manual_comments[rel]
    if path.name.lower() in config.manual_comments:
        return config.manual_comments[path.name.lower()]
    if path.is_dir():
        return semantic_comment_for_dir(path, root) or context.existing_comments.get(
            path.name.lower()
        )
    semantic = semantic_comment_for_file(path, root, text)
    if semantic:
        return semantic
    if rel in context.existing_comments:
        return context.existing_comments[rel]
    if path.name.lower() in context.existing_comments:
        return context.existing_comments[path.name.lower()]
    return None


def build_tree_node(
    path: Path, root: Path, config: TreeConfig, context: AnalysisContext, depth: int = 0
) -> TreeNode | None:
    if is_excluded(path, root, config):
        return None
    rel = rel_key(path, root)
    text = file_text_for_analysis(path) if path.is_file() else ""
    kind, _ = classify_path(path, root, text)
    if path.is_file():
        if not should_include_file(path, root, config):
            return None
        comment = resolve_comment_for_path(path, root, context, config, text)
        return TreeNode(
            path=path,
            rel=rel,
            is_dir=False,
            kind=kind or "file",
            comment=comment,
            children=[],
        )

    if depth > config.max_depth and not rel.startswith(
        (
            "apps",
            "config",
            "shared",
            "tests",
            "docs",
            "scripts",
            "requirements",
            "docker",
        )
    ):
        return None
    children: list[TreeNode] = []
    for candidate in visible_children(path, root, config):
        node = build_tree_node(candidate, root, config, context, depth + 1)
        if node is not None:
            children.append(node)
    if not children and path != root:
        if rel in {
            "apps",
            "config",
            "shared",
            "tests",
            "docs",
            "scripts",
            "requirements",
            "docker",
        }:
            comment = resolve_comment_for_path(path, root, context, config)
            return TreeNode(
                path=path,
                rel=rel,
                is_dir=True,
                kind=kind or "directory",
                comment=comment,
                children=[],
            )
        return None
    comment = resolve_comment_for_path(path, root, context, config)
    return TreeNode(
        path=path,
        rel=rel,
        is_dir=True,
        kind=kind or "directory",
        comment=comment,
        children=children,
    )


def build_tree_model(
    root: Path, context: AnalysisContext, config: TreeConfig
) -> TreeModel:
    children: list[TreeNode] = []
    for candidate in visible_children(root, root, config):
        node = build_tree_node(candidate, root, config, context, 0)
        if node is not None:
            children.append(node)
    return TreeModel(root_label=context.root_label, children=tuple(children))


def render_entry(node: TreeNode, prefix: str, is_last: bool) -> list[str]:
    branch = "└── " if is_last else "├── "
    label = node.label
    text = f"{prefix}{branch}{label}"
    if node.comment:
        text = f"{text:<62}  # {node.comment}"
    lines = [text.rstrip()]
    if node.is_dir:
        next_prefix = prefix + ("    " if is_last else "│   ")
        for index, child in enumerate(node.children):
            lines.extend(
                render_entry(child, next_prefix, index == len(node.children) - 1)
            )
    return lines


def build_tree_text(model: TreeModel) -> str:
    lines = [f"{model.root_label}/"]
    for index, child in enumerate(model.children):
        lines.extend(render_entry(child, "", index == len(model.children) - 1))
    return "\n".join(lines)


def flatten_nodes(nodes: Sequence[TreeNode]) -> list[TreeNode]:
    flat: list[TreeNode] = []

    def walk(node: TreeNode) -> None:
        flat.append(node)
        for child in node.children:
            walk(child)

    for node in nodes:
        walk(node)
    return flat


def snapshot_from_model(model: TreeModel) -> TreeSnapshot:
    paths: list[str] = []
    for node in flatten_nodes(model.children):
        paths.append(f"{node.rel}/" if node.is_dir else node.rel)
    return TreeSnapshot(root_label=model.root_label, paths=tuple(paths))


def summarize_paths(paths: Sequence[str], limit: int = 12) -> list[str]:
    items = sorted(paths)
    if len(items) <= limit:
        return items
    return [*items[:limit], f"... ({len(items) - limit} más)"]


def is_report_relevant(path: str) -> bool:
    if path.startswith("docs/test/"):
        return path in {
            "docs/test/",
            "docs/test/README_TEST.md",
            "docs/test/TRAZABILIDAD_ERS_GHERKIN.md",
        }
    if path.startswith("tests/"):
        return path in {
            "tests/ers/",
            "tests/integration/",
            "tests/conftest.py",
            "tests/factories.py",
        }
    if path.startswith("apps/"):
        if path.endswith("/"):
            return path.count("/") == 2
        if "/tests/" in path:
            return path.endswith("tests/")
        return Path(path.rstrip("/")).name in {
            "models.py",
            "serializers.py",
            "views.py",
            "urls.py",
            "services.py",
            "selectors.py",
            "permissions.py",
            "exceptions.py",
            "signals.py",
            "tasks.py",
            "middleware.py",
            "admin.py",
        }
    if path.startswith(
        (
            "docs/architecture/",
            "docs/api/",
            "docs/requisitos/",
            "docs/calidad_restricciones/",
        )
    ):
        return True
    if path.startswith(("config/", "shared/", "scripts/", "requirements/", "docker/")):
        return True
    return path in {
        "README.md",
        "manage.py",
        "pytest.ini",
        "schema.yml",
        "docker-compose.yml",
        "docker-compose.prod.yml",
    }


def detect_moves(
    added: set[str], removed: set[str]
) -> tuple[list[str], set[str], set[str]]:
    additions_by_name: dict[tuple[str, bool], list[str]] = defaultdict(list)
    removals_by_name: dict[tuple[str, bool], list[str]] = defaultdict(list)
    for path in added:
        is_dir = path.endswith("/")
        additions_by_name[(Path(path.rstrip("/")).name, is_dir)].append(path)
    for path in removed:
        is_dir = path.endswith("/")
        removals_by_name[(Path(path.rstrip("/")).name, is_dir)].append(path)
    moves: list[str] = []
    matched_added: set[str] = set()
    matched_removed: set[str] = set()
    for key in sorted(additions_by_name.keys() & removals_by_name.keys()):
        for new_path, old_path in zip(
            sorted(additions_by_name[key]), sorted(removals_by_name[key])
        ):
            if (
                Path(new_path.rstrip("/")).parent.as_posix()
                == Path(old_path.rstrip("/")).parent.as_posix()
            ):
                continue
            moves.append(f"{old_path} -> {new_path}")
            matched_added.add(new_path)
            matched_removed.add(old_path)
    return moves, matched_added, matched_removed


def build_change_report(model: TreeModel, previous: TreeSnapshot) -> str:
    current = snapshot_from_model(model)
    current_paths = set(current.paths)
    previous_paths = set(previous.paths)
    added = {
        path for path in current_paths - previous_paths if is_report_relevant(path)
    }
    removed = {
        path for path in previous_paths - current_paths if is_report_relevant(path)
    }
    moves, matched_added, matched_removed = detect_moves(set(added), set(removed))
    added -= matched_added
    removed -= matched_removed

    app_additions = [
        path
        for path in added
        if path.startswith("apps/") and path.count("/") == 2 and path.endswith("/")
    ]
    module_additions = [
        path
        for path in added
        if path.startswith("apps/")
        and not path.endswith("/")
        and any(
            path.endswith(suffix)
            for suffix in (
                "services.py",
                "selectors.py",
                "views.py",
                "urls.py",
                "models.py",
                "serializers.py",
                "permissions.py",
                "tasks.py",
                "middleware.py",
                "signals.py",
                "exceptions.py",
            )
        )
    ]
    docs_additions = [path for path in added if path.startswith("docs/")]

    lines = [
        "# Reporte de cambios arquitectónicos",
        "",
        f"Fuente: {DEFAULT_README.relative_to(ROOT).as_posix()}",
        f"Base previa: {previous.root_label or '(sin bloque previo)'}",
        f"Actual: {model.root_label}",
        "",
        "## Resumen",
        f"- Nuevos nodos relevantes: {len(added)}",
        f"- Eliminados: {len(removed)}",
        f"- Reorganizaciones: {len(moves)}",
    ]
    if app_additions:
        lines.append(f"- Apps nuevas: {len(app_additions)}")
    if module_additions:
        lines.append(f"- Módulos relevantes nuevos: {len(module_additions)}")
    if docs_additions:
        lines.append(f"- Docs relevantes nuevas: {len(docs_additions)}")
    lines.append("")

    if app_additions:
        lines.extend(
            [
                "## Apps nuevas",
                *[f"- {item}" for item in summarize_paths(app_additions)],
                "",
            ]
        )
    if module_additions:
        lines.extend(
            [
                "## Módulos nuevos",
                *[f"- {item}" for item in summarize_paths(module_additions)],
                "",
            ]
        )
    if moves:
        lines.extend(
            [
                "## Reorganizaciones",
                *[f"- {item}" for item in summarize_paths(moves)],
                "",
            ]
        )
    if added:
        lines.extend(
            [
                "## Altas relevantes",
                *[f"- {item}" for item in summarize_paths(added)],
                "",
            ]
        )
    if removed:
        lines.extend(
            [
                "## Bajas relevantes",
                *[f"- {item}" for item in summarize_paths(removed)],
                "",
            ]
        )
    if not added and not removed and not moves:
        lines.extend(
            [
                "## Estado",
                "- Sin cambios estructurales relevantes detectados respecto al README actual.",
                "",
            ]
        )
    return "\n".join(lines).rstrip() + "\n"


def replace_architecture_section(readme_text: str, tree_text: str) -> str:
    anchor_index = readme_text.find(SECTION_ANCHOR)
    if anchor_index < 0:
        raise RuntimeError(
            "No se encontró la sección arquitectónica objetivo en el README"
        )
    block_start = readme_text.find("```", anchor_index)
    if block_start < 0:
        raise RuntimeError(
            "No se encontró el bloque de árbol dentro de la sección arquitectónica"
        )
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
        raise FileNotFoundError(
            f"No existe el README de arquitectura: {readme_path}"
        ) from exc
    updated = replace_architecture_section(original, tree_text)
    readme_path.write_text(updated, encoding="utf-8")


def write_report(report_path: Path, content: str) -> None:
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text(content, encoding="utf-8")


def build_external_config(config: TreeConfig, external: dict) -> TreeConfig:
    excluded_dirs = set(config.excluded_dirs)
    excluded_dirs.update(_normalize_config_list(external.get("excluded_dirs")))
    excluded_suffixes = set(config.excluded_suffixes)
    excluded_suffixes.update(_normalize_config_list(external.get("excluded_suffixes")))
    excluded_names = set(config.excluded_names)
    excluded_names.update(_normalize_config_list(external.get("excluded_names")))
    forced_includes = set(config.forced_includes)
    forced_includes.update(_normalize_config_list(external.get("forced_includes")))
    manual_comments = dict(config.manual_comments)
    manual_comments.update(
        _normalize_comment_map(
            external.get("manual_comments") or external.get("comments")
        )
    )
    root_label = str(external.get("root_label", config.root_label))
    max_depth = int(external.get("max_depth", config.max_depth))
    return TreeConfig(
        root_label=root_label,
        excluded_dirs=excluded_dirs,
        excluded_suffixes=excluded_suffixes,
        excluded_names=excluded_names,
        forced_includes=forced_includes,
        max_depth=max_depth,
        manual_comments=manual_comments,
        doc_paths=config.doc_paths,
    )


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Genera la estructura del proyecto y sincroniza el README arquitectónico."
    )
    parser.add_argument(
        "--root", type=Path, default=ROOT, help="Raíz del proyecto a analizar"
    )
    parser.add_argument(
        "--readme",
        type=Path,
        default=DEFAULT_README,
        help="Archivo README de arquitectura a actualizar",
    )
    parser.add_argument(
        "--config", type=Path, default=None, help="Configuración externa JSON opcional"
    )
    parser.add_argument(
        "--report",
        type=Path,
        default=DEFAULT_REPORT,
        help="Reporte auxiliar de cambios arquitectónicos",
    )
    parser.add_argument(
        "--dry-run", action="store_true", help="Imprime el árbol sin modificar archivos"
    )
    args = parser.parse_args(argv)

    root = args.root.resolve()
    readme_path = args.readme.resolve()
    report_path = args.report.resolve()

    tree_config = load_tree_config(root, readme_path, args.config)
    external = load_json_config(args.config)
    if external:
        tree_config = build_external_config(tree_config, external)

    context = load_existing_architecture_context(
        root, readme_path, tree_config.doc_paths
    )
    model = build_tree_model(root, context, tree_config)
    tree_text = build_tree_text(model)

    previous_snapshot = parse_rendered_tree_snapshot(
        extract_existing_tree_block(extract_text(readme_path))
    )
    report_text = build_change_report(model, previous_snapshot)

    if args.dry_run:
        print(tree_text)
        return 0

    update_readme_section(readme_path, tree_text)
    write_report(report_path, report_text)
    print(f"Estructura arquitectónica actualizada en {readme_path}")
    print(f"Reporte de cambios arquitectónicos actualizado en {report_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
