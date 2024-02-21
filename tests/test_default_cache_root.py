import os

import pytest

import audmodel


os.environ["AUDMODEL_CACHE_ROOT"] = pytest.CACHE_ROOT


def test_default_cache_root():
    assert audmodel.default_cache_root() == pytest.CACHE_ROOT
