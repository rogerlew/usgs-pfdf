"""
Functions that validate LFPS query parameters
----------
Individual inputs:
    layer           - Checks an input represents a single data layer
    job_time        - Ensures a timing parameter is a number greater than 15
    max_job_time    - Checks an input represents the maximum job time
    refresh_rate    - Checks an input represents a refresh rate

Request parameters:
    submit_job      - Checks that job submission parameters are valid
    job_status      - Checks that job status query parameters are valid

Response:
    field           - Returns a field from an LFPS JSON response
"""

from __future__ import annotations

import typing
from math import inf

import pfdf._validate.core as cvalidate
from pfdf._utils import real
from pfdf.data._utils import validate
from pfdf.errors import MissingAPIFieldError

if typing.TYPE_CHECKING:
    from typing import Any


#####
# Individual inputs
#####


def layer(layer: Any) -> str:
    "Checks an input represents a single data layer"

    layer = cvalidate.string(layer, "layer")
    if ";" in layer:
        raise ValueError("layer cannot contain semicolons (;)")
    return layer


def job_time(time: Any, name: str) -> float:
    "Ensures a job querying parameter is a float >= 15 (seconds)"
    time = cvalidate.scalar(time, name, dtype=real)
    cvalidate.inrange(time, name, min=15)
    return float(time)


def max_job_time(time: Any) -> float:
    if time is None:
        return inf
    else:
        return job_time(time, "max_job_time")


def refresh_rate(time: Any) -> float:
    time = job_time(time, "refresh_rate")
    if time > 3600:
        raise ValueError("refresh_rate cannot be greater than 3600 seconds (1 hour)")
    return time


#####
# Request parameters
#####


def submit_job(layers: Any, bounds: Any, email: Any) -> dict:
    "Checks that job submission parameters are valid"
    return {
        "Layer_List": validate.strings(layers, "layers", delimiter=";"),
        "Area_of_Interest": validate.bounds(bounds, delimiter=" "),
        "Email": cvalidate.string(email, "email"),
    }


def job_status(id: str) -> dict:
    "Checks that job status query parameters are valid"
    return {"JobId": cvalidate.string(id, "job id")}


#####
# Response fields
#####


def field(response: dict, field: str, description: str) -> Any:
    "Returns a field from an LFPS JSON response"
    if field not in response or response[field] == "":
        raise MissingAPIFieldError(f"LANDFIRE LFPS failed to return the {description}")
    return response[field]
