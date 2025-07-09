"""
Utility module to handle HTTP requests to data servers
----------
This module provides utilities that leverage the "requests" library to acquire data
from remote servers. Many of these functions are intended to help validate server
responses and provide informative errors when an HTTP request is invalid.
----------
Main functions:
    query_url           - Builds a query URL from base URL and parameters
    get                 - Validates and returns an HTTP response
    content             - Validates and returns HTTP response content (as bytes)
    json                - Validates and returns an HTTP response as a JSON dict

Utilities:
    _validate           - Parses timeout and error info for an HTTP request
    _connect_timeout    - Builds an informative error for a connection timeout
    _read_timeout       - Builds an informative error for a read timeout
    _check_connections  - Adds connection info to a timeout error
"""

from __future__ import annotations

import typing
from urllib.parse import unquote

import requests
from requests.exceptions import ConnectTimeout, HTTPError, JSONDecodeError, ReadTimeout

from pfdf._utils import aslist
from pfdf._validate import core as validate
from pfdf.errors import InvalidJSONError

if typing.TYPE_CHECKING:
    from pathlib import Path
    from typing import Any, Optional

    from requests import Response

    from pfdf.typing.core import strs, timeout

    servers = list[str]
    outages = list[str | None]


#####
# Main
#####


def _validate(
    timeout: Any, servers: strs, outages: strs | None
) -> tuple[timeout, servers, outages]:
    "Parses timeout and error info for an HTTP request"

    timeout = validate.timeout(timeout)
    servers = aslist(servers)
    if outages is None:
        outages = [None] * len(servers)
    else:
        outages = aslist(outages)
    return timeout, servers, outages


def query_url(base: str, params: dict, decode: bool) -> str:
    "Builds a query URL from a base URL and parameters"

    request = requests.Request(url=base, params=params)
    url = request.prepare().url
    if decode:
        url = unquote(url)
    return url


def get(
    url: str,
    params: dict[str, Any],
    timeout: Any,
    servers: strs,
    outages: Optional[strs] = None,
) -> Response:
    """Makes an HTTP request and returns the response. Provides informative errors if
    the request times out, or the request was not successful"""

    # Validate. Make the query
    timeout, servers, outages = _validate(timeout, servers, outages)
    try:
        response = requests.get(url, params=params, timeout=timeout)

    # Informative error if the request timed out
    except ConnectTimeout as error:
        raise _connect_timeout(servers, outages) from error
    except ReadTimeout as error:
        raise _read_timeout(servers, outages) from error

    # Check the response code
    try:
        response.raise_for_status()
    except HTTPError as error:
        raise HTTPError(
            f"There was a problem connecting with the {servers[0]} server. "
            f"Please see the above error for details."
        ) from error
    return response


def content(
    url: str,
    params: dict[str, Any],
    timeout: Any,
    servers: strs,
    outages: Optional[strs] = None,
) -> bytes:
    "Validates an HTTP request and returns the response content as bytes"

    response = get(url, params, timeout, servers, outages)
    return response.content


def json(
    url: str,
    params: dict[str, Any],
    timeout: Any,
    servers: strs,
    outages: Optional[strs] = None,
) -> dict:
    "Validates and returns an HTTP request as a JSON dict"

    # Validate and get response
    servers = aslist(servers)
    response = get(url, params, timeout, servers, outages)

    # Convert response to JSON
    try:
        return response.json()
    except JSONDecodeError as error:
        raise InvalidJSONError(
            f"The {servers[0]} response was not valid JSON"
        ) from error


def download(
    path: Path,
    url: str,
    params: dict[str, Any],
    timeout: Any,
    servers: strs,
    outages: Optional[strs] = None,
) -> Path:
    "Downloads a web dataset to the indicated path"

    response = content(url, params, timeout, servers, outages)
    path.write_bytes(response)
    return path


#####
# Timeout errors
#####


def _connect_timeout(servers: servers, outages: outages) -> ConnectTimeout:
    "Builds a ConnectTimeout error with an informative error message"

    message = f"Took too long to connect to the {servers[0]} server."
    servers = ["your internet connection"] + servers
    outages = [None] + outages
    message += _check_connections(servers, outages)
    return ConnectTimeout(message)


def _read_timeout(servers: servers, outages: outages) -> ReadTimeout:
    "Builds a ReadTimeout error with an informative error message"

    message = f"The {servers[0]} server took too long to respond."
    message += _check_connections(servers, outages)
    return ReadTimeout(message)


def _check_connections(connections: servers, outages: outages) -> str:
    "Builds an informative message indicating server connections that may be down"
    message = " Try checking:\n"
    for connection, outage in zip(connections, outages, strict=True):
        line = f"  * If {connection} is down"
        if outage is not None:
            line += f" ({outage})"
        message += line + "\n"
    message += (
        "If a connection is down, then wait a bit and try again later.\n"
        'Otherwise, try increasing "timeout" to a longer interval.'
    )
    return message
