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
    df = audmodel.get_lookup_table(name, version, subgroup=pytest.SUBGROUP)
    assert df.columns.to_list() == sorted(pytest.COLUMNS)
    for params, (_, row) in zip(pytest.PARAMS, df.iterrows()):
        for key, value in params.items():
            assert row[key] == value
