import os
import pytest
import tempfile
import shutil

import audmodel
import audeer
import audfactory


@pytest.mark.usefixtures('create')
def test_parameters():
    uid = pytest.UIDS[0]
    params = audmodel.parameters(uid)
    assert params == pytest.PARAMS[0]
