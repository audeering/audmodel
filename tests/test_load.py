import os
import pytest
import tempfile
import shutil

import audmodel
import audeer
import audfactory


@pytest.mark.usefixtures('create')
@pytest.mark.parametrize('verbose', [True, False])
def test_load(verbose):
    uid = pytest.UIDS[0]
    root = os.path.join(tempfile._get_default_tempdir(), 'audmodel')
    model_root = audmodel.load(uid, root=root, verbose=verbose)
    expected_uid = os.path.basename(model_root)
    assert expected_uid == uid
    group_id = f'{audmodel.core.define.defaults.GROUP_ID}.{pytest.SUBGROUP}'
    assert model_root == os.path.join(
        root,
        audfactory.group_id_to_path(group_id),
        pytest.NAME,
        pytest.VERSION,
        uid,
    )
    x = [os.path.basename(file) for file in
         audeer.list_file_names(pytest.ROOT)]
    y = [os.path.basename(file) for file in
         audeer.list_file_names(model_root)]
    assert x == y
    shutil.rmtree(root)
