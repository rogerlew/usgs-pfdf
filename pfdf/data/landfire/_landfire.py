"""
Functions to acquire data from LFPS
----------
Functions:
    read            - Read data from a LFPS raster dataset as a Raster object
    download        - Downloads a LFPS data product to the local file system

Utilities:
    _execute_job    - Queries a job until it succeeds or times out
    _check_status   - Checks if a job has succeeded
"""

from __future__ import annotations

import typing
from pathlib import Path
from tempfile import TemporaryDirectory
from time import sleep

import pfdf._validate.core as cvalidate
from pfdf.data._utils import requests, unzip
from pfdf.data.landfire import _validate, job
from pfdf.errors import DataAPIError, InvalidLFPSJobError, LFPSJobTimeoutError
from pfdf.raster import Raster

if typing.TYPE_CHECKING:
    from typing import Optional

    from pfdf.typing.core import Pathlike, timeout
    from pfdf.typing.raster import BoundsInput


#####
# User Functions
#####


def download(
    layer: str,
    bounds: BoundsInput,
    email: str,
    *,
    parent: Optional[Pathlike] = None,
    name: Optional[str] = None,
    timeout: Optional[timeout] = 10,
    max_job_time: Optional[float] = 60,
    refresh_rate: float = 15,
) -> Path:
    """
    Download a product from LANDFIRE LFPS
    ----------
    download(layer, bounds, email)
    Downloads data files for the indicated data layer to the local file system. The
    `layer` should be the name of an LFPS raster layer. You can find a list of LFPS
    layer names here: https://lfps.usgs.gov/helpdocs/productstable.html
    The `bounds` input is used to limit the size of the data query, and should be a
    BoundingBox-like input with a CRS. the command will only download data within this
    domain. Finally, you must provide an email address, which LFPS uses to track usage
    statistics.

    By default, this command will download data into a folder named "landfire-<layer>"
    within the current directory, but see below for other path options. Raises an
    error if the path already exists. Returns the path to the data folder upon
    successful completion of a download.

    download(..., *, parent)
    download(..., *, name)
    Options for downloading the the data folder. The `parent` option is the path to the
    parent folder where the data folder should be downloaded. If a relative path, then
    `parent` is interpreted relative to the current folder. Use `name` to set the name
    of the downloaded data folder. Rases an error if the path to the data folder already
    exists.

    download(..., *, max_job_time)
    download(..., *, refresh_rate)
    download(..., *, timeout)
    Timing parameters for the download. When you request a product from LFPS, the system creates
    a job for the product, and then processes the job before the data can be downloaded.
    Use `max_job_time` to specify the maximum number of seconds that this command should
    wait for the job to finish (default = 60 seconds). Raises a LFPSJobTimeoutError if
    the job exceeds this limit. Alternatively, set max_job_time=None to allow any amount
    of time - this may be useful for some large queries, but is generally not
    recommended as your code may hang indefinitely if the job is slow.

    After the job has been created, this command will query the API on a fixed interval
    to check if the job has completed processing. Use the `refresh_rate` option to
    specify this fixed interval (in seconds - default is every 15 seconds). The refresh
    rate must be a value between 15 (seconds) and 3600 (1 hour).

    Finally, the "timeout" option specifies a maximum time in seconds for connecting to
    the LFPS server. This option is typically a scalar, but may also use a vector with
    two elements. In this case, the first value is the timeout to connect with the
    server, and the second value is the time for the server to return the first byte.
    You can also set timeout to None, in which case API queries will never time out.
    This may be useful for some slow connections, but is generally not recommended as
    your code may hang indefinitely if the server fails to respond.
    ----------
    Inputs:
        layer: The name of a LFPS data layer
        bounds: The bounding box in which data should be downloaded
        email: An email address associated with the data request
        parent: The path to the parent folder where the data folder should be downloaded.
            Defaults to the current folder.
        name: The name for the downloaded data folder. Defaults to landfire-<layer>
        max_job_time: A maximum allowed time (in seconds) for a job to complete processing
        refresh_rate: The frequency (in seconds) at which this command should check the
            status of a submitted job.
        timeout: The maximum time in seconds to establish a connection with the LFPS server

    Outputs:
        Path: The path to the downloaded data folder
    """

    # Validate. Only a single layer is supported
    layer = _validate.layer(layer)
    path = cvalidate.download_path(
        parent, name, default_name=f"landfire-{layer}", overwrite=False
    )
    max_job_time = _validate.max_job_time(max_job_time)
    refresh_rate = _validate.refresh_rate(refresh_rate)

    # Submit job. Query status until the job succeeds or times out. Get the download
    # URL and extract the download ID. (Note that this differs from the processing ID
    # used to query the job). Download the dataset.
    id = job.submit(layer, bounds, email, timeout=timeout)
    url = _execute_job(id, max_job_time, refresh_rate, timeout)
    id = Path(url).stem
    data = requests.content(url, {}, timeout, "LANDFIRE LFPS")

    # Unzip the dataset in a temp folder
    with TemporaryDirectory() as temp:
        extracted = Path(temp) / "extracted"
        unzip(data, extracted)

        # Replace the job ID in filenames with the download name. Note that the
        # download job ID is different from the processing job ID used for queries
        for file in list(extracted.iterdir()):
            filename = file.name
            if id in filename:
                filename = filename.replace(id, path.name)
                file.rename(extracted / filename)

        # Also rename the folder and return the final path
        extracted.rename(path)
    return path


