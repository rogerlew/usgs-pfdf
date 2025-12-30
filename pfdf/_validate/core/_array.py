"""
Functions that validate the shape and dtype of numpy arrays
----------
Low level:
    real_dtype      - Checks an input represents a numeric real-valued dtype
    dtype_          - Checks a dtype is an allowed value
    shape_          - Checks that a shape is allowed
    nonsingletons   - Locates nonsingleton dimensions

Shape and Type:
    array           - Checks an input represents a numpy array
    scalar          - Checks input represents a scalar
    vector          - Checks input represents a vector
    matrix          - Checks input represents a matrix
    broadcastable   - Checks two shapes can be broadcasted
"""

from __future__ import annotations

import typing

import numpy as np

from pfdf._utils import aslist, astuple, real
from pfdf.errors import DimensionError, EmptyArrayError, ShapeError

if typing.TYPE_CHECKING:
    from typing import Any, Optional

    from pfdf.typing.core import (
        MatrixArray,
        RealArray,
        ScalarArray,
        VectorArray,
        dtypes,
        shape,
        shape2d,
        strs,
    )

#####
# Low Level
#####


def real_dtype(input: Any, name: str) -> np.dtype:
    "Checks that an input represents a numeric real-valued numpy dtype"

    # Convert to dtype
    try:
        dtype = np.dtype(input)
    except Exception as error:
        raise TypeError(f"Could not convert {name} to a numpy dtype") from error

    # Require real-valued type
    dtype_(name, allowed=real, actual=dtype)
    return dtype


def dtype_(name: str, allowed: dtypes, actual: type) -> None:
    """
    dtype_  Checks that a dtype is an allowed value
    ----------
    dtype_(name, allowed, actual)
    Checks that the input dtype is an allowed type. Raises an exception if not.
    Note that the dtypes in "allowed" should consist of numpy scalar types and
    not Python built-in types. By contrast, "actual" may be either a numpy or
    built-in type. If allowed=None, conducts no checking and exits.
    ----------
    Inputs:
        name: A name for the input being tested for use in error messages.
        allowed: A list of allowed dtypes. Must consist of numpy scalar types.
            If None, disables type checking.
        actual: The dtype of the array being tested

    Raises:
        TypeError: If the dtype is not allowed
    """
    # Iterate through allowed types. Exit if any match
    if allowed is not None:
        allowed = aslist(allowed)
        for type in allowed:
            if np.issubdtype(actual, type):
                return

        # TypeError if type was not allowed
        allowed = ", ".join([str(type)[8:-2] for type in allowed])
        raise TypeError(
            f"The dtype of {name} ({actual}) is not an allowed dtype. "
            f"Allowed types are: {allowed}"
        )


def shape_(name: str, axes: strs, required: shape, actual: shape) -> None:
    """
    shape_  Checks that a numpy ndarray shape is valid
    ----------
    shape_(name, axes, required, actual)
    Checks that an input shape is valid. Raises an exception if not. Setting
    required=None disables shape checking altogether. If an element of required
    is -1, disables shape checking for that dimension.
    ----------
    Inputs:
        name: The name of the array being tested for use in error messages
        axes: The names of the elements of each dimension being tested. Should
            have one string per element of the required shape.
        shape: The required shape of the numpy array. If an element of shape is
            -1, disables shape checking for that dimension.
        actual: The actual shape of the numpy array

    Raises:
        ShapeError: If the array does not have the required shape.
    """

    # Convert inputs to sequences
    if required is not None:
        axes = aslist(axes)
        required = astuple(required)
        actual = astuple(actual)

        # Check the length of each dimension
        for axis, required, actual in zip(axes, required, actual):
            if required != -1 and required != actual:
                raise ShapeError(
                    f"{name} must have {required} {axis}, but it has {actual} {axis} instead."
                )


def nonsingleton(array: np.ndarray) -> list[bool]:
    """
    nonsingleton  Finds the non-singleton dimensions of a numpy array
    ----------
    nonsingleton(array)
    Returns a bool list with one element per dimension of the input array.
    True indicates a nonsingleton dimensions (length > 1). False is singleton.
    ----------
    Inputs:
        array: The ndarray being inspected

    Returns:
        list[bool]: Indicates the non-singleton dimensions.
    """
    return [shape > 1 for shape in array.shape]


#####
# Shapes and types
#####


def array(
    input: Any, name: str, dtype=None, *, copy: bool = False, allow_empty: bool = False
) -> RealArray:
    """
    array  Validates an input numpy array
    ----------
    array(input, name)
    Converts the input to a numpy array with at least 1 dimension. Raises an
    EmptyArrayError if the array does not contain any elements.

    array(input, name, dtype)
    Also checks the input is derived from one of the listed dtypes.

    array(..., copy=True)
    Returns a copy of the input array. Default is to not copy whenever possible.

    array(..., allow_empty=True)
    Permits an empty array.
    ----------
    Inputs:
        input: The input being checked
        name: The name of the input for use in error messages.
        dtype: A list of allowed dtypes
        copy: True to return a copy of the input array. False (default) to not copy
            whenever possible
        allow_empty: True to treat an empty array as valid. False (default) to raise
            an error

    Outputs:
        numpy array (at least 1D): The input as a numpy array

    Raises:
        EmptyArrayError - If the array is empty
    """

    # Convert to array with minimum of 1D. Copy as needed.
    # Use copy parameter directly - numpy 1.26+ requires bool, not None
    input = np.array(input, copy=copy)
    input = np.atleast_1d(input)

    # Optionally prevent empty arrays
    if not allow_empty and input.size == 0:
        raise EmptyArrayError(f"{name} does not have any elements.")

    # Optionally check dtype
    dtype_(name, allowed=dtype, actual=input.dtype)
    return input


