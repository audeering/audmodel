import pytest

import audmodel

from .config import config


@pytest.mark.usefixtures('create')
@pytest.mark.parametrize(
    'name,version',
    [
        (
            config.NAME,
            config.DEFAULT_VERSION,
        ),
        pytest.param(  # table does not exist
            config.NAME,
            '2.0.0',
            marks=pytest.mark.xfail(raises=RuntimeError),
        ),
    ]
)
def test_get_lookup_table(name, version):
    df = audmodel.get_lookup_table(name, version)
    assert df.columns.to_list() == sorted(config.DEFAULT_COLUMNS)
    for params, (_, row) in zip(config.DEFAULT_PARAMS, df.iterrows()):
        for key, value in params.items():
            assert row[key] == value
