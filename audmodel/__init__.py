from audmodel.core.api import (
    default_cache_root,
    parameters,
    latest_version,
    load,
    lookup_table,
    name,
    publish,
    remove,
    subgroup,
    uid,
    url,
    version,
    versions,
)
from audmodel.core.config import config
from audmodel.core.params import (
    Parameter,
    Parameters,
)

# Disencourage from audmodel import *
__all__ = []


# Dynamically get the version of the installed module
try:
    import pkg_resources
    __version__ = pkg_resources.get_distribution(__name__).version
except Exception:  # pragma: no cover
    pkg_resources = None  # pragma: no cover
finally:
    del pkg_resources
