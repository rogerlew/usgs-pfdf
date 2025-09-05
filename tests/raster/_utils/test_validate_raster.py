from math import inf
from unittest.mock import patch

import numpy as np
import pytest
import rasterio
from requests import Response
from requests.exceptions import HTTPError

from pfdf.errors import DimensionError
from pfdf.projection import BoundingBox
from pfdf.raster._utils import validate as validate

#####
# Nodata
#####


class TestCastingOption:
    @pytest.mark.parametrize(
        "input, expected",
        (
            ("safe", "safe"),
            ("UNSAFE", "unsafe"),
            ("EqUiV", "equiv"),
        ),
    )
    def test_valid(_, input, expected):
        output = validate.casting_option(input, "test")
        assert output == expected

    def test_invalid(_, assert_contains):
        with pytest.raises(ValueError) as error:
            validate.casting_option("invalid", "test name")
        assert_contains(
            error,
            "test name (invalid) is not a recognized option",
            "Supported options are: no, equiv, safe, same_kind, unsafe",
        )


class TestCasting:
    def test_bool(_):
        a = np.array(True).reshape(1)
        assert validate.casting(a, "", bool, "safe") == True

    def test_bool_as_number(_):
        a = np.array(1.00).reshape(1)
        assert validate.casting(a, "", bool, casting="safe") == True

    def test_castable(_):
        a = np.array(2.2).reshape(1)
        assert validate.casting(a, "", int, casting="unsafe") == 2

    def test_not_castable(_, assert_contains):
        a = np.array(2.2).reshape(1)
        with pytest.raises(TypeError) as error:
            validate.casting(a, "test name", int, casting="safe")
        assert_contains(error, "Cannot cast test name")


class TestNodata:
    def test_nodata(_):
        output = validate.nodata(5, "safe")
        assert output == 5

    def test_casting(_):
        output = validate.nodata(2.2, "unsafe", int)
        assert output == 2

    def test_invalid_casting_option(_, assert_contains):
        with pytest.raises(ValueError) as error:
            validate.nodata(1, "invalid", bool)
        assert_contains(error, "casting")

    def test_invalid_nodata(_, assert_contains):
        with pytest.raises(TypeError) as error:
            validate.nodata("invalid", "unsafe")
        assert_contains(error, "nodata")

    def test_invalid_casting(_, assert_contains):
        with pytest.raises(TypeError) as error:
            validate.nodata(2.2, "safe", int)
        assert_contains(error, "Cannot cast the NoData value")


#####
# Array Shapes
#####


class TestShape2D:

    @pytest.mark.parametrize(
        "input",
        (
            (1, 2),
            [1, 2],
            [1.0, 2.0],
            np.array([1, 2]),
            np.array([1, 2]).astype(float),
        ),
    )
    def test(_, input):
        output = validate.shape2d(input, "test")
        assert isinstance(output, tuple)
        assert output == (1, 2)
        assert isinstance(output[0], int)
        assert isinstance(output[1], int)

    def test_wrong_length(_, assert_contains):
        with pytest.raises(DimensionError) as error:
            validate.shape2d((1, 2, 3), "test")
        assert_contains(error, "test must have exactly 2 elements")

    def test_invalid_type(_, assert_contains):
        with pytest.raises(TypeError) as error:
            validate.shape2d((1, "invalid"), "test")
        assert_contains(error, 'The elements of "test" must be integers')

    def test_invalid_float(_, assert_contains):
        with pytest.raises(TypeError) as error:
            validate.shape2d((1.1, 2), "test")
        assert_contains(error, 'The elements of "test" must be integers')

    def test_zero(_):
        assert validate.shape2d((0, 0), "") == (0, 0)

    def test_negative(_, assert_contains):
        with pytest.raises(ValueError) as error:
            validate.shape2d((1, -2), "test")
        assert_contains(error, 'The elements of "test" cannot be negative')


