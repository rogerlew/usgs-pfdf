"""
Functions that return information about LANDFIRE products
----------
These functions query LFPS for information on available products and layers. A given
LANDFIRE product may have multiple versions, and each version is referred to as a
"layer". LANDFIRE uses acronyms to refer to individual products (which may have multiple
versions), and you can use these acronyms to filter results in this module. You can
find a complete list of supported acronyms using the `acronyms` function, and can
determine the latest version of a given product using the `latest` function.
----------
General Queries:
    query       - Returns information about queried LANDFIRE layers
    acronyms    - Returns a list of supported product acronyms
    layers      - Returns the names of queried LANDFIRE layers

Specific Layers:
    latest      - Returns info of the latest version of a specific product
    layer       - Returns info on a queried layer
"""

from __future__ import annotations

import typing

import pfdf._validate.core as cvalidate
from pfdf.data._utils import requests
from pfdf.data.landfire import _validate, url

if typing.TYPE_CHECKING:
    from typing import Optional

    from pfdf.typing.core import timeout


def query(
    acronym: Optional[str] = None, *, timeout: Optional[timeout] = 10
) -> list[dict]:
    """
    Returns information about available LANDFIRE layers
    ----------
    query()
    query(acronym)
    Returns a list of product info dicts for available LANDFIRE layers. By default,
    returns info for all available products. Use the `acronym` input to only return info
    on products matching the specified acronym. You can retrieve a list of supported
    acronyms using the `acronyms` function.

    query(..., *, timeout)
    The "timeout" option specifies a maximum time in seconds for connecting to
    the LFPS server. This option is typically a scalar, but may also use a vector with
    two elements. In this case, the first value is the timeout to connect with the
    server, and the second value is the time for the server to return the first byte.
    You can also set timeout to None, in which case API queries will never time out.
    This may be useful for some slow connections, but is generally not recommended as
    your code may hang indefinitely if the server fails to respond.
    ----------
    Inputs:
        acronym: A product acronym used to filter product info results
        timeout: The maximum time in seconds to establish a connection with the LFPS server

    Outputs:
        list[dict]: A list of product info dicts
    """

    # Make the request
    base_url = url.products()
    products = requests.json(base_url, {}, timeout, "LANDFIRE LFPS")
    products = _validate.field(products, "products", '"products" field')

    # Optionally sort by acronym
    if acronym is not None:
        cvalidate.string(acronym, "acronym")
        products = [
            product
            for product in products
            if product["acronym"].lower() == acronym.lower()
        ]
    return products


def acronyms(*, timeout: Optional[timeout] = 10) -> list[str]:
    """
    Returns the list of product acronyms supported by LANDFIRE LFPS
    ----------
    acronyms()
    Queries LANDFIRE and returns the complete list of product acronyms supported by
    LFPS. These acronyms can be used to query products that have multiple versions.

    acronyms(*, timeout)
    Specifies a maximum time in seconds for connecting to
    the LFPS server. This option is typically a scalar, but may also use a vector with
    two elements. In this case, the first value is the timeout to connect with the
    server, and the second value is the time for the server to return the first byte.
    You can also set timeout to None, in which case API queries will never time out.
    This may be useful for some slow connections, but is generally not recommended as
    your code may hang indefinitely if the server fails to respond.
    ----------
    Inputs:
        timeout: The maximum time in seconds to establish a connection with the LFPS server

    Outputs:
        list[str]: The list of product acronyms supported by LFPS
    """

    products = query(timeout=timeout)
    acronyms = []
    for product in products:
        acronym = product["acronym"]
        if acronym not in acronyms:
            acronyms.append(acronym)
    return acronyms


def layers(
    acronym: Optional[str] = None, *, timeout: Optional[timeout] = 10
) -> list[str]:
    """
    Returns the names of LANDFIRE layers
    ----------
    layers()
    layers(acronym)
    Returns the names of LANDFIRE layers. By default, returns the names of all LANDFIRE
    layers available via LFPS. Use the `acronym` input to only return the names of
    layers matching the specified acronym. You can retrieve a list of supported acronyms
    using the `acronyms` function.

    layers(..., *, timeout)
    Specifies a maximum time in seconds for connecting to
    the LFPS server. This option is typically a scalar, but may also use a vector with
    two elements. In this case, the first value is the timeout to connect with the
    server, and the second value is the time for the server to return the first byte.
    You can also set timeout to None, in which case API queries will never time out.
    This may be useful for some slow connections, but is generally not recommended as
    your code may hang indefinitely if the server fails to respond.
    ----------
    Inputs:
        acronym: A product acronym used to filter layer names
        timeout: The maximum time in seconds to establish a connection with the LFPS server

    Outputs:
        list[str]: A list of LANDFIRE layer names
    """

    products = query(acronym, timeout=timeout)
    return [product["layerName"] for product in products]


def latest(acronym: str, *, timeout: Optional[timeout] = 10) -> dict:
    """
    Returns info on the latest version of a specific product
    ----------
    latest(acronym)
    Returns the product info dict for the latest version of the LANDFIRE product
    matching the queried acronym.

    latest(..., *, timeout)
    Specifies a maximum time in seconds for connecting to
    the LFPS server. This option is typically a scalar, but may also use a vector with
    two elements. In this case, the first value is the timeout to connect with the
    server, and the second value is the time for the server to return the first byte.
    You can also set timeout to None, in which case API queries will never time out.
    This may be useful for some slow connections, but is generally not recommended as
    your code may hang indefinitely if the server fails to respond.
    ----------
    Inputs:
        acronym: The acronym of the product whose latest version should be determined
        timeout: The maximum time in seconds to establish a connection with the LFPS server

    Output:
        dict: The product info dict of the latest version of the queried product
    """

    # Get the layers matching the acronym
    layers = query(acronym, timeout=timeout)
    if len(layers) == 0:
        raise ValueError(
            f'There are no LANDFIRE LFPS products matching the "{acronym}" acronym'
        )

    # Return the most recent version
    version = "0"
    for layer in layers:
        if layer["version"] > version:
            latest = layer
            version = latest["version"]
    return latest


def layer(layer: str, *, timeout: Optional[timeout] = 10) -> dict:
    """
    Returns the product info dict for a queried layer
    ----------
    layer(layer)
    Returns the product info dict for the queried LANDFIRE layer.

    layer(..., *, timeout)
    Specifies a maximum time in seconds for connecting to
    the LFPS server. This option is typically a scalar, but may also use a vector with
    two elements. In this case, the first value is the timeout to connect with the
    server, and the second value is the time for the server to return the first byte.
    You can also set timeout to None, in which case API queries will never time out.
    This may be useful for some slow connections, but is generally not recommended as
    your code may hang indefinitely if the server fails to respond.
    ----------
    Inputs:
        layer: The name of the LANDFIRE layer whose info should be returned
        timeout: The maximum time in seconds to establish a connection with the LFPS server

    Outputs:
        dict: The product info dict for the queried layer
    """

    # Validate. Use lower case layer name for case-insensitive matching
    cvalidate.string(layer, "layer")
    layer = layer.lower()

    # Return the matching layer
    products = query(timeout=timeout)
    for product in products:
        if product["layerName"].lower() == layer:
            return product

    # Informative error if nothing was found
    raise ValueError(
        f'There are no LANDFIRE LFPS products matching the "{layer}" layer name'
    )
