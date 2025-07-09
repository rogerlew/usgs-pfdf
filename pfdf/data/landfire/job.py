"""
Functions that interact with LFPS jobs
----------
These functions support interactions with LFPS jobs. LFPS jobs are used to collect
data from the LANDFIRE catalog into downloadable zip archives. You can submit a job
using the `submit` command. After submission, the job is executed asynchronously, and
you can query a job's status using the `query` or `status` commands. Once complete, the
job will contain the zip archive download URL in the JSON response.
----------
Functions:
    submit      - Submits a job to LANDFIRE LFPS and returns the job ID
    status      - Queries the status of an LFPS job and returns the JSON response
    status_code - Returns the status code of a queried LFPS job

Internal:
    _job_error  - Returns an informative error for a failed job status query
"""

from __future__ import annotations

import typing

from pfdf.data._utils import requests
from pfdf.data.landfire import _validate, url
from pfdf.errors import DataAPIError

if typing.TYPE_CHECKING:
    from typing import Optional

    from pfdf.typing.core import strs, timeout
    from pfdf.typing.raster import BoundsInput


def submit(
    layers: strs, bounds: BoundsInput, email: str, *, timeout: Optional[timeout] = 10
) -> str:
    """
    Submits a job to LFPS and returns the job ID
    ----------
    submit(layers, bounds, email)
    Submits a job for the indicated LFPS data layers in the specified bounding box.
    Returns the job ID upon successful job submission.

    You can use the `pfdf.data.landfire.products.layers` function to find a list of
    supported LFPS layer names. The `layers` input may be a string, or a sequence of
    strings. The `bounds` input may be any BoundingBox-like input, and must have a CRS.
    The LFPS job will restrict layer data to this bounding box. Finally, an email
    address is required for job submission - this is used by LFPS to track usage
    statistics.

    submit(..., *, timeout)
    Specifies a maximum time in seconds for connecting to
    the LFPS server. This option is typically a scalar, but may also use a vector with
    two elements. In this case, the first value is the timeout to connect with the
    server, and the second value is the time for the server to return the first byte.
    You can also set timeout to None, in which case API queries will never time out.
    This may be useful for some slow connections, but is generally not recommended as
    your code may hang indefinitely if the server fails to respond.
    ----------
    Inputs:
        layers: The LANDFIRE layers that should be included in the job
        bounds: A bounding box for the job
        email: An email address associated with the job submission
        timeout: The maximum time in seconds to establish a connection with the LFPS server

    Outputs:
        str: The ID of the newly submitted job
    """

    base_url = url.job("submit")
    params = _validate.submit_job(layers, bounds, email)
    response = requests.json(base_url, params, timeout, "LANDFIRE LFPS")
    return _validate.field(response, "jobId", "job ID")


def status(id: str, *, timeout: Optional[timeout] = 10, strict: bool = True) -> dict:
    """
    Queries an LFPS job's status and returns the JSON response
    ----------
    status(id)
    status(..., *, strict=False)
    Queries a LFPS job's status and returns the JSON response. By default, raises an
    error if the JSON response indicates a query failure. Set strict=False to return
    the response for failed queries (useful for debugging).

    status(..., *, timeout)
    Specifies a maximum time in seconds for connecting to
    the LFPS server. This option is typically a scalar, but may also use a vector with
    two elements. In this case, the first value is the timeout to connect with the
    server, and the second value is the time for the server to return the first byte.
    You can also set timeout to None, in which case API queries will never time out.
    This may be useful for some slow connections, but is generally not recommended as
    your code may hang indefinitely if the server fails to respond.
    ----------
    Inputs:
        id: The ID of the LFPS job to query
        strict: True (default) to raise an error if the JSON response indicates a query
            failure. False to return all JSON responses.
        timeout: The maximum time in seconds to establish a connection with the LFPS server

    Outputs:
        dict: The JSON response for an LFPS job status query
    """

    # Query the job
    base_url = url.job("status")
    params = _validate.job_status(id)
    job = requests.json(base_url, params, timeout, "LANDFIRE LFPS")

    # Optionally stop if there were errors
    if strict and "success" in job and job["success"] == False:
        raise _job_error(job, id)
    return job


def status_code(id: str, *, timeout: Optional[timeout] = 10) -> str:
    """
    Returns the status code of a queried LFPS job
    ----------
    status_code(id)
    Returns the status code of the queried LFPS job. The status code will be one of the
    following strings: Pending, Executing, Succeeded, Failed, or Canceled. Raises an
    error if the job ID does not exist on the LFPS system.

    status_code(..., *, timeout)
    Specifies a maximum time in seconds for connecting to
    the LFPS server. This option is typically a scalar, but may also use a vector with
    two elements. In this case, the first value is the timeout to connect with the
    server, and the second value is the time for the server to return the first byte.
    You can also set timeout to None, in which case API queries will never time out.
    This may be useful for some slow connections, but is generally not recommended as
    your code may hang indefinitely if the server fails to respond.
    ----------
    Inputs:
        id: An LFPS job ID
        timeout: The maximum time in seconds to establish a connection with the LFPS server

    Outputs:
        str: The status of the queried job
    """

    job = status(id, timeout=timeout, strict=True)
    return _validate.field(job, "status", "job status code")


def _job_error(job: dict, id: str) -> ValueError | DataAPIError:
    "Returns an informative error for a failed job status query"

    # Parse any job messages
    if "message" in job and isinstance(job["message"], str):
        message = job["message"]

        # Informative error if the job is missing
        if message == "JobId not found":
            return ValueError(
                f"The queried job ({id}) could not be found on the LFPS server.\n"
                f"Try checking that the job ID is spelled correctly.\n"
                f"If you submitted the job a while ago, "
                f"then the job may have been deleted."
            )

        # Otherwise, provide as much error info as possible
        else:
            return DataAPIError(
                f"LANDFIRE LFPS reported the following error in the API query "
                f"for job {id}:\n{message}",
            )

    # If there's no message, just indicate that an error occurred
    else:
        return DataAPIError(
            f"LANDFIRE LFPS reported an error in the API query for job {id}"
        )
