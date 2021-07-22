import os

import pytest

import audmodel


audmodel.config.CACHE_ROOT = pytest.CACHE_ROOT
audmodel.config.REPOSITORIES = pytest.REPOSITORIES

SUBGROUP = f'{pytest.ID}.publish'


@pytest.mark.parametrize(
    'root, name, params, version, author, date, meta, subgroup, repository',
    (
        pytest.param(
            pytest.MODEL_ROOT,
            pytest.NAME,
            pytest.PARAMS,
            '1.0.0',
            pytest.AUTHOR,
            pytest.DATE,
            pytest.META['1.0.0'],
            SUBGROUP,
            audmodel.config.REPOSITORIES[0],
        ),
        # different name
        pytest.param(
            pytest.MODEL_ROOT,
            'other',
            pytest.PARAMS,
            '1.0.0',
            pytest.AUTHOR,
            pytest.DATE,
            pytest.META['1.0.0'],
            SUBGROUP,
            audmodel.config.REPOSITORIES[0],
        ),
        # different subgroup
        pytest.param(
            pytest.MODEL_ROOT,
            pytest.NAME,
            pytest.PARAMS,
            '1.0.0',
            pytest.AUTHOR,
            pytest.DATE,
            pytest.META['1.0.0'],
            f'{SUBGROUP}.other',
            audmodel.config.REPOSITORIES[0],
        ),
        # different parameters
        pytest.param(
            pytest.MODEL_ROOT,
            pytest.NAME,
            {},
            '1.0.0',
            pytest.AUTHOR,
            pytest.DATE,
            pytest.META['1.0.0'],
            SUBGROUP,
            audmodel.config.REPOSITORIES[0],
        ),
        # new version
        pytest.param(
            pytest.MODEL_ROOT,
            pytest.NAME,
            pytest.PARAMS,
            '2.0.0',
            pytest.AUTHOR,
            pytest.DATE,
            pytest.META['2.0.0'],
            SUBGROUP,
            audmodel.config.REPOSITORIES[0],
        ),
        # new version in second repository
        pytest.param(
            pytest.MODEL_ROOT,
            pytest.NAME,
            pytest.PARAMS,
            '3.0.0',
            pytest.AUTHOR,
            pytest.DATE,
            pytest.META['3.0.0'],
            SUBGROUP,
            audmodel.config.REPOSITORIES[1],
        ),
        # already published
        pytest.param(
            pytest.MODEL_ROOT,
            pytest.NAME,
            pytest.PARAMS,
            '1.0.0',
            pytest.AUTHOR,
            pytest.DATE,
            pytest.META['1.0.0'],
            SUBGROUP,
            audmodel.config.REPOSITORIES[0],
            marks=pytest.mark.xfail(raises=RuntimeError)
        ),
        pytest.param(
            pytest.MODEL_ROOT,
            pytest.NAME,
            pytest.PARAMS,
            '1.0.0',
            pytest.AUTHOR,
            pytest.DATE,
            pytest.META['1.0.0'],
            SUBGROUP,
            audmodel.config.REPOSITORIES[1],
            marks=pytest.mark.xfail(raises=RuntimeError),
        ),
        # invalid root
        pytest.param(
            './does-not-exist',
            pytest.NAME,
            pytest.PARAMS,
            '1.0.0',
            pytest.AUTHOR,
            pytest.DATE,
            pytest.META['1.0.0'],
            SUBGROUP,
            audmodel.config.REPOSITORIES[0],
            marks=pytest.mark.xfail(raises=FileNotFoundError)
        ),
        # invalid subgroup
        pytest.param(
            pytest.MODEL_ROOT,
            pytest.NAME,
            pytest.PARAMS,
            '1.0.0',
            pytest.AUTHOR,
            pytest.DATE,
            pytest.META['1.0.0'],
            '_uid',
            audmodel.config.REPOSITORIES[0],
            marks=pytest.mark.xfail(raises=ValueError)
        ),
    )
)
def test_publish(root, name, subgroup, params, author, date, meta, version,
                 repository):

    uid = audmodel.publish(
        root,
        name,
        params,
        version,
        author=author,
        date=date,
        meta=meta,
        repository=repository,
        subgroup=subgroup,
    )

    assert audmodel.exists(uid)
    assert uid == audmodel.uid(
        name,
        params,
        version,
        subgroup=subgroup,
    )

    header = audmodel.header(uid)

    assert header['author'] == author
    assert audmodel.author(uid) == author

    assert header['date'] == date
    assert audmodel.date(uid) == str(date)

    assert header['name'] == name
    assert audmodel.name(uid) == name

    assert header['parameters'] == params
    assert audmodel.parameters(uid) == params

    assert header['subgroup'] == subgroup
    assert audmodel.subgroup(uid) == subgroup

    assert header['version'] == version
    assert audmodel.version(uid) == version

    assert audmodel.meta(uid) == meta

    assert os.path.exists(audmodel.url(uid))
    assert os.path.exists(audmodel.url(uid, type='header'))
    assert os.path.exists(audmodel.url(uid, type='meta'))


def test_publish_interrupt():

    # create object that cannot be pickled
    # so it will raise an error when converted to yaml
    class CannotPickle:
        def __getstate__(self):
            raise Exception('cannot pickle object')

    meta = {
        'object': CannotPickle()
    }

    name = pytest.NAME
    params = {}
    version = '1.0.0'

    err_msg = 'Could not publish model due to an unexpected error.'
    with pytest.raises(RuntimeError, match=err_msg):
        audmodel.publish(
            pytest.MODEL_ROOT,
            name,
            params,
            version,
            meta=meta,
            repository=audmodel.config.REPOSITORIES[0],
        )

    uid = audmodel.uid(
        name,
        params,
        version,
    )
    assert not audmodel.exists(uid)