def scalar(input: Any, name: str, dtype: Optional[dtypes] = None) -> ScalarArray:
    """
    scalar  Validate an input represents a scalar
    ----------
    scalar(input, name)
    Checks that an input represents a scalar. Raises an exception if not. Returns
    the input as a 1D numpy array.

    scalar(input, name, dtype)
    Also check that the input is derived from one of the listed dtypes.
    ----------
    Inputs:
        input: The input being checked
        name: A name for the input for use in error messages.
        dtype: A list of allowed dtypes

    Outputs:
        numpy 1D array: The input as a 1D numpy array.

    Raises:
        DimensionError: If the input has more than one element
    """

    input = array(input, name, dtype, copy=False)
    if input.size != 1:
        raise DimensionError(
            f"{name} must have exactly 1 element, but it has {input.size} elements instead."
        )
    return input[0]


def vector(
    input: Any,
    name: str,
    *,
    dtype: Optional[dtypes] = None,
    length: Optional[int] = None,
    allow_empty: bool = False,
) -> VectorArray:
    """
    vector  Validate an input represents a 1D numpy array
    ----------
    vector(input, name)
    Checks the input represents a 1D numpy array. Valid inputs may only have a
    single non-singleton dimension. Raises an exception if this criteria is not
    met. Otherwise, returns the array as a numpy 1D array.

    vector(..., *, dtype)
    Also checks that the vector has an allowed dtype. Raises a TypeError if not.

    vector(..., *, length)
    Also checks that the vector has the specified length. Raises a ShapeError if
    this criteria is not met.

    vector(..., *, allow_empty)
    Indicate whether the vector may be empty. Default is to not allow empty vectors.
    ----------
    Input:
        input: The input being checked
        name: A name for the input for use in error messages.
        dtype: A list of allowed dtypes
        length: A required length for the vector
        allow_empty: True to permit empty vectors. False (default) to raise an error

    Outputs:
        numpy 1D array: The input as a 1D numpy array

    Raises:
        DimensionError: If the input has more than 1 non-singleton dimension
    """

    # Initial validation
    input = array(input, name, dtype, copy=False, allow_empty=allow_empty)

    # Only 1 non-singleton dimension is allowed
    nonsingletons = nonsingleton(input)
    if sum(nonsingletons) > 1:
        raise DimensionError(
            f"{name} can only have 1 dimension with a length greater than 1."
        )

    # Optionally check shape. Return as 1D vector.
    shape_(name, "element(s)", required=length, actual=input.size)
    return input.reshape(-1)


def matrix(
    input: Any,
    name: str,
    *,
    dtype: Optional[dtypes] = None,
    shape: Optional[shape2d] = None,
    copy: bool = False,
) -> MatrixArray:
    """
    matrix  Validate input represents a 2D numpy array
    ----------
    matrix(input, name)
    Checks the input represents a 2D numpy array. Raises an exception
    if not. Otherwise, returns the output as a 2D numpy array. Valid inputs may
    have any number of dimension, but only the first two dimensions may be
    non-singleton. A 1D array is interpreted as a 1xN array.

    matrix(..., *, dtype)
    Also checks the array has an allowed dtype. Raises a TypeError if not.

    matrix(..., *, shape)
    Also checks that the array matches the requested shape. Raises a ShapeError
    if not. Use -1 to disable shape checking for a particular axis.

    matrix(..., *, copy=True)
    Returns a validated array that is a copy of the input.
    ----------
    Inputs:
        input: The input being checked
        name: A name for the input for use in error messages.
        dtype: A list of allowed dtypes
        shape: A requested shape for the matrix. A tuple with two elements - the
            first element is the number of rows, and the second is the number
            of columns. Setting an element to -1 disables the shape checking for
            that axis.
        copy: True to return a copy of the input array. False (default) to not copy

    Outputs:
        numpy 2D array: The input as a 2D numpy array

    Raises:
        TypeError: If the input does not have an allowed dtype
        DimensionError: If the input has non-singleton dimensions that are not
            the first 2 dimensions.
        ShapeError: If the input does not have an allowed shape
    """

    # Initial validation. Handle vector shapes
    input = array(input, name, dtype, copy=copy)
    if input.ndim == 1:
        input = input.reshape(input.size, 1)

    # Only the first 2 dimensions can be non-singleton
    if input.ndim > 2:
        nonsingletons = nonsingleton(input)[2:]
        if any(nonsingletons):
            raise DimensionError(
                f"Only the first two dimension of {name} can be longer than 1. "
            )

    # Cast as 2D array. Optionally check shape. Return array
    nrows, ncols = input.shape[0:2]
    input = input.reshape(nrows, ncols)
    shape_(name, ["row(s)", "column(s)"], required=shape, actual=input.shape)
    return input


def broadcastable(shape1: shape, name1: str, shape2: shape, name2: str) -> shape:
    """
    broadcastable  Checks that two array shapes can be broadcasted
    ----------
    broadcastable(shape1, name1, shape2, name2)
    Checks that the input arrays have broadcastable shapes. Raises a ValueError
    if not. If the shapes are compatible, returns the broadcasted shape.
    ----------
    Inputs:
        shape1: The first shape being checked
        name1: The name of the array associated with shape1
        shape2: The second shape being checked
        name2: The name of the array associated with shape2

    Outputs:
        int tuple: The broadcasted shape

    Raises:
        ValueError  - If the arrays are not broadcastable
    """

    try:
        return np.broadcast_shapes(shape1, shape2)
    except ValueError:
        raise ValueError(
            f"The shape of the {name1} array {shape1} cannot be broadcasted "
            f"with the shape of the {name2} array {shape2}."
        )
