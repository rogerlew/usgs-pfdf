"""
Context manager to monkey-patch pysheds 0.4 for numpy 2+
----------
When numpy updated to 2.0, it changed the API for the `can_cast` function. This change
broke the NoData dtype checks in pysheds 0.4. This module provides a context manager
that swaps out the affected pysheds function with a patched version until a fix can be
released by pysheds.
----------
Contents:
    Patch   - A context manager that patches the broken pysheds function
    _new    - A patched version of the `pysheds.sview.Raster.__new__` method
"""

import numpy as np
from pysheds import _sgrid as _self
from pysheds.sgrid import sGrid
from pysheds.sview import Raster, ViewFinder


class NodataPatch:
    """
    Context manager for patching the NoData issue
    ----------
    Methods:
        __init__    - Stores a reference to the original (buggy) function
        __enter__   - Replaces the original function with a patched version of the code
        __exit__    - Restores the original function
        patch       - A patched version of pysheds.sview.Raster.__new__
    """

    def __init__(self):
        "Stores a reference to the original (buggy) function"
        self.initial = Raster.__new__

    def __enter__(self):
        "Replaces the affected function with the patched code"
        Raster.__new__ = self.patch

    def __exit__(self, *args, **kwargs) -> None:
        "Restores the original function"
        Raster.__new__ = self.initial

    @staticmethod  # pragma: no cover
    def patch(cls, input_array, viewfinder=None, metadata={}):
        "A patched version of pysheds.sview.Raster.__new__"
        try:
            # MultiRaster must be subclass of ndarray
            assert isinstance(input_array, np.ndarray)
            # Ensure MultiRaster is 2D
            assert input_array.ndim == 2
        except:
            raise TypeError("Input must be a 2-dimensional array-like object.")
        # Handle case where input is a Raster itself
        if isinstance(input_array, Raster):
            input_array, viewfinder, metadata = cls._handle_raster_input(
                input_array, viewfinder, metadata
            )
        # Create a numpy array from the input
        obj = np.asarray(input_array).view(cls)
        # If no viewfinder provided, construct one congruent with the array shape
        if viewfinder is None:
            viewfinder = ViewFinder(shape=obj.shape)
        # If a viewfinder is provided, ensure that it is a viewfinder...
        else:
            try:
                assert isinstance(viewfinder, ViewFinder)
            except:
                raise ValueError("Must initialize with a ViewFinder.")
            # Ensure that viewfinder shape is correct...
            try:
                assert viewfinder.shape == obj.shape
            except:
                raise ValueError("Viewfinder and array shape must be the same.")
        # Test typing of array
        try:
            assert not np.issubdtype(obj.dtype, object)
            assert not np.issubdtype(obj.dtype, np.flexible)
        except:
            raise TypeError("`object` and `flexible` dtypes not allowed.")
        try:

            #####
            # Here is the patch - it updates the dtype check for the new numpy API
            #####
            nodata = np.array(viewfinder.nodata)
            casted = nodata.astype(obj.dtype, casting="unsafe")
            assert (nodata == casted) or np.can_cast(nodata, obj.dtype, casting="safe")

        except:
            raise TypeError("`nodata` value not representable in dtype of array.")
        # Don't allow original viewfinder and metadata to be modified
        viewfinder = viewfinder.copy()
        metadata = metadata.copy()
        # Set attributes of array
        obj._viewfinder = viewfinder
        obj.metadata = metadata
        return obj


class RidgePatch:
    """
    Context manager for patching _d8_distance_to_ridge
    ----------
    Methods:
        __init__    - Stores a reference to the original (buggy) function
        __enter__   - Replaces the original function with a patched version of the code
        __exit__    - Restores the original function
        patch       - A patched version of pysheds.sgrid.sGrid._d8_distance_to_ridge
    """

    def __init__(self):
        "Stores a reference to the original (buggy) function"
        self.initial = sGrid._d8_distance_to_ridge

    def __enter__(self):
        "Replaces the affected function with the patched code"
        sGrid._d8_distance_to_ridge = self.patch

    def __exit__(self, *args, **kwargs) -> None:
        "Restores the original function"
        sGrid._d8_distance_to_ridge = self.initial

    @staticmethod  # pragma: no cover
    def patch(
        self,
        fdir,
        weights,
        dirmap=(64, 128, 1, 2, 4, 8, 16, 32),
        algorithm="iterative",
        nodata_out=np.nan,
        **kwargs,
    ):
        "A patched version of pysheds.sgrid.sGrid._d8_distance_to_ridge"
        # Find nodata cells and invalid cells
        nodata_cells = self._get_nodata_cells(fdir)
        invalid_cells = ~np.isin(fdir.ravel(), dirmap).reshape(fdir.shape)
        # Set nodata cells to zero
        fdir[nodata_cells] = 0
        fdir[invalid_cells] = 0
        # TODO: Should this be ones for all cells?
        if weights is None:
            weights = (~nodata_cells).reshape(fdir.shape).astype(np.float64)
        startnodes = np.arange(fdir.size, dtype=np.int64)
        endnodes = _self._flatten_fdir_numba(fdir, dirmap).reshape(fdir.shape)

        #####
        # Here is the patch - it adds the minlength input to np.bincount
        #####
        indegree = np.bincount(endnodes.ravel(), minlength=fdir.size).astype(np.uint8)

        startnodes = startnodes[(indegree == 0)]
        rdist = np.zeros(fdir.shape, dtype=np.float64)
        if algorithm.lower() == "iterative":
            rdist = _self._d8_reverse_distance_iter_numba(
                rdist, endnodes, indegree, startnodes, weights
            )
        elif algorithm.lower() == "recursive":
            rdist = _self._d8_reverse_distance_recur_numba(
                rdist, endnodes, indegree, startnodes, weights
            )
        else:
            raise ValueError("Algorithm must be `iterative` or `recursive`.")
        rdist = self._output_handler(
            data=rdist,
            viewfinder=fdir.viewfinder,
            metadata=fdir.metadata,
            nodata=nodata_out,
        )
        return rdist
