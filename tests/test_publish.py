import pytest

import pandas as pd

import audfactory
import audmodel

from .default import default


@pytest.mark.parametrize(
    'root,name,params,version,create',
    [
        pytest.param(
            default.ROOT,
            default.NAME,
            default.PARAMS[0],
            default.VERSION,
            False,
            marks=pytest.mark.xfail(raises=RuntimeError)
        ),
        (
            default.ROOT,
            default.NAME,
            default.PARAMS[0],
            default.VERSION,
            True,
        ),
        (
            default.ROOT,
            default.NAME,
            default.PARAMS[1],
            default.VERSION,
            False,
        ),
        pytest.param(
            default.ROOT,
            default.NAME,
            default.PARAMS[1],
            default.VERSION,
            False,
            marks=pytest.mark.xfail(raises=RuntimeError)
        ),
        pytest.param(
            default.ROOT,
            default.NAME,
            {'bad': 'params'},
            default.VERSION,
            False,
            marks=pytest.mark.xfail(raises=RuntimeError)
        ),
        pytest.param(
            './invalid-folder',
            default.NAME,
            default.PARAMS[2],
            default.VERSION,
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
