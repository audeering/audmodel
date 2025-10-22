from audmodel.core.api import aliases
from audmodel.core.api import author
from audmodel.core.api import date
from audmodel.core.api import default_cache_root
from audmodel.core.api import exists
from audmodel.core.api import header
from audmodel.core.api import latest_version
from audmodel.core.api import legacy_uid
from audmodel.core.api import load
from audmodel.core.api import meta
from audmodel.core.api import name
from audmodel.core.api import parameters
from audmodel.core.api import publish
from audmodel.core.api import resolve_alias
from audmodel.core.api import set_alias
from audmodel.core.api import subgroup
from audmodel.core.api import uid
from audmodel.core.api import update_meta
from audmodel.core.api import url
from audmodel.core.api import version
from audmodel.core.api import versions
from audmodel.core.config import config
from audmodel.core.repository import Repository


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
