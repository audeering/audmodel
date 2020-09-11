import pytest

import audmodel


PARAMS = {**pytest.PARAMS[0], **{'extend': None}}


@pytest.mark.usefixtures('create')
@pytest.mark.parametrize('name,params,version', [
    (
        pytest.NAME,
        PARAMS,
        pytest.VERSION,
    ),
    (
        pytest.NAME,
        PARAMS,
        None,
    ),
    pytest.param(
        pytest.NAME,
        {'bad': 'params'},
        pytest.VERSION,
        marks=pytest.mark.xfail(raises=RuntimeError),
    ),
])
def test_uid(name, params, version):
    uid = audmodel.uid(
        name,
        params,
        version,
        subgroup=pytest.SUBGROUP,
        private=pytest.PRIVATE,
    )
    if version is None:
        version = audmodel.latest_version(
            name,
            params,
            subgroup=pytest.SUBGROUP,
            private=pytest.PRIVATE,
        )
    lookup = audmodel.lookup_table(
        name,
        version,
        subgroup=pytest.SUBGROUP,
        private=pytest.PRIVATE,
    )
    assert uid in lookup.ids
    assert lookup[uid] == {key: params[key] for key in sorted(params)}
