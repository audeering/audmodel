import os

import pytest

import audmodel


audmodel.config.BACKEND_HOST = pytest.BACKEND_HOST
audmodel.config.CACHE_ROOT = pytest.CACHE_ROOT

SUBGROUP = f'{pytest.ID}.publish'


@pytest.mark.parametrize(
    'root, name, params, version, author, date, meta, subgroup, private',
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
            False,
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
            False,
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
            False,
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
            False,
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
            False,
        ),
        # new version in private repository
        pytest.param(
            pytest.MODEL_ROOT,
            pytest.NAME,
            pytest.PARAMS,
            '3.0.0',
            pytest.AUTHOR,
            pytest.DATE,
            pytest.META['3.0.0'],
            SUBGROUP,
            True,
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
            False,
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
            True,
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
            False,
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
            False,
            marks=pytest.mark.xfail(raises=ValueError)
        ),
    )
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

    assert header['meta'] == meta
    assert audmodel.meta(uid) == meta

    assert header['name'] == name
    assert audmodel.name(uid) == name

    assert header['parameters'] == params
    assert audmodel.parameters(uid) == params

    assert header['subgroup'] == subgroup
    assert audmodel.subgroup(uid) == subgroup

    assert header['version'] == version

    assert os.path.exists(audmodel.url(uid))
    assert os.path.exists(audmodel.url(uid, header=True))
