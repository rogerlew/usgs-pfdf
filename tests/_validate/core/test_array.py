import numpy as np
import pytest

import pfdf._validate.core._array as validate
from pfdf.errors import DimensionError, EmptyArrayError, ShapeError

###
# Low-level
###


class TestRealDtype:
    @pytest.mark.parametrize(
        "input, expected",
        (
            (float, np.dtype(float)),
            ("uint16", np.dtype("uint16")),
            (np.dtype("int8"), np.dtype("int8")),
        ),
    )
    def test_valid(_, input, expected):
        output = validate.real_dtype(input, "test")
        assert output == expected

    def test_not_dtype(_, assert_contains):
        with pytest.raises(TypeError) as error:
            validate.real_dtype(5, "test")
        assert_contains(error, "Could not convert test to a numpy dtype")

    def test_not_allowed_dtype(_, assert_contains):
        with pytest.raises(TypeError) as error:
            validate.real_dtype(str, "test name")
        assert_contains(
            error,
            "The dtype of test name",
            "is not an allowed dtype",
        )


class TestShape:
    name = "test name"
    axes = ["rows", "columns"]
    shape = (10, 5)

    @pytest.mark.parametrize("required, axis", [((2, 5), "rows"), ((10, 2), "columns")])
    def test_failed(self, required, axis, assert_contains):
        with pytest.raises(ShapeError) as error:
            validate.shape_(self.name, self.axes, required, self.shape)
        assert_contains(error, self.name, axis)

    def test_none(self):
        validate.shape_(self.name, self.axes, None, self.shape)

    def test_pass(self):
        validate.shape_(self.name, self.axes, self.shape, self.shape)

    def test_skip(self):
        required = (-1, self.shape[1])
        validate.shape_(self.name, self.axes, required, self.shape)


class TestDtype:
    name = "test name"
    dtype = np.integer
    string = "numpy.integer"

    @pytest.mark.parametrize(
        "allowed, string",
        [(bool, "bool"), ([np.floating, bool], "numpy.floating")],
    )
    def test_failed(self, allowed, string, assert_contains):
        with pytest.raises(TypeError) as error:
            validate.dtype_(self.name, allowed, self.dtype)
        assert_contains(error, self.name, string, self.string)

    def test_none(self):
        validate.dtype_(self.name, None, self.dtype)

    @pytest.mark.parametrize("allowed", [(np.integer), ([np.floating, np.integer])])
    def test_pass(self, allowed):
        validate.dtype_(self.name, allowed, self.dtype)


class TestNonsingleton:
    def test(_):
        array = np.arange(0, 36).reshape(2, 1, 1, 3, 1, 6)
        tf = [True, False, False, True, False, True]
        assert validate.nonsingleton(array) == tf


#####
# Shape and Type
#####


class TestArray:
    def test_scalar(_):
        a = 1
        expected = np.atleast_1d(np.array(a))
        output = validate.array(a, "")
        assert np.array_equal(output, expected)

    def test_ND(_):
        a = np.arange(0, 27).reshape(3, 3, 3)
        output = validate.array(a, "")
        assert np.array_equal(a, output)

    def test_invalid_empty(_, assert_contains):
        a = np.array([])
        with pytest.raises(EmptyArrayError) as error:
            validate.array(a, "test name")
        assert_contains(error, "test name")

    def test_valid_empty(_):
        a = np.array([])
        assert 0 in a.shape
        output = validate.array(a, "", allow_empty=True)
        assert np.array_equal(output, [])
        assert 0 in output.shape

    def test_dtype(_):
        a = np.arange(0, 10, dtype=float)
        output = validate.array(a, "", dtype=float)
        assert np.array_equal(a, output)

    def test_dtype_failed(_, assert_contains):
        a = np.arange(0, 10, dtype=float)
        with pytest.raises(TypeError) as error:
            validate.array(a, "test name", dtype=int)
        assert_contains(error, "test name")

    def test_copy(_):
        a = np.arange(10)
        output = validate.array(a, "", copy=True)
        assert output is not a
        assert output.base is None

    def test_no_copy(_):
        a = np.arange(10)
        output = validate.array(a, "", copy=False)
        assert output is a


