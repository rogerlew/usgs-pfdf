data package
============

The :ref:`data package <pfdf.data>` contains modules with routines to download commonly-used datasets from the internet. Users should not feel obligated to use these specific datasets. Instead, this package is intended to simplify the data acquisition process for certain common workflows.

The data acquisition utilities are organized into subpackages by different data providers. Currently, these include:

* :ref:`landfire <pfdf.data.landfire>`: `LANDFIRE`_ datasets, including existing vegetation type (EVT) rasters
* :ref:`noaa <pfdf.data.noaa>`: `NOAA`_ datasets, including precipitation frequency estimates from NOAA Atlas 14
* :ref:`retainments <pfdf.data.retainments>`: Locations of debris retainment features, and
* :ref:`usgs <pfdf.data.usgs>`: Various `USGS`_ datasets, including DEMs, STATSGO soil data, and HUC boundaries

Most datasets are ultimately accessed via a ``read`` and/or ``download`` function in their associated module. A ``read`` function will read a raster dataset from a data server, and return the dataset as a Raster object. A ``download`` function will download one or more files onto the local file system. This is more common for vector feature datasets, and datasets that bundle multiple rasters.

Many of these data subpackages also include low-level functions for querying data provider APIs. Most users will not need these API utilities, but developers may find them useful for acquiring datasets not directly supported by pfdf, as well as for troubleshooting API responses.

The remainder of this page outlines the contents of the ``data`` package, and the :doc:`Data Tutorial </tutorials/notebooks/03_Download_Data>` demonstrates several common use cases.

.. _LANDFIRE: https://www.landfire.gov/
.. _NOAA: https://www.noaa.gov
.. _NOAA Atlas 14: https://hdsc.nws.noaa.gov/pfds/
.. _USGS: https://www.usgs.gov


LANDFIRE
--------
The landfire package contains routines for accessing data from the `LANDFIRE Product Service (LFPS) <https://lfps.usgs.gov/>`_. The LFPS provides access to a variety of land use and wildfire datasets that may be useful for pfdf users. These include existing vegetation type (EVT) rasters, which are often used to build water and human-development masks. You can find additional information on LFPS products here: `LANDFIRE Data Portal <https://landfire.gov/data>`_.

Most users will want to start with the :ref:`read function <pfdf.data.landfire.read>`. This function streams data from a LANDFIRE raster data layer within a bounding box - the read data is returned as a Raster object. Alternatively, use the :ref:`download command <pfdf.data.landfire.download>` to save a product to the local file system. Unlike the ``read`` function, the ``download`` command can be used to acquire datasets derived from vector features. You can find a list of available data layer names here: `LANDFIRE Layers <https://lfps.usgs.gov/products>`_.

This package also includes the :ref:`products <pfdf.data.landfire.products>`, :ref:`job <pfdf.data.landfire.job>`, and :ref:`url <pfdf.data.landfire.url>` modules, which can be used for low-level interactions with LFPS. Most users will not need these modules, but developers may find them useful for custom data acquisition routines. In brief, the typical workflow is to:

1. Submit a job request for a data product
2. Wait/Query the job until it completes
3. Download staged data products

and please consult the module APIs for more details.


NOAA Atlas 14
-------------
The :ref:`noaa package <pfdf.data.noaa>` includes the :ref:`atlas14 module <pfdf.data.noaa.atlas14>`, which is used to load precipitation frequency estimates (PFEs) from NOAA Atlas 14. Most users will want to use the :ref:`download command <pfdf.data.noaa.atlas14.download>`, which downloads a .csv file with PFEs at a given lat-lon coordinate. This command allows users to query PFEs with the following options:

**statistic**

* mean: Returns mean PFEs (default)
* upper: Returns the upper bound of the 90% confidence interval
* lower: Returns the lower bound of the 90% confidence interval
* all: Mean, upper, and lower

**data**

* intensity: Values are precipitation intensities (default)
* depth: Values are precipitation depths

**series**

* pds: Returns PFEs estimated from partial duration time series (default)
* ams: Returns PFEs estimated from annual maximum time series

**units**

* metric: PFEs returned in mm or mm/hour (default)
* english: PFEs returned in inches or inches/hour



Retainments
-----------

