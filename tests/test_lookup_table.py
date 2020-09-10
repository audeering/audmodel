import pytest

import audmodel


@pytest.mark.usefixtures('create')
@pytest.mark.parametrize('name,version,private', [
    (
        pytest.NAME,
        pytest.VERSION,
        True,
    ),
    (
        pytest.NAME,
        None,
        True,
    ),
    pytest.param(  # table does not exist
        pytest.NAME,
        pytest.VERSION,
        False,
        marks=pytest.mark.xfail(raises=RuntimeError),
    ),
    pytest.param(  # table does not exist
        pytest.NAME,
        '2.0.0',
        True,
        marks=pytest.mark.xfail(raises=RuntimeError),
    ),
])
def test_lookup_table(name, version, private):
    lookup = audmodel.lookup_table(
        name,
        version,
        subgroup=pytest.SUBGROUP,
        private=private,
    )
    assert lookup.columns == sorted(pytest.COLUMNS)
    for params, row in zip(pytest.PARAMS, lookup.table[1:]):
        for idx, key in enumerate(lookup.columns):
            assert row[idx + 1] == params[key]
