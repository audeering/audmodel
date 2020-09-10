import pytest

import audmodel


@pytest.mark.parametrize('root,name,params,version,create,verbose', [
    pytest.param(
        pytest.ROOT,
        pytest.NAME,
        pytest.PARAMS[0],
        pytest.VERSION,
        False,
        False,
        marks=pytest.mark.xfail(raises=RuntimeError)
    ),
    (
        pytest.ROOT,
        pytest.NAME,
        pytest.PARAMS[0],
        pytest.VERSION,
        True,
        True,
    ),
    (
        pytest.ROOT,
        pytest.NAME,
        pytest.PARAMS[1],
        pytest.VERSION,
        False,
        False,
    ),
    pytest.param(
        pytest.ROOT,
        pytest.NAME,
        pytest.PARAMS[1],
        pytest.VERSION,
        False,
        False,
        marks=pytest.mark.xfail(raises=RuntimeError)
    ),
    pytest.param(
        pytest.ROOT,
        pytest.NAME,
        {'bad': 'params'},
        pytest.VERSION,
        False,
        False,
        marks=pytest.mark.xfail(raises=RuntimeError)
    ),
    pytest.param(
        './invalid-folder',
        pytest.NAME,
        pytest.PARAMS[2],
        pytest.VERSION,
        False,
        False,
        marks=pytest.mark.xfail(raises=FileNotFoundError)
    ),
])
def test_publish(root, name, params, version, create, verbose):
    uid = audmodel.publish(
        root,
        name,
        params,
        version,
        subgroup=pytest.SUBGROUP,
        private=pytest.PRIVATE,
        create=create,
        verbose=verbose,
    )
    expected_uid = audmodel.uid(
        name,
        params,
        version,
        subgroup=pytest.SUBGROUP,
        private=pytest.PRIVATE,
    )
    assert uid == expected_uid

    lookup = audmodel.lookup_table(
        name,
        version,
        subgroup=pytest.SUBGROUP,
        private=pytest.PRIVATE,
    )
    assert lookup[uid] == {key: params[key] for key in sorted(params)}
