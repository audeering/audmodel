from .core.api import (
    create_lookup_table,
    delete_lookup_table,
    get_lookup_table,
    get_model_id,
    latest_version,
    load,
    load_by_id,
    publish,
    remove,
    versions,
)


# Disencourage from audmodel import *
__all__ = []


# Dynamically get the version of the installed module
try:
    import pkg_resources
    __version__ = pkg_resources.get_distribution(__name__).version
except Exception:
    pkg_resources = None
finally:
    del pkg_resources
