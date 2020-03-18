import pytest

import audmodel


@pytest.mark.usefixtures('create')
@pytest.mark.parametrize('name,version,force', [
    pytest.param(  # table does not exist
        pytest.NAME,
        pytest.VERSION,
        False,
        marks=pytest.mark.xfail(raises=RuntimeError),
    ),
    (
        pytest.NAME,
        pytest.VERSION,
        True,
    ),
])
def test_delete_lookup_table(name, version, force):
    audmodel.delete_lookup_table(name, version,
                                 subgroup=pytest.SUBGROUP, force=force)
    try:
        audmodel.get_lookup_table(name, version, subgroup=pytest.SUBGROUP)
    except RuntimeError:
        assert True
