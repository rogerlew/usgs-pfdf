"""
_utils  Low-level utilities used throughout the package
----------
Type hint:
    real        - A list of numpy dtypes considered to be real-valued numbers

IO Functions:
    aslist      - Returns an input as a list
    astuple     - Returns an input as a tuple
    all_nones   - True if every input is None
    no_nones    - True if every input is not None

Misc Functions:
    clean_dims  - Optionally removes trailing singleton dimensions from an array
    limits      - Trims index limits to valid indices
    rowcol      - Converts spatial coordinates to pixel indices

Modules:
    buffers     - Function to standardize buffer units
    classify    - Function for classifying arrays using thresholds
    merror      - Functions to supplement memory-related error messages
    nodata      - Utilities for working with NoData values
    patches     - Context managers for patching pysheds
    slug        - Functions to generate anchor link slugs for the docs
    units       - Functions to facilitate unit conversion
"""

from __future__ import annotations

import typing

import numpy as np
import rasterio.transform

if typing.TYPE_CHECKING:
    from typing import Any, Callable

    from affine import Affine

    from pfdf.typing.core import RealArray, vector

    indices = list[int]
    start_stop = tuple[int, int]

# Combination numpy dtype for real-valued data
real = [np.integer, np.floating, bool]

#####
# IO
#####


def aslist(input: Any) -> list:
    """
    aslist  Returns an input as a list
    ----------
    aslist(input)
    Returns the input as a list. If the input is a tuple, converts to a list. If
    the input is a list, returns it unchanged. Otherwise, places the input within
    a new list.
    """
    if isinstance(input, (tuple, np.ndarray)):
        input = list(input)
    elif not isinstance(input, list):
        input = [input]
    return input


def astuple(input: Any) -> tuple:
    """
    astuple  Returns an input as a tuple
    ----------
    astuple(input)
    Returns the input as a tuple. If the input is a list, converts to a tuple. If
    the input is a tuple, returns it unchanged. Otherwise, places the input within
    a new tuple.
    """
    if isinstance(input, (list, np.ndarray)):
        input = tuple(input)
    elif not isinstance(input, tuple):
        input = (input,)
    return input


def all_nones(*args: Any) -> bool:
    "True if every input is None. Otherwise False"
    for arg in args:
        if arg is not None:
            return False
    return True


def no_nones(*args: Any) -> bool:
    "True if none of the inputs are None. Otherwise False"

    for arg in args:
        if arg is None:
            return False
    return True


#####
# Misc Functions
#####


def clean_dims(X: RealArray, keepdims: bool) -> RealArray:
    "Optionally removes trailing singleton dimensions"
    if not keepdims:
        X = np.atleast_1d(np.squeeze(X))
    return X


def limits(start: int, stop: int, length: int) -> start_stop:
    "Trims index limits to valid indices"
    start = max(start, 0)
    stop = min(stop, length)
    return (start, stop)


#####
# Pixel indices
#####


def rowcol(
    affine: Affine, xs: vector, ys: vector, op: Callable
) -> tuple[indices, indices]:
    "Converts spatial coordinates to pixel indices"

    rows, cols = rasterio.transform.rowcol(affine, xs, ys, op=op)
    rows = np.array(rows).astype(int).tolist()
    cols = np.array(cols).astype(int).tolist()
    return rows, cols


def pixel_limits(affine: Affine, bounds) -> tuple[start_stop, start_stop]:

    rows, cols = rowcol(affine, bounds.xs, bounds.ys, op=round)
    rows = (min(rows), max(rows))
    cols = (min(cols), max(cols))
    return rows, cols
