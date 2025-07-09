"""
Functions used to validate data acquisition routines
----------
Functions:
    bounds          - Validates a bounding box. Optionally converts to delimited EPSG:4326 string
    strings         - Checks an input represents a delimited string list
"""

from __future__ import annotations

import typing

import pfdf._validate.projection as pvalidate
from pfdf._utils import aslist

if typing.TYPE_CHECKING:
    from typing import Any


def bounds(bounds: Any, as_string: bool = True, delimiter: str = ",") -> str:
    "Validates a bounding box as a delimited EPSG:4326 string"
    bounds = pvalidate.bounds(bounds, require_crs=True)
    if as_string:
        bounds = bounds.reproject(4326)
        bounds = delimiter.join(str(bound) for bound in bounds.bounds)
    return bounds


def strings(strings: Any, name: str, delimiter=",") -> str:
    "Converts a list of names to a delimited string"

    strings = aslist(strings)
    for s, string in enumerate(strings):
        if not isinstance(string, str):
            raise TypeError(
                f"{name} must be a string or list of strings, "
                f"but {name}[{s}] is not a string"
            )
    return delimiter.join(strings)
