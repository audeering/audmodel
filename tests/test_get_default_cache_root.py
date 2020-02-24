import os

import audmodel


def test_default_cache_root():
    root = os.environ.get('AUDMODEL_CACHE_ROOT') or '~/audmodel'
    assert root == audmodel.get_default_cache_root()
