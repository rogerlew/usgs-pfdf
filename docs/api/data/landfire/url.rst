data.landfire.url module
========================

.. _pfdf.data.landfire.url:

.. py:module:: pfdf.data.landfire.url

Functions that return URLs used to query the LANDFIRE LFPS API. Note that these functions do not actually query the API themselves - instead, they return URLs that can be used to implement such queries.


.. list-table::
    :header-rows: 1

    * - Function
      - Description
    * -
      -
    * - **Base URLs**
      -
    * - :ref:`api <pfdf.data.landfire.url.api>`
      - Returns the base URL for the LANDFIRE LFPS API
    * - :ref:`products <pfdf.data.landfire.url.products>`
      - Returns the base URL used to query LANDFIRE product info
    * - :ref:`job <pfdf.data.landfire.url.job>`
      - Returns base URLs for job queries
    * - 
      - 
    * - **Jobs**
      - 
    * - :ref:`submit_job <pfdf.data.landfire.url.submit_job>`
      - Returns the URL used to submit a job
    * - :ref:`job_status <pfdf.data.landfire.url.job_status>`
      - Returns the URL used to query a job's status

----


Base URLs
---------

.. _pfdf.data.landfire.url.api:

.. py:function:: api()
    :module: pfdf.data.landfire.url

    Returns the base URL to the LANDFIRE LFPS API

    ::

        api()

    :Outputs:
        *str* -- The API URL
        

.. _pfdf.data.landfire.url.products:

.. py:function:: products()
    :module: pfdf.data.landfire.url

    Returns the base URL used to query API products

    ::

        products()

    :Outputs:
        *str* -- The base URL


.. _pfdf.data.landfire.url.job:

.. py:function:: job(action = None)
    :module: pfdf.data.landfire.url

    Returns the base URLs for job queries

    .. dropdown:: Base URL

        ::

            job()

        Returns the base URL for job queries.

    .. dropdown:: Job Action

        ::

            job(action)

        Returns the base URL used to implement a particular job action. Supported job actions are "submit", "status", and "cancel".

    :Inputs:
        * **action** (*str*) -- A job action whose base URL should be returned

    :Outputs:
        *str* -- The base URL for a job query
        



Jobs
----


.. _pfdf.data.landfire.url.submit_job:

.. py:function:: submit_job(layers, bounds, email, *, decode = False)
    :module: pfdf.data.landfire.url

    Returns the URL used to submit a job

    ::

        submit_job(layers, bounds, email)
        submit_job(..., *, decode=True)

    Returns the URL used to submit a job. The ``layers`` input should be a string or sequence of strings indicating the LANDFIRE layers included in the job. The ``bounds`` input should be a BoundingBox-like input, and must have a CRS. The email address must be a string, and is used by LANDFIRE to track usage statistics. By default, returns a percent encoded URL. Set decode=True to return a decoded URL instead.

    :Inputs:
        * **layers** (*str | list[str]*) -- A list of LANDFIRE layers to include in the job
        * **bounds** (*BoundingBox-like*) -- The bounding box for the job
        * **email** (*str*) -- An email address associated with the job
        * **decode** (*bool*) -- True to return a decoded URL. False (default) to return a percent encoded URL

    :Outputs:
        *str* -- The URL for the job submission


.. _pfdf.data.landfire.url.job_status:

.. py:function:: job_status(id, *, decode = False)
    :module: pfdf.data.landfire.url

    Returns the URL used to query a job's status

    ::

        job_status(id)
        job_status(..., *, decode=True)

    Returns the URL used to query the status of the job with the indicated processing ID. By default, returns a percent encoded URL. Set decode=True to return a decoded URL instead.

    :Inputs:
        * **id** (*str*) -- The processing ID of the queried job
        * **decode** (*bool*) -- True to return a decoded URL. False (default) to return a percent encoded URL

    :Outputs:
        *str* -- The URL used to query a job's status
            
