import pytest

import audmodel

from .default import default


@pytest.mark.parametrize(
    'name,columns,version,force',
    [
        (
            default.NAME,
            [],
            '1.0.0',
            False,
        ),
        pytest.param(  # columns do not match
            default.NAME,
            ['property1', 'property2', 'property3'],
            '1.0.0',
            False,
            marks=pytest.mark.xfail(raises=RuntimeError),
        ),
        (
            default.NAME,
            ['property1', 'property2', 'property3'],
            '2.0.0',
            False,
        ),
        (
            default.NAME,
            ['property1', 'property2', 'property3'],
            '2.0.0',
            True,
        ),
        pytest.param(  # model exists
            default.NAME,
            ['property1', 'property2', 'property3'],
            '2.0.0',
            False,
            marks=pytest.mark.xfail(raises=RuntimeError),
        ),
    ]
)
def test_create_lookup_table(name, columns, version, force):
    audmodel.create_lookup_table(name, columns, version, force=force)
    df = audmodel.get_lookup_table(name, version)
    assert df.columns.to_list() == sorted(columns)
