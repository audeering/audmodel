import pytest

import pandas as pd

import audfactory
import audmodel

from .default import default


@pytest.mark.parametrize(
    'root,name,params,version,create,verbose',
    [
        pytest.param(
            default.ROOT,
            default.NAME,
            default.PARAMS[0],
            default.VERSION,
            False,
            False,
            marks=pytest.mark.xfail(raises=RuntimeError)
        ),
        (
            default.ROOT,
            default.NAME,
            default.PARAMS[0],
            default.VERSION,
            True,
            True,
        ),
        (
            default.ROOT,
            default.NAME,
            default.PARAMS[1],
            default.VERSION,
            False,
            False,
        ),
        pytest.param(
            default.ROOT,
            default.NAME,
            default.PARAMS[1],
            default.VERSION,
            False,
            False,
            marks=pytest.mark.xfail(raises=RuntimeError)
        ),
        pytest.param(
            default.ROOT,
            default.NAME,
            {'bad': 'params'},
            default.VERSION,
            False,
            False,
            marks=pytest.mark.xfail(raises=RuntimeError)
        ),
        pytest.param(
            './invalid-folder',
            default.NAME,
            default.PARAMS[2],
            default.VERSION,
            False,
            False,
            marks=pytest.mark.xfail(raises=FileNotFoundError)
        ),
    ]
)
def test_publish(root, name, params, version, create, verbose):
    url = audmodel.publish(root, name, params, version,
                           create=create, verbose=verbose)
    assert audfactory.artifactory_path(url).exists()
    uid = audmodel.get_model_id(name, params, version, verbose=verbose)
    df = audmodel.get_lookup_table(name, version, verbose=verbose)
    pd.testing.assert_series_equal(df.loc[uid], pd.Series(params, name=uid))
