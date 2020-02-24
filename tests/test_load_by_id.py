import os
import pytest
import tempfile
import shutil

import audmodel
import audeer

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
    ]
)
def test_load_by_id(name, params, version):
    root = os.path.join(tempfile._get_default_tempdir(), 'audmodel')
    uid = audmodel.get_model_id(name, params, version)
    model_root = audmodel.load_by_id(name, uid, root=root)
    assert model_root == os.path.join(root, config.NAME, version, uid)
    x = [os.path.basename(file) for file in
         audeer.list_file_names(config.ROOT)]
    y = [os.path.basename(file) for file in
         audeer.list_file_names(model_root)]
    assert x == y
    shutil.rmtree(root)
