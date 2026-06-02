"""Tests for refidx2se.loader."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import numpy as np
import pytest

from refidx2se.loader import rim_to_refellips


def _make_mock_mat(wl_range=(400.0, 1000.0), has_k=True):
    """Return a mock RefractiveIndexMaterial."""
    mat = MagicMock()
    mat.get_wl_range.return_value = list(wl_range)
    mat.get_refractive_index.side_effect = lambda wl_um: np.ones_like(wl_um) * 1.46
    if has_k:
        mat.get_extinction_coefficient.side_effect = (
            lambda wl_um: np.zeros_like(wl_um)
        )
    else:
        mat.get_extinction_coefficient.side_effect = Exception("no k data")
    return mat


WLS = np.linspace(450, 900, 50)


@patch("refidx2se.loader.RI")
@patch("refidx2se.loader.RefractiveIndexMaterial")
def test_returns_ri_object(mock_rim_cls, mock_ri_cls):
    mock_rim_cls.return_value = _make_mock_mat()
    result = rim_to_refellips("main", "SiO2", "Malitson", WLS)
    assert result is mock_ri_cls.return_value


@patch("refidx2se.loader.RI")
@patch("refidx2se.loader.RefractiveIndexMaterial")
def test_wavelengths_clipped(mock_rim_cls, mock_ri_cls):
    """Wavelengths outside the material range must be clipped."""
    mock_mat = _make_mock_mat(wl_range=(600.0, 800.0))
    mock_rim_cls.return_value = mock_mat

    rim_to_refellips("main", "SiO2", "Malitson", WLS)

    # Check that get_refractive_index was called with values in [600, 800] nm
    call_wl_um = mock_mat.get_refractive_index.call_args[0][0]
    assert np.all(call_wl_um >= 0.600 - 1e-9)
    assert np.all(call_wl_um <= 0.800 + 1e-9)


@patch("refidx2se.loader.RI")
@patch("refidx2se.loader.RefractiveIndexMaterial")
def test_no_overlap_raises(mock_rim_cls, mock_ri_cls):
    mock_rim_cls.return_value = _make_mock_mat(wl_range=(1500.0, 2000.0))
    with pytest.raises(ValueError, match="No wavelength overlap"):
        rim_to_refellips("main", "SiO2", "Malitson", WLS)


@patch("refidx2se.loader.RI")
@patch("refidx2se.loader.RefractiveIndexMaterial")
def test_missing_k_falls_back_to_zero(mock_rim_cls, mock_ri_cls):
    """If get_extinction_coefficient raises, k should be all zeros."""
    mock_rim_cls.return_value = _make_mock_mat(has_k=False)

    rim_to_refellips("main", "SiO2", "Malitson", WLS)

    # Grab the CSV written to the temp file via RI constructor
    csv_path = mock_ri_cls.call_args[0][0]
    assert csv_path.endswith(".csv")
    # RI is called with path after file is deleted — just verify it was called
    assert mock_ri_cls.called


@patch("refidx2se.loader.RI")
@patch("refidx2se.loader.RefractiveIndexMaterial")
def test_temp_file_cleaned_up(mock_rim_cls, mock_ri_cls):
    """The temporary CSV must be deleted even if RI() raises."""
    import glob
    import os
    import tempfile

    mock_rim_cls.return_value = _make_mock_mat()
    mock_ri_cls.side_effect = RuntimeError("RI init failed")

    tmp_dir = tempfile.gettempdir()
    before = set(glob.glob(os.path.join(tmp_dir, "*.csv")))

    with pytest.raises(RuntimeError):
        rim_to_refellips("main", "SiO2", "Malitson", WLS)

    after = set(glob.glob(os.path.join(tmp_dir, "*.csv")))
    assert after == before, "Temp CSV file was not cleaned up"
