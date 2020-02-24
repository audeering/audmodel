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
            config.DEFAULT_VERSION
        ),
        (
            config.NAME,
            config.DEFAULT_PARAMS[1],
            None
        ),
        pytest.param(  # bad parameters
            config.NAME,
            {
                key: value * 2 for key, value in
                config.DEFAULT_PARAMS[0].items()
            },
            config.DEFAULT_VERSION,
            marks=pytest.mark.xfail(raises=RuntimeError),
        ),
        pytest.param(  # bad version
            config.NAME,
            config.DEFAULT_PARAMS[0],
            '2.0.0',
            marks=pytest.mark.xfail(raises=RuntimeError),
        ),
        pytest.param(  # invalid columns
            config.NAME,
            {
                'bad': 'column'
            },
            config.DEFAULT_VERSION,
            marks=pytest.mark.xfail(raises=RuntimeError),
        ),
    ]
)
def test_load(name, params, version):
    root = os.path.join(tempfile._get_default_tempdir(), 'audmodel')
    model_root = audmodel.load(name, params, version, root=root)
    version = version or audmodel.latest_version(name)
    uid = os.path.basename(model_root)
    assert model_root == os.path.join(root, config.NAME, version, uid)
    x = [os.path.basename(file) for file in
         audeer.list_file_names(config.ROOT)]
    y = [os.path.basename(file) for file in
         audeer.list_file_names(model_root)]
    assert x == y
    shutil.rmtree(root)
