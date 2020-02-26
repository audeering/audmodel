import pytest

import audmodel

from .default import default


@pytest.mark.usefixtures('create')
@pytest.mark.parametrize(
    'name,version,force',
    [
        pytest.param(  # table does not exist
            default.NAME,
            default.VERSION,
            False,
            marks=pytest.mark.xfail(raises=RuntimeError),
        ),
        (
            default.NAME,
            default.VERSION,
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