class TestScalar:
    name = "test name"

    def test_int(_):
        a = 4
        assert validate.scalar(a, "") == np.array(a)

    def test_float(_):
        a = 5.5
        assert validate.scalar(a, "") == np.array(5.5)

    def test_1D(_):
        a = np.array(2.2)
        assert validate.scalar(a, "") == a

    def test_ND(_):
        a = np.array(2.2).reshape(1, 1, 1, 1, 1, 1, 1, 1, 1, 1)
        assert validate.scalar(a, "") == a.reshape(1)

    def test_dtype(_):
        a = np.array(2.2, dtype=float)
        assert validate.scalar(a, "", dtype=np.floating) == a

    def test_empty(self, assert_contains):
        with pytest.raises(EmptyArrayError) as error:
            validate.scalar([], self.name)
        assert_contains(error, self.name)

    def test_failed_list(self, assert_contains):
        a = [1, 2, 3, 4]
        with pytest.raises(DimensionError) as error:
            validate.scalar(a, self.name)
        assert_contains(error, self.name, f"{len(a)} elements")

    def test_failed_numpy(self, assert_contains):
        a = np.array([1, 2, 3, 4])
        with pytest.raises(DimensionError) as error:
            validate.scalar(a, self.name)
        assert_contains(error, self.name, f"{a.size} elements")

    def test_dtype_failed(self, assert_contains):
        a = np.array(4, dtype=int)
        allowed = bool
        string = "bool"
        with pytest.raises(TypeError) as error:
            validate.scalar(a, self.name, dtype=allowed)
        assert_contains(error, self.name, string)


class TestVector:
    name = "test name"

    def test_list(_):
        a = [1, 2, 3, 4, 5]
        output = validate.vector(a, "")
        np.array_equal(output, np.array(a))

    def test_tuple(_):
        a = (1, 2, 3, 4, 5)
        output = validate.vector(a, "")
        np.array_equal(output, np.array(a))

    def test_1D(_):
        a = np.array([1, 2, 3, 4, 5])
        output = validate.vector(a, "")
        np.array_equal(output, a)

    @pytest.mark.parametrize("shape", [(1, 5), (1, 1, 1, 1, 5), (1, 1, 5, 1, 1)])
    def test_ND(_, shape):
        a = np.array([1, 2, 3, 4, 5]).reshape(*shape)
        output = validate.vector(a, "")
        np.array_equal(output, a.reshape(5))

    @pytest.mark.parametrize("types", [(np.integer), ([np.integer, np.floating])])
    def test_dtype(_, types):
        a = np.array([1, 2, 3, 4, 5])
        output = validate.vector(a, "", dtype=types)
        np.array_equal(output, a)

    def test_length(_):
        a = np.arange(1, 6)
        output = validate.vector(a, "", length=5)
        np.array_equal(output, a)

    def test_scalar(self):
        a = 2.2
        output = validate.vector(a, "")
        np.array_equal(output, np.array(a).reshape(1))

    def test_dtype_failed(self, assert_contains):
        a = np.arange(0, 5, dtype=int)
        allowed = bool
        string = "bool"
        with pytest.raises(TypeError) as error:
            validate.vector(a, self.name, dtype=allowed)
        assert_contains(error, self.name, string)

    def test_invalid_empty(self, assert_contains):
        with pytest.raises(EmptyArrayError) as error:
            validate.vector([], self.name)
        assert_contains(error, self.name)

    def test_valid_empty(self):
        output = validate.vector([], "", allow_empty=True)
        assert output.shape == (0,)
        assert np.array_equal(output, [])

    def test_ND_failed(self, assert_contains):
        a = np.arange(0, 10).reshape(2, 5)
        with pytest.raises(DimensionError) as error:
            validate.vector(a, self.name)
        assert_contains(error, self.name)

    @pytest.mark.parametrize("length", [(1), (2), (3)])
    def test_length_failed(self, length, assert_contains):
        a = np.arange(0, 10)
        with pytest.raises(ShapeError) as error:
            validate.vector(a, self.name, length=length)
        assert_contains(error, self.name, f"{len(a)} element(s)")


