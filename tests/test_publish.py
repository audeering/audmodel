import pytest

import audmodel


audmodel.config.BACKEND_HOST = pytest.BACKEND_HOST
audmodel.config.CACHE_ROOT = pytest.CACHE_ROOT

SUBGROUP = f'{pytest.ID}.publish'


@pytest.mark.parametrize(
    'root, name, params, version, author, date, meta, subgroup, private',
    [
        pytest.param(
            pytest.ROOT,
            pytest.NAME,
            pytest.PARAMS,
            '1.0.0',
            pytest.AUTHOR,
            pytest.DATE,
            pytest.META,
            SUBGROUP,
            False,
        ),
        # different repository
        pytest.param(
            pytest.ROOT,
            pytest.NAME,
            pytest.PARAMS,
            '1.0.0',
            pytest.AUTHOR,
            pytest.DATE,
            pytest.META,
            SUBGROUP,
            True,
        ),
        # different name
        pytest.param(
            pytest.ROOT,
            'other',
            pytest.PARAMS,
            '1.0.0',
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
            '1.0.0',
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
            '1.0.0',
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
        # already published
        pytest.param(
            pytest.ROOT,
            pytest.NAME,
            pytest.PARAMS,
            '1.0.0',
            pytest.AUTHOR,
            pytest.DATE,
            pytest.META,
            SUBGROUP,
            False,
            marks=pytest.mark.xfail(raises=RuntimeError)
        ),
        # invalid root
        pytest.param(
            './does-not-exist',
            pytest.NAME,
            pytest.PARAMS,
            '1.0.0',
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
        private=private,
    )

    assert name == audmodel.name(uid)
    assert subgroup == audmodel.subgroup(uid)
    assert version in audmodel.versions(uid)

    header = audmodel.header(uid, version=version)

    assert header['author'] == author
    assert audmodel.author(uid, version=version) == author
    assert header['date'] == str(date)
    assert audmodel.date(uid, version=version) == str(date)
    assert header['meta'] == meta
    assert audmodel.meta(uid, version=version) == meta
    assert header['params'] == params
    assert audmodel.parameters(uid) == params
    assert header['version'] == version
