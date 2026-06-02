"""
refidx — lightweight interface to the refractiveindex.info database.
"""

from .catalog import print_material_options, return_material_option, search_material
from .loader import rim_to_refellips

__all__ = [
    "search_material",
    "print_material_options",
    "return_material_option",
    "rim_to_refellips",
]

__version__ = "0.1.0"
