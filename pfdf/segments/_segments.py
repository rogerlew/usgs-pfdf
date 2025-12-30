"""
A class to build and manage stream segment networks
----------
This module implements the "Segments" class. Much of the class functionality is
within this file. However, complex routines may use other internal modules within
the parent subpackage.
----------
Classes:
    Segments    - Builds and manages a stream segment network
"""

from __future__ import annotations

import typing
from math import inf, nan

import fiona
import numpy as np
from rasterio.transform import rowcol

import pfdf._validate.core as validate
import pfdf.segments._validate as svalidate
from pfdf import watershed
from pfdf._utils import all_nones, real
from pfdf._utils.nodata import NodataMask
from pfdf.errors import MissingCRSError, MissingTransformError
from pfdf.projection import crs
from pfdf.raster import Raster
from pfdf.segments import _basins, _confinement, _geojson, _update

if typing.TYPE_CHECKING:
    from pathlib import Path
    from typing import Literal, Optional

    import shapely
    from geojson import FeatureCollection

    from pfdf.projection import CRS, BoundingBox, Transform
    from pfdf.typing.core import (
        BooleanMatrix,
        MatrixArray,
        Pathlike,
        RealArray,
        ScalarArray,
        Units,
        VectorArray,
        scalar,
        shape2d,
        vector,
    )
    from pfdf.typing.raster import RasterInput
    from pfdf.typing.segments import (
        BooleanIndices,
        CatchmentValues,
        ExportType,
        NetworkIndices,
        Outlets,
        PixelIndices,
        PropertyDict,
        SegmentParents,
        SegmentValues,
        Selection,
        SelectionType,
        StatFunction,
        Statistic,
        TerminalValues,
    )


# Supported statistics -- name: (function, description)
_STATS = {
    "outlet": (None, "Values at stream segment outlet pixels"),
    "min": (np.amin, "Minimum value"),
    "max": (np.amax, "Maximum value"),
    "mean": (np.mean, "Mean"),
    "median": (np.median, "Median"),
    "std": (np.std, "Standard deviation"),
    "sum": (np.sum, "Sum"),
    "var": (np.var, "Variance"),
    "nanmin": (np.nanmin, "Minimum value, ignoring NaNs"),
    "nanmax": (np.nanmax, "Maximum value, ignoring NaNs"),
    "nanmean": (np.nanmean, "Mean value, ignoring NaNs"),
    "nanmedian": (np.nanmedian, "Median value, ignoring NaNs"),
    "nanstd": (np.nanstd, "Standard deviation, ignoring NaNs"),
    "nansum": (np.nansum, "Sum, ignoring NaNs"),
    "nanvar": (np.nanvar, "Variance, ignoring NaNs"),
}


