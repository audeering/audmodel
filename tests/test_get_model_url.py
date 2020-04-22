import pytest

import audfactory

import audmodel


@pytest.mark.usefixtures('create')
def test_get_model_url():
    url = audmodel.get_model_url(pytest.NAME, pytest.UID,
                                 subgroup=pytest.SUBGROUP)
    assert audfactory.artifactory_path(url).exists()
    with pytest.raises(RuntimeError):
        audmodel.get_model_url(pytest.NAME, 'bad', subgroup=pytest.SUBGROUP)
