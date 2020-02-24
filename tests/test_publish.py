import pytest

import pandas as pd

import audfactory
import audmodel

from .config import config


@pytest.mark.parametrize(
    'name,params,version,create',
    [
        pytest.param(
            config.NAME,
            config.DEFAULT_PARAMS[0],
            config.DEFAULT_VERSION,
            False,
            marks=pytest.mark.xfail(raises=RuntimeError)
        ),
        (
            config.NAME,
            config.DEFAULT_PARAMS[0],
            config.DEFAULT_VERSION,
            True,
        ),
        (
            config.NAME,
            config.DEFAULT_PARAMS[1],
            config.DEFAULT_VERSION,
            False,
        ),
    ]
)
def test_publish(name, params, version, create):
    url = audmodel.publish(config.ROOT, name, params, version, create=create)
    assert audfactory.artifactory_path(url).exists()
    uid = audmodel.get_model_id(name, params, version)
    df = audmodel.get_lookup_table(name, version)
    pd.testing.assert_series_equal(df.loc[uid], pd.Series(params, name=uid))
