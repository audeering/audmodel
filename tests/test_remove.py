import pytest
import audmodel


@pytest.mark.usefixtures('create')
def test_remove():
    uid = pytest.UIDS[0]
    audmodel.remove(uid)
    lookup = audmodel.lookup_table(
        pytest.NAME,
        pytest.VERSION,
        subgroup=pytest.SUBGROUP,
        private=pytest.PRIVATE,
    )
    assert uid not in lookup.ids
    # Fail when UID does not exists
    error_msg = f"A model with ID '{uid}' does not exist"
    with pytest.raises(RuntimeError, match=error_msg):
        audmodel.remove(uid)
