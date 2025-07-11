"""
Functions that validate file/folder paths
----------
Functions:
    _path           - Checks an input represents a Path. Returns the resolved path
    input_file      - Checks an input is an existing path. Note that folders are permitted
    output_file     - Checks an output is a path, optionally allowed overwriting
    download_path   - Checks options for a file download
"""

from __future__ import annotations

import typing
from pathlib import Path

import pfdf._validate.core._low as validate

if typing.TYPE_CHECKING:
    from typing import Any


def _path(path: Any, isparent: bool = False) -> Path:
    "Checks an input represents a Path object and returns the resolved path"

    # Get names
    if isparent:
        name = "parent"
        type_name = "path"
    else:
        name = "path"
        type_name = "filepath"
    if isinstance(path, str):
        path = Path(path)
    validate.type(path, name, Path, type_name)
    return path.resolve()


def input_file(path: Any) -> Path:
    """Checks an input is an existing path. Note that folders are permitted because
    many GIS "files" are actually a structured folder (e.g. geodatabases)"""

    path = _path(path)
    return path.resolve(strict=True)


def output_file(path: Any, overwrite: bool) -> Path:
    "Checks a path is suitable for an output file, optionally allowing overwriting"

    path = _path(path)
    if (not overwrite) and path.exists():
        raise FileExistsError(
            f"Output file already exists:\n\t{path}\n"
            'If you want to replace existing files, set "overwrite=True"'
        )
    return path


def download_path(parent: Any, name: Any, default_name: str, overwrite: bool) -> Path:
    "Checks path options for a data download"

    # Validate parent is a path. Default to current directory
    if parent is None:
        parent = Path.cwd()
    else:
        parent = _path(parent, isparent=True)

    # Validate name
    if name is None:
        name = default_name
    else:
        name = validate.string(name, "name")

    # Optionally prevent overwriting
    path = parent / name
    if path.exists():
        if not overwrite:
            raise FileExistsError(f"Download path already exists:\n\t{path}")
        elif not path.is_file():
            raise FileExistsError(
                f"Cannot overwrite because the current path is not a file:\n\t{path}"
            )
    return path
