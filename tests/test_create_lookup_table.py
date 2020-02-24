import pytest

import audmodel

from .config import config


@pytest.mark.parametrize(
    'name,columns,version,force',
    [
        (
            config.NAME,
            [],
            '1.0.0',
            False,
        ),
        pytest.param(  # columns do not match
            config.NAME,
            ['property1', 'property2', 'property3'],
            '1.0.0',
            False,
            marks=pytest.mark.xfail(raises=RuntimeError),
        ),
        (
            config.NAME,
            ['property1', 'property2', 'property3'],
            '2.0.0',
            False,
        ),
        (
            config.NAME,
            ['property1', 'property2', 'property3'],
            '2.0.0',
            True,
        ),
        pytest.param(  # model exists
            config.NAME,
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
