import os
import pytest
import tempfile
import shutil

import audmodel
import audeer
import audfactory


@pytest.mark.usefixtures('create')
@pytest.mark.parametrize('name,params,version,verbose', [
    (
        pytest.NAME,
        pytest.PARAMS[0],
        pytest.VERSION,
        True,
    ),
    (
        pytest.NAME,
        pytest.PARAMS[1],
        None,
        False,
    ),
    pytest.param(  # bad parameters
        pytest.NAME,
        {
            key: value * 2 for key, value in
            pytest.PARAMS[0].items()
        },
        pytest.VERSION,
        False,
        marks=pytest.mark.xfail(raises=RuntimeError),
    ),
    pytest.param(  # bad version
        pytest.NAME,
        pytest.PARAMS[0],
        '2.0.0',
        False,
        marks=pytest.mark.xfail(raises=RuntimeError),
    ),
    pytest.param(  # invalid columns
        pytest.NAME,
        {
            'bad': 'column'
        },
        pytest.VERSION,
        False,
        marks=pytest.mark.xfail(raises=RuntimeError),
    ),
])
def test_load(name, params, version, verbose):
    root = os.path.join(tempfile._get_default_tempdir(), 'audmodel')
    model_root = audmodel.load(name, params, version,
                               subgroup=pytest.SUBGROUP,
                               root=root, verbose=verbose)
    version = version or audmodel.latest_version(name,
                                                 subgroup=pytest.SUBGROUP)
    uid = os.path.basename(model_root)
    group_id = f'{audmodel.config.GROUP_ID}.{pytest.SUBGROUP}'
    assert model_root == os.path.join(root,
                                      audfactory.group_id_to_path(group_id),
                                      name, version, uid)
    x = [os.path.basename(file) for file in
         audeer.list_file_names(pytest.ROOT)]
    y = [os.path.basename(file) for file in
         audeer.list_file_names(model_root)]
    assert x == y
    shutil.rmtree(root)
