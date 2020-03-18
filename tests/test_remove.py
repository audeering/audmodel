import pytest
import audmodel


@pytest.mark.usefixtures('create')
@pytest.mark.parametrize('name,params,version', [
    (
        pytest.NAME,
        pytest.PARAMS[0],
        pytest.VERSION,
    ),
    pytest.param(
        pytest.NAME,
        pytest.PARAMS[0],
        pytest.VERSION,
        marks=pytest.mark.xfail(raises=RuntimeError)
    ),
])
def test_remove(name, params, version):
    uid = audmodel.remove(name, params, version, subgroup=pytest.SUBGROUP)
    df = audmodel.get_lookup_table(name, version, subgroup=pytest.SUBGROUP)
    assert uid not in df.index
