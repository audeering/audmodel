import pytest

import audmodel


@pytest.mark.usefixtures('create')
@pytest.mark.parametrize('name,params,version', [
    (
        pytest.NAME,
        pytest.PARAMS[0],
        pytest.VERSION,
    ),
    (
        pytest.NAME,
        pytest.PARAMS[0],
        None,
    ),
    pytest.param(
        pytest.NAME,
        {'bad': 'params'},
        pytest.VERSION,
        marks=pytest.mark.xfail(raises=RuntimeError),
    ),
])
def test_get_model_id(name, params, version):
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
    lookup = audmodel.get_lookup_table(
        name,
        version,
        subgroup=pytest.SUBGROUP,
        private=pytest.PRIVATE,
    )
    assert uid in lookup.ids
    assert lookup[uid] == {key: params[key] for key in sorted(params)}
