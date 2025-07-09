data.landfire.products module
=============================

.. _pfdf.data.landfire.products:

.. py:module:: pfdf.data.landfire.products

Functions that return information about LANDFIRE products. A given LANDFIRE product may have multiple versions, and each version is referred to as a "layer". LANDFIRE uses acronyms to refer to individual products (which may have multiple versions), and you can use these acronyms to filter results in this module.

.. list-table::
    :header-rows: 1

    * - Function
      - Description
    * -
      -
    * - **General Queries**
      -
    * - :ref:`query <pfdf.data.landfire.products.query>`
      - Returns information about queried LANDFIRE layers
    * - :ref:`acronyms <pfdf.data.landfire.products.acronyms>`
      - Returns a list of supported product acronyms
    * - :ref:`layers <pfdf.data.landfire.products.layers>`
      - Returns the names of queried LANDFIRE layers
    * - 
      - 
    * - **Specific Layers**
      - 
    * - :ref:`latest <pfdf.data.landfire.products.latest>`
      - Returns info of the latest version of a specific product
    * - :ref:`layer <pfdf.data.landfire.products.layer>`
      - Returns info on a queried layer

----

General Queries
---------------

.. _pfdf.data.landfire.products.query:

.. py:function:: query(acronym = None, *, timeout = 10)
    :module: pfdf.data.landfire.products

    Returns information about available LANDFIRE layers

    .. dropdown:: Product Info

        ::

            query()
            query(acronym)

        Returns a list of product info dicts for available LANDFIRE layers. By default, returns info for all available products. Use the ``acronym`` input to only return info on products matching the specified acronym. You can retrieve a list of supported acronyms using the :ref:`acronyms <pfdf.data.landfire.products.acronyms>` function.

    .. dropdown:: Timeout

        ::

            query(..., *, timeout)

        Specifies a maximum time in seconds for connecting to the LFPS server. This option is typically a scalar, but may also use a vector with two elements. In this case, the first value is the timeout to connect with the server, and the second value is the time for the server to return the first byte. You can also set timeout to None, in which case API queries will never time out. This may be useful for some slow connections, but is generally not recommended as your code may hang indefinitely if the server fails to respond.

    :Inputs:
        * **acronym** (*str*) -- A product acronym used to filter product info results
        * **timeout** (*scalar | vector*) -- The maximum time in seconds to establish a connection with the LFPS server

    :Outputs:
        *list[dict]* -- A list of product info dicts


.. _pfdf.data.landfire.products.acronyms:

.. py:function:: acronyms(*, timeout = 10)
    :module: pfdf.data.landfire.products

    Returns the list of product acronyms supported by LANDFIRE LFPS

    .. dropdown:: List Acronyms

        ::

            acronyms()

        Queries LANDFIRE and returns the complete list of product acronyms supported by LFPS. These acronyms can be used to query products that have multiple versions.

    .. dropdown:: Timeout

        ::

            acronyms(*, timeout)

        Specifies a maximum time in seconds for connecting to the LFPS server. This option is typically a scalar, but may also use a vector with two elements. In this case, the first value is the timeout to connect with the server, and the second value is the time for the server to return the first byte. You can also set timeout to None, in which case API queries will never time out. This may be useful for some slow connections, but is generally not recommended as your code may hang indefinitely if the server fails to respond.

    :Inputs:
        * **timeout** (*scalar | vector*) -- The maximum time in seconds to establish a connection with the LFPS server

    :Outputs:
        *list[str]* -- The list of product acronyms supported by LFPS


.. _pfdf.data.landfire.products.layers:

.. py:function:: layers(acronym = None, *, timeout = 10)
    :module: pfdf.data.landfire.products

    Returns the names of LANDFIRE layers

    .. dropdown:: List Layer Names

        ::

            layers()
            layers(acronym)

        Returns the names of LANDFIRE layers. By default, returns the names of all LANDFIRE layers available via LFPS. Use the ``acronym`` input to only return the names of layers matching the specified acronym. You can retrieve a list of supported acronyms using the :ref:`acronyms <pfdf.data.landfire.products.acronyms>` function.

    .. dropdown:: Timeout

        ::

            layers(..., *, timeout)

        Specifies a maximum time in seconds for connecting to the LFPS server. This option is typically a scalar, but may also use a vector with two elements. In this case, the first value is the timeout to connect with the server, and the second value is the time for the server to return the first byte. You can also set timeout to None, in which case API queries will never time out. This may be useful for some slow connections, but is generally not recommended as your code may hang indefinitely if the server fails to respond.

    :Inputs:
        * **acronym** (*str*) -- A product acronym used to filter layer names
        * **timeout** (*scalar | vector*) -- The maximum time in seconds to establish a connection with the LFPS server

    :Outputs:
        *list[str]* -- A list of LANDFIRE layer names
        


Specific Layers
---------------

.. _pfdf.data.landfire.products.latest:

.. py:function:: latest(acronym, *, timeout = 10)
    :module: pfdf.data.landfire.products

    Returns info on the latest version of a specific product

    .. dropdown:: Latest Version

        ::

            latest(acronym)

        Returns the product info dict for the latest version of the LANDFIRE product matching the queried acronym.

    .. dropdown:: Timeout

        ::

            latest(..., *, timeout)

        Specifies a maximum time in seconds for connecting to the LFPS server. This option is typically a scalar, but may also use a vector with two elements. In this case, the first value is the timeout to connect with the server, and the second value is the time for the server to return the first byte. You can also set timeout to None, in which case API queries will never time out. This may be useful for some slow connections, but is generally not recommended as your code may hang indefinitely if the server fails to respond.

    :Inputs:
        * **acronym** (*str*) -- The acronym of the product whose latest version should be determined
        * **timeout** (*scalar | vector*) -- The maximum time in seconds to establish a connection with the LFPS server

    :Output:
        *dict* -- The product info dict of the latest version of the queried product
        

.. _pfdf.data.landfire.products.layer:

.. py:function:: layer(layer, *, timeout = 10)
    :module: pfdf.data.landfire.products

    Returns the product info dict for a queried layer

    .. dropdown:: Layer Info

        ::

            layer(layer)

        Returns the product info dict for the queried LANDFIRE layer.

    .. dropdown:: Timeout

        ::

            layer(..., *, timeout)

        Specifies a maximum time in seconds for connecting to the LFPS server. This option is typically a scalar, but may also use a vector with two elements. In this case, the first value is the timeout to connect with the server, and the second value is the time for the server to return the first byte. You can also set timeout to None, in which case API queries will never time out. This may be useful for some slow connections, but is generally not recommended as your code may hang indefinitely if the server fails to respond.

    :Inputs:
        * **layer** (*str*) -- The name of the LANDFIRE layer whose info should be returned
        * **timeout** (*scalar | vector*) -- The maximum time in seconds to establish a connection with the LFPS server

    :Outputs:
        *dict* -- The product info dict for the queried layer
        