This package contains modules to help acquire datasets indicating the locations of debris retainment features (sometimes referred to as "debris basins"). Currently, this package is limited to debris retainments in Los Angeles County CA, but additional datasets may be added upon request.

To download retainment features from Los Angeles County, CA, load the :ref:`retainments.la_county <pfdf.data.retainments.la_county>` module, and call the :ref:`download command <pfdf.data.retainments.la_county.download>`. This will download a geodatabase of point features indicating the locations of retainment features.


USGS
----

The ``usgs`` package includes modules to access a variety of USGS datasets. These include digital elevation models (DEMs) and hydrologic unit (HU) boundaries from the USGS National Map (TNM), as well as soil KF-factors and soil thickness data from the STATSGO soil characteristic archive. Additional datasets may also be added upon request.

Currently, the package is organized into the :ref:`tnm package <pfdf.data.usgs.tnm>` (used to access products from The National Map - including DEMs, HUCs, and low-level APIs), and the :ref:`statsgo module <pfdf.data.usgs.statsgo>` (used to access the soil characteristic archive).

STATSGO
+++++++

The :ref:`statsgo module <pfdf.data.usgs.statsgo>` loads soil characteristic data from the `STATSGO archive <https://www.sciencebase.gov/catalog/item/675083c6d34ea60e894354ad>`_. This includes KF-factor and soil thickness datasets, which are needed to run the debris-flow likelihood models in the :ref:`staley2017 module <pfdf.models.staley2017>`. You can load soil data within a bounding box using the :ref:`read command <pfdf.data.usgs.statsgo.read>`.

The `source STATSGO archive <https://www.sciencebase.gov/catalog/item/631405c5d34e36012efa3187>`_ is a collection of Shapefiles recording soil characteristic data for map units across the US. However, several of the data fields in the source archive have been reformatted as cloud-optimized GeoTIFF (COG) rasters. This module loads data from the `COG collection <https://www.sciencebase.gov/catalog/item/675083c6d34ea60e894354ad>`_. This collection currently includes COGs for the Kf-factor (KFFACT) and soil thickness (THICK) data layers from the source archive.



TNM
+++

The :ref:`usgs.tnm <pfdf.data.usgs.tnm>` package includes modules to download datasets from the USGS National Map (TNM). 

DEM
...

The :ref:`dem module <pfdf.data.usgs.tnm.dem>` allows users to stream digital elevation models (DEMs) into memory using the :ref:`read command <pfdf.data.usgs.tnm.dem.read>`. The command currently supports the following DEMs:

.. list-table::
    :header-rows: 1

    * - DEM
      - Description
    * - 1/3 arc-second
      - Continuous, nominal 10 meter resolution. Recommended for most pfdf applications within the US.
    * - 1 arc-second
      - Nominal 30 meter resolution
    * - 1 meter
      - 1 meter resolution
    * - 1/9 arc-second
      - Legacy dataset with nominal 3 meter resolution
    * - 2 arc-second
      - Alaska only. Nominal 60 meter resolution
    * - 5 meter
      - Alaska only. 5 meter resolution

NHD
...

Separately, the :ref:`nhd module <pfdf.data.usgs.tnm.nhd>` allows users to download hydrologic unit (HU) data bundles from the National Hydrologic Dataset (NHD). The watershed boundary datasets in these bundles can prove useful for dividing large-scale analyses, as they form a natural unit for catchment analysis.

To download data, call the :ref:`download command <pfdf.data.usgs.tnm.nhd.download>` on a HU-4 or HU-8 code. Although the command is limited to HU-4 and HU-8 queries, the downloaded data bundle includes datasets for the 2 to 16 digit HUs associated with the query. We suggest HU-10s as a reasonable starting point for large scale analyses.

API
...
Ultimately, the DEM and NHD datasets are download via the `TNM API <https://apps.nationalmap.gov/tnmaccess/>`_, and the :ref:`api module <pfdf.data.usgs.tnm.api>` provides functions to facilitate low-level API calls. Most users won't need this module, but advanced developers may find this useful for accessing data products not directly supported by pfdf. The two most important functions in this module are :ref:`nproducts <pfdf.data.usgs.tnm.api.nproducts>`, which returns the number of TNM products matching search results; and :ref:`products <pfdf.data.usgs.tnm.api.nproducts>`, which returns metadata on queried TNM products.