class TestMatrix:
    name = "test name"

    def test_list(_):
        a = [1, 2, 3, 4]
        output = validate.matrix(a, "")
        np.array_equal(output, np.array(a).reshape(1, 4))

    def test_tuple(_):
        a = (1, 2, 3, 4)
        output = validate.matrix(a, "")
        np.array_equal(output, np.array(a).reshape(1, 4))

    def test_2D(_):
        a = np.arange(0, 10).reshape(2, 5)
        output = validate.matrix(a, "")
        np.array_equal(output, a)

    def test_trailing(_):
        a = np.arange(0, 10).reshape(2, 5, 1, 1, 1)
        output = validate.matrix(a, "")
        np.array_equal(output, a.reshape(2, 5))

    def test_dtype(_):
        a = np.arange(0, 10, dtype=int).reshape(2, 5)
        output = validate.matrix(a, "", dtype=np.integer)
        np.array_equal(output, a)

    def test_shape(_):
        a = np.arange(0, 10).reshape(2, 5)
        output = validate.matrix(a, "", shape=(2, 5))
        np.array_equal(output, a)

    def test_skip_shape(_):
        a = np.arange(0, 10).reshape(2, 5)
        output = validate.matrix(a, "", shape=(-1, 5))
        np.array_equal(output, a)
        output = validate.matrix(a, "", shape=(2, -1))
        np.array_equal(output, a)
        output = validate.matrix(a, "", shape=(-1, -1))
        np.array_equal(output, a)

    def test_scalar(_):
        a = 5
        output = validate.matrix(a, "")
        np.array_equal(output, np.array(a).reshape(1, 1))

    def test_vector(_):
        a = np.arange(0, 10)
        output = validate.matrix(a, "")
        np.array_equal(output, a.reshape(1, -1))

    def test_dtype_failed(self, assert_contains):
        a = np.arange(0, 10, dtype=int)
        allowed = bool
        string = "bool"
        with pytest.raises(TypeError) as error:
            validate.matrix(a, self.name, dtype=allowed)
        assert_contains(error, self.name, string)

    def test_empty(self, assert_contains):
        with pytest.raises(EmptyArrayError) as error:
            validate.matrix([], self.name)
        assert_contains(error, self.name)

    @pytest.mark.parametrize(
        "array",
        [(np.arange(0, 27).reshape(3, 3, 3)), (np.arange(0, 10).reshape(1, 2, 5))],
    )
    def test_ND(self, array, assert_contains):
        with pytest.raises(DimensionError) as error:
            validate.matrix(array, self.name)
        assert_contains(error, self.name)

    @pytest.mark.parametrize(
        "shape, axis", [((3, 5), "3 row(s)"), ((2, 7), "7 column(s)")]
    )
    def test_shape_failed(self, shape, axis, assert_contains):
        a = np.arange(0, 10).reshape(2, 5)
        with pytest.raises(ShapeError) as error:
            validate.matrix(a, self.name, shape=shape)
        assert_contains(error, self.name, axis)

    def test_copy(_):
        a = np.ones((5, 5))
        output = validate.matrix(a, "", copy=True)
        assert output is not a
        assert output.base is not a

    def test_no_copy(_):
        a = np.ones((5, 5))
        output = validate.matrix(a, "")
        assert output.base is a


class TestBroadcastable:
    def test(_):
        a = (4, 5, 1, 3, 1, 7)
        b = (5, 6, 1, 1, 7)
        output = validate.broadcastable(a, "", b, "")
        expected = (4, 5, 6, 3, 1, 7)
        assert output == expected

    def test_failed(_, assert_contains):
        a = (4, 5)
        b = (5, 6)
        with pytest.raises(ValueError) as error:
            validate.broadcastable(a, "test-name-1", b, "test-name-2")
        assert_contains(error, "test-name-1", "test-name-2")
