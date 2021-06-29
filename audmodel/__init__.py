from audmodel.core.api import (
    author,
    date,
    default_cache_root,
    exists,
    header,
    header_url,
    latest_version,
    legacy_uid,
    load,
    meta,
    name,
    parameters,
    publish,
    subgroup,
    uid,
    url,
    version,
    versions,
)
from audmodel.core.config import config


# Discourage from audmodel import *
__all__ = []


# Dynamically get the version of the installed module
try:
    import pkg_resources
    __version__ = pkg_resources.get_distribution(__name__).version
except Exception:  # pragma: no cover
    pkg_resources = None  # pragma: no cover
finally:
    del pkg_resources
