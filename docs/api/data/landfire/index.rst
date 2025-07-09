data.landfire package
=====================

.. _pfdf.data.landfire:

.. py:module:: pfdf.data.landfire

Utilities to load `LANDFIRE <https://www.landfire.gov/>`_ datasets, including existing vegetation type (EVT) rasters. This data is accessed via the `LANDFIRE Product Service (LFPS) API <https://lfps.usgs.gov/arcgis/rest/services/LandfireProductService/GPServer>`_. Consult the `LANDFIRE data portal <https://landfire.gov/data>`_ for additional details.

.. list-table::
    :header-rows: 1

    * - Content
      - Description
    * -
      -
    * - **Functions**
      -
    * - :ref:`read <pfdf.data.landfire.read>`
      - Loads LANDFIRE data into memory as a :ref:`Raster <pfdf.raster.Raster>` object
    * - :ref:`download <pfdf.data.landfire.download>`
      - Downloads LANDFIRE data onto the local filesystem.
    * -
      -
    * - **Modules**
      -
    * - :ref:`products <pfdf.data.landfire.products>`
      - Functions that query LFPS for product information
    * - :ref:`job <pfdf.data.landfire.job>`
      - Functions for interacting with LFPS jobs
    * - :ref:`url <pfdf.data.landfire.url>`
      - Functions that return URLs used to query LFPS

----

.. _pfdf.data.landfire.read:

.. py:function:: read(layer, bounds, email, *, timeout = 10, max_job_time = 60, refresh_rate = 15)
    :module: pfdf.data.landfire

    Reads a LANDFIRE raster into memory as a Raster object

    .. dropdown:: Read data

        ::

            read(layer, bounds, email)

        Reads data from a LFPS raster dataset into memory as a :ref:`Raster object <pfdf.raster.Raster>`. The ``layer``` should be the name of an LFPS raster layer. You can find a list of LFPS layer names here: `LFPS Layers <https://lfps.usgs.gov/helpdocs/productstable.html>`_. The ``bounds`` input is used to limit the size of the data query, and should be a BoundingBox-like input with a CRS. The command will only read data from within this bounding box. Finally, you must provide an email address, which LFPS uses to track usage statistics.

    .. dropdown:: Timeout Options

        ::

            read(..., *, max_job_time)
            read(..., *, refresh_rate)
            read(..., *, timeout)

        Timing parameters for the data read. When you request from LFPS, the system creates a job for the product, and then processes the job before the data can be downloaded. Use ``max_job_time`` to specify the maximum number of seconds that this command should wait for the job to finish (default = 60 seconds). Raises a LFPSJobTimeoutError if the job exceeds this limit. Alternatively, set max_job_time=None to allow any amount of time - this may be useful for some large queries, but is generally not recommended as your code may hang indefinitely if the job is slow.

        After the job has been created, this command will query the API on a fixed interval to check if the job has completed processing. Use the ``refresh_rate`` option to specify this fixed interval (in seconds - default is every 15 seconds). The refresh rate must be a value between 15 (seconds) and 3600 (1 hour).

        Finally, the ``timeout`` option specifies a maximum time in seconds for connecting to the LFPS server. This option is typically a scalar, but may also use a vector with two elements. In this case, the first value is the timeout to connect with the server, and the second value is the time for the server to return the first byte.  You can also set timeout to None, in which case API queries will never time out. This may be useful for some slow connections, but is generally not recommended as your code may hang indefinitely if the server fails to respond.

    :Inputs:
        * **layer** (*str*) -- The name of a LFPS data layer
        * **bounds** (*BoundingBox-like*) -- The bounding box in which data should be read
        * **email** (*str*) -- An email address associated with the data request
        * **max_job_time** (*scalar*) -- A maximum allowed time (in seconds) for a job to complete processing
        * **refresh_rate** (*scalar*) -- The frequency (in seconds) at which this command should check the status of a submitted job.
        * **timeout** (*scalar | vector*) -- The maximum time in seconds to establish a connection with the LFPS server

    :Outputs:
        *Raster* -- The queried LANDFIRE raster dataset


.. _pfdf.data.landfire.download:

.. py:function:: download(layer, bounds, email, *, parent = None, name = None, timeout = 10, max_job_time = 60, refresh_rate = 15)
    :module: pfdf.data.landfire

    Download a product from LANDFIRE LFPS

    .. dropdown:: Download Data

        ::

            download(layer, bounds, email)

        Downloads data files for the indicated data layer to the local file system. The ``layer`` should be the name of an LFPS raster layer. You can find a list of LFPS layer names here: `LFPS Layers <https://lfps.usgs.gov/helpdocs/productstable.html>`_. The ``bounds`` input is used to limit the size of the data query, and should be a BoundingBox-like input with a CRS. the command will only download data within this domain. Finally, you must provide an email address, which LFPS uses to track usage statistics.

        By default, this command will download data into a folder named ``landfire-<layer>`` within the current directory, but refer below for other path options. Raises an error if the path already exists. Returns the path to the data folder upon successful completion of a download.

    .. dropdown:: File Path

        ::

            download(..., *, parent)
            download(..., *, name)

        Options for downloading the the data folder. The ``parent`` option is the path to the parent folder where the data folder should be downloaded. If a relative path, then parent is interpreted relative to the current folder. Use ``name`` to set the name of the downloaded data folder. Rases an error if the path to the data folder already exists.

    .. dropdown:: Timeout Options

        ::

            download(..., *, max_job_time)
            download(..., *, refresh_rate)
            download(..., *, timeout)

        Timing parameters for the download. When you request a product from LFPS, the system creates a job for the product, and then processes the job before the data can be downloaded. Use ``max_job_time`` to specify the maximum number of seconds that this command should wait for the job to finish (default = 60 seconds). Raises a LFPSJobTimeoutError if the job exceeds this limit. Alternatively, set max_job_time=None to allow any amount of time - this may be useful for some large queries, but is generally not recommended as your code may hang indefinitely if the job is slow.

        After the job has been created, this command will query the API on a fixed interval to check if the job has completed processing. Use the ``refresh_rate`` option to specify this fixed interval (in seconds - default is every 15 seconds). The refresh rate must be a value between 15 (seconds) and 3600 (1 hour).

        Finally, the ``timeout`` option specifies a maximum time in seconds for connecting to the LFPS server. This option is typically a scalar, but may also use a vector with two elements. In this case, the first value is the timeout to connect with the server, and the second value is the time for the server to return the first byte. You can also set timeout to None, in which case API queries will never time out. This may be useful for some slow connections, but is generally not recommended as your code may hang indefinitely if the server fails to respond.

    :Inputs:
        * **layer** (*str*) -- The name of a LFPS data layer
        * **bounds** (*BoundingBox-like*) -- The bounding box in which data should be downloaded
        * **email** (*str*) -- An email address associated with the data request
        * **parent** (*Path-like*) -- The path to the parent folder where the data folder should be downloaded. Defaults to the current folder.
        * **name** (*str*) -- The name for the downloaded data folder. Defaults to landfire-<layer>
        * **max_job_time** (*scalar*) -- A maximum allowed time (in seconds) for a job to complete processing
        * **refresh_rate** (*scalar*) -- The frequency (in seconds) at which this command should check the status of a submitted job.
        * **timeout** (*scalar | vector*) -- The maximum time in seconds to establish a connection with the LFPS server

    :Outputs:
        *Path* -- The path to the downloaded data folder

----

.. toctree::
    
    products module <products>
    job module <job>
    url module <url>