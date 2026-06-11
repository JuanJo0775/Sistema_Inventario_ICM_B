from __future__ import annotations

from pathlib import Path

from scripts.project_structure.generate_project_structure import (
    build_change_report,
    build_tree_model,
    build_tree_text,
    load_existing_architecture_context,
    load_tree_config,
    parse_rendered_tree_snapshot,
    semantic_comment_for_file,
)


def _write(path: Path, text: str = "") -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def _make_readme(root: Path, tree_text: str = "icm_backend/\n") -> Path:
    readme = root / "docs" / "README_ARQUITECTURA.md"
    _write(
        readme,
        "# Arquitectura\n\n## 3. Estructura del Proyecto\n\nEstructura de Directorios del Proyecto:\n\n```text\n"
        + tree_text
        + "```\n",
    )
    return readme


def test_semantic_comment_for_services_is_specific(tmp_path: Path) -> None:
    root = tmp_path
    readme = _make_readme(root)
    services = root / "apps" / "payments" / "services.py"
    _write(
        services,
        "from django.db import transaction\n"
        "from apps.movements.models import Movement, StockByLocation\n\n"
        "@transaction.atomic\n"
        "def register():\n"
        "    return Movement, StockByLocation\n",
    )
    config = load_tree_config(root, readme)
    context = load_existing_architecture_context(root, readme, config.doc_paths)
    comment = semantic_comment_for_file(
        services, root, services.read_text(encoding="utf-8")
    )
    assert (
        comment
        == "Reglas de negocio del ledger y actualización transaccional del stock"
    )
    model = build_tree_model(root, context, config)
    tree_text = build_tree_text(model)
    assert "payments/" in tree_text
    assert "services.py" in tree_text
    assert "migrations" not in tree_text


def test_tree_ignores_noise_and_keeps_relevant_nodes(tmp_path: Path) -> None:
    root = tmp_path
    readme = _make_readme(root)
    _write(root / "apps" / "payments" / "__pycache__" / "cache.pyc", "binary")
    _write(root / "apps" / "payments" / "migrations" / "0001_initial.py", "# migration")
    _write(root / "apps" / "payments" / "services.py", "def work():\n    pass\n")
    _write(root / "docs" / "architecture" / "architecture_drivers.md", "# Drivers\n")
    config = load_tree_config(root, readme)
    context = load_existing_architecture_context(root, readme, config.doc_paths)
    model = build_tree_model(root, context, config)
    tree_text = build_tree_text(model)
    assert "__pycache__" not in tree_text
    assert "migrations" not in tree_text
    assert "payments/" in tree_text
    assert "services.py" in tree_text
    assert "architecture_drivers.md" in tree_text


def test_change_report_detects_additions_and_removals(tmp_path: Path) -> None:
    root = tmp_path
    old_tree = "icm_backend/\n├── apps/\n└── README.md\n"
    readme = _make_readme(root, old_tree)
    _write(
        root / "apps" / "payments" / "services.py",
        "@transaction.atomic\ndef run():\n    pass\n",
    )
    _write(
        root / "apps" / "payments" / "tests" / "test_services.py",
        "def test_run():\n    assert True\n",
    )
    config = load_tree_config(root, readme)
    context = load_existing_architecture_context(root, readme, config.doc_paths)
    model = build_tree_model(root, context, config)
    report = build_change_report(model, parse_rendered_tree_snapshot(old_tree))
    assert "apps/payments/" in report
    assert "services.py" in report
    assert "README.md" in report or "Eliminados" in report
