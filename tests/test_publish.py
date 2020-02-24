import pytest

import pandas as pd

import audfactory
import audmodel

from .config import config


@pytest.mark.parametrize(
    'root,name,params,version,create',
    [
        pytest.param(
            config.ROOT,
            config.NAME,
            config.DEFAULT_PARAMS[0],
            config.DEFAULT_VERSION,
            False,
            marks=pytest.mark.xfail(raises=RuntimeError)
        ),
        (
            config.ROOT,
            config.NAME,
            config.DEFAULT_PARAMS[0],
            config.DEFAULT_VERSION,
            True,
        ),
        (
            config.ROOT,
            config.NAME,
            config.DEFAULT_PARAMS[1],
            config.DEFAULT_VERSION,
            False,
        ),
        pytest.param(
            config.ROOT,
            config.NAME,
            config.DEFAULT_PARAMS[1],
            config.DEFAULT_VERSION,
            False,
            marks=pytest.mark.xfail(raises=RuntimeError)
        ),
        pytest.param(
            config.ROOT,
            config.NAME,
            {'bad': 'params'},
            config.DEFAULT_VERSION,
            False,
            marks=pytest.mark.xfail(raises=RuntimeError)
        ),
        pytest.param(
            './invalid-folder',
            config.NAME,
            config.DEFAULT_PARAMS[2],
            config.DEFAULT_VERSION,
            False,
            marks=pytest.mark.xfail(raises=FileNotFoundError)
        ),
    ]
)
def test_publish(root, name, params, version, create):
    url = audmodel.publish(root, name, params, version, create=create)
    assert audfactory.artifactory_path(url).exists()
    uid = audmodel.get_model_id(name, params, version)
    df = audmodel.get_lookup_table(name, version)
    pd.testing.assert_series_equal(df.loc[uid], pd.Series(params, name=uid))
