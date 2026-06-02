"""
catalog.py — Download, cache, and search the refractiveindex.info catalog.
"""

from __future__ import annotations

from functools import lru_cache
from typing import Any

import requests
import yaml

CATALOG_URL = (
    "https://raw.githubusercontent.com/"
    "polyanskiy/refractiveindex.info-database/main/database/catalog-nk.yml"
)


@lru_cache(maxsize=1)
def _load_catalog() -> Any:
    """Download and parse catalog-nk.yml from GitHub (in-process cache)."""
    resp = requests.get(CATALOG_URL, timeout=15)
    resp.raise_for_status()
    return yaml.safe_load(resp.text)


def search_material(book: str) -> list[dict[str, Any]]:
    """
    Search for all shelf/page combinations matching a book name.

    Parameters
    ----------
    book:
        Case-insensitive search term, e.g. ``'polystyrene'``, ``'SiO2'``.

    Returns
    -------
    list of dicts with keys: ``shelf``, ``book``, ``page``, ``name``.
    """
    catalog = _load_catalog()
    results: list[dict[str, Any]] = []
    book_lower = book.lower()

    for shelf_entry in catalog:
        shelf_name = shelf_entry.get("SHELF", "")
        for item in shelf_entry.get("content", []):
            if "BOOK" not in item:
                continue
            book_name: str = item["BOOK"]
            if book_lower not in book_name.lower():
                continue
            for page_entry in item.get("content", []):
                if "PAGE" not in page_entry:
                    continue
                results.append(
                    {
                        "shelf": shelf_name,
                        "book": book_name,
                        "page": page_entry["PAGE"],
                        "name": page_entry.get("name", ""),
                    }
                )
    return results


def return_material_option(
    book: str, idx: int = 0
) -> tuple[str, str, str]:
    """
    Return a single ``(shelf, book, page)`` tuple for a search term and index.

    Parameters
    ----------
    book:
        Case-insensitive search term.
    idx:
        Index of the desired match (default ``0``).

    Raises
    ------
    ValueError
        If no matches are found or *idx* is out of range.
    """
    results = search_material(book)
    if not results:
        raise ValueError(f"No results found for '{book}'")
    if idx < 0 or idx >= len(results):
        raise ValueError(
            f"Index {idx} out of range for {len(results)} result(s)"
        )
    r = results[idx]
    return r["shelf"], r["book"], r["page"]


def print_material_options(book: str) -> None:
    """Pretty-print all shelf/page options for a given book search term."""
    results = search_material(book)
    if not results:
        print(f"No results found for '{book}'")
        return

    print(f"\n{len(results)} entries matching '{book}':\n")
    print(
        f"  {'option':<8} {'shelf':<12} {'book':<25} {'page':<35} description"
    )
    print(
        f"  {'-'*8} {'-'*12} {'-'*25} {'-'*35} {'-'*45}"
    )
    for n, r in enumerate(results):
        print(
            f"  {n:<8} {r['shelf']:<12} {r['book']:<25}"
            f" {r['page']:<35} {r['name']}"
        )
