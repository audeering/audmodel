import os
import pytest
import tempfile
import shutil

import audmodel
import audeer


@pytest.mark.usefixtures('create')
@pytest.mark.parametrize('name,params,version,uid', [
    (
        pytest.NAME,
        pytest.PARAMS[0],
        pytest.VERSION,
        None,
    ),
    pytest.param(
        pytest.NAME,
        None,
        None,
        '1234',
        marks=pytest.mark.xfail(raises=RuntimeError)
    ),
])
def test_load_by_id(name, params, version, uid):
    root = os.path.join(tempfile._get_default_tempdir(), 'audmodel')
    uid = uid or audmodel.get_model_id(name, params, version,
                                       subgroup=pytest.SUBGROUP)
    model_root = audmodel.load_by_id(name, uid, subgroup=pytest.SUBGROUP,
                                     root=root)
    x = [os.path.basename(file) for file in
         audeer.list_file_names(pytest.ROOT)]
    y = [os.path.basename(file) for file in
         audeer.list_file_names(model_root)]
    assert x == y
    shutil.rmtree(root)
