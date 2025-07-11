from math import inf

import numpy as np
import pytest

from pfdf.data.landfire import _validate
from pfdf.errors import DimensionError, MissingAPIFieldError, MissingCRSError

#####
# Individual inputs
#####


class TestLayer:
    def test_valid(_):
        output = _validate.layer("240EVT")
        assert output == "240EVT"

    def test_multiple(_, assert_contains):
        with pytest.raises(ValueError) as error:
            _validate.layer("240EVT;230EVT")
        assert_contains(error, "layer cannot contain semicolons")


class TestJobTime:
    def test_valid(_):
        input = np.array(15)
        output = _validate.job_time(input, "")
        assert output == 15
        assert isinstance(output, float)

    def test_invalid(_, assert_contains):
        with pytest.raises(DimensionError) as error:
            _validate.job_time([1, 2, 3], "test name")
        assert_contains(error, "test name must have exactly 1 element")

    def test_too_small(_, assert_contains):
        with pytest.raises(ValueError) as error:
            _validate.job_time(10, "test name")
        assert_contains(error, "test name must be greater than or equal to 15")


class TestMaxJobTime:
    def test_none(_):
        output = _validate.max_job_time(None)
        assert output == inf

    def test_valid(_):
        input = np.array(15).reshape(1)
        output = _validate.max_job_time(input)
        assert isinstance(output, float)
        assert output == 15

    def test_invalid(_, assert_contains):
        with pytest.raises(ValueError) as error:
            _validate.max_job_time(10)
        assert_contains(error, "max_job_time must be greater than or equal to 15")


class TestRefreshRate:
    def test_valid(_):
        input = np.array(15).reshape(1)
        output = _validate.refresh_rate(input)
        assert isinstance(output, float)
        assert output == 15

    def test_too_large(_, assert_contains):
        with pytest.raises(ValueError) as error:
            _validate.refresh_rate(3601)
        assert_contains(
            error, "refresh_rate cannot be greater than 3600 seconds (1 hour)"
        )

    def test_too_small(_, assert_contains):
        with pytest.raises(ValueError) as error:
            _validate.refresh_rate(10)
        assert_contains(error, "refresh_rate must be greater than or equal to 15")


#####
# Request parameters
#####


class TestSubmitJob:
    def params(_):
        return {
            "layers": ["250EVT", "240EVT"],
            "bounds": [-113.79, 42.29, -113.56, 42.148, 4326],
            "email": "test@usgs.gov",
        }

    def test_valid(self):
        output = _validate.submit_job(**self.params())
        assert output == {
            "Layer_List": "250EVT;240EVT",
            "Area_of_Interest": "-113.79 42.29 -113.56 42.148",
            "Email": "test@usgs.gov",
        }

    def test_layer(self, assert_contains):
        params = self.params()
        params["layers"] = 5
        with pytest.raises(TypeError) as error:
            _validate.submit_job(**params)
        assert_contains(
            error,
            "layers must be a string or list of strings, but layers[0] is not a string",
        )

    def test_bounds(self, assert_contains):
        params = self.params()
        params["bounds"] = params["bounds"][:-1]
        with pytest.raises(MissingCRSError) as error:
            _validate.submit_job(**params)
        assert_contains(error, "bounds must have a CRS")

    def test_email(self, assert_contains):
        params = self.params()
        params["email"] = 5
        with pytest.raises(TypeError) as error:
            _validate.submit_job(**params)
        assert_contains(error, "email must be a string")


#####
# Response
#####


class TestField:
    def test(_):
        response = {
            "field1": 1,
            "field2": 2,
            "field3": 3,
        }
        output = _validate.field(response, "field2", "")
        assert output == 2

    def test_missing(_, assert_contains):
        response = {
            "field1": 1,
            "field2": 2,
        }
        with pytest.raises(MissingAPIFieldError) as error:
            _validate.field(response, "field3", "test field")
        assert_contains(error, "LANDFIRE LFPS failed to return the test field")
