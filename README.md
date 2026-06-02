# refidxdb

[![CI](https://github.com/agauer/refidxdb/actions/workflows/ci.yml/badge.svg)](https://github.com/agauer/refidxdb/actions)
[![PyPI](https://img.shields.io/pypi/v/refidxdb)](https://pypi.org/project/refidxdb/)
[![Python](https://img.shields.io/pypi/pyversions/refidxdb)](https://pypi.org/project/refidxdb/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

A lightweight Python interface to the [refractiveindex.info](https://refractiveindex.info) database, with built-in conversion to [`refellips`](https://github.com/refnx/refellips) `RI` objects for spectroscopic ellipsometry workflows.

## Features

- **Search** the full refractiveindex.info catalog by material name (case-insensitive, partial matching).
- **Load** any material entry directly into a `refellips.RI` object — no manual file management.
- Wavelength ranges are **automatically clipped** to the material's valid range.
- Catalog fetched from GitHub and **cached in-process** — only one network request per session.

## Installation

```bash
pip install refidxdb
```

Or from source:

```bash
git clone https://github.com/agauer/refidxdb.git
cd refidxdb
pip install -e ".[dev]"
```

## Quick start

```python
import numpy as np
import refidxdb
from refellips.reflect_modelSE import ReflectModelSE
from refellips.dispersion import RI, load_material

# 1. Explore available entries
refidxdb.print_material_options("SiO2")
# 4 entries matching 'SiO2':
#   option   shelf        book                      page                                description
#   -------- ------------ ------------------------- ----------------------------------- ---------------------------------------------
#   0        main         SiO2                      Malitson                            Malitson 1965: n 0.21–6.7 µm
#   1        main         SiO2                      ...

# 2. Pick one by index
shelf, book, page = refidxdb.return_material_option("SiO2", idx=0)

# 3. Load into refellips
wavelengths = np.linspace(400, 900, 200)   # nm
ri = refidxdb.rim_to_refellips(shelf, book, page, wavelengths)

# 4. Create a model
si = load_material("silicon")
air = RI("/path/to/refellips/materials/air.csv")

est_thickness = 20  # Å
min_thickness = 1
max_thickness = 50

sio2 = ri(est_thickness)
sio2.thick.setp(vary=True, bounds=(min_thickness, max_thickness))

stack = air() | sio2 | si()
model = ReflectModelSE(stack)

# 5. Continue with refellips analysis
```

## API reference

### `search_material(book: str) -> list[dict]`

Returns all catalog entries whose book name contains `book` (case-insensitive).
Each dict has keys `shelf`, `book`, `page`, `name`.

### `return_material_option(book: str, idx: int = 0) -> tuple[str, str, str]`

Returns `(shelf, book, page)` for the *idx*-th match. Raises `ValueError` if
no matches exist or `idx` is out of range.

### `print_material_options(book: str) -> None`

Pretty-prints a numbered table of all matches — handy for interactive use.

### `rim_to_refellips(shelf, book, page, wavelengths_nm) -> refellips.RI`

Fetches the material from refractiveindex.info, clips the requested wavelength
array to the material's valid range, and returns a `refellips.RI` object.
Missing *k* data is silently replaced with zeros.

## License

MIT — see [LICENSE](LICENSE).
