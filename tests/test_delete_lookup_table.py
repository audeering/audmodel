import pytest

import audmodel

from .config import config


@pytest.mark.usefixtures('create')
@pytest.mark.parametrize(
    'name,version,force',
    [
        pytest.param(  # table does not exist
            config.NAME,
            config.DEFAULT_VERSION,
            False,
            marks=pytest.mark.xfail(raises=RuntimeError),
        ),
        (
            config.NAME,
            config.DEFAULT_VERSION,
            True
        ),
    ]
)
def test_delete_lookup_table(name, version, force):
    audmodel.delete_lookup_table(name, version, force=force)
    try:
        audmodel.get_lookup_table(name, version)
    except RuntimeError:
        assert True
