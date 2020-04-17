import pytest

import audmodel


@pytest.mark.usefixtures('create')
@pytest.mark.parametrize('name,version,new_params', [
    (
        pytest.NAME,
        pytest.VERSION,
        'string',
    ),
    (
        pytest.NAME,
        pytest.VERSION,
        ['list'],
    ),
    (
        pytest.NAME,
        pytest.VERSION,
        [],
    ),
    (
        pytest.NAME,
        pytest.VERSION,
        {'key': 'value'},
    ),
    (
        pytest.NAME,
        pytest.VERSION,
        {},
    ),
])
def test_get_model_id(name, version, new_params):

    old_params = audmodel.get_params(name, version, subgroup=pytest.SUBGROUP)
    df = audmodel.extend_params(name, version, new_params,
                                subgroup=pytest.SUBGROUP)
    params = audmodel.get_params(name, version, subgroup=pytest.SUBGROUP)

    if isinstance(new_params, str):
        new_params = [new_params]
    if isinstance(new_params, (tuple, list)):
        new_params = {param: None for param in new_params}

    for param, value in new_params.items():
        assert all([x == value for x in df[param]])

    assert sorted(params) == sorted(old_params + list(new_params))
