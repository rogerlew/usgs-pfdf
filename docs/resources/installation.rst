Installation
============

.. note:: These instructions are for pfdf users. If you plan to develop pfdf, you should do a :ref:`developer installation <dev-install>` instead.

Prerequisites
-------------

Python
++++++
pfdf requires `Python 3.11+ <https://www.python.org/downloads/>`_.

.. _install-environment:

Virtual Environment
+++++++++++++++++++
We **strongly recommend** installing pfdf in a clean virtual environment. This is because other geospatial software can sometimes interfere with pfdf's backend. There are many tools for managing virtual environments including `miniforge`_, `conda`_, `venv`_, and `virtualenv`_. If you are not familiar with virtual environments, then `miniforge`_ may be a good starting point.

For example, after installing miniforge, you can create a new python environment using::

    conda create -n pfdf python=3.13 --yes

and then activate the environment with::

    conda activate pfdf

.. _miniforge: https://github.com/conda-forge/miniforge
.. _conda: https://anaconda.org/anaconda/conda
.. _venv: https://docs.python.org/3/library/venv.html
.. _virtualenv: https://virtualenv.pypa.io/en/latest


Quick Install
-------------

We recommend installing pfdf using::

    pip install pfdf -i https://code.usgs.gov/api/v4/groups/859/-/packages/pypi/simple

The URL in this command instructs `pip <https://pypi.org/project/pip/>`_ to install pfdf from the official USGS package registry. This ensures that you are installing pfdf from a USGS source, rather than a similarly named package from a third party. The 859 in the URL is the code for packages released by the `Landslide Hazards Program <https://www.usgs.gov/programs/landslide-hazards>`_.

.. _tutorial-install:

Tutorials
---------
To run the tutorials, you will need to install pfdf with some additional software resources. You can do this using::

    pip install pfdf[tutorials] -i https://code.usgs.gov/api/v4/groups/859/-/packages/pypi/simple


.. _install-lock:

Building from Lock
------------------
In rare cases, pfdf may break due to changes in a dependency library. For example, when a dependency releases a new version that breaks backwards compatibility. If this is the case, you can use `poetry <https://python-poetry.org/>`_ to install pfdf from known working dependencies. This method requires you `install poetry <https://python-poetry.org/docs/#installation>`_ in addition to the usual prerequisites.

To use this method, you should first clone the pfdf repository at the desired release. For example, if you have `git <https://git-scm.com/>`_ installed, then you can clone the 3.0.0 release to the current directory using::

    git clone https://code.usgs.gov/ghsc/lhp/pfdf.git --branch 3.0.0

Next, use poetry to install pfdf from the ``poetry.lock`` file::

    poetry install

The ``poetry.lock`` file records the dependencies used to test pfdf, so represents a collection of known-working dependencies.

