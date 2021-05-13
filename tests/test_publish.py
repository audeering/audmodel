import os

import pytest

import audmodel


audmodel.config.BACKEND_HOST = pytest.BACKEND_HOST
audmodel.config.CACHE_ROOT = pytest.CACHE_ROOT

SUBGROUP = f'{pytest.ID}.publish'
VERSION = '1.0.0'


@pytest.mark.parametrize(
    'root, name, params, version, author, date, meta, subgroup, private',
    [
        pytest.param(
            pytest.ROOT,
            pytest.NAME,
            pytest.PARAMS,
            VERSION,
            pytest.AUTHOR,
            pytest.DATE,
            pytest.META,
            SUBGROUP,
            False,
        ),
        # different name
        pytest.param(
            pytest.ROOT,
            'other',
            pytest.PARAMS,
            VERSION,
            pytest.AUTHOR,
            pytest.DATE,
            pytest.META,
            SUBGROUP,
            False,
        ),
        # different subgroup
        pytest.param(
            pytest.ROOT,
            pytest.NAME,
            pytest.PARAMS,
            VERSION,
            pytest.AUTHOR,
            pytest.DATE,
            pytest.META,
            f'{SUBGROUP}.other',
            False,
        ),
        # different parameters
        pytest.param(
            pytest.ROOT,
            pytest.NAME,
            {'foo': 'bar'},
            VERSION,
            pytest.AUTHOR,
            pytest.DATE,
            pytest.META,
            SUBGROUP,
            False,
        ),
        # new version
        pytest.param(
            pytest.ROOT,
            pytest.NAME,
            pytest.PARAMS,
            '2.0.0',
            pytest.AUTHOR,
            pytest.DATE,
            pytest.META,
            SUBGROUP,
            False,
        ),
        # new version in private repository
        pytest.param(
            pytest.ROOT,
            pytest.NAME,
            pytest.PARAMS,
            '3.0.0',
            pytest.AUTHOR,
            pytest.DATE,
            pytest.META,
            SUBGROUP,
            True,
        ),
        # already published
        pytest.param(
            pytest.ROOT,
            pytest.NAME,
            pytest.PARAMS,
            VERSION,
            pytest.AUTHOR,
            pytest.DATE,
            pytest.META,
            SUBGROUP,
            False,
            marks=pytest.mark.xfail(raises=RuntimeError)
        ),
        pytest.param(
            pytest.ROOT,
            pytest.NAME,
            pytest.PARAMS,
            VERSION,
            pytest.AUTHOR,
            pytest.DATE,
            pytest.META,
            SUBGROUP,
            True,
            marks=pytest.mark.xfail(raises=RuntimeError),
        ),
        # invalid root
        pytest.param(
            './does-not-exist',
            pytest.NAME,
            pytest.PARAMS,
            VERSION,
            pytest.AUTHOR,
            pytest.DATE,
            pytest.META,
            SUBGROUP,
            False,
            marks=pytest.mark.xfail(raises=FileNotFoundError)
        ),
    ]
)
def test_publish(root, name, subgroup, params, author, date, meta, version,
                 private):

    uid = audmodel.publish(
        root,
        name,
        params,
        version,
        author=author,
        date=date,
        meta=meta,
        subgroup=subgroup,
        private=private,
    )

    assert uid == audmodel.uid(
        name,
        params,
        subgroup=subgroup,
    )

    header = audmodel.header(uid, version=version)

    assert header['author'] == author
    assert audmodel.author(uid, version=version) == author

    assert header['date'] == str(date)
    assert audmodel.date(uid, version=version) == str(date)

    assert header['meta'] == meta
    assert audmodel.meta(uid, version=version) == meta

    assert header['name'] == name
    assert audmodel.name(uid) == name

    assert header['params'] == params
    assert audmodel.parameters(uid) == params

    assert header['subgroup'] == subgroup
    assert audmodel.subgroup(uid) == subgroup

    assert header['version'] == version
    assert version in audmodel.versions(uid)

    assert os.path.exists(audmodel.url(uid, version=version))
    assert os.path.exists(audmodel.url(uid, header=True, version=version))
