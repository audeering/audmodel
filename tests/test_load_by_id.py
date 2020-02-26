import os
import pytest
import tempfile
import shutil

import audmodel
import audeer

from .default import default


@pytest.mark.usefixtures('create')
@pytest.mark.parametrize(
    'name,params,version,uid',
    [
        (
            default.NAME,
            default.PARAMS[0],
            default.VERSION,
            None,
        ),
        pytest.param(
            default.NAME,
            None,
            None,
            '1234',
            marks=pytest.mark.xfail(raises=RuntimeError)
        ),
    ]
)
def test_load_by_id(name, params, version, uid):
    root = os.path.join(tempfile._get_default_tempdir(), 'audmodel')
    uid = uid or audmodel.get_model_id(name, params, version)
    model_root = audmodel.load_by_id(name, uid, root=root)
    x = [os.path.basename(file) for file in
         audeer.list_file_names(default.ROOT)]
    y = [os.path.basename(file) for file in
         audeer.list_file_names(model_root)]
    assert x == y
    shutil.rmtree(root)
