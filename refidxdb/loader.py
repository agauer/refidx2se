"""
loader.py — Load a refractiveindex.info material into a refellips RI object.
"""

from __future__ import annotations

import os
import tempfile

import numpy as np
import numpy.typing as npt
from refellips import RI
from refractiveindex import RefractiveIndexMaterial

Array = npt.NDArray[np.float64]


def rim_to_refellips(
    shelf: str,
    book: str,
    page: str,
    wavelengths_nm: Array,
) -> RI:
    """
    Convert a refractiveindex.info entry into a :class:`refellips.RI` object.

    Wavelengths are automatically clipped to the material's valid range.
    If extinction-coefficient (*k*) data are unavailable, *k* is set to zero.

    Parameters
    ----------
    shelf:
        Shelf identifier, e.g. ``'main'``.
    book:
        Book identifier, e.g. ``'SiO2'``.
    page:
        Page identifier, e.g. ``'Malitson'``.
    wavelengths_nm:
        1-D array of requested wavelengths in nanometres.

    Returns
    -------
    :class:`refellips.RI`
        Refractive-index object interpolated at the clipped wavelengths.

    Raises
    ------
    ValueError
        If there is no wavelength overlap between *wavelengths_nm* and the
        material's valid range.
    """
    mat = RefractiveIndexMaterial(shelf=shelf, book=book, page=page)

    wl_range = mat.get_wl_range()
    wl_min_nm, wl_max_nm = np.min(wl_range), np.max(wl_range)

    wls = wavelengths_nm[
        (wavelengths_nm >= wl_min_nm) & (wavelengths_nm <= wl_max_nm)
    ]
    if len(wls) == 0:
        raise ValueError(
            f"No wavelength overlap: requested "
            f"{wavelengths_nm[0]:.0f}–{wavelengths_nm[-1]:.0f} nm, "
            f"material valid {wl_min_nm:.0f}–{wl_max_nm:.0f} nm."
        )

    wl_um = wls * 1e-3
    n = mat.get_refractive_index(wl_um)
    try:
        k = mat.get_extinction_coefficient(wl_um)
    except Exception:
        k = np.zeros_like(wls)

    # Write a temp CSV and load via refellips
    with tempfile.NamedTemporaryFile(
        mode="w", suffix=".csv", delete=False, newline=""
    ) as f:
        f.write("wavelength,n,k\n")
        for wl, ni, ki in zip(wls, n, k):
            f.write(f"{wl:.4f},{ni:.6f},{ki:.6f}\n")
        tmp_path = f.name

    try:
        ri_obj = RI(tmp_path)
    finally:
        os.unlink(tmp_path)

    return ri_obj