def read(
    layer: str,
    bounds: BoundsInput,
    email: str,
    *,
    timeout: Optional[timeout] = 10,
    max_job_time: Optional[float] = 60,
    refresh_rate: float = 15,
) -> Raster:
    """
    Reads a LANDFIRE raster into memory as a Raster object
    ----------
    read(layer, bounds, email)
    Reads data from a LFPS raster dataset into memory as a Raster object. The
    `layer` should be the name of an LFPS raster layer. You can find a list of LFPS
    layer names here: https://lfps.usgs.gov/helpdocs/productstable.html
    The `bounds` input is used to limit the size of the data query, and should be a
    BoundingBox-like input with a CRS. The command will only read data from within this
    bounding box. Finally, you must provide an email address, which LFPS uses to track
    usage statistics.

    read(..., *, max_job_time)
    read(..., *, refresh_rate)
    read(..., *, timeout)
    Timing parameters for the data read. When you request from LFPS, the system creates
    a job for the product, and then processes the job before the data can be downloaded.
    Use `max_job_time` to specify the maximum number of seconds that this command should
    wait for the job to finish (default = 60 seconds). Raises a LFPSJobTimeoutError if
    the job exceeds this limit. Alternatively, set max_job_time=None to allow any amount
    of time - this may be useful for some large queries, but is generally not
    recommended as your code may hang indefinitely if the job is slow.

    After the job has been created, this command will query the API on a fixed interval
    to check if the job has completed processing. Use the `refresh_rate` option to
    specify this fixed interval (in seconds - default is every 15 seconds). The refresh
    rate must be a value between 15 (seconds) and 3600 (1 hour).

    Finally, the "timeout" option specifies a maximum time in seconds for connecting to
    the LFPS server. This option is typically a scalar, but may also use a vector with
    two elements. In this case, the first value is the timeout to connect with the
    server, and the second value is the time for the server to return the first byte.
    You can also set timeout to None, in which case API queries will never time out.
    This may be useful for some slow connections, but is generally not recommended as
    your code may hang indefinitely if the server fails to respond.
    ----------
    Inputs:
        layer: The name of a LFPS data layer
        bounds: The bounding box in which data should be read
        email: An email address associated with the data request
        max_job_time: A maximum allowed time (in seconds) for a job to complete processing
        refresh_rate: The frequency (in seconds) at which this command should check the
            status of a submitted job.
        timeout: The maximum time in seconds to establish a connection with the LFPS server

    Outputs:
        Raster: The queried LANDFIRE raster dataset
    """

    # Download the data layer into a temp folder
    with TemporaryDirectory() as temp:
        parent = Path(temp)
        download(
            layer,
            bounds,
            email,
            parent=parent,
            name="data",
            timeout=timeout,
            max_job_time=max_job_time,
            refresh_rate=refresh_rate,
        )

        # Ensure the file was a raster
        path = parent / "data" / "data.tif"
        if not path.exists():
            raise FileNotFoundError(
                f"Could not locate a raster dataset for the layer ({layer}). "
                "If you are trying to access a non-raster dataset, "
                "then use the `download` command instead."
            )

        # Load and return the raster dataset
        return Raster.from_file(path)


#####
# Utilities
#####


def _execute_job(
    id: str, max_job_time: float, refresh_rate: float, timeout: timeout
) -> dict:
    "Queries a job until it succeeds or times out"

    # Wait several seconds, then query the job status
    while max_job_time > 0:
        sleep(refresh_rate)
        info = job.status(id, timeout=timeout, strict=True)
        status = _validate.field(info, "status", "job status")
        succeeded = _check_status(id, status)

        # If successful, return the download URL. Otherwise, reduce the timeout clock
        if succeeded:
            url = _validate.field(info, "outputFile", '"outputFile" download URL')
            return url
        max_job_time -= refresh_rate

    # Informative error if timed out
    raise LFPSJobTimeoutError(
        f"LANDFIRE LFPS took too long to process job {id}. Either try using a "
        f"smaller bounding box, or try again later if the server is running slowly.",
        id,
    )


def _check_status(id: str, status: str) -> bool:
    "Checks that a job has succeeded, or provides an informative error if it failed"

    # Extract completion status. Return boolean for valid status codes
    if status in ["Pending", "Executing"]:
        return False
    elif status == "Succeeded":
        return True

    # Informative error if the job failed
    if status == "Canceled":
        raise InvalidLFPSJobError(
            f"Cannot download job {id} because the job was cancelled. "
            f"Try submitting a new job.",
            id,
        )
    elif status == "Failed":
        raise InvalidLFPSJobError(
            f"Cannot download job {id} because the job failed. "
            f"Try submitting a new job with different parameters.",
            id,
        )
    else:
        raise DataAPIError(
            f"LANDFIRE LFPS returned an unrecognized status code: {status}"
        )
