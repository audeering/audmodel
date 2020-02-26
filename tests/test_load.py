import os
import pytest
import tempfile
import shutil

import audmodel
import audeer

from .default import default


@pytest.mark.usefixtures('create')
@pytest.mark.parametrize(
    'name,params,version',
    [
        (
            default.NAME,
            default.PARAMS[0],
            default.VERSION
        ),
        (
            default.NAME,
            default.PARAMS[1],
            None
        ),
        pytest.param(  # bad parameters
            default.NAME,
            {
                key: value * 2 for key, value in
                default.PARAMS[0].items()
            },
            default.VERSION,
            marks=pytest.mark.xfail(raises=RuntimeError),
        ),
        pytest.param(  # bad version
            default.NAME,
            default.PARAMS[0],
            '2.0.0',
            marks=pytest.mark.xfail(raises=RuntimeError),
        ),
        pytest.param(  # invalid columns
            default.NAME,
            {
                'bad': 'column'
            },
            default.VERSION,
            marks=pytest.mark.xfail(raises=RuntimeError),
        ),
    ]
)
def test_load(name, params, version):
    root = os.path.join(tempfile._get_default_tempdir(), 'audmodel')
    model_root = audmodel.load(name, params, version, root=root)
    version = version or audmodel.latest_version(name)
    uid = os.path.basename(model_root)
    assert model_root == os.path.join(root, default.NAME, version, uid)
    x = [os.path.basename(file) for file in
         audeer.list_file_names(default.ROOT)]
    y = [os.path.basename(file) for file in
         audeer.list_file_names(model_root)]
    assert x == y
    shutil.rmtree(root)
