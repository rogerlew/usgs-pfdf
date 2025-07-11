"""
Checks that the Jupyter kernel is set up correctly for running the tutorials
----------
In brief, this module:
1. Checks the Python version is supported,
2. Checks pfdf is installed and is a supported version, and
3. Checks dependency libraries are installed

Note that the Python check should occur *before* any other imports. This way, the
imported utilities are known to exist.
"""

# Require supported Python version *before* importing other tools
import sys

version = sys.version_info
if version.major != 3:
    raise RuntimeError("You must use a Python 3 kernel to run this notebook")
elif version.minor < 11:
    raise RuntimeError(
        "You must use Python 3.11+ to run this notebook, "
        "but the current kernel uses Python 3.%i" % version.minor
    )

# Import installation utilities
from importlib.util import find_spec
from importlib.metadata import version

# Check pfdf is installed...
if find_spec("pfdf") is None:
    raise ImportError(
        "pfdf is not installed. Please see the installation guide for instructions on\n"
        "installing pfdf with tutorial resources:\n"
        "\n"
        "https://ghsc.code-pages.usgs.gov/lhp/pfdf/resources/installation.html#tutorials\n"
        "\n"
        "If you already installed pfdf, then you may be using the wrong Jupyter kernel."
    )

# ...and a supported version
major = version("pfdf").split(".")[0]
if int(major) < 3:
    raise RuntimeError(
        f"The tutorials require pfdf 3+, but the current kernel uses pfdf {major}"
    )

# Finally, check the dependency libraries are installed
dependencies = ["matplotlib", "cartopy", "contextily"]
for dep in dependencies:
    if find_spec(dep) is None:
        raise RuntimeError(
            f"{dep} is not installed. Please see the installation guide for instructions on\n"
            f"installing pfdf with tutorial resources:\n"
            f"\n"
            f"https://ghsc.code-pages.usgs.gov/lhp/pfdf/resources/installation.html#tutorials\n"
        )

# Notify user that everything is installed
print("pfdf and tutorial resources are installed")
