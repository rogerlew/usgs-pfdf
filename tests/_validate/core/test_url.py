from unittest.mock import patch

import pytest
from requests import Response
from requests.exceptions import ConnectTimeout, HTTPError, ReadTimeout

from pfdf._validate.core import _url as validate
from pfdf.errors import ShapeError


class TestURL:
    def test_valid(_):
        scheme = validate.url("https://www.example.com")
        assert scheme == "https"

    def test_no_scheme(_, assert_contains):
        with pytest.raises(ValueError) as error:
            validate.url("www.example.com")
        assert_contains(
            error,
            (
                "The URL is missing a scheme. "
                "Some common schemes are http, https, and ftp. "
                "If you are trying to access a dataset from the internet, "
                "be sure to include `http://` or `https://` at the start of the URL."
            ),
        )

    def test_invalid(_, assert_contains):
        with pytest.raises(TypeError) as error:
            validate.url(5)
        assert_contains(error, "url must be a str")


class TestHttp:
    def test_not_http(_, assert_contains):
        with pytest.raises(ValueError) as error:
            validate.http("file:///path/to/some/file.txt", 5)
        assert_contains(
            error,
            "URL must have an 'http' or 'https' scheme, but it has a 'file' scheme instead",
        )

    @patch("requests.head")
    def test_invalid_connection(_, mock, assert_contains):
        response = Response()
        response.status_code = 404
        mock.return_value = response

        url = "https://www.usgs.gov/this-is-not-a-valid-page"
        with pytest.raises(HTTPError) as error:
            validate.http(url, 5)
        assert_contains(
            error,
            "There was a problem connecting to the URL. See the above error for more details",
        )

    @patch("requests.head")
    def test_valid(_, mock):
        response = Response()
        response.status_code = 200
        mock.return_value = response
        url = "https://www.usgs.gov"
        validate.http(url, 5)

    @patch("requests.head")
    def test_connect_timeout(_, mock, assert_contains):
        mock.side_effect = ConnectTimeout("Took too long")
        with pytest.raises(ConnectTimeout) as error:
            validate.http("https://www.usgs.gov", timeout=10)
        assert_contains(
            error, "Could not connect to the remote server in the allotted time"
        )

    @patch("requests.head")
    def test_read_timeout(_, mock, assert_contains):
        mock.side_effect = ReadTimeout("Took too long")
        with pytest.raises(ReadTimeout) as error:
            validate.http("https://www.usgs.gov", timeout=10)
        assert_contains(error, "The remote server did not respond in the allotted time")


class TestTimeout:
    def test_none(_):
        assert validate.timeout(None) is None

    def test_scalar(_):
        output = validate.timeout(10)
        assert output == 10.0

    def test_vector(_):
        output = validate.timeout([10, 5])
        assert output == (10.0, 5.0)

    def test_too_many(_, assert_contains):
        with pytest.raises(ShapeError) as error:
            validate.timeout([1, 2, 3, 4])
        assert_contains(error, "timeout must have either 1 or 2 elements")

    def test_negative(_, assert_contains):
        with pytest.raises(ValueError) as error:
            validate.timeout(0)
        assert_contains(
            error,
            "The data elements of timeout must be greater than 0, but element [0] (value=0) is not",
        )
