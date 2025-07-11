import json
from unittest.mock import patch

import pytest
from requests import Response
from requests.exceptions import ConnectTimeout, HTTPError, ReadTimeout

from pfdf.data._utils import requests as _requests
from pfdf.errors import InvalidJSONError

#####
# Testing Fixtures
#####


@pytest.fixture
def args():
    url = "https://www.usgs.gov"
    params = {"example": 1, "parameters": 2}
    timeout = None
    servers = ["TNM", "ScienceBase"]
    outages = ["some url", "another url"]
    return url, params, timeout, servers, outages


#####
# Utils
#####


class TestValidate:
    def test_outages(_):
        timeout, servers, outages = _requests._validate(
            None, ["server 1", "server 2"], ["outage 1", "outage 2"]
        )
        assert timeout is None
        assert servers == ["server 1", "server 2"]
        assert outages == ["outage 1", "outage 2"]

    def test_no_outages(_):
        timeout, servers, outages = _requests._validate(
            None, ["server 1", "server 2"], None
        )
        assert timeout is None
        assert servers == ["server 1", "server 2"]
        assert outages == [None, None]

    def test_single_server(_):
        timeout, servers, outages = _requests._validate(
            15, "test server", "test outage"
        )
        assert timeout == 15
        assert servers == ["test server"]
        assert outages == ["test outage"]

    def test_invalid_timeout(_, assert_contains):
        with pytest.raises(TypeError) as error:
            _requests._validate("invalid", "server", None)
        assert_contains(error, "dtype of timeout")


class TestCheckConnections:
    def test_outages(_):
        connections = ["TNM", "ScienceBase"]
        outages = ["some url", "another url"]
        output = _requests._check_connections(connections, outages)
        assert output == (
            " Try checking:\n"
            "  * If TNM is down (some url)\n"
            "  * If ScienceBase is down (another url)\n"
            "If a connection is down, then wait a bit and try again later.\n"
            'Otherwise, try increasing "timeout" to a longer interval.'
        )

    def test_no_outages(_):
        connections = ["TNM", "ScienceBase"]
        outages = [None, None]
        output = _requests._check_connections(connections, outages)
        assert output == (
            " Try checking:\n"
            "  * If TNM is down\n"
            "  * If ScienceBase is down\n"
            "If a connection is down, then wait a bit and try again later.\n"
            'Otherwise, try increasing "timeout" to a longer interval.'
        )


class TestConnectTimeout:
    def test(_, assert_contains):
        servers = ["TNM", "ScienceBase"]
        outages = ["some url", "another url"]
        with pytest.raises(ConnectTimeout) as error:
            raise _requests._connect_timeout(servers, outages)
        assert_contains(
            error,
            (
                "Took too long to connect to the TNM server. Try checking:\n"
                "  * If your internet connection is down\n"
                "  * If TNM is down (some url)\n"
                "  * If ScienceBase is down (another url)\n"
                "If a connection is down, then wait a bit and try again later.\n"
                'Otherwise, try increasing "timeout" to a longer interval.'
            ),
        )


class TestReadTimeout:
    def test(_, assert_contains):
        servers = ["TNM", "ScienceBase"]
        outages = ["some url", "another url"]
        with pytest.raises(ReadTimeout) as error:
            raise _requests._read_timeout(servers, outages)
        assert_contains(
            error,
            (
                "The TNM server took too long to respond. Try checking:\n"
                "  * If TNM is down (some url)\n"
                "  * If ScienceBase is down (another url)\n"
                "If a connection is down, then wait a bit and try again later.\n"
                'Otherwise, try increasing "timeout" to a longer interval.'
            ),
        )


#####
# Requests
#####


class TestQueryUrl:
    def test(_):
        base = "https://www.usgs.gov"
        params = {
            "test": "(in_parens)",
            "another": 5,
        }
        output = _requests.query_url(base, params, decode=False)
        assert output == r"https://www.usgs.gov/?test=%28in_parens%29&another=5"

    def test_decode(_):
        base = "https://www.usgs.gov"
        params = {
            "test": "(in_parens)",
            "another": 5,
        }
        output = _requests.query_url(base, params, decode=True)
        assert output == r"https://www.usgs.gov/?test=(in_parens)&another=5"


class TestGet:
    @patch("requests.get", spec=True)
    def test_valid(_, mock, response, args):
        mock.return_value = response(200, b"Some content")
        output = _requests.get(*args)
        assert isinstance(output, Response)

    @patch("requests.get", spec=True)
    def test_connect_timeout(_, mock, args, assert_contains):
        mock.side_effect = ConnectTimeout("Took too long")
        with pytest.raises(ConnectTimeout) as error:
            _requests.get(*args)
        assert_contains(error, "Took too long to connect to the TNM server")

    @patch("requests.get", spec=True)
    def test_read_timeout(_, mock, args, assert_contains):
        mock.side_effect = ReadTimeout("Took too long")
        with pytest.raises(ReadTimeout) as error:
            _requests.get(*args)
        assert_contains(error, "The TNM server took too long to respond")

    @patch("requests.get", spec=True)
    def test_http_error(_, mock, response, args, assert_contains):
        mock.return_value = response(404, b"File not found")
        with pytest.raises(HTTPError) as error:
            _requests.get(*args)
        assert_contains(
            error,
            "There was a problem connecting with the TNM server. Please see the above error for details.",
        )


class TestContent:
    @patch("requests.get", spec=True)
    def test(_, mock, response, args):
        mock.return_value = response(200, b"Here is some content")
        output = _requests.content(*args)
        assert isinstance(output, bytes)
        assert output == b"Here is some content"


class TestJson:
    @patch("requests.get", spec=True)
    def test_valid(_, mock, json_response, args):
        content = {
            "text": "Some text",
            "number": 2.2,
            "list": [1, 2, 3],
        }
        mock.return_value = json_response(content)
        output = _requests.json(*args)
        assert isinstance(output, dict)
        assert output == content

    @patch("requests.get", spec=True)
    def test_invalid(_, mock, response, args, assert_contains):
        mock.return_value = response(200, b"This is not valid JSON")
        with pytest.raises(InvalidJSONError) as error:
            _requests.json(*args)
        assert_contains(error, "The TNM response was not valid JSON")


class TestDownload:
    @patch("requests.get", spec=True)
    def test(_, mock, tmp_path, response, args):
        mock.return_value = response(200, b"This is some file")
        path = tmp_path / "test.txt"
        output = _requests.download(path, *args)

        assert output == path
        assert output.read_text() == "This is some file"


#####
# Live requests - queries TNM for JSON response
#####


@pytest.mark.web(api="tnm")
class TestLive:
    @staticmethod
    def args():
        url = "https://tnmaccess.nationalmap.gov/api/v1/products"
        params = {
            "datasets": "National Elevation Dataset (NED) 1/3 arc-second Current",
            "max": 1,
            "outputFormat": "JSON",
        }
        timeout = 60
        servers = ["TNM", "ScienceBase"]
        outages = [None, None]
        return url, params, timeout, servers, outages

    def test_content(self):
        output = _requests.content(*self.args())
        assert isinstance(output, bytes)

    def test_json(self):
        output = _requests.json(*self.args())
        assert isinstance(output, dict)