class TestSlice:
    @pytest.mark.parametrize(
        "input, start",
        (
            (-4, 0),
            (-3, 1),
            (-2, 2),
            (-1, 3),
            (0, 0),
            (1, 1),
            (2, 2),
            (3, 3),
        ),
    )
    def test_valid_int(_, input, start):
        output = validate._slice(input, "", length=4)
        assert isinstance(output, slice)
        assert output.start == start
        assert output.stop == start + 1
        assert output.step == 1

    @pytest.mark.parametrize(
        "input",
        (-6, -5, 4, 5),
    )
    def test_invalid_int(_, input, assert_contains):
        with pytest.raises(IndexError) as error:
            validate._slice(input, "test", length=4)
        assert_contains(
            error,
            f"The test index ({input}) is out of range. Valid indices are from -4 to 3",
        )

    @pytest.mark.parametrize(
        "input, name",
        (
            (0.0, "float"),
            ("invalid", "str"),
        ),
    )
    def test_invalid_type(_, input, name, assert_contains):
        with pytest.raises(TypeError) as error:
            validate._slice(input, "test", 4)
        assert_contains(
            error, f"test indices must be an int or slice, but they are {name} instead"
        )

    @pytest.mark.parametrize(
        "input, expected",
        (
            (slice(1, 3), slice(1, 3, 1)),
            (slice(1, 3, 1), slice(1, 3, 1)),
            (slice(1, 100), slice(1, 4, 1)),
            (slice(1, -1), slice(1, 3, 1)),
            (slice(-3, 3), slice(1, 3, 1)),
            (slice(-3, -1), slice(1, 3, 1)),
            (slice(-100, 100), slice(0, 4, 1)),
        ),
    )
    def test_valid_slice(_, input, expected):
        output = validate._slice(input, "", 4)
        assert output == expected

    @pytest.mark.parametrize(
        "input",
        (
            slice(5, 100),
            slice(3, 1),
            slice(3, -4),
            slice(-1, -3),
            slice(-1, -100),
            slice(-100, -5),
            slice(-100, -200),
        ),
    )
    def test_empty(_, input, assert_contains):
        with pytest.raises(IndexError) as error:
            validate._slice(input, "test", 4)
        assert_contains(error, "test indices must select at least one element")

    def test_invalid_step(_, assert_contains):
        input = slice(0, 100, 2)
        with pytest.raises(IndexError) as error:
            validate._slice(input, "test", length=1000)
        assert_contains(error, "test indices must have a step size of 1")


class TestSlices:
    @pytest.mark.parametrize("shape", ((0, 4), (4, 0)))
    def test_zero(_, shape, assert_contains):
        indices = (slice(1), slice(1))
        with pytest.raises(IndexError) as error:
            validate.slices(indices, shape)
        assert_contains(
            error, "Indexing is not supported when the raster shape contains a 0"
        )

    def test_1D(_, assert_contains):
        with pytest.raises(IndexError) as error:
            validate.slices(5, (100, 100))
        assert_contains(
            error,
            "You must provide indices for exactly 2 dimensions, "
            "but there are indices for 1 dimension",
        )

    def test_3D(_, assert_contains):
        with pytest.raises(IndexError) as error:
            validate.slices((1, 1, 1), (100, 100))
        assert_contains(
            error,
            "You must provide indices for exactly 2 dimensions, "
            "but there are indices for 3 dimension(s) instead",
        )

    def test_valid(_):
        rows = 5
        cols = slice(50, -2)
        indices = (rows, cols)
        outrows, outcols = validate.slices(indices, (100, 100))
        assert outrows == slice(5, 6, 1)
        assert outcols == slice(50, 98, 1)


#####
# Preprocess
#####


class TestResampling:
    @pytest.mark.parametrize(
        "name, value",
        (
            ("nearest", 0),
            ("bilinear", 1),
            ("cubic", 2),
            ("cubic_spline", 3),
            ("lanczos", 4),
            ("average", 5),
            ("mode", 6),
            ("max", 8),
            ("min", 9),
            ("med", 10),
            ("q1", 11),
            ("q3", 12),
            ("sum", 13),
            ("rms", 14),
        ),
    )
    def test_valid(_, name, value):
        assert validate.resampling(name) == value

    def test_invalid(_):
        with pytest.raises(ValueError):
            validate.resampling("invalid")


class TestDataBound:
    @pytest.mark.parametrize(
        "dtype, edge, expected",
        (
            ("int16", "min", np.iinfo("int16").min),
            ("int16", "max", np.iinfo("int16").max),
            ("uint8", "min", np.iinfo("uint8").min),
            ("uint8", "max", np.iinfo("uint8").max),
            (bool, "min", False),
            (bool, "max", True),
            ("float32", "min", -inf),
            ("float32", "max", inf),
        ),
    )
    def test_default(_, dtype, edge, expected):
        output = validate.data_bound(None, edge, dtype)
        assert output == expected

    def test_valid(_):
        output = validate.data_bound(2.2, min, float)
        assert output == 2.2

    def test_invalid(_):
        with pytest.raises(TypeError):
            validate.data_bound("invalid", "min", float)

    def test_not_scalar(_):
        with pytest.raises(DimensionError):
            validate.data_bound([1, 2, 3], "min", float)

    def test_invalid_casting(_, assert_contains):
        with pytest.raises(TypeError) as error:
            validate.data_bound(2.2, "min", int)
        assert_contains(error, "min", "cast", "safe")


