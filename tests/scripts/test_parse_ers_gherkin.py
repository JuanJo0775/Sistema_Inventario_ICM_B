"""Tests para scripts/docs/parse_ers_gherkin.py — wrapper que invoca generate_docs.utils.main(['--only', 'gherkin'])."""

from __future__ import annotations

from unittest.mock import patch

import scripts.generate_docs.utils
import scripts.docs.parse_ers_gherkin


def test_wrapper_is_alias_of_generate_docs_main():
    """Verifica que el main del wrapper sea el mismo objeto que generate_docs.utils.main."""
    assert scripts.docs.parse_ers_gherkin.main is scripts.generate_docs.utils.main


def test_wrapper_passthrough_return_values():
    """Verifica que el wrapper propague códigos de retorno."""
    for expected in (0, 1):
        with patch.object(scripts.docs.parse_ers_gherkin, "main", return_value=expected):
            result = scripts.docs.parse_ers_gherkin.main()
            assert result == expected
