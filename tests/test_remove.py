import pytest
import audmodel

from .default import default


@pytest.mark.usefixtures('create')
@pytest.mark.parametrize(
    'name,params,version',
    [
        (
            default.NAME,
            default.PARAMS[0],
            default.VERSION,
        ),
        pytest.param(
            default.NAME,
            default.PARAMS[0],
            default.VERSION,
            marks=pytest.mark.xfail(raises=RuntimeError)
        ),
    ]
)
def test_remove(name, params, version):
    uid = audmodel.remove(name, params, version)
    df = audmodel.get_lookup_table(name, version)
    assert uid not in df.index
