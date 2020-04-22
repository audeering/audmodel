import pytest

import pandas as pd

import audfactory
import audmodel


@pytest.mark.parametrize('root,name,params,version,create,verbose', [
    pytest.param(
        pytest.ROOT,
        pytest.NAME,
        pytest.PARAMS[0],
        pytest.VERSION,
        False,
        False,
        marks=pytest.mark.xfail(raises=RuntimeError)
    ),
    (
        pytest.ROOT,
        pytest.NAME,
        pytest.PARAMS[0],
        pytest.VERSION,
        True,
        True,
    ),
    (
        pytest.ROOT,
        pytest.NAME,
        pytest.PARAMS[1],
        pytest.VERSION,
        False,
        False,
    ),
    pytest.param(
        pytest.ROOT,
        pytest.NAME,
        pytest.PARAMS[1],
        pytest.VERSION,
        False,
        False,
        marks=pytest.mark.xfail(raises=RuntimeError)
    ),
    pytest.param(
        pytest.ROOT,
        pytest.NAME,
        {'bad': 'params'},
        pytest.VERSION,
        False,
        False,
        marks=pytest.mark.xfail(raises=RuntimeError)
    ),
    pytest.param(
        './invalid-folder',
        pytest.NAME,
        pytest.PARAMS[2],
        pytest.VERSION,
        False,
        False,
        marks=pytest.mark.xfail(raises=FileNotFoundError)
    ),
])
def test_publish(root, name, params, version, create, verbose):
    uid = audmodel.publish(root, name, params, version,
                           subgroup=pytest.SUBGROUP, create=create,
                           verbose=verbose)
    assert uid == audmodel.get_model_id(name, params, version,
                                        subgroup=pytest.SUBGROUP,
                                        verbose=verbose)

    df = audmodel.get_lookup_table(name, version,
                                   subgroup=pytest.SUBGROUP, verbose=verbose)
    pd.testing.assert_series_equal(df.loc[uid], pd.Series(params, name=uid))
