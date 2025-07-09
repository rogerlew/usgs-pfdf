from unittest.mock import patch

import pytest

from pfdf.data.landfire import products as _products


def check_mock(mock):
    mock.assert_called_with(
        url="https://lfps.usgs.gov/api/products",
        params={},
        timeout=10,
    )


def product(name, acronym, version):
    return {
        "layerName": name,
        "acronym": acronym,
        "version": version,
    }


@pytest.fixture
def evts():
    return [
        product("230EVT", "EVT", "2.3.0"),
        product("240EVT", "EVT", "2.4.0"),
        product("250EVT", "EVT", "2.5.0"),
    ]


@pytest.fixture
def others():
    return [
        product("other100", "other", "1.0.0"),
        product("other200", "other", "2.0.0"),
        product("other210", "other", "2.1.0"),
    ]


@pytest.fixture
def products(evts, others):
    return evts + others


@pytest.fixture
def response(json_response, products):
    response = {"products": products}
    return json_response(response)


class TestQuery:
    @patch("requests.get", spec=True)
    def test_all(_, mock, response, products):
        mock.return_value = response
        output = _products.query()
        assert output == products
        check_mock(mock)

    @patch("requests.get", spec=True)
    def test_acronym(_, mock, response, evts):
        mock.return_value = response
        output = _products.query(acronym="EVT")
        assert output == evts
        check_mock(mock)


class TestAcronyms:
    @patch("requests.get", spec=True)
    def test(_, mock, response):
        mock.return_value = response
        output = _products.acronyms()
        assert output == ["EVT", "other"]
        check_mock(mock)

    @pytest.mark.web
    def test_live(_):
        output = _products.acronyms()
        assert sorted(output) == [
            "Asp",
            "BPS",
            "CBD",
            "CBH",
            "CC",
            "CFFDRS",
            "CH",
            "Dist",
            "ESP",
            "EVC",
            "EVH",
            "EVT",
            "Elev",
            "FBFM13",
            "FBFM40",
            "FCCS",
            "FDist",
            "FRG",
            "FRI",
            "FVC",
            "FVH",
            "FVT",
            "HDist",
            "LDist",
            "MFRI",
            "MF_F40",
            "MF_FVC",
            "MF_FVH",
            "NVC",
            "PDist",
            "PFS",
            "PLS",
            "PMS",
            "PRS",
            "Roads",
            "SClass",
            "SlpD",
            "SlpP",
            "VCC",
            "VDep",
            "mz",
        ]


class TestLayers:
    @patch("requests.get", spec=True)
    def test_all(_, mock, response):
        mock.return_value = response
        output = _products.layers()
        assert output == [
            "230EVT",
            "240EVT",
            "250EVT",
            "other100",
            "other200",
            "other210",
        ]
        check_mock(mock)

    @patch("requests.get", spec=True)
    def test_acronym(_, mock, response):
        mock.return_value = response
        output = _products.layers(acronym="EVT")
        assert output == ["230EVT", "240EVT", "250EVT"]
        check_mock(mock)


class TestLatest:
    @patch("requests.get", spec=True)
    def test(_, mock, response):
        mock.return_value = response
        output = _products.latest("EVT")
        assert output == product("250EVT", "EVT", "2.5.0")
        check_mock(mock)

    @patch("requests.get", spec=True)
    def test_unknown_acronym(_, mock, response, assert_contains):
        mock.return_value = response
        with pytest.raises(ValueError) as error:
            _products.latest("unknown")
        assert_contains(
            error, 'There are no LANDFIRE LFPS products matching the "unknown" acronym'
        )


class TestLayer:
    @patch("requests.get", spec=True)
    def test(_, mock, response):
        mock.return_value = response
        output = _products.layer("other200")
        assert output == product("other200", "other", "2.0.0")
        check_mock(mock)

    @patch("requests.get", spec=True)
    def test_no_match(_, mock, response, assert_contains):
        mock.return_value = response
        with pytest.raises(ValueError) as error:
            _products.layer("missing")
        assert_contains(
            error,
            'There are no LANDFIRE LFPS products matching the "missing" layer name',
        )
        check_mock(mock)
