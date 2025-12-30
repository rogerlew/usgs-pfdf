import numpy as np
import pytest

from pfdf._utils import all_nones, aslist, astuple, clean_dims, limits, no_nones, real

#####
# Misc
#####


def test_real():
    assert real == [np.integer, np.floating, bool]


@pytest.mark.parametrize(
    "input, expected",
    (
        (1, [1]),
        ([1, 2, 3], [1, 2, 3]),
        ("test", ["test"]),
        ({"a": "test"}, [{"a": "test"}]),
        ((1, 2, 3), [1, 2, 3]),
    ),
)
def test_aslist(input, expected):
    assert aslist(input) == expected


@pytest.mark.parametrize(
    "input, expected",
    (
        (1, (1,)),
        ([1, 2, 3], (1, 2, 3)),
        ("test", ("test",)),
        ({"a": "test"}, ({"a": "test"},)),
        ((1, 2, 3), (1, 2, 3)),
    ),
)
def test_astuple(input, expected):
    assert astuple(input) == expected


class TestCleanDims:
    def test_clean(_):
        a = np.ones((4, 4, 1))
        output = clean_dims(a, keepdims=False)
        assert output.shape == (4, 4)
        assert np.array_equal(output, np.ones((4, 4)))

    def test_no_clean(_):
        a = np.ones((4, 4, 1))
        output = clean_dims(a, keepdims=True)
        assert output.shape == (4, 4, 1)
        assert np.array_equal(a, output)


class TestAllNones:
    def test_all_nones(_):
        assert all_nones(None, None, None, None) == True

    def test_no_nones(_):
        assert all_nones(1, 2, 3, 4, 5, 6, 7) == False

    def test_mixed(_):
        assert all_nones(None, 2, None, 4) == False


class TestNoNones:
    def test_all_nones(_):
        assert no_nones(None, None, None, None) == False

    def test_no_nones(_):
        assert no_nones(1, 2, 3, 4, 5, 6, 7) == True

    def test_mixed(_):
        assert no_nones(1, None, 2, None) == False


class TestLimits:
    def test(_):
        assert limits(-2, 6, 10) == (0, 6)
        assert limits(5, 15, 10) == (5, 10)
        assert limits(5, 8, 10) == (5, 8)
        assert limits(-2, 15, 10) == (0, 10)
