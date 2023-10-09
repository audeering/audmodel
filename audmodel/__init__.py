from audmodel.core.api import (
    author,
    date,
    default_cache_root,
    exists,
    header,
    latest_version,
    legacy_uid,
    load,
    meta,
    name,
    parameters,
    publish,
    subgroup,
    uid,
    update_meta,
    url,
    version,
    versions,
)
from audmodel.core.config import config


# Discourage from audmodel import *
__all__ = []


# Dynamically get the version of the installed module
try:
    import importlib.metadata
    __version__ = importlib.metadata.version(__name__)
except Exception:  # pragma: no cover
    importlib = None  # pragma: no cover
finally:
    del importlib
