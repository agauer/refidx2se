"""Tests for refidx2se.catalog."""

from __future__ import annotations

import pytest
import responses

from refidx2se.catalog import (
    CATALOG_URL,
    _load_catalog,
    print_material_options,
    return_material_option,
    search_material,
)

# ── Minimal fake catalog YAML ────────────────────────────────────────────────

FAKE_CATALOG_YAML = """
- SHELF: main
  content:
    - BOOK: SiO2
      content:
        - PAGE: Malitson
          name: "Malitson 1965"
        - PAGE: Gao
          name: "Gao 2013"
    - BOOK: polystyrene
      content:
        - PAGE: Sultanova
          name: "Sultanova 2009"
- SHELF: organic
  content:
    - BOOK: polystyrene
      content:
        - PAGE: Jones
          name: "Jones 2020"
"""


@pytest.fixture(autouse=True)
def mock_catalog():
    with responses.RequestsMock() as rsps:
        rsps.add(
            responses.GET,
            CATALOG_URL,
            body=FAKE_CATALOG_YAML,
            status=200,
        )
        _load_catalog.cache_clear()
        yield
        _load_catalog.cache_clear()


# ── search_material ──────────────────────────────────────────────────────────

def test_search_exact_match():
    results = search_material("SiO2")
    assert len(results) == 2
    assert results[0]["page"] == "Malitson"
    assert results[1]["page"] == "Gao"


def test_search_case_insensitive():
    results = search_material("sio2")
    assert len(results) == 2


def test_search_partial_match():
    results = search_material("poly")
    # matches 'polystyrene' in both shelves
    assert len(results) == 2


def test_search_no_match():
    results = search_material("unobtanium")
    assert results == []


def test_search_result_keys():
    results = search_material("SiO2")
    assert set(results[0].keys()) == {"shelf", "book", "page", "name"}


# ── return_material_option ───────────────────────────────────────────────────

def test_return_first_option():
    shelf, book, page = return_material_option("SiO2")
    assert shelf == "main"
    assert book == "SiO2"
    assert page == "Malitson"


def test_return_second_option():
    _, _, page = return_material_option("SiO2", idx=1)
    assert page == "Gao"


def test_return_option_no_results():
    with pytest.raises(ValueError, match="No results found"):
        return_material_option("unobtanium")


def test_return_option_out_of_range():
    with pytest.raises(ValueError, match="out of range"):
        return_material_option("SiO2", idx=99)


# ── print_material_options ───────────────────────────────────────────────────

def test_print_material_options_output(capsys):
    print_material_options("SiO2")
    captured = capsys.readouterr()
    assert "Malitson" in captured.out
    assert "Gao" in captured.out


def test_print_material_options_no_match(capsys):
    print_material_options("unobtanium")
    captured = capsys.readouterr()
    assert "No results found" in captured.out
