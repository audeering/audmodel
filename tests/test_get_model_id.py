import pytest
import pandas as pd

import audmodel

from .default import default


@pytest.mark.usefixtures('create')
@pytest.mark.parametrize(
    'name,params,version',
    [
        (
            default.NAME,
            default.PARAMS[0],
            default.VERSION,
        ),
        (
            default.NAME,
            default.PARAMS[0],
            None,
        ),
        pytest.param(
            default.NAME,
            {'bad': 'params'},
            default.VERSION,
            marks=pytest.mark.xfail(raises=RuntimeError),
        ),
    ]
)
def test_get_model_id(name, params, version):
    uid = audmodel.get_model_id(name, params, version)
    if version is None:
        version = audmodel.latest_version(name, params)
    df = audmodel.get_lookup_table(name, version)
    s = pd.Series(params, name=uid)
    s.sort_index(inplace=True)
    pd.testing.assert_series_equal(df.loc[uid], s)
