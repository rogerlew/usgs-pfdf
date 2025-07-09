"""
Classes that define custom exceptions
----------
Numpy Arrays:
    ArrayError              - Generic class for invalid numpy arrays
    EmptyArrayError         - When a numpy array has no elements
    DimensionError          - When a numpy array has invalid nonsingleton dimensions
    ShapeError              - When a numpy axis has the wrong length

Metadata:
    CRSError                - When a coordinate reference system is invalid
    MissingCRSError         - When a required CRS is missing
    TransformError          - When an affine transformation is invalid
    MissingTransformError   - When a required transform is missing
    MissingNoDataError      - When a required NoData value is missing

Rasters:
    RasterError             - Generic class for invalid raster metadata
    RasterShapeError        - When a raster array has an invalid shape
    RasterTransformError    - When a raster has an invalid affine transformation
    RasterCRSError          - When a raster has an invalid coordinate reference system

Vector Features:
    FeaturesError           - When vector features are not valid
    FeatureFileError        - When a vector feature file cannot be read
    NoFeaturesError         - When there are no vector features to convert to a raster
    GeometryError           - When a feature geometry is not valid
    CoordinateError         - When a feature's coordinates are not valid
    PolygonError            - When a polygon's coordinates are not valid
    PointError              - When a point's coordinates are not valid

Overlap:
    NoOverlapError          - When a dataset does not overlap a bounding box
    NoOverlappingFeaturesError  - When vector features do not overlap a bounding box

Models:
    DurationsError          - When queried rainfall durations are not recognized

Data Acquisition:
    DataAPIError            - When an API response is not valid
    InvalidJSONError        - When an API JSON is not valid
    MissingAPIFieldError    - When an API JSON response is missing a required field
    TNMError                - Errors unique to the TNM API
    TooManyTNMProductsError - When a TNM query has too many search results
    NoTNMProductsError      - When there are no TNM products in the search results
    LFPSError               - Errors unique to the LANDFIRE LFPS API
    InvalidLFPSJobError     - When a LANDFIRE LFPS job cannot be used for a data read
    LFPSJobTimeoutError     - When a LANDFIRE LFPS job takes too long to execute
"""

#####
# Numpy Arrays
#####


class ArrayError(Exception):
    "Generic class for invalid numpy arrays"


class EmptyArrayError(ArrayError):
    "When a numpy array has no elements"


class DimensionError(ArrayError):
    "When a numpy array has invalid non-singleton dimensions"


class ShapeError(ArrayError):
    "When a numpy axis has the wrong length"


#####
# Projection Metadata
#####


class CRSError(Exception):
    "When a coordinate reference system is invalid"


class MissingCRSError(CRSError):
    "When a required CRS is missing"


class TransformError(Exception):
    "When an affine transformation is invalid"


class MissingTransformError(TransformError):
    "When a required transform is missing"


class MissingNoDataError(Exception):
    "When a required NoData value is missing"


#####
# Rasters
#####


class RasterError(Exception):
    "Generic class for invalid rasters"


class RasterShapeError(RasterError, ShapeError):
    "When a raster array has an invalid shape"


class RasterTransformError(RasterError, TransformError):
    "When a raster has an invalid affine transformation"


class RasterCRSError(RasterError, CRSError):
    "When a raster has an invalid coordinate reference system"


#####
# Vector Features
#####


class FeaturesError(Exception):
    "When vector features are not valid"


class FeatureFileError(FeaturesError):
    "When a vector feature file cannot be read"


class NoFeaturesError(FeaturesError):
    "When there are no vector features to convert to a raster"


class GeometryError(FeaturesError):
    "When a vector feature geometry is not valid"


class CoordinateError(GeometryError):
    "When vector feature geometry coordinates are not valid"


class PolygonError(CoordinateError):
    "When polygon feature coordinates are not valid"


class PointError(CoordinateError):
    "When point feature coordinates are not valid"


#####
# Overlap
#####


class NoOverlapError(Exception):
    "When a dataset does not overlap an indicated bounding box"


class NoOverlappingFeaturesError(NoOverlapError, NoFeaturesError):
    "When vector features do not overlap a required bounding box"


#####
# Models
#####


class DurationsError(Exception):
    "When queried rainfall durations are not reported in Table 4 of Staley et al., 2017"


#####
# Data Acquisition
#####


class DataAPIError(Exception):
    "When an API response is not valid"


class InvalidJSONError(DataAPIError):
    "When API JSON is not valid"


class MissingAPIFieldError(DataAPIError, KeyError):
    "When an API JSON response is missing a required field"


class TNMError(DataAPIError):
    "Errors unique to the TNM API"


class TooManyTNMProductsError(TNMError):
    "When a TNM query has too many search results"


class NoTNMProductsError(TNMError):
    "When there are no TNM products in the search results"


class LFPSError(DataAPIError):
    "Errors unique to the LANDFIRE LFPS API"

    def __init__(self, message, id=None):
        super().__init__(message)
        self.id = id


class InvalidLFPSJobError(LFPSError):
    "When a LANDFIRE LFPS job cannot be used for a data read"


class LFPSJobTimeoutError(LFPSError):
    "When a LANDFIRE LFPS job takes too long to execute"
