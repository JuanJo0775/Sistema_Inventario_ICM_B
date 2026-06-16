"""Tests unitarios para scripts/generate_docs/utils.py.

Verifican las funciones de clasificación, construcción de nodos y utilidades
de escritura de archivos. No dependen de la base de datos ni del entorno Django.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from scripts.generate_docs.utils import GenerationSummary
from scripts.generate_docs.utils import TestNode as DocTestNode
from scripts.generate_docs.utils import (
    _remove_stale_markdown,
    _write_text_if_needed,
    classify_test,
)

# ── DocTestNode (TestNode del script de docs) ─────────────────────────────────


def test_docnode_short_name_simple():
    node = DocTestNode(
        "apps/foo/tests/test_views.py::test_list_ok",
        "apps/foo/tests/test_views.py",
        10,
        "unit",
    )
    assert node.short_name == "test_list_ok"


def test_docnode_short_name_class_method():
    node = DocTestNode(
        "tests/test_x.py::SomeClass::test_method", "tests/test_x.py", 5, "integration"
    )
    assert node.short_name == "test_method"


# ── classify_test ─────────────────────────────────────────────────────────────


@pytest.mark.parametrize(
    "rel_path,expected",
    [
        ("tests/ers/impl/movements.py", "gherkin"),
        ("tests/ers/test_gherkin_dynamic.py", "gherkin"),
        ("tests/integration/test_api_integration.py", "integration"),
        ("tests/concurrency/test_concurrent_movements.py", "integration"),
        ("apps/movements/tests/test_services.py", "unit"),
        ("apps/catalog/tests/test_views.py", "unit"),
        ("tests/scripts/test_seed_db.py", "auxiliary"),
        ("tests/shared/test_location_validators.py", "auxiliary"),
        ("tests/test_service_sla.py", "auxiliary"),
        ("tests/scripts/test_generate_docs.py", "auxiliary"),
    ],
)
def test_classify_test_coverage(rel_path: str, expected: str):
    assert classify_test(rel_path) == expected


# ── GenerationSummary ─────────────────────────────────────────────────────────


def test_generation_summary_absorb_merges_paths(tmp_path: Path):
    a = GenerationSummary(kind="unit")
    a.written.append(tmp_path / "a.md")
    b = GenerationSummary(kind="unit")
    b.written.append(tmp_path / "b.md")
    b.changed = True

    a.absorb(b)

    assert a.changed is True
    assert len(a.written) == 2


def test_generation_summary_absorb_does_not_unset_changed():
    a = GenerationSummary(kind="unit", changed=True)
    b = GenerationSummary(kind="unit", changed=False)
    a.absorb(b)
    assert a.changed is True


# ── _write_text_if_needed ─────────────────────────────────────────────────────


def test_write_creates_file(tmp_path: Path):
    target = tmp_path / "sub" / "output.md"
    changed = _write_text_if_needed(target, "hello")
    assert changed is True
    assert target.read_text() == "hello"


def test_write_skips_if_content_unchanged(tmp_path: Path):
    target = tmp_path / "output.md"
    target.write_text("same")
    changed = _write_text_if_needed(target, "same")
    assert changed is False


def test_write_updates_if_content_changed(tmp_path: Path):
    target = tmp_path / "output.md"
    target.write_text("old")
    changed = _write_text_if_needed(target, "new")
    assert changed is True
    assert target.read_text() == "new"


def test_write_check_mode_does_not_write(tmp_path: Path):
    target = tmp_path / "output.md"
    target.write_text("old")
    out_of_sync = _write_text_if_needed(target, "new", check=True)
    assert out_of_sync is True
    assert target.read_text() == "old"  # no se escribe en modo check


# ── _remove_stale_markdown ────────────────────────────────────────────────────


def test_remove_stale_deletes_unexpected_files(tmp_path: Path):
    (tmp_path / "keep.md").write_text("keep")
    (tmp_path / "stale.md").write_text("stale")

    removed = _remove_stale_markdown(tmp_path, expected_names={"keep.md"})

    assert len(removed) == 1
    assert removed[0].name == "stale.md"
    assert not (tmp_path / "stale.md").exists()
    assert (tmp_path / "keep.md").exists()


def test_remove_stale_check_mode_does_not_delete(tmp_path: Path):
    (tmp_path / "keep.md").write_text("keep")
    (tmp_path / "stale.md").write_text("stale")

    removed = _remove_stale_markdown(tmp_path, expected_names={"keep.md"}, check=True)

    assert len(removed) == 1
    assert (tmp_path / "stale.md").exists()  # no borrado en modo check


def test_remove_stale_nonexistent_dir_returns_empty():
    removed = _remove_stale_markdown(Path("/nonexistent/path"), expected_names={"x.md"})
    assert removed == []