class Segments:
    """
    Segments  Builds and manages a stream segment network
    ----------
    The Segments class is used to build and manage a stream segment network. Here,
    a stream segment is approximately equal to the stream bed of a catchment basin.
    The class constructor delineates an initial network. The class then provides
    methods to compute earth-system variables for the individual stream segments,
    and to filter the network to model-worthy segments. Other method compute
    inputs for hazard assessment models, and the "save" method exports results to
    standard GIS file formats. Please see the user guide for more detailed instructions
    on working with this class.
    ----------
    **PROPERTIES**
    Network:
        size                - The number of segments in the network
        nlocal              - The number of local drainage networks in the full network
        crs                 - The coordinate reference system associated with the network
        crs_units           - The units of the CRS along the X and Y axes

    Segments:
        segments            - A list of shapely.LineString objects representing the stream segments
        ids                 - A unique integer ID associated with each stream segment
        terminal_ids        - The IDs of the terminal segments
        indices             - The indices of each segment's pixels in the stream segment raster
        npixels             - The number of pixels in the catchment basin of each stream segment

    Raster Metadata:
        flow                - The flow direction raster used to build the network
        raster_shape        - The shape of the stream segment raster
        transform           - The affine Transform of the stream segment raster
        bounds              - The BoundingBox of the stream segment raster
        located_basins      - True when the object has pre-located outlet basins

    **METHODS**
    Object Creation:
        __init__            - Builds an initial stream segment network

    Dunders:
        __len__             - The number of segments in the network
        __repr__            - A string summarizing key info about the network
        __geo_interface__   - A geojson-like dict of the network

    Outlets:
        isterminal          - Indicates whether segments are terminal segments
        termini             - Returns the IDs of terminal segments
        outlets             - Returns the row and column indices of outlet pixels

    Local Networks:
        parents             - Returns the IDs of segments immediately upstream
        child               - Returns the ID of the segment immediately downstream
        ancestors           - Returns the IDs of upstream segments in a local network
        descendents         - Returns the IDs of downstream segments in a local network
        family              - Returns the IDs of segments in a local network
        isnested            - Indicates whether segments are in a nested network

    Rasters:
        locate_basins       - Builds and saves the basin raster, optionally in parallel
        raster              - Returns a raster representation of the stream segment network
        catchment_mask      - Returns the catchment basin mask for the queried stream segment

    Generic Statistics:
        statistics          - Print or return info about supported statistics
        summary             - Compute summary statistics over the pixels for each segment
        catchment_summary   - Compute summary statistics over catchment basins

    Earth system variables:
        area                - Computes the total basin areas
        burn_ratio          - Computes the burned proportion of basins
        burned_area         - Computes the burned area of basins
        catchment_ratio     - Computes the proportion of catchment pixels that meet a criteria
        confinement         - Computes the confinement angle for each segment
        developed_area      - Computes the developed area of basins
        in_mask             - Checks whether each segment is within a mask
        in_perimeter        - Checks whether each segment is within a fire perimeter
        kf_factor           - Computes mean basin KF-factors
        length              - Computes the length of each stream segment
        scaled_dnbr         - Computes mean basin dNBR / 1000
        scaled_thickness    - Computes mean basin soil thickness / 100
        sine_theta          - Computes mean basin sin(theta)
        slope               - Computes the mean slope of each segment
        relief              - Computes the vertical relief to highest ridge cell for each segment
        ruggedness          - Computes topographic ruggedness (relief / sqrt(area)) for each segment

    Filtering:
        continuous          - Indicates segments that can be filtered while preserving flow continuity
        keep                - Restricts the network to the indicated segments
        remove              - Removes the indicated segments from the network
        copy                - Returns a deep copy of the Segments object

    Export:
        geojson             - Returns the network as a geojson.FeatureCollection
        save                - Saves the network to file

    **INTERNAL:**
    Attributes:
        _flow                   - The flow direction raster for the watershed
        _segments               - A list of shapely LineStrings representing the segments
        _ids                    - The ID for each segment
        _indices                - A list of each segment's pixel indices
        _npixels                - The number of catchment pixels for each stream segment
        _child                  - The index of each segment's downstream child
        _parents                - The indices of each segment's upstream parents
        _basins                 - Saved nested drainage basin raster values

    Utilities:
        _indices_to_ids         - Converts segment IDs to indices
        _basin_npixels          - Returns the number of pixels in catchment or terminal outlet basins
        _nbasins                - Returns the number of catchment or terminal outlet basins
        _preallocate            - Initializes an array to hold summary values
        _accumulation           - Computes flow accumulation values

    Local Networks:
        _get_parents            - Returns indices of valid parent segments

    Rasters:
        _segments_raster        - Builds a stream segment raster array
        _locate_basins          - Returns the basin raster's data array

    Summaries:
        _summarize              - Computes a summary statistic
        _values_at_outlets      - Returns the data values at the outlet pixels
        _accumulation_summary   - Computes basin summaries using flow accumulation
        _catchment_summary      - Computes summaries by iterating over basin catchments

    Filtering:
        _removable              - Locates requested segments on the edges of their local flow networks
    """

    #####
    # Dunders
    #####

    def __init__(
        self,
        flow: RasterInput,
        mask: RasterInput,
        max_length: scalar = inf,
        units: Units = "meters",
    ) -> None:
        """
        Creates a new Segments object
        ----------
        Segments(flow, mask)
        Builds a Segments object to manage the stream segments in a drainage network.
        Note that stream segments approximate the river beds in the catchment basins,
        rather than the full catchment basins. The returned object records the
        pixels associated with each segment in the network.

        The stream segment network is determined using a TauDEM-style D8 flow direction
        raster and a raster mask (and please see the documentation of the pfdf.watershed
        module for details of this style). Note the the flow direction raster must have
        both a CRS and an affine Transform. The mask is used to indicate the pixels under
        consideration as stream segments. True pixels may possibly be assigned to a
        stream segment, False pixels will never be assigned to a stream segment. The
        mask typically screens out pixels with low flow accumulations, and may include
        other screenings - for example, to remove pixels in large bodies of water, or
        pixels below developed areas.

        Segments(..., max_length)
        Segments(..., max_length, units)
        Also specifies a maximum length for the segments in the network. Any segment
        longer than this length will be split into multiple pieces. The split pieces
        will all have the same length, which will be < max_length. Note that the
        max_length must be at least as long as the diagonal of the raster pixels.
        By default, this command interprets max_length in meters. Use the "units"
        option to specify max_length in different units instead. Unit options include:
        "base" (CRS/Transform base unit), "meters" (default), "kilometers", "feet",
        and "miles".
        ----------
        Inputs:
            flow: A TauDEM-style D8 flow direction raster
            mask: A raster whose True values indicate the pixels that may potentially
                belong to a stream segment.
            max_length: A maximum allowed length for segments in the network.
            units: Specifies the units of max_length. Options include:
                "base" (CRS base units), "meters" (default)", "kilometers", "feet",
                and "miles".

        Outputs:
            Segments: A Segments object recording the stream segments in the network.
        """

        # Initialize attributes
        self._flow: Raster = None
        self._segments: list[shapely.LineString] = None
        self._ids: SegmentValues = None
        self._indices: NetworkIndices = None
        self._npixels: SegmentValues = None
        self._child: SegmentValues = None
        self._parents: SegmentParents = None
        self._basins: Optional[MatrixArray] = None

        # Validate and record flow raster
        flow = Raster(flow, "flow directions")
        if flow.crs is None:
            raise MissingCRSError("The flow direction raster must have a CRS.")
        elif flow.transform is None:
            raise MissingTransformError(
                "The flow direction raster must have an affine Transform."
            )
        self._flow = flow

        # Validate max_length
        max_length = validate.scalar(max_length, "max_length", dtype=real)
        units = validate.units(units)
        pixel_diagonal = flow.pixel_diagonal(units=units)
        if max_length < pixel_diagonal:
            if units == "base":
                units = crs.yunit(flow.crs)
            raise ValueError(
                f"max_length (value = {max_length} {units}) must be at least as "
                f"long as the diagonals of the pixels in the flow direction raster "
                f"(length = {pixel_diagonal} {units})"
            )

        # Calculate network. Assign IDs
        self._segments = watershed.network(self.flow, mask, max_length, units)
        self._ids = np.arange(self.size, dtype=int) + 1

        # Initialize attributes - indices, child, parents
        self._indices = []
        self._child = np.full(self.size, -1, dtype=int)
        self._parents = np.full((self.size, 2), -1, dtype=int)

        # Initialize variables used to determine connectivity and split points.
        # (A split point is where a long stream segment was split into 2 pieces)
        starts = np.empty((self.size, 2), float)
        outlets = np.empty((self.size, 2), float)
        split = False

        # Get the spatial coordinates of each segment
        for s, segment in enumerate(self.segments):
            coords = np.array(segment.coords)
            starts[s, :] = coords[0, :]
            outlets[s, :] = coords[-1, :]

            # Get the pixel indices for each segment. Ensure they are lists
            # (different rasterio versions may return lists or numpy arrays)
            rows, cols = rowcol(
                self.flow.transform.affine, xs=coords[:, 0], ys=coords[:, 1]
            )
            rows = np.array(rows).astype(int).tolist()
            cols = np.array(cols).astype(int).tolist()

            # If the first two indices match, then this is downstream of a split point
            if rows[0] == rows[1] and cols[0] == cols[1]:
                split = True

            # If the segment is downstream of a split point, then remove the
            # first index so that split pixels are assigned to the split segment
            # that contains the majority of the pixel
            if split:
                del rows[0]
                del cols[0]
                split = False

            # If the final two indices are identical, then the next segment
            # is downstream of a split point.
            if rows[-1] == rows[-2] and cols[-1] == cols[-2]:
                split = True

            # Record pixel indices. Remove the final coordinate so that junctions
            # are assigned to the downstream segment.
            indices = (rows[:-1], cols[:-1])
            self._indices.append(indices)

        # Find upstream parents (if any)
        for s, start in enumerate(starts):
            parents = np.equal(start, outlets).all(axis=1)
            parents = np.argwhere(parents)

            # Add extra columns if there are more parents than initially expected
            nextra = parents.size - self._parents.shape[1]
            if nextra > 0:
                fill = np.full((self.size, nextra), -1, dtype=int)
                self._parents = np.concatenate((self._parents, fill), axis=1)

            # Record child-parent relationships
            self._child[parents] = s
            self._parents[s, 0 : parents.size] = parents.flatten()

        # Compute flow accumulation
        self._npixels = self._accumulation()

    def __len__(self) -> int:
        """
        The number of stream segments in the network
        ----------
        len(self)
        Returns the total number of stream segments in the network.
        ----------
        Outputs:
            int: The number of segments in the network
        """
        return len(self._segments)

    def __repr__(self) -> str:
        """
        A string summarizing the Segments object
        ----------
        repr(self)
        Returns a string summarizing key info about the Segments object.
        ----------
        Outputs:
            str: A string summarizing the Segments object
        """

        return (
            f"Segments:\n"
            f"    Total Segments: {len(self)}\n"
            f"    Local Networks: {self.nlocal}\n"
            f"    Located Basins: {self.located_basins}\n"
            f"    Raster Metadata:\n"
            f"        Shape: {self.raster_shape}\n"
            f'        CRS("{self.crs.name}")\n'
            f"        {self.transform}\n"
            f"        {self.bounds}\n"
        )

    @property
    def __geo_interface__(self) -> FeatureCollection:
        "A geojson-like dict of the Segments object"
        return self.geojson(type="segments", properties=None)

    #####
    # Properties
    #####

    ##### Network

    @property
    def size(self) -> int:
        "The number of stream segments in the network"
        return len(self)

    @property
    def nlocal(self) -> int:
        "The number of local drainage networks"
        ntermini = np.sum(self.isterminal())
        return int(ntermini)

    @property
    def crs(self) -> CRS:
        "The coordinate reference system of the stream segment network"
        return self._flow.crs

    @property
    def crs_units(self) -> tuple[str, str]:
        "The units of the CRS along the X and Y axes"
        return self._flow.crs_units

    ##### Segments

    @property
    def segments(self) -> list[shapely.LineString]:
        "A list of shapely LineStrings representing the stream segments"
        return self._segments.copy()

    @property
    def ids(self) -> SegmentValues:
        "The ID of each stream segment"
        return self._ids.copy()

    @property
    def terminal_ids(self) -> TerminalValues:
        "The IDs of the terminal segments in the network"
        return self.ids[self.isterminal()]

    @property
    def indices(self) -> NetworkIndices:
        "The row and column indices of the stream raster pixels for each segment"
        return self._indices.copy()

    @property
    def npixels(self) -> SegmentValues:
        "The number of pixels in the catchment basin of each stream segment"
        return self._npixels.copy()

    ##### Raster metadata

    @property
    def flow(self) -> Raster:
        "The flow direction raster used to build the network"
        return self._flow

    @property
    def raster_shape(self) -> shape2d:
        "The shape of the stream segment raster"
        return self._flow.shape

    @property
    def transform(self) -> Transform:
        "The (affine) Transform of the stream segment raster"
        return self._flow.transform

    @property
    def bounds(self) -> BoundingBox:
        "The BoundingBox of the stream segment raster"
        return self._flow.bounds

    @property
    def located_basins(self) -> bool:
        "True if the Segments object has pre-located the outlet basins"
        return self._basins is not None

    #####
    # Utilities
    #####

    def _indices_to_ids(self, indices: RealArray) -> RealArray:
        "Converts segment indices to (user-facing) IDs"

        # If empty, just return directly
        indices = np.array(indices, copy=False)
        if indices.size == 0:
            return indices

        # Otherwise, convert to ids
        ids = np.zeros(indices.shape)
        valid = indices != -1
        ids[valid] = self._ids[indices[valid]]
        return ids

    def _basin_npixels(self, terminal: bool) -> CatchmentValues | TerminalValues:
        "Returns the number of pixels in catchment or terminal outlet basins"
        if terminal:
            return self._npixels[self.isterminal()]
        else:
            return self._npixels

    def _nbasins(self, terminal: bool) -> int:
        "Returns the number of catchment or terminal outlet basins"
        if terminal:
            return self.nlocal
        else:
            return self.size

    def _preallocate(self, terminal: bool = False) -> SegmentValues | TerminalValues:
        "Preallocates an array to hold summary values"
        length = self._nbasins(terminal)
        return np.empty(length, dtype=float)

    def _accumulation(
        self,
        weights: Optional[RasterInput] = None,
        mask: Optional[RasterInput] = None,
        terminal: bool = False,
        omitnan: bool = False,
    ) -> CatchmentValues:
        "Computes flow accumulation values"

        # Default case is just npixels
        if all_nones(weights, mask) and (self._npixels is not None):
            return self._basin_npixels(terminal).copy()

        # Otherwise, compute the accumulation at each outlet
        accumulation = watershed.accumulation(
            self.flow, weights, mask, omitnan=omitnan, check_flow=False
        )
        return self._values_at_outlets(accumulation, terminal=terminal)

    #####
    # Outlets
    #####

    def isterminal(self, ids: Optional[vector] = None) -> SegmentValues | VectorArray:
        """
        Indicates whether segments are terminal segments
        ----------
        self.isterminal()
        Determines whether each segment is a terminal segment or not. A segment
        is terminal if it does not have a downstream child. (Note that there may
        still be other segments furhter downstream if the segment is in a nested drainage
        network). Returns a boolean 1D numpy array with one element per segment
        in the network. True elements indicate terminal segments, False elements
        are segments that are not terminal.

        self.isterminal(ids)
        Determines whether the queried segments are terminal segments or not.
        Returns a boolean 1D array with one element per queried segment.
        ----------
        Inputs:
            ids: The IDs of segments being queried. If not set, queries all segments
                in the network.

        Outputs:
            boolean 1D numpy array: Whether each segment is terminal.
        """

        indices = svalidate.ids(self, ids)
        return self._child[indices] == -1

    def termini(self, ids: Optional[vector] = None) -> SegmentValues | VectorArray:
        """
        Returns the IDs of terminal segments
        ----------
        self.termini()
        Determines the ID of the terminal segment for each stream segment in the
        network. Returns a numpy 1D array with one element per stream segment.
        Typically, many segments will drain to the same terminal segment, so this
        array will usually contain many duplicate IDs.

        If you instead want the unique IDs of the terminal segments, use:
            >>> self.terminal_ids

        self.termini(ids)
        Only returns terminal segment IDs for the queried segments. The output
        array will have one element per queried segment.
        ----------
        Inputs:
            ids: The IDs of the queried segments. If not set, then queries every
                segment in the network.

        Outputs:
            numpy 1D array: The ID of the terminal segment for each queried segment
        """

        # Walk downstream to locate the terminal index for each queried segment
        indices = svalidate.ids(self, ids)
        termini = []
        for index in indices:
            while self._child[index] != -1:
                index = self._child[index]
            termini.append(index)

        # Return as a numpy array of IDs
        termini = np.array(termini).reshape(-1)
        return self._indices_to_ids(termini)

    def outlets(
        self,
        ids: Optional[vector] = None,
        *,
        segment_outlets: bool = False,
        as_array: bool = False,
    ) -> Outlets | MatrixArray:
        """
        Returns the row and column indices of outlet pixels
        ----------
        self.outlets()
        Returns the row and column index of the terminal outlet pixel for each
        segment in the network. Returns a list with one element per segment in
        the network. Each element is a tuple of two integers. The first element
        is the row index of the outlet pixel in the stream network raster, and
        the second element is the column index.

        self.outlets(ids)
        Only returns outlet pixel indices for the queried segments. The output
        list will have one element per queried segment.

        self.outlets(..., *, segment_outlets=True)
        Returns the indices of each segment's immediate outlet pixel, rather than
        the indices of the terminal outlet pixels. Each segment outlet is the final
        pixel in the stream segment itself. (Compare with a terminal outlet, which
        is the final pour point in the segment's local drainage network).

        self.outlets(..., *, as_array=True)
        Returns the outlet pixel indices as a numpy array, rather than as a list.
        The output array will have one row per queried stream segment, and two
        columns. The first column is the row indices, and the second column is
        the column indices.
        ----------
        Inputs:
            ids: The IDs of the queried stream segments. If not set, queries all
                segments in the network.
            segment_outlets: True to return the indices of each stream segment's
                outlet pixel. False (default) to return the indices of terminal
                outlet pixels
            as_array: True to return the pixel indices as an Nx2 numpy array.
                False (default) to return indices as a list of 2-tuples.

        Outputs:
            list[tuple[int, int]] | numpy array: The outlet pixel indices of the
                queried stream segments
        """

        # Get the indices of the appropriate segments
        if not segment_outlets:
            ids = self.termini(ids)
        indices = svalidate.ids(self, ids)

        # Extract outlet pixel indices
        outlets = []
        for index in indices:
            pixels = self._indices[index]
            row = pixels[0][-1]
            column = pixels[1][-1]
            outlets.append((row, column))

        # Optionally convert to array
        if as_array:
            outlets = np.array(outlets).reshape(-1, 2)
        return outlets

    #####
    # Local Networks
    #####

    def _get_parents(self, index: int) -> list[int]:
        "Returns the indices of valid parent segments"
        parents = self._parents[index, :]
        return [index for index in parents if index != -1]

    def parents(self, id: scalar) -> list[int] | None:
        """
        Returns the IDs of the queried segment's parent segments
        ----------
        self.parents(id)
        Given a stream segment ID, returns the IDs of the segment's parents. If
        the segment has parents, returns a list of IDs. If the segment does not
        have parents, returns None.
        ----------
        Inputs:
            id: The queried stream segment

        Outputs:
            list[int] | None: The IDs of the parent segments
        """

        index = svalidate.id(self, id)
        parents = self._get_parents(index)
        if len(parents) == 0:
            return None
        else:
            parents = self._indices_to_ids(parents)
            return parents.tolist()

    def child(self, id: scalar) -> int | None:
        """
        Returns the ID of the queried segment's child segment
        ----------
        self.child(id)
        Given a stream segment ID, returns the ID of the segment's child segment
        as an int. If the segment does not have a child, returns None.
        ----------
        Inputs:
            id: The ID of the queried segment

        Outputs:
            int | None: The ID of the segment's child
        """

        index = svalidate.id(self, id)
        child = self._child[index]
        if child == -1:
            return None
        else:
            child = self._indices_to_ids(child)
            return int(child)

    def ancestors(self, id: scalar) -> VectorArray:
        """
        Returns the IDs of all upstream segments in a local drainage network
        ----------
        self.ancestors(id)
        For a queried stream segment ID, returns the IDs of all upstream segments
        in the local drainage network. These are the IDs of the queried segment's
        parents, the IDs of the parents parents, etc. If the queried segment does
        not have any parent segments, returns an empty array.
        ----------
        Inputs:
            id: The ID of a stream segment in the network

        Outputs:
            numpy 1D array: The IDs of all segments upstream of the queried segment
                within the local drainage network.
        """

        # Validate ID and initial ancestors with immediate parents
        segment = svalidate.id(self, id)
        ancestors = self._get_parents(segment)

        # Recursively add parents of parents
        k = 0
        while k < len(ancestors):
            index = ancestors[k]
            upstream = self._get_parents(index)
            ancestors += upstream
            k += 1

        # Convert indices to IDs and return as array
        ancestors = np.array(ancestors).reshape(-1)
        return self._indices_to_ids(ancestors)

    def descendents(self, id: scalar) -> VectorArray:
        """
        Returns the IDs of all downstream segments in a local drainage network
        ----------
        self.descendents(id)
        For a queried stream segment, returns the IDs of all downstream segments
        in the queried segment's local drainage network. This is the ID of any
        child segment, the child of that child, etc. If the queried segment does
        not have any descendents, then the returned array will be empty.
        ----------
        Inputs:
            id: The ID of the queried stream segment

        Outputs:
            numpy 1D array: The IDs of all downstream segments in the local
                drainage network.
        """

        # Validate ID and initialize descendent list
        segment = svalidate.id(self, id)
        descendents = []

        # Recursively add children of children
        child = self._child[segment]
        while child != -1:
            descendents.append(child)
            segment = child
            child = self._child[segment]

        # Convert to IDs and return as array
        descendents = np.array(descendents).reshape(-1)
        return self._indices_to_ids(descendents)

    def family(self, id: scalar) -> VectorArray:
        """
        Return the IDs of stream segments in a local drainage network
        -----------
        self.family(id)
        Returns the IDs of all stream segments in the queried segment's local
        drainage network. This includes all segments in the local network that flow
        to the queried segment's outlet, including the queried segment itself.
        Note that the returned IDs may include segments that are neither ancestors
        nor descendents of the queried segment, as the network may contain multiple
        branches draining to the same outlet.
        -----------
        Inputs:
            id: The ID of the queried stream segment

        Outputs:
            numpy 1D array: The IDs of all segments in the local drainage network.
        """

        # Locate segments in the local drainage network
        svalidate.id(self, id)
        terminus = self.termini(id)
        upstream = self.ancestors(terminus)

        # Group into family array
        family = np.empty(upstream.size + 1, upstream.dtype)
        family[0] = terminus[0]
        family[1:] = upstream
        return family

    def isnested(self, ids: Optional[vector] = None) -> SegmentValues | VectorArray:
        """
        Determines which segments are in nested drainage basins
        ----------
        self.isnested()
        Identifies segments in nested drainage basins. A nested drainage basin is
        a local drainage network that flows into another local drainage network
        further downstream. Nesting is an indication of flow discontinuity.
        Returns a 1D boolean numpy array with one element per stream segment.
        True elements indicate segments in nested networks. False elements are
        segments not in a nested network.

        self.isnested(ids)
        Determines whether the queried segments are in nested drainage basins.
        The output array will have one element per queried segment.
        ----------
        Inputs:
            ids: The IDs of the segments being queried. If unset, queries all
                segments in the network.

        Outputs:
            boolean 1D numpy array: Whether each segment is in a nested drainage
                network
        """

        # Get the unique set of outlet IDs for the queried segments
        termini = self.termini(ids)
        outlet_ids = np.unique(termini)

        # Get the basin IDs and identify nested outlets
        outlets = self.outlets(outlet_ids, as_array=True)
        basins = self._locate_basins()
        basin_ids = basins[outlets[:, 0], outlets[:, 1]]
        nested_outlets = outlet_ids[outlet_ids != basin_ids]
        return np.isin(termini, nested_outlets)

    #####
    # Rasters
    #####

    def catchment_mask(self, id: scalar) -> Raster:
        """
        Return a mask of the queried segment's catchment basin
        ----------
        self.basin_mask(id)
        Returns the catchment basin mask for the queried segment. The catchment
        basin consists of all pixels that drain into the segment. The output will
        be a boolean raster whose True elements indicate pixels that are in the
        catchment basin.
        ----------
        Inputs:
            id: The ID of the stream segment whose catchment mask should be determined

        Outputs:
            Raster: The boolean raster mask for the catchment basin. True elements
                indicate pixels that are in the catchment
        """

        svalidate.id(self, id)
        [[row, column]] = self.outlets(id, segment_outlets=True)
        return watershed.catchment(self.flow, row, column, check_flow=False)

    def raster(self, basins=False) -> Raster:
        """
        Return a raster representation of the stream network
        ----------
        self.raster()
        Returns the stream segment raster for the network. This raster has a 0
        background. Non-zero pixels indicate stream segment pixels. The value of
        each pixel is the ID of the associated stream segment.

        self.raster(basins=True)
        Returns the terminal outlet basin raster for the network. This raster has
        a 0 background. Non-zero pixels indicate terminal outlet basin pixels. The
        value of each pixel is the ID of the terminal segment associated with the
        basin. If a pixel is in multiple basins, then its value to assigned to
        the ID of the terminal segment that is farthest downstream.

        Note that you can use Segments.locate_basins to pre-build the raster
        before calling this command. If not pre-built, then this command will
        generate the terminal basin raster sequentially, which may take a while.
        Note that the "locate_basins" command includes options to parallelize
        this process, which may improve runtime.
        ----------
        Inputs:
            basins: False (default) to return the stream segment raster. True to
                return a terminal basin raster

        Outputs:
            Raster: A stream segment raster, or terminal outlet basin raster.
        """

        if basins:
            raster = self._locate_basins()
        else:
            raster = self._segments_raster()
        return Raster.from_array(
            raster, nodata=0, crs=self.crs, transform=self.transform, copy=False
        )

    def locate_basins(
        self, parallel: bool = False, nprocess: Optional[int] = None
    ) -> None:
        """
        locate_basins  Builds and saves a terminal basin raster, optionally in parallel
        ----------
        self.locate_basins()
        Builds the terminal basin raster and saves it internally. The saved
        raster will be used to quickly implement other commands that require it.
        (For example, Segments.raster, Segments.geojson, and Segments.save).
        Note that the saved raster is deleted if any of the terminal outlets are
        removed from the Segments object, so it is usually best to call this
        command *after* filtering the network.

        self.locate_basins(parallel=True)
        self.locate_basins(parallel=True, nprocess)
        Building a basin raster is computationally difficult and can take a while
        to run. Setting parallel=True allows this process to run on multiple CPUs,
        which can improve runtime. However, the use of this option imposes two
        restrictions:

        * You cannot use the "parallel" option from an interactive python session.
          Instead, the pfdf code MUST be called from a script via the command line.
          For example, something like:  $ python -m my_script
        * The code in the script must be within a
            if __name__ == "__main__":
          block. Otherwise, the parallel processes will attempt to rerun the script,
          resulting in an infinite loop of CPU process creation.

        By default, setting parallel=True will create a number of parallel processes
        equal to the number of CPUs - 1. Use the nprocess option to specify a
        different number of parallel processes. Note that you can obtain the number
        of available CPUs using os.cpu_count(). Also note that parallelization
        options are ignored if only 1 CPU is available.
        ----------
        Inputs:
            parallel: True to build the raster in parallel. False (default) to
                build sequentially.
            nprocess: The number of parallel processes. Must be a scalar, positive
                integer. Default is the number of CPUs - 1.
        """
        if self._basins is None:
            self._basins = _basins.build(self, parallel, nprocess)

    def _locate_basins(self) -> MatrixArray:
        "Returns basin raster array values"
        self.locate_basins()
        return self._basins

    def _segments_raster(self) -> MatrixArray:
        "Builds a stream segment raster array"
        raster = np.zeros(self._flow.shape, dtype="int32")
        for id, (rows, cols) in zip(self._ids, self._indices):
            raster[rows, cols] = id
        return raster

    #####
    # Generic summaries
    #####

    @staticmethod
    def statistics(asdict: bool = False) -> dict[str, str] | None:
        """
        statistics  Prints or returns info about supported statistics
        ----------
        Segments.statistics()
        Prints information about supported statistics to the console. The printed
        text is a table with two columns. The first column holds the names of
        statistics that can be used with the "summary" and "catchment_summary" methods.
        The second column is a description of each statistic.

        Segments.statistics(asdict=True)
        Returns info as a dict, rather than printing to console. The keys of the
        dict are the names of the statistics. The values are the descriptions.
        ----------
        Inputs:
            asdict: True to return info as a dict. False (default) to print info
                to the console.

        Outputs:
            None | dict[str,str]: None if printing to console. Otherwise a dict
                whose keys are statistic names, and values are descriptions.
        """

        if asdict:
            return {name: values[1] for name, values in _STATS.items()}
        else:
            print("Statistic | Description\n" "--------- | -----------")
            for name, values in _STATS.items():
                description = values[1]
                print(f"{name:9} | {description}")

    @staticmethod
    def _summarize(
        statistic: StatFunction, raster: Raster, indices: PixelIndices | BooleanMatrix
    ) -> ScalarArray:
        """Compute a summary statistic over indicated pixels. Converts NoData elements
        to NaN. Returns NaN if no data elements are selected or all elements are NaN"""

        # Get the values. Require float with at least 1 dimension
        values = raster.values[indices].astype(float)
        values = np.atleast_1d(values)

        # Set NoData values to NaN
        nodatas = NodataMask(values, raster.nodata)
        values = nodatas.fill(values, nan)

        # Return NaN if there's no data, or if everything is already NaN.
        # Otherwise, compute the statistic
        if (values.size == 0) or np.isnan(values).all():
            return np.array(nan)
        else:
            return statistic(values).reshape(1)[0]

    def _values_at_outlets(
        self, raster: Raster, terminal: bool = False
    ) -> SegmentValues:
        "Returns the values at segment outlets. Returns NoData values as NaN"

        identity = lambda input: input
        values = self._preallocate(terminal)
        if terminal:
            ids = self.terminal_ids
        else:
            ids = self.ids
        outlets = self.outlets(ids, segment_outlets=True)
        for k, outlet in enumerate(outlets):
            values[k] = self._summarize(identity, raster, indices=outlet)
        return values

    def summary(self, statistic: Statistic, values: RasterInput) -> SegmentValues:
        """
        Computes a summary value over stream segment pixels
        ----------
        self.summary(statistic, values)
        Computes a summary statistic for each stream segment. Each summary
        value is computed over the associated stream segment pixels. Returns
        the statistical summaries as a numpy 1D array with one element per segment.

        Note that NoData values are converted to NaN before computing statistics.
        If using one of the statistics that ignores NaN values (e.g. nanmean),
        a segment's summary value will still be NaN if every pixel in the stream
        segment is NaN.
        ----------
        Inputs:
            statistic: A string naming the requested statistic. See Segments.statistics()
                for info on supported statistics
            values: A raster of data values over which to compute stream segment
                summary values.

        Outputs:
            numpy 1D array: The summary statistic for each stream segment
        """

        # Validate
        statistic = validate.option(statistic, "statistic", allowed=_STATS.keys())
        values = svalidate.raster(self, values, "values raster")

        # Either get outlet values...
        if statistic == "outlet":
            return self._values_at_outlets(values)

        # ...or compute a statistical summary
        statistic = _STATS[statistic][0]
        summary = self._preallocate()
        for i, pixels in enumerate(self._indices):
            summary[i] = self._summarize(statistic, values, pixels)
        return summary

    def catchment_summary(
        self,
        statistic: Statistic,
        values: RasterInput,
        mask: Optional[RasterInput] = None,
        terminal: bool = False,
    ) -> CatchmentValues:
        """
        Computes a summary statistic over each catchment basin's pixel
        ----------
        self.catchment_summary(statistic, values)
        Computes the indicated statistic over the catchment basin pixels for each
        stream segment. Uses the input values raster as the data value for each pixel.
        Returns a numpy 1D array with one element per stream segment.

        Note that NoData values are converted to NaN before computing statistics.
        If using one of the statistics that ignores NaN values (e.g. nanmean),
        a basin's summary value will still be NaN if every pixel in the basin
        basin is NaN.

        When possible, we recommend only using the "outlet", "mean", "sum", "nanmean",
        and "nansum" statistics when computing summaries for every catchment basin.
        The remaining statistics require a less efficient algorithm, and so are much
        slower to compute. Alternatively, see below for an option to only compute
        statistics for terminal outlet basins - this is typically a faster operation,
        and more suitable for other statistics.

        self.catchment_summary(statistic, values, mask)
        Computes masked statistics over the catchment basins. True elements in the
        mask indicate pixels that should be included in statistics. False elements
        are ignored. If a catchment does not contain any True pixels, then its
        summary statistic is set to NaN. Note that a mask will have no effect
        on the "outlet" statistic.

        self.catchment_summary(..., terminal=True)
        Only computes statistics for the terminal outlet basins. The output will
        have one element per terminal segment. The order of values will match the
        order of IDs reported by the "Segments.termini" method. The number of
        terminal outlet basins is often much smaller than the total number of
        segments. As such, this option presents a faster alternative and is
        particularly suitable when computing statistics other than "outlet",
        "mean", "sum", "nanmean", or "nansum".
        ----------
        Inputs:
            statistic: A string naming the requested statistic. See Segments.statistics()
                for info on supported statistics.
            values: A raster of data values over which to compute basin summaries
            mask: An optional raster mask for the data values. True elements
                are used to compute basin statistics. False elements are ignored.
            terminal: True to only compute statistics for terminal outlet basins.
                False (default) to compute statistics for every catchment basin.

        Outputs:
            numpy 1D array: The summary statistic for each basin
        """

        # Validate
        statistic = validate.option(statistic, "statistic", allowed=_STATS.keys())
        values = svalidate.raster(self, values, "values raster")
        if mask is not None:
            mask = svalidate.raster(self, mask, "mask")
            mask = validate.boolean(mask.values, mask.name, ignore=mask.nodata)

        # Outlet values
        if statistic == "outlet":
            return self._values_at_outlets(values, terminal)

        # Sum or mean are derived from accumulation
        elif statistic in ["sum", "mean", "nansum", "nanmean"]:
            return self._accumulation_summary(statistic, values, mask, terminal)

        # Anything else needs to iterate through basin catchments
        else:
            return self._catchment_summary(statistic, values, mask, terminal)

    def _accumulation_summary(
        self,
        statistic: Literal["sum", "mean", "nansum", "nanmean"],
        values: Raster,
        mask: BooleanMatrix | None,
        terminal: bool,
    ) -> CatchmentValues:
        "Uses flow accumulation to compute basin summaries"

        # Note whether the summary should omit NaN and NoData values
        if "nan" not in statistic:
            omitnan = False
        else:
            omitnan = True

            # A mask is required to omit NaNs. Initialize if not provided.
            if mask is None:
                mask = np.ones(values.shape, dtype=bool)

            # Update the mask to ignore pixels that are NoData or NaN
            nodatas = NodataMask(values.values, values.nodata)
            if not nodatas.isnan(values.nodata):
                nodatas = nodatas | np.isnan(values.values)
            nodatas.fill(mask, False)

        # Compute sums and pixels counts. If there are no pixels, the statistic is NaN
        sums = self._accumulation(values, mask=mask, terminal=terminal, omitnan=omitnan)
        npixels = self._accumulation(mask=mask, terminal=terminal)
        sums[npixels == 0] = nan

        # Return the sum or mean, as appropriate
        if "sum" in statistic:
            return sums
        else:
            return sums / npixels

    def _catchment_summary(
        self,
        statistic: Statistic,
        values: Raster,
        mask: Raster | None,
        terminal: bool,
    ) -> CatchmentValues:
        "Iterates through basin catchments to compute summaries"

        # Get statistic, preallocate, and locate catchment outlets
        statistic = _STATS[statistic][0]
        summary = self._preallocate(terminal=terminal)
        ids = self.ids
        if terminal:
            ids = ids[self.isterminal()]
        outlets = self.outlets(ids, segment_outlets=True)

        # Iterate through catchment basins and compute summaries
        for k, outlet in enumerate(outlets):
            catchment = watershed.catchment(self.flow, *outlet, check_flow=False)
            catchment = catchment.values
            if mask is not None:
                catchment = catchment & mask
            summary[k] = self._summarize(statistic, values, catchment)
        return summary

    #####
    # Earth system variables
    #####

    def area(
        self,
        mask: Optional[RasterInput] = None,
        *,
        units: Units = "kilometers",
        terminal: bool = False,
    ) -> CatchmentValues:
        """
        Returns catchment areas
        ----------
        self.area()
        self.area(..., *, units)
        self.area(..., *, terminal=True)
        Computes the total area of the catchment basin for each stream segment.
        By default, returns areas in kilometers^2. Use the "units" option to
        return areas in other units (squared) instead. Supported units include:
        "base" (CRS base units), "meters", "kilometers", "feet", and "miles".
        By default, returns an area for each segment in the network. Set terminal=True
        to only return values for the terminal outlet basins.

        self.area(mask)
        Computes masked areas for the basins. True elements in the mask indicate
        pixels that should be included in the calculation of areas. False pixels
        are ignored and given an area of 0. Nodata elements are interpreted as False.
        ----------
        Inputs:
            mask: A raster mask whose True elements indicate the pixels that should
                be used to compute upslope areas.
            units: The units (squared) in which to return areas. Options include:
                "base" (CRS base units), "meters", "kilometers" (default), "feet",
                and "miles".
            terminal: True to only compute values for terminal outlet basins.
                False (default) to compute values for all catchment basins.

        Outputs:
            numpy 1D array: The catchment area for each stream segment
        """

        units = validate.units(units)
        if mask is None:
            N = self._basin_npixels(terminal)
        else:
            N = self._accumulation(mask=mask, terminal=terminal)
        return N * self.flow.pixel_area(units)

    def burn_ratio(
        self, isburned: RasterInput, terminal: bool = False
    ) -> CatchmentValues:
        """
        Returns the proportion of burned pixels in basins
        ----------
        self.burn_ratio(isburned)
        self.burn_ratio(..., terminal=True)
        Given a mask of burned pixel locations, determines the proportion of
        burned pixels in the catchment basin of each stream segment. Ratios are
        on the interval from 0 to 1. By default, returns a numpy 1D array with
        the ratio for each segment. Set terminal=True to only return values for
        the terminal outlet basins.
        ----------
        Inputs:
            isburned: A raster mask whose True elements indicate the locations
                of burned pixels in the watershed.
            terminal: True to only compute values for terminal outlet basins.
                False (default) to compute values for all catchment basins.

        Outputs:
            numpy 1D array: The proportion of burned pixels in each basin
        """
        return self.catchment_ratio(isburned, terminal)

    def burned_area(
        self,
        isburned: RasterInput,
        *,
        units: Units = "kilometers",
        terminal: bool = False,
    ) -> CatchmentValues:
        """
        Returns the total burned area of basins
        ----------
        self.burned_area(isburned)
        self.burned_area(..., *, units)
        self.burned_area(..., *, terminal=True)
        Given a mask of burned pixel locations, returns the total burned area in
        the catchment of each stream segment. By default, returns areas in kilometers^2.
        Use the "units" option to return areas in other units (squared) instead.
        Supported units include: "base" (CRS base units), "meters", "kilometers",
        "feet", and "miles". By default, returns the burned catchment area for
        each segment in the network. Set terminal=True to only return values for
        the terminal outlet basins.
        ----------
        Inputs:
            isburned: A raster mask whose True elements indicate the locations of
                burned pixels within the watershed
            units: The units (squared) in which to return areas. Options include:
                "base" (CRS base units), "meters", "kilometers" (default), "feet",
                and "miles".
            terminal: True to only compute values for terminal outlet basins.
                False (default) to compute values for all catchment basins.

        Outputs:
            numpy 1D array: The burned catchment area for the basins
        """
        return self.area(isburned, units=units, terminal=terminal)

    def catchment_ratio(
        self, mask: RasterInput, terminal: bool = False
    ) -> CatchmentValues:
        """
        Returns the proportion of catchment pixels within a mask
        ----------
        self.catchment_ratio(mask)
        Given a raster mask, computes the proportion of True pixels in the
        catchment basin for each stream segment. Returns the ratios as a numpy 1D
        array with one element per stream segment. Ratios will be on the interval
        from 0 to 1. Note that NoData pixels in the mask are interpreted as False.

        self.catchment_ratio(mask, terminal=True)
        Only computes values for the terminal outlet basins.
        ----------
        Inputs:
            mask: A raster mask for the watershed. The method will compute the
                proportion of True elements in each catchment
            terminal: True to only compute values for the terminal outlet basins.
                False (default) to compute values for all catchment basins.

        Outputs:
            numpy 1D array: The proportion of True values in each catchment basin
        """
        counts = self._accumulation(mask=mask, terminal=terminal)
        npixels = self._basin_npixels(terminal)
        return counts / npixels

    def confinement(
        self,
        dem: RasterInput,
        neighborhood: scalar,
        dem_per_m: Optional[scalar] = None,
    ) -> SegmentValues:
        """
        Returns the mean confinement angle of each stream segment
        ----------
        self.confinement(dem, neighborhood)
        self.confinement(..., dem_per_m)
        Computes the mean confinement angle for each stream segment. Returns these
        angles as a numpy 1D array. The order of angles matches the order of
        segment IDs in the object.

        The confinement angle for a given pixel is calculated using the slopes in the
        two directions perpendicular to stream flow. A given slope is calculated using
        the maximum DEM height within N pixels of the processing pixel in the
        associated direction. Here, the number of pixels searched in each direction
        (N) is equivalent to the "neighborhood" input. The slope equation is thus:

            slope = max height(N pixels) / (N * length)

        where length is one of the following:
            * X axis resolution (for flow along the Y axis)
            * Y axis resolution (for flow along the X axis)
            * length of a raster cell diagonal (for diagonal flow)
        Recall that slopes are computed perpendicular to the flow direction,
        hence the use X axis resolution for Y axis flow and vice versa.

        The confinment angle is then calculated using:

            theta = 180 - tan^-1(slope1) - tan^-1(slope2)

        and the mean confinement angle is calculated over all the pixels in the
        stream segment.

        Example:
        Consider a pixel flowing east with neighborhood=4. (East here indicates
        that the pixel is flowing to the next pixel on its right - it is not an
        indication of actual geospatial directions). Confinement angles are then
        calculated using slopes to the north and south. The north slope is
        determined using the maximum DEM height in the 4 pixels north of the
        stream segment pixel, such that:

            slope = max height(4 pixels north) / (4 * Y axis resolution)

        and the south slope is computed similarly. The two slopes are used to
        compute the confinement angle for the pixel, and this process is then
        repeated for all pixels in the stream segment. The final value for the
        stream segment will be the mean of these values.

        By default, this routine assumes that the DEM units are meters. If this
        is not the case, then use the "dem_per_m" to specify a conversion factor
        (number of DEM units per meter).
        ----------
        Inputs:
            dem: A raster of digital elevation model (DEM) data. Should have
                square pixels.
            neighborhood: The number of raster pixels to search for maximum heights.
                Must be a positive integer.
            dem_per_m: A conversion factor from DEM units to meters

        Outputs:
            numpy 1D array: The mean confinement angle for each stream segment.
        """
        return _confinement.angles(self, dem, neighborhood, dem_per_m)

    def developed_area(
        self,
        isdeveloped: RasterInput,
        *,
        units: Units = "kilometers",
        terminal: bool = False,
    ) -> CatchmentValues:
        """
        developed_area  Returns the total developed area of basins
        ----------
        self.developed_area(isdeveloped)
        self.developed_area(..., *, units)
        self.developed_area(..., *, terminal=True)
        Given a mask of developed pixel locations, returns the total developed
        area in the catchment of each stream segment. By default, returns areas in kilometers^2.
        Use the "units" option to return areas in other units (squared) instead.
        Supported units include: "base" (CRS base units), "meters", "kilometers",
        "feet", and "miles". By default, returns the burned catchment area for
        each segment in the network. Set terminal=True to only return values for
        the terminal outlet basins.
        ----------
        Inputs:
            isdeveloped: A raster mask whose True elements indicate the locations
                of developed pixels within the watershed.
            units: The units (squared) in which to return areas. Options include:
                "base" (CRS base units), "meters", "kilometers" (default), "feet",
                and "miles".
            terminal: True to only compute values for terminal outlet basins.
                False (default) to compute values for all catchment basins.

        Outputs:
            numpy 1D array: The developed catchment area for each basin
        """
        return self.area(isdeveloped, units=units, terminal=terminal)

    def in_mask(self, mask: RasterInput, terminal: bool = False) -> SegmentValues:
        """
        Determines whether segments have pixels within a mask
        ----------
        self.in_mask(mask)
        self.in_mask(mask, terminal=True)
        Given a raster mask, returns a boolean 1D numpy array with one element
        per segment. True elements indicate segments that have at least one pixel
        within the mask. False elements have no pixels within the mask. If
        terminal=True, only returns values for the terminal segments.
        ----------
        Inputs:
            mask: A raster mask for the watershed.
            terminal: True to only return values for terminal segments.
                False (default) to return values for all segments.

        Outputs:
            boolean 1D numpy array: Whether each segment has at least one pixel
                within the mask.
        """

        mask = svalidate.raster(self, mask, "mask")
        validate.boolean(mask.values, "mask", ignore=mask.nodata)
        isin = self.summary("nanmax", mask) == 1
        if terminal:
            isin = isin[self.isterminal()]
        return isin

    def in_perimeter(
        self, perimeter: RasterInput, terminal: bool = False
    ) -> SegmentValues:
        """
        Determines whether segments have pixels within a fire perimeter
        ----------
        self.in_perimeter(perimeter)
        self.in_perimeter(perimeter, terminal=True)
        Given a fire perimeter mask, returns a boolean 1D numpy array with one
        element per segment. True elements indicate segments that have at least
        one pixel within the fire perimeter. False elements have no pixels within
        the mask. If terminal=True, only returns values for the terminal segments.
        ----------
        Inputs:
            perimeter: A fire perimeter raster mask
            terminal: True to only return values for terminal segments.
                False (default) to return values for all segments.

        Outputs:
            boolean 1D numpy array: Whether each segment has at least one pixel
                within the fire perimeter.
        """
        return self.in_mask(perimeter, terminal)

    def kf_factor(
        self,
        kf_factor: RasterInput,
        mask: Optional[RasterInput] = None,
        *,
        terminal: bool = False,
        omitnan: bool = False,
    ) -> CatchmentValues:
        """
        kf_factor  Computes mean soil KF-factor for basins
        ----------
        self.kf_factor(kf_factor)
        Computes the mean catchment KF-factor for each stream segment in the
        network. Note that the KF-Factor raster must have all positive values.
        If a catchment basin contains NaN or NoData values, then its mean KF-Factor
        is set to NaN.

        self.kf_factor(kf_factor, mask)
        Also specifies a data mask for the watershed. True elements of the mask
        are used to compute mean KF-Factors. False elements are ignored. If a
        basin only contains False elements, then its mean Kf-factor is set
        to NaN.

        self.kf_factor(..., *, omitnan=True)
        Ignores NaN and NoData values when computing mean KF-factors. If a basin
        only contains NaN and/or NoData values, then its mean KF-factor will still
        be NaN.

        self.kf_factor(..., *, terminal=True)
        Only computes values for the terminal outlet basins.
        ----------
        Inputs:
            kf_factor: A raster of soil KF-factor values. Cannot contain negative
                elements.
            mask: A raster mask whose True elements indicate the pixels that should
                be used to compute mean KF-factors
            omitnan: True to ignore NaN and NoData values. If False (default),
                any basin with (unmasked) NaN or NoData values will have its mean
                Kf-factor set to NaN.
            terminal: True to only compute values for terminal outlet basins.
                False (default) to compute values for all catchment basins.

        Outputs:
            numpy 1D array: The mean catchment KF-Factor for each basin
        """

        # Validate
        kf_factor = svalidate.raster(self, kf_factor, "kf_factor")
        validate.positive(kf_factor.values, "kf_factor", ignore=[kf_factor.nodata, nan])

        # Summarize
        if omitnan:
            method = "nanmean"
        else:
            method = "mean"
        return self.catchment_summary(
            method,
            kf_factor,
            mask,
            terminal,
        )

    def length(
        self, *, units: Units = "meters", terminal: bool = False
    ) -> SegmentValues:
        """
        Returns the length of each stream segment
        ----------
        self.length()
        self.length(*, units)
        self.length(*, terminal=True)
        Returns the length of each stream segment in the network. By default,
        returns lengths in meters. Use the "units" option to return lengths in
        other units. Supported units include: "base" (CRS base units), "meters",
        "kilometers", "feet", and "miles". By default, returns a numpy 1D array
        with one element per segment. Set terminal=True to only return values
        for the terminal outlet segments.
        ----------
        Inputs:
            units: Indicates the units in which to return segment lengths. Options
                include: "base" (CRS base units), "meters" (default), "kilometers",
                "feet", and "miles".
            terminal: True to only return the lengths of terminal outlet segments.
                False (default) to return the length of every segment in the network

        Outputs:
            numpy 1D array: The lengths of the segments in the network
        """
        units = validate.units(units)
        lengths = np.array([segment.length for segment in self._segments])
        if terminal:
            lengths = lengths[self.isterminal()]
        if units != "base":
            lengths = crs.base_to_units(self.crs, "y", lengths, units)
        return lengths

    def scaled_dnbr(
        self,
        dnbr: RasterInput,
        mask: Optional[RasterInput] = None,
        *,
        terminal: bool = False,
        omitnan: bool = False,
    ) -> CatchmentValues:
        """
        scaled_dnbr  Computes mean catchment dNBR / 1000 for basins
        ----------
        self.scaled_dnbr(dnbr)
        Computes mean catchment dNBR for each stream segment in the network.
        These mean dNBR values are then divided by 1000 to place dNBR values
        roughly on the interval from 0 to 1. Returns the scaled dNBR values as a
        numpy 1D array. If a basin contains NaN or NoData values, then its dNBR
        value is set to NaN.

        self.scaled_dnbr(dnbr, mask)
        Also specifies a data mask for the watershed. True elements of the mask
        are used to compute scaled dNBR values. False elements are ignored. If a
        catchment only contains False elements, then its scaled dNBR value is set
        to NaN.

        self.scaled_dnbr(..., *, omitnan=True)
        Ignores NaN and NoData values when computing scaled dNBR values. However,
        if a basin only contains these values, then its scaled dNBR value will
        still be NaN.

        self.scaled_dnbr(..., *, terminal=True)
        Only computes values for the terminal outlet basins.
        ----------
        Inputs:
            dnbr: A dNBR raster for the watershed
            mask: A raster mask whose True elements indicate the pixels that should
                be used to compute scaled dNBR
            omitnan: True to ignore NaN and NoData values. If False (default),
                any basin with (unmasked) NaN or NoData values will have its value
                set to NaN.
            terminal: True to only compute values for terminal outlet basins.
                False (default) to compute values for all catchment basins.

        Outputs:
            numpy 1D array: The mean catchment dNBR/1000 for the basins
        """

        if omitnan:
            method = "nanmean"
        else:
            method = "mean"
        dnbr = self.catchment_summary(method, dnbr, mask, terminal)
        return dnbr / 1000

    def scaled_thickness(
        self,
        soil_thickness: RasterInput,
        mask: Optional[RasterInput] = None,
        *,
        omitnan: bool = False,
        terminal: bool = False,
    ) -> CatchmentValues:
        """
        scaled_thickness  Computes mean catchment soil thickness / 100 for basins
        ----------
        self.scaled_thickness(soil_thickness)
        Computes mean catchment soil-thickness for each segment in the network.
        Then divides these values by 100 to place soil thicknesses approximately
        on the interval from 0 to 1. Returns a numpy 1D array with the scaled soil
        thickness values for each segment. Note that the soil thickness raster
        must have all positive values.

        self.scaled_thickness(soil_thickness, mask)
        Also specifies a data mask for the watershed. True elements of the mask
        are used to compute mean soil thicknesses. False elements are ignored. If
        a catchment only contains False elements, then its scaled soil thickness
        is set to NaN.

        self.scaled_thickness(..., *, omitnan=True)
        Ignores NaN and NoData values when computing scaled soil thickness values.
        However, if a basin only contains NaN and NoData, then its scaled soil
        thickness will still be NaN.

        self.scaled_thickness(..., *, terminal=True)
        Only computes values for the terminal outlet basins.
        ----------
        Inputs:
            soil_thickess: A raster with soil thickness values for the watershed.
                Cannot contain negative values.
            mask: A raster mask whose True elements indicate the pixels that should
                be used to compute scaled soil thicknesses
            omitnan: True to ignore NaN and NoData values. If False (default),
                any basin with (unmasked) NaN or NoData values will have its value
                set to NaN.
            terminal: True to only compute values for terminal outlet basins.
                False (default) to compute values for all catchment basins.

        Outputs:
            numpy 1D array: The mean catchment soil thickness / 100 for each basin
        """

        # Validate
        soil_thickness = svalidate.raster(self, soil_thickness, "soil_thickness")
        validate.positive(
            soil_thickness.values, "soil_thickness", ignore=[soil_thickness.nodata, nan]
        )

        # Summarize
        if omitnan:
            method = "nanmean"
        else:
            method = "mean"
        soil_thickness = self.catchment_summary(method, soil_thickness, mask, terminal)
        return soil_thickness / 100

    def sine_theta(
        self,
        sine_thetas,
        mask: Optional[RasterInput] = None,
        *,
        omitnan: bool = False,
        terminal: bool = False,
    ) -> CatchmentValues:
        """
        sine_theta  Computes the mean sin(theta) value for each segment's catchment
        ----------
        self.sine_theta(sine_thetas)
        Given a raster of watershed sin(theta) values, computes the mean sin(theta)
        value for each stream segment catchment. Here, theta is the slope angle. Note
        that the pfdf.utils.slope module provides utilities for converting from
        slope gradients (rise/run) to other slope measurements, including
        sin(theta) values. All sin(theta) values should be on the interval from
        0 to 1. Returns a numpy 1D array with the sin(theta) values for each segment.

        self.sine_theta(sine_thetas, mask)
        Also specifies a data mask for the watershed. True elements of the mask
        are used to compute mean sin(theta) values. False elements are ignored.
        If a catchment only contains False elements, then its sin(theta) value
        is set to NaN.

        self.sine_theta(..., *, omitnan=True)
        Ignores NaN and NoData values when computing mean sine theta values.
        However, if a basin only contains NaN and NoData, then its sine theta
        value will still be NaN.

        self.sine_theta(..., terminal=True)
        Only computes values for the terminal outlet basins.
        ----------
        Inputs:
            sine_thetas: A raster of sin(theta) values for the watershed
            mask: A raster mask whose True elements indicate the pixels that should
                be used to compute sin(theta) values
            omitnan: True to ignore NaN and NoData values. If False (default),
                any basin with (unmasked) NaN or NoData values will have its value
                set to NaN.
            terminal: True to only compute values for terminal outlet basins.
                False (default) to compute values for all catchment basins.

        Outputs:
            numpy 1D array: The mean sin(theta) value for each basin
        """

        # Validate
        sine_thetas = svalidate.raster(self, sine_thetas, "sine_thetas")
        validate.inrange(
            sine_thetas.values,
            sine_thetas.name,
            min=0,
            max=1,
            ignore=[sine_thetas.nodata, nan],
        )

        # Summarize
        if omitnan:
            method = "nanmean"
        else:
            method = "mean"
        return self.catchment_summary(method, sine_thetas, mask, terminal)

    def slope(
        self, slopes: RasterInput, *, terminal: bool = False, omitnan: bool = False
    ) -> SegmentValues:
        """
        slope  Returns the mean slope (rise/run) for each segment
        ----------
        self.slope(slopes)
        self.slope(..., *, terminal=True)
        Given a raster of slope gradients (rise/run), returns the mean slope for each
        segment as a numpy 1D array. If a stream segment's pixels contain NaN or
        NoData values, then the slope for the segment is set to NaN. If terminal=True,
        only returns values for the terminal segments.

        self.slope(..., *, omitnan=True)
        Ignores NaN and NoData values when computing mean slope. However, if a
        segment only contains NaN and NoData values, then its value will still
        be NaN.
        ----------
        Inputs:
            slopes: A slope gradient (rise/run) raster for the watershed
            terminal: True to only return values for terminal segments.
                False (default) to return values for all segments.

        Outputs:
            numpy 1D array: The mean slopes for the segments.
        """
        if omitnan:
            method = "nanmean"
        else:
            method = "mean"
        slopes = self.summary(method, slopes)
        if terminal:
            slopes = slopes[self.isterminal()]
        return slopes

    def relief(self, relief: RasterInput, terminal: bool = False) -> SegmentValues:
        """
        relief  Returns the vertical relief for each segment
        ----------
        self.relief(relief)
        self.relief(relief, terminal=True)
        Returns the vertical relief between each stream segment's outlet and the
        nearest ridge cell as a numpy 1D array. If terminal=True, only returns
        values for the terminal segments.
        ----------
        Inputs:
            relief: A vertical relief raster for the watershed
            terminal: True to only return values for terminal segments.
                False (default) to return values for all segments.

        Outputs:
            numpy 1D array: The vertical relief for each segment
        """

        relief = svalidate.raster(self, relief, "relief")
        relief = self._values_at_outlets(relief)
        if terminal:
            relief = relief[self.isterminal()]
        return relief

    def ruggedness(
        self,
        relief: RasterInput,
        relief_per_m: Optional[scalar] = None,
        *,
        terminal: bool = False,
    ) -> SegmentValues:
        """
        Returns the ruggedness of each stream segment catchment
        ----------
        self.ruggedness(relief)
        self.ruggedness(relief, relief_per_m)
        Returns the ruggedness of the catchment for each stream segment in the
        network in units of meters^-1. Ruggedness is defined as a stream segment's
        vertical relief, divided by the square root of its catchment area. By default,
        interprets relief values as meters. If this is not the case, use the
        "relief_per_m" option to provide a conversion factor between relief units
        and meters. This ensures that ruggedness values are scaled correctly.

        self.ruggedness(..., terminal=True)
        Only returns values for the terminal segments.
        ----------
        Inputs:
            relief: A vertical relief raster for the watershed
            relief_per_m: A conversion factor between relief units and meters
            terminal: True to only return values for terminal segments.
                False (default) to return values for all segments.

        Outputs:
            numpy 1D array: The topographic ruggedness of each stream segment
        """

        relief_per_m = validate.conversion(relief_per_m, "relief_per_m")
        area = self.area(units="meters", terminal=terminal)
        relief = self.relief(relief, terminal=terminal)
        if relief_per_m is not None:
            relief = relief / relief_per_m
        return relief / np.sqrt(area)

    #####
    # Filtering
    #####

    @staticmethod
    def _removable(
        requested: BooleanIndices,
        child: SegmentValues,
        parents: SegmentParents,
        keep_upstream: bool,
        keep_downstream: bool,
    ) -> BooleanIndices:
        "Returns the indices of requested segments on the edges of their local networks"

        edge = False
        if not keep_downstream:
            edge = edge | (child == -1)
        if not keep_upstream:
            edge = edge | (parents == -1).all(axis=1)
        return requested & edge

    def continuous(
        self,
        selected: Selection,
        type: SelectionType = "indices",
        *,
        remove: bool = False,
        keep_upstream: bool = False,
        keep_downstream: bool = False,
    ) -> SegmentValues:
        """
        Indicates segments that can be filtered while preserving flow continuity
        ----------
        self.continuous(selected)
        self.continuous(..., *, remove=True)
        self.continuous(..., type="ids")
        Given a selection of segments that will be filtered using the "keep" or
        "remove" commands, returns the boolean indices of segments that can be
        filtered while preserving flow continuity. By default, assumes that the
        selected segments are for use with the "keep" command. Set remove=True
        to indicate that selected segments are for use with the "remove" command
        instead.

        By default, expects the selected segments to be a boolean numpy 1D array
        with one element per segment in the network. True/False elements should
        indicate segments for the keep/remove commands, as appropriate. Set
        type="ids" to select segments using segment IDs instead. In this case,
        the selected segments should be a list or numpy 1D array whose elements
        are the IDs of the segments selected for filtering.

        self.continuous(..., *, keep_upstream=True)
        self.continuous(..., *, keep_downstream=True)
        Further customizes the flow continuity algorithm. Set keep_upstream=True
        to always retain segments on the upstream end of a local drainage network.
        Set keep_downstream=True to always retain segments on the downstream end
        of a local drainage network.
        ----------
        Inputs:
            selected: The segments being selected for filtering
            type: "indices" (default) to select segments using a boolean vector.
                "ids" to select segments using segments IDs
            remove: True to indicate that segments are selected for removal.
                False (default) to indicate that selected segments should be kept.
            keep_upstream: True to always retain segments on the upstream end of
                a local drainage network. False (default) to treat as usual.
            keep_downstream: True to always retain segments on the downstream end
                of a local drainage network. False (default) to treat as usual.

        Outputs:
            boolean 1D numpy array: The boolean indices of segments that can be
                filtered while preserving flow continuity. If remove=False (default),
                then True elements indicate segments that should be retained in
                the network. If remove=True, then True elements indicate segments
                that should be removed from the network.
        """

        # Get the segments requested for removal
        requested_remove = svalidate.selection(self, selected, type)
        if not remove:
            requested_remove = ~requested_remove

        # Initialize segments actually being removed. Get working copies of
        # parent-child relationships.
        final_remove = np.zeros(self.size, bool)
        child = self._child.copy()
        parents = self._parents.copy()

        # Iteratively select requested segments on the edges of their local networks.
        # Update child-parent segments and repeat for new edge segments
        removable = self._removable(
            requested_remove, child, parents, keep_upstream, keep_downstream
        )
        while np.any(removable):
            final_remove[removable] = True
            requested_remove[removable] = False
            _update.family(child, parents, removable)
            removable = self._removable(
                requested_remove, child, parents, keep_upstream, keep_downstream
            )

        # Return keep/remove indices as appropriate
        if remove:
            return final_remove
        else:
            return ~final_remove

    def remove(self, selected: Selection, type: SelectionType = "indices") -> None:
        """
        Remove segments from the network
        ----------
        self.remove(selected)
        self.remove(selected, type="ids")
        Removes the indicated segments from the network. By default, expects a
        boolean numpy 1D array with one element per segment in the network. True
        elements indicate segments that should be removed, and False elements
        are segments that should be retained.

        Set type="ids" to select segments using IDs, rather than a boolean vector.
        In this case, the input should be a list or numpy 1D array whose elements
        are the IDs of the segments that should be removed from the network.

        Note that removing terminal outlet segments can cause any previously located
        basins to be deleted. As such we recommend calling the "locate_basins"
        command after this command.
        ----------
        Inputs:
            selected: The segments that should be removed from the network
            type: "indices" (default) to select segments using a boolean vector.
                "ids" to select segments using segments IDs
        """

        # Validate. Get segments being kept / removed
        remove = svalidate.selection(self, selected, type)
        keep = ~remove

        # Compute new attributes
        segments, indices = _update.segments(self, remove)
        ids = self.ids[keep]
        npixels = self.npixels[keep]
        child, parents = _update.connectivity(self, remove)
        basins = _update.basins(self, remove)

        # Update object
        self._segments = segments
        self._ids = ids
        self._indices = indices
        self._npixels = npixels
        self._child = child
        self._parents = parents
        self._basins = basins

    def keep(self, selected: Selection, type: SelectionType = "indices") -> None:
        """
        Restricts the network to the indicated segments
        ----------
        self.keep(selected)
        self.keep(selected, type="ids")
        Restricts the network to the indicated segments, discarding all other
        segments. By default, expects a boolean numpy 1D array with one element
        per segment in the network. True elements indicate segments that should
        be retained, and False elements are segments that should be discarded.

        Set type="ids" to select segments using IDs, rather than a boolean vector.
        In this case, the input should be a list or numpy 1D array whose elements
        are the IDs of the segments that should be retained in the network.

        Note that discarding terminal outlet segments can cause any previously
        located basins to be deleted. As such, we recommend calling "locate_basins"
        after this command.
        ----------
        Inputs:
            selected: The segments that should be retained in the network
            type: "indices" (default) to select segments using a boolean vector.
                "ids" to select segments using segments IDs
        """

        keep = svalidate.selection(self, selected, type)
        self.remove(~keep)

    def copy(self) -> Segments:
        """
        copy  Returns a copy of a Segments object
        ----------
        self.copy()
        Returns a copy of the current Segments object. Stream segments can be
        removed from the new/old objects without affecting one another. Note that
        the flow direction raster and saved basin rasters are not duplicated in
        memory. Instead, both objects reference the same underlying array.
        ----------
        Outputs:
            Segments: A copy of the current Segments object.
        """

        copy = super().__new__(Segments)
        copy._flow = self._flow
        copy._segments = self._segments.copy()
        copy._ids = self._ids.copy()
        copy._indices = self._indices.copy()
        copy._npixels = self._npixels.copy()
        copy._child = self._child.copy()
        copy._parents = self._parents.copy()
        copy._basins = None
        copy._basins = self._basins
        return copy

    #####
    # Export
    #####

    def geojson(
        self,
        type: ExportType = "segments",
        properties: Optional[PropertyDict] = None,
        *,
        crs: Optional[CRS] = None,
    ) -> FeatureCollection:
        """
        geosjon  Exports the network to a geojson.FeatureCollection object
        ----------
        self.geojson()
        self.geojson(type='segments')
        Exports the network to a geojson.FeatureCollection object. The individual
        Features have LineString geometries whose coordinates proceed from upstream
        to downstream. Will have one feature per stream segment.

        self.geojson(type='basins')
        Exports terminal outlet basins as a collection of Polygon features. The
        number of features will be <= the number of local drainage networks.
        (The number of features will be < the number of local networks if there
        are nested drainage networks).

        Note that you can use Segments.locate_basins to pre-locate the basins
        before calling this command. If not pre-located, then this command will
        locate the basins sequentially, which may take a while. Note that the
        "locate_basins" command includes options to parallelize this process,
        which may improve runtime.

        self.geojson(type='outlets')
        self.geojson(type='segment outlets')
        Exports outlet points as a collection of Point features. If type="outlets",
        exports the terminal outlet points, which will have one feature per local
        drainage network. If type="segment outlets", exports the complete set of
        outlet points, which will have one feature per segment in the network.

        self.geojson(..., properties)
        Specifies data properties for the GeoJSON features. The "properties" input
        should be a dict. Each key should be a string and will be interpreted as
        the name of the associated property field. Each value should be a numpy
        1D array with a boolean, integer, floating, or string dtype. Boolean
        values are converted to integers in the output GeoJSON object.

        If exporting segments or segment outlets, then each array should have one
        element per segment in the network. If exporting outlets or basins, each
        array may have either (1) one element per segment in the network, or (2)
        one outlet per terminal segment in the network. If using one element per
        segment, extracts the values for the terminal segments prior to GeoJSON export.

        self.geojson(..., *, crs)
        Specifies the CRS of the output geometries. By default, returns geometries
        in the CRS of the flow direction raster used to derive the network. Use
        this option to return geometries in a different CRS instead. The "crs" input
        may be a pyproj.CRS, any input convertible to a pyproj.CRS, or a Raster /
        RasterMetadata object with a defined CRS.
        ----------
        Inputs:
            type: A string indicating the type of feature to export. Options are
                "segments", "basins", "outlets", or "segment outlets"
            properties: A dict whose keys are the (string) names of the property
                fields. Each value should be a numpy 1D array with a boolean,
                integer, floating, or string dtype. Each array may have one element
                per segment (any type of export), or one element per local drainage
                network (basins and outlets only).
            crs: The CRS of the output geometries. Defaults to the CRS of the
                flow-direction raster used to derive the network.

        Outputs:
            geojson.FeatureCollection: The collection of stream network features
        """
        return _geojson.features(self, type, properties, crs)[0]

    def save(
        self,
        path: Pathlike,
        type: ExportType = "segments",
        properties: Optional[PropertyDict] = None,
        *,
        crs: Optional[CRS] = None,
        driver: Optional[str] = None,
        overwrite: bool = False,
    ) -> Path:
        """
        Saves the network to a vector feature file
        ----------
        self.save(path)
        self.save(path, type='segments')
        self.save(..., *, overwrite=True)
        Saves the network to the indicated path. Each segment is saved as a vector
        feature with a LineString geometry whose coordinates proceed from upstream
        to downstream. The vector features will not have any data properties. In
        the default state, the method will raise a FileExistsError if the file
        already exists. Set overwrite=True to enable the replacement of existing
        files. Returns the absolute path to the saved file as output.

        By default, the method will attempt to guess the intended file format based
        on the path extensions, and will raise an Exception if the file format
        cannot be guessed. However, see below for a syntax to specify the driver,
        regardless of extension. You can use:
            >>> pfdf.utils.driver.extensions('vector')
        to return a summary of supported file format drivers, and their associated
        extensions.

        self.save(path, type='basins', ...)
        Saves the terminal outlet basins as a collection of Polygon features.
        The number of features will be <= the number of local drainage networks.
        (The number of features will be < the number of local networks if there
        are nested drainage networks).

        Note that you can use Segments.locate_basins to pre-locate the basins
        before calling this command. If not pre-located, then this command will
        locate the basins sequentially, which may take a while. Note that the
        "locate_basins" command includes options to parallelize this process,
        which may improve runtime.

        self.save(path, type='outlets', ...)
        self.save(path, type='segment outlets', ...)
        Saves outlet points as a collection of Point features. If type="outlets",
        saves the terminal outlet points, which will have one feature per local
        drainage network. If type="segment outlets", saves the complete set of
        outlet points, which will have one feature per segment in the network.

        self.save(..., properties)
        Specifies data properties for the saved features. The "properties" input
        should be a dict. Each key should be a string and will be interpreted as
        the name of the associated property field. Each value should be a numpy
        1D array with a boolean, integer, floating, or string dtype. Boolean
        values are converted to integers in the output GeoJSON object.

        If exporting segments or segment outlets, then each array should have one
        element per segment in the network. If exporting outlets or basins, each
        array may have either (1) one element per segment in the network, or (2)
        one outlet per terminal segment in the network. If using one element per
        segment, extracts the values for the terminal segments prior to saving.

        self.save(..., *, crs)
        Specifies the CRS of the output file. By default, uses the CRS of the flow
        direction raster used to derive the network. Use this option to export
        results in a different CRS instead. The "crs" input may be a pyproj.CRS, any
        input convertible to a pyproj.CRS, or a Raster/RasterMetadata object with a
        defined CRS.

        self.save(..., *, driver)
        Specifies the file format driver to used to write the vector feature file.
        Uses this format regardless of the file extension. You can call:
            >>> pfdf.utils.driver.vectors()
        to return a summary of file format drivers that are expected to always work.

        More generally, the pfdf package relies on fiona (which in turn uses GDAL/OGR)
        to write vector files, and so additional drivers may work if their
        associated build requirements are met. You can call:
            >>> fiona.drvsupport.vector_driver_extensions()
        to summarize the drivers currently supported by fiona, and a complete
        list of driver build requirements is available here:
        https://gdal.org/drivers/vector/index.html
        ----------
        Inputs:
            path: The path to the output file
            type: A string indicating the type of feature to export. Options are
                "segments", "basins", "outlets", or "segment outlets"
            properties: A dict whose keys are the (string) names of the property
                fields. Each value should be a numpy 1D array with a boolean,
                integer, floating, or string dtype. Each array may have one element
                per segment (any type of export), or one element per local drainage
                network (basins and outlets only).
            crs: The CRS of the output file. Defaults to the CRS of the flow-direction
                raster used to derive the network.
            overwrite: True to allow replacement of existing files. False (default)
                to prevent overwriting.
            driver: The name of the file-format driver to use when writing the
                vector feature file. Uses this driver regardless of file extension.

        Outputs:
            Path: The path to the saved file
        """

        # Validate and get features as geojson
        path = validate.output_file(path, overwrite)
        collection, property_schema, crs = _geojson.features(
            self, type, properties, crs
        )

        # Build the file schema
        geometries = {
            "segments": "LineString",
            "basins": "Polygon",
            "outlets": "Point",
            "segment outlets": "Point",
        }
        schema = {
            "geometry": geometries[type],
            "properties": property_schema,
        }

        # Write file
        records = collection["features"]
        with fiona.open(path, "w", driver=driver, crs=crs, schema=schema) as file:
            file.writerecords(records)
        return path