#####
# Factories
#####


class TestValidateUrl:
    @patch("requests.head")
    def test_valid(_, mock):
        response = Response()
        response.status_code = 200
        mock.return_value = response

        url = "https://www.usgs.gov"
        output, bounds = validate.url(url, False, None, None, 1, (1, 2, 3, 4), "safe")
        assert output == url
        assert bounds == BoundingBox(1, 2, 3, 4)

    @patch("requests.head")
    def test_invalid_http(_, mock, assert_contains):
        response = Response()
        response.status_code = 404
        mock.return_value = response
        url = "https://www.usgs.gov/this-is-not-a-valid-page"
        with pytest.raises(HTTPError) as error:
            validate.url(url, True, 10, None, 1, None, "safe")
        assert_contains(
            error,
            "There was a problem connecting to the URL. See the above error for more details",
        )

    def test_invalid_timeout(_, assert_contains):
        url = "https://www.usgs.gov"
        with pytest.raises(ValueError) as error:
            validate.url(url, True, 0, None, 1, None, "safe")
        assert_contains(
            error,
            "The data elements of timeout must be greater than 0, but element [0] (value=0) is not",
        )

    def test_invalid_file_option(_, assert_contains):
        url = "https://www.usgs.gov"
        with pytest.raises(TypeError) as error:
            validate.url(url, False, None, 5, 1, None, None)
        assert_contains(error, "driver must be a string")


class TestFile:
    def test_string(_, fraster):
        path, bounds = validate.file(str(fraster), None, 1, (1, 2, 3, 4), "safe")
        assert path == fraster
        assert bounds == BoundingBox(1, 2, 3, 4)

    def test_path(_, fraster):
        path, bounds = validate.file(fraster, None, 1, None, "safe")
        assert path == fraster
        assert bounds is None

    def test_missing_string(_):
        with pytest.raises(FileNotFoundError):
            validate.file("not-a-file", None, 1, None, "safe")

    def test_missing_path(_, fraster):
        fraster.unlink()
        with pytest.raises(FileNotFoundError):
            validate.file(fraster, None, 1, None, "safe")

    def test_invalid_file_option(_, fraster, assert_contains):
        with pytest.raises(TypeError) as error:
            validate.file(fraster, 5, 1, "safe", None)
        assert_contains(error, "driver must be a string")


class TestFileOptions:
    def test_invalid_driver(_, assert_contains):
        with pytest.raises(TypeError) as error:
            validate.file_options(5, 1, "safe", None)
        assert_contains(error, "driver must be a string")

    def test_invalid_band(_, assert_contains):
        with pytest.raises(TypeError) as error:
            validate.file_options(None, "invalid", "safe", None)
        assert_contains(error, "band must be a int")

    def test_missing_band(_, assert_contains):
        with pytest.raises(TypeError) as error:
            validate.file_options(None, None, "safe", None)
        assert_contains(error, "band must be a int")

    def test_invalid_bounds(_, assert_contains):
        with pytest.raises(TypeError) as error:
            validate.file_options(None, 1, "safe", "invalid")
        assert_contains(
            error,
            "bounds must be a BoundingBox, Raster, RasterMetadata, dict, list, or tuple",
        )

    def test_bounds(_):
        bounds = validate.file_options(None, 1, "safe", (1, 2, 3, 4))
        assert isinstance(bounds, BoundingBox)
        assert bounds == BoundingBox(1, 2, 3, 4)

    def test_invalid_casting_option(_, assert_contains):
        with pytest.raises(ValueError) as error:
            validate.file_options(None, 1, "invalid", None)
        assert_contains(
            error,
            "casting (invalid) is not a recognized option. Supported options are: no, equiv, safe, same_kind, unsafe",
        )

    def test_missing_casting_option(_, assert_contains):
        with pytest.raises(TypeError) as error:
            validate.file_options(None, 1, None, None)
        assert_contains(error, "casting must be a string")


class TestReader:
    @staticmethod
    def reader(path):
        with rasterio.open(path) as reader:
            return reader

    def test_valid(self, fraster):
        reader = self.reader(fraster)
        path = validate.reader(reader)
        assert path == fraster

    def test_old_reader(self, fraster, assert_contains):
        reader = self.reader(fraster)
        fraster.unlink()
        with pytest.raises(FileNotFoundError) as error:
            validate.reader(reader)
        assert_contains(error, "no longer exists")

    def test_invalid(_, fraster, assert_contains):
        with pytest.raises(TypeError) as error:
            validate.reader(fraster)
        assert_contains(error, "input raster must be a rasterio.DatasetReader object")
