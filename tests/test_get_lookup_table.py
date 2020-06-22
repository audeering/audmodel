import pytest

import audmodel


@pytest.mark.usefixtures('create')
@pytest.mark.parametrize('name,version', [
    (
        pytest.NAME,
        pytest.VERSION,
    ),
    (
        pytest.NAME,
        None,
    ),
    pytest.param(  # table does not exist
        pytest.NAME,
        '2.0.0',
        marks=pytest.mark.xfail(raises=RuntimeError),
    ),
])
def test_get_lookup_table(name, version):
    lookup = audmodel.get_lookup_table(name, version, subgroup=pytest.SUBGROUP)
    assert lookup.columns == sorted(pytest.COLUMNS)
    for params, row in zip(pytest.PARAMS, lookup.table[1:]):
        for idx, key in enumerate(lookup.columns):
            assert row[idx + 1] == params[key]
