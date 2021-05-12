from audmodel.core.api import (
    author,
    date,
    default_cache_root,
    exists,
    header,
    latest_version,
    load,
    name,
    parameters,
    publish,
    remove,
    subgroup,
    uid,
    url,
    versions,
)
from audmodel.core.config import config

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
