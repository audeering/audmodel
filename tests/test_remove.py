import pytest
import audmodel

from .config import config


@pytest.mark.usefixtures('create')
@pytest.mark.parametrize(
    'name,params,version',
    [
        (
            config.NAME,
            config.DEFAULT_PARAMS[0],
            config.DEFAULT_VERSION,
        ),
        pytest.param(
            config.NAME,
            config.DEFAULT_PARAMS[0],
            config.DEFAULT_VERSION,
            marks=pytest.mark.xfail(raises=RuntimeError)
        ),
    ]
)
def test_remove(name, params, version):
    uid = audmodel.remove(name, params, version)
    df = audmodel.get_lookup_table(name, version)
    assert uid not in df.index
