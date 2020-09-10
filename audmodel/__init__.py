from audmodel.core.api import (
    get_default_cache_root,
    get_lookup_table,
    get_model_id,
    parameters,
    latest_version,
    load,
    name,
    publish,
    remove,
    subgroup,
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
