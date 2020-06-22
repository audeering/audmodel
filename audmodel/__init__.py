from audmodel.core.api import (
    create_lookup_table,
    delete_lookup_table,
    extend_params,
    get_default_cache_root,
    get_lookup_table,
    get_model_id,
    get_model_url,
    get_params,
    latest_version,
    load,
    load_by_id,
    publish,
    remove,
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
