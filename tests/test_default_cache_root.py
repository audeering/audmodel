import os

import audmodel


def test_default_cache_root():
    root = os.environ.get('CACHE_ROOT') or '~/audmodel'
    assert root == audmodel.default_cache_root()
