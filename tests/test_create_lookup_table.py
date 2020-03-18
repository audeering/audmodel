import pytest

import audmodel


@pytest.mark.parametrize('name,columns,version,force', [
    (
        pytest.NAME,
        [],
        '1.0.0',
        False,
    ),
    pytest.param(  # columns do not match
        pytest.NAME,
        ['property1', 'property2', 'property3'],
        '1.0.0',
        False,
        marks=pytest.mark.xfail(raises=RuntimeError),
    ),
    (
        pytest.NAME,
        ['property1', 'property2', 'property3'],
        '2.0.0',
        False,
    ),
    (
        pytest.NAME,
        ['property1', 'property2', 'property3'],
        '2.0.0',
        True,
    ),
    pytest.param(  # model exists
        pytest.NAME,
        ['property1', 'property2', 'property3'],
        '2.0.0',
        False,
        marks=pytest.mark.xfail(raises=RuntimeError),
    ),
])
def test_create_lookup_table(name, columns, version, force):
    audmodel.create_lookup_table(name, columns, version,
                                 subgroup=pytest.SUBGROUP,
                                 force=force)
    df = audmodel.get_lookup_table(name, version, subgroup=pytest.SUBGROUP)
    assert df.columns.to_list() == sorted(columns)
