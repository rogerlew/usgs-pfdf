data.landfire.job module
========================

.. _pfdf.data.landfire.job:

.. py:module:: pfdf.data.landfire.job

Functions for interacting with jobs on the `LANDFIRE Product Service (LFPS) <https://lfps.usgs.gov>`_

.. list-table::
    :header-rows: 1

    * - Function
      - Description
    * - :ref:`submit <pfdf.data.landfire.job.submit>`
      - Submits a job to LANDFIRE LFPS and returns the job ID
    * - :ref:`status <pfdf.data.landfire.job.status>`
      - Queries the status of an LFPS job and returns the JSON response
    * - :ref:`status_code <pfdf.data.landfire.job.status_code>`
      - Returns the status code of a queried LFPS job

----

.. _pfdf.data.landfire.job.submit:

.. py:function:: submit(layers, bounds, email, *, timeout = 10)
    :module: pfdf.data.landfire.job

    Submits a job to LFPS and returns the job ID

    .. dropdown:: Submit Job

        ::
            
            submit(layers, bounds, email)

        Submits a job for the indicated LFPS data layers in the specified bounding box. Returns the job ID upon successful job submission.

        You can use the :ref:`landfire.products.layers <pfdf.data.landfire.products.layers>` function to find a list of supported LFPS layer names. The ``layers`` input may be a string, or a sequence of strings. The ``bounds`` input may be any BoundingBox-like input, and must have a CRS. The LFPS job will restrict layer data to this bounding box. Finally, an email address is required for job submission - this is used by LFPS to track usage statistics.

    .. dropdown:: Timeout

        ::

            submit(..., *, timeout)

        Specifies a maximum time in seconds for connecting to the LFPS server. This option is typically a scalar, but may also use a vector with two elements. In this case, the first value is the timeout to connect with the server, and the second value is the time for the server to return the first byte. You can also set timeout to None, in which case API queries will never time out. This may be useful for some slow connections, but is generally not recommended as your code may hang indefinitely if the server fails to respond.

    :Inputs:
        * **layers** (*str | list[str]*) -- The LANDFIRE layers that should be included in the job
        * **bounds** (*BoundingBox-like*) -- A bounding box for the job
        * **email** (*str*) -- An email address associated with the job submission
        * **timeout** (*scalar | vector*) -- The maximum time in seconds to establish a connection with the LFPS server

    :Outputs:
        *str* -- The ID of the newly submitted job


.. _pfdf.data.landfire.job.status:

.. py:function:: status(id, *, timeout = 10, strict = True)
    :module: pfdf.data.landfire.job

    Queries an LFPS job's status and returns the JSON response

    .. dropdown:: Job Status

        ::

            status(id)
            status(..., *, strict=False)

        Queries a LFPS job's status and returns the JSON response. By default, raises an error if the JSON response indicates a query failure. Set strict=False to return the response for failed queries (useful for debugging).

    .. dropdown:: Timeout

        ::
    
            status(..., *, timeout)

        Specifies a maximum time in seconds for connecting to the LFPS server. This option is typically a scalar, but may also use a vector with two elements. In this case, the first value is the timeout to connect with the server, and the second value is the time for the server to return the first byte. You can also set timeout to None, in which case API queries will never time out. This may be useful for some slow connections, but is generally not recommended as your code may hang indefinitely if the server fails to respond.

    :Inputs:
        * **id** (*str*) -- The ID of the LFPS job to query
        * **strict** (*bool*) -- True (default) to raise an error if the JSON response indicates a query failure. False to return all JSON responses.
        * **timeout** (*scalar | vector*) -- The maximum time in seconds to establish a connection with the LFPS server

    :Outputs:
        *dict* -- The JSON response for an LFPS job status query
    

.. _pfdf.data.landfire.job.status_code:

.. py:function:: status_code(id, *, timeout = 10)
    :module: pfdf.data.landfire.job

    Returns the status code of a queried LFPS job

    .. dropdown:: Status Code

        ::
    
            status_code(id)

        Returns the status code of the queried LFPS job. The status code will be one of the following strings: Pending, Executing, Succeeded, Failed, or Canceled. Raises an error if the job ID does not exist on the LFPS system.

    .. dropdown:: Timeout

        ::
    
            status_code(..., *, timeout)

        Specifies a maximum time in seconds for connecting to the LFPS server. This option is typically a scalar, but may also use a vector with two elements. In this case, the first value is the timeout to connect with the server, and the second value is the time for the server to return the first byte. You can also set timeout to None, in which case API queries will never time out. This may be useful for some slow connections, but is generally not recommended as your code may hang indefinitely if the server fails to respond.

    :Inputs:
        * **id** (*str*) -- An LFPS job ID
        * **timeout** (*scalar | vector*) -- The maximum time in seconds to establish a connection with the LFPS server

    :Outputs:
        *str* -- The status of the queried job
    