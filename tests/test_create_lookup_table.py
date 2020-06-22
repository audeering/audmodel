import pytest

import audmodel


@pytest.mark.parametrize('name,params,version,force', [
    (
        pytest.NAME,
        [],
        '1.0.0',
        False,
    ),
    pytest.param(  # columns do not match
        pytest.NAME,
        pytest.COLUMNS,
        '1.0.0',
        False,
        marks=pytest.mark.xfail(raises=RuntimeError),
    ),
    (
        pytest.NAME,
        pytest.PARAMS_OBJ.to_dict(),
        '2.0.0',
        False,
    ),
    (
        pytest.NAME,
        pytest.COLUMNS,
        '2.0.0',
        True,
    ),
    pytest.param(  # model exists
        pytest.NAME,
        pytest.COLUMNS,
        '2.0.0',
        False,
        marks=pytest.mark.xfail(raises=RuntimeError),
    ),
])
def test_create_lookup_table(name, params, version, force):
    audmodel.create_lookup_table(name, params, version,
                                 subgroup=pytest.SUBGROUP,
                                 force=force)
    lookup = audmodel.get_lookup_table(name, version, subgroup=pytest.SUBGROUP)
    if isinstance(params, audmodel.Parameters):
        params = params.keys()
    assert lookup.columns == sorted(params)
