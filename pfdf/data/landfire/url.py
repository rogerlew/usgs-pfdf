"""
Functions that return URLs used to query the LANDFIRE LFPS API
----------
The functions in this module return base URLs for the API, as well as URLs that
incorporate query parameters. Note that these functions do not actually query the API
themselves - instead, they return URLs that can be used to implement such queries.
----------
Base URLs:
    api         - Returns the base URL for the LANDFIRE LFPS API
    products    - Returns the base URL used to query LANDFIRE product info
    job         - Returns base URLs for job queries

Jobs:
    submit_job  - Returns the URL used to submit a job
    job_status  - Returns the URL used to query a job's status

Internal:
    _query  - Returns the base URL for a specific API query
"""

from __future__ import annotations

import typing

import pfdf._validate.core as cvalidate
from pfdf.data._utils import requests
from pfdf.data.landfire import _validate

if typing.TYPE_CHECKING:
    from typing import Literal, Optional

    from pfdf.typing.core import strs
    from pfdf.typing.raster import BoundsInput

    JobAction = Literal["cancel", "status", "submit"]


#####
# Base URLs
#####


def api() -> str:
    """
    Returns the base URL to the LANDFIRE LFPS API
    ----------
    api()
    Returns the base URL to the LANDFIRE LFPS API
    ----------
    Outputs:
        str: The API URL
    """
    return "https://lfps.usgs.gov/api"


def _query(query: str) -> str:
    "Returns the base URL for a given API query"
    return f"{api()}/{query}"


def products() -> str:
    """
    Returns the base URL used to query API products
    ----------
    products()
    Returns the base URL used to query API products.
    ----------
    Outputs:
        str: The base URL
    """
    return _query("products")


def job(action: Optional[JobAction] = None) -> str:
    """
    Returns the base URLs for job queries
    ----------
    job()
    Returns the base URL for job queries.

    job(action)
    Returns the base URL used to implement a particular job action. Supported job
    actions are "submit", "status", and "cancel".
    ----------
    Inputs:
        action: A job action whose base URL should be returned

    Outputs:
        str: The base URL for a job query
    """

    url = _query("job")
    if action is not None:
        action = cvalidate.option(
            action, "action", allowed=["cancel", "status", "submit"]
        )
        url = f"{url}/{action}"
    return url


#####
# Job queries
#####


def submit_job(
    layers: strs, bounds: BoundsInput, email: str, *, decode: bool = False
) -> str:
    """
    Returns the URL used to submit a job
    ----------
    submit_job(layers, bounds, email)
    submit_job(..., *, decode=True)
    Returns the URL used to submit a job. The `layers` input should be a string or
    sequence of strings indicating the LANDFIRE layers included in the job. The `bounds`
    input should be a BoundingBox-like input, and must have a CRS. The email address
    must be a string, and is used by LANDFIRE to track usage statistics. By default,
    returns a percent encoded URL. Set decode=True to return a decoded URL instead.
    ----------
    Inputs:
        layers: A list of LANDFIRE layers to include in the job
        bounds: The bounding box for the job
        email: An email address associated with the job
        decode: True to return a decoded URL. False (default) to return a percent
            encoded URL

    Outputs:
        str: The URL for the job submission
    """

    base = job("submit")
    params = _validate.submit_job(layers, bounds, email)
    return requests.query_url(base, params, decode)


def job_status(id: str, *, decode: bool = False) -> str:
    """
    Returns the URL used to query a job's status
    ----------
    job_status(id)
    job_status(..., *, decode=True)
    Returns the URL used to query the status of the job with the indicated processing
    ID. By default, returns a percent encoded URL. Set decode=True to return a decoded
    URL instead.
    ----------
    Inputs:
        id: The processing ID of the queried job
        decode: True to return a decoded URL. False (default) to return a percent
            encoded URL

    Outputs:
        str: The URL used to query a job's status
    """

    base = job("status")
    params = _validate.job_status(id)
    return requests.query_url(base, params, decode)
