import pytest

import audmodel

from .default import default


@pytest.mark.usefixtures('create')
@pytest.mark.parametrize(
    'name,version',
    [
        (
            default.NAME,
            default.VERSION,
        ),
        pytest.param(  # table does not exist
            default.NAME,
            '2.0.0',
            marks=pytest.mark.xfail(raises=RuntimeError),
        ),
    ]
)
def test_get_lookup_table(name, version):
    df = audmodel.get_lookup_table(name, version)
    assert df.columns.to_list() == sorted(default.COLUMNS)
    for params, (_, row) in zip(default.PARAMS, df.iterrows()):
        for key, value in params.items():
            assert row[key] == value
