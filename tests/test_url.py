import pytest

import audeer
import audfactory

import audmodel


URL = (
    f'{audmodel.core.define.defaults.ARTIFACTORY_HOST}/'
    f'{audmodel.core.define.defaults.REPOSITORY_PUBLIC}'
)


@pytest.mark.parametrize(
    'group_id,subgroup,name',
    [
        (
            'com.audeering.models',
            None,
            'mymodel',
        ),
        (
            'com.audeering.models',
            'audmodel',
            'mymodel',
        ),
        (
            'com.audeering.models',
            'audmodel1.audmodel2',
            'mymodel',
        ),
    ],
)
def test_from_url(group_id, subgroup, name):
    version = '1.0.0'
    repository = audmodel.config.REPOSITORY_PUBLIC
    audmodel.config.GROUP_ID = group_id
    if subgroup is None:
        group_id = group_id
    else:
        group_id = f'{group_id}.{subgroup}'
    url = (
        f'{URL}/'
        f'{audfactory.group_id_to_path(group_id)}/'
        f'{name}/'
        f'uid/{version}/uid-{version}.zip'
    )
    assert audmodel.core.legacy.subgroup_from_url(url) == subgroup
    assert audmodel.core.legacy.name_from_url(url) == name
    assert audmodel.core.legacy.version_from_url(url) == version
    assert audmodel.core.legacy.repository_from_url(url) == repository


@pytest.mark.usefixtures('create')
def test_url():
    uid = pytest.UIDS[0]
    url = audmodel.url(uid)
    assert audfactory.path(url).exists()
    error_msg = f"'bad-id' is not a valid ID"
    with pytest.raises(ValueError, match=error_msg):
        audmodel.url('bad-id')
    uid = audeer.uid()
    error_msg = f"A model with ID '{uid}' does not exist"
    with pytest.raises(RuntimeError, match=error_msg):
        audmodel.url(uid)
