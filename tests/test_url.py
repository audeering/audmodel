import pytest

import audeer
import audfactory

import audmodel


@pytest.mark.usefixtures('create')
def test_url():
    uid = pytest.UIDS[0]
    url = audmodel.url(uid)
    assert audfactory.artifactory_path(url).exists()
    error_msg = 'Provided unique ID not valid'
    with pytest.raises(ValueError, match=error_msg):
        audmodel.url('bad-id')
    uid = audeer.uid()
    error_msg = f"A model with ID '{uid}' does not exist"
    with pytest.raises(RuntimeError, match=error_msg):
        audmodel.url(uid)
