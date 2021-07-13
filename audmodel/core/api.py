import datetime
import errno
import os
import typing

import oyaml as yaml

import audbackend
import audeer

from audmodel.core.backend import (
    archive_path,
    get_archive,
    get_backend,
    get_header,
    header_path,
    header_versions,
    put_archive,
    put_header,
    split_uid,
)
from audmodel.core.config import config
import audmodel.core.define as define
import audmodel.core.legacy as legacy
import audmodel.core.utils as utils


def author(
        uid: str,
        *,
        cache_root: str = None,
) -> str:
    r"""Author of model.

    Args:
        uid: unique model ID
        cache_root: cache folder where models and headers are stored.
            If not set :meth:`aumodel.default_cache_root` is used

    Returns:
        model author

    Raises:
        ConnectionError: if Artifactory is not available
        RuntimeError: if model does not exist

    Example:
        >>> author('5fbbaf38-3.0.0')
        'Calvin and Hobbes'

    """
    return header(uid, cache_root=cache_root)['author']


def date(
        uid: str,
        *,
        cache_root: str = None,
) -> str:
    r"""Publication date of model.

    Args:
        uid: unique model ID
        cache_root: cache folder where models and headers are stored.
            If not set :meth:`aumodel.default_cache_root` is used

    Returns:
        model publication date

    Raises:
        ConnectionError: if Artifactory is not available
        RuntimeError: if model does not exist

    Example:
        >>> date('5fbbaf38-3.0.0')
        '1985-11-18'

    """
    return str(header(uid, cache_root=cache_root)['date'])


def default_cache_root() -> str:
    r"""Default path under which models are stored.

    It first looks for the environment variable
    ``AUDMODEL_CACHE_ROOT``,
    which can be set in bash:

    .. code-block:: bash

        export AUDMODEL_CACHE_ROOT=/path/to/your/cache

    If it the environment variable is not set,
    :attr:`config.CACHE_ROOT`
    is returned.

    Returns:
        path to model cache

    """
    return os.environ.get('AUDMODEL_CACHE_ROOT') or config.CACHE_ROOT


def exists(
        uid: str,
) -> bool:
    r"""Check if a model with this ID exists.

    Args:
        uid: unique model ID

    Returns:
        ``True`` if a model with this ID is found

    Raises:
        ConnectionError: if Artifactory is not available
        RuntimeError: if Artifactory REST API query fails

    Example:
        >>> exists('5fbbaf38-3.0.0')
        True
        >>> exists('5fbbaf38-9.9.9')
        False

    """
    try:
        url(uid)
    except RuntimeError:
        return False

    return True


def header(
        uid: str,
        *,
        cache_root: str = None,
) -> typing.Dict[str, typing.Any]:
    r"""Load model header.

    Args:
        uid: unique model ID
        cache_root: cache folder where models and headers are stored.
            If not set :meth:`aumodel.default_cache_root` is used

    Raises:
        ConnectionError: if Artifactory is not available
        RuntimeError: if header does not exist

    Returns:
        dictionary with header fields

    Examples:
        >>> d = header('5fbbaf38-3.0.0')
        >>> print(yaml.dump(d))
        author: Calvin and Hobbes
        date: 1985-11-18
        meta:
          data:
            emodb:
              version: 1.1.1
              format: wav
              mixdown: true
          melspec64:
            win_dur: 32ms
            hop_dur: 10ms
            num_fft: 512
          cnn10:
            learning-rate: 0.01
            optimizer: adam
        name: test
        parameters:
          feature: melspec64
          model: cnn10
          sampling_rate: 16000
        subgroup: audmodel.docstring
        version: 3.0.0
        <BLANKLINE>

    """
    cache_root = audeer.safe_path(cache_root or default_cache_root())
    short_id, version = split_uid(uid)
    return get_header(short_id, version, cache_root)[1]


def latest_version(
        uid: str,
) -> str:
    r"""Latest available version of model.

    Args:
        uid: unique or short model ID

    Returns:
        latest version of model

    Raises:
        ConnectionError: if Artifactory is not available
        RuntimeError: if model does not exist

    Example:
        >>> latest_version('5fbbaf38')
        '3.0.0'
        >>> latest_version('5fbbaf38-1.0.0')
        '3.0.0'

    """
    if utils.is_legacy_uid(uid):
        url = legacy.url(uid)
        return legacy.latest_version(
            legacy.name_from_url(url),
            legacy.parameters(uid),
            subgroup=legacy.subgroup_from_url(url),
            private=legacy.private_from_url(url),
        )
    else:
        short_id = uid.split('-')[0]
        vs = versions(short_id)
        if not vs:
            raise RuntimeError(
                f"A model with short ID "
                f"'{short_id}' "
                f"does not exist."
            )
        return vs[-1]


def legacy_uid(
        name: str,
        params: typing.Dict[str, typing.Any],
        version: str,
        *,
        subgroup: str = None,
        private: bool = False,
) -> str:
    r"""Unique model ID in legacy format.

    Args:
        name: model name
        params: dictionary with parameters
        version: version string
        subgroup: extend group ID to
            ``com.audeering.models.<subgroup>``.
            You can increase the depth
            by using dot-notation,
            e.g. setting
            ``subgroup=foo.bar``
            will result in
            ``com.audeering.models.foo.bar``
        private: repository is private

    Returns:
        unique model ID

    """
    group_id = f'com.audeering.models.{name}' if subgroup is None \
        else f'com.audeering.models.{subgroup}.{name}'
    repository = config.LEGACY_REPOSITORY_PRIVATE if private \
        else config.LEGACY_REPOSITORY_PUBLIC
    unique_string = (
        str(params)
        + group_id
        + 'lookup'
        + version
        + repository
    )
    return audeer.uid(from_string=unique_string)


@audeer.deprecated_keyword_argument(
    deprecated_argument='root',
    new_argument='cache_root',
    mapping=lambda value: value,
    removal_version='1.0.0',
)
def load(
        uid: str,
        *,
        cache_root: str = None,
        verbose: bool = False,
) -> str:
    r"""Download a model by its unique ID.

    If ``root`` is not set,
    the model is downloaded to the default cache folder,
    see :meth:`audmodel.default_cache_root`.
    If the model already exists in the cache folder,
    the download is skipped.

    Args:
        uid: unique model ID
        cache_root: cache folder where models and headers are stored.
            If not set :meth:`aumodel.default_cache_root` is used
        verbose: show debug messages

    Returns:
        path to model folder

    Raises:
        ConnectionError: if Artifactory is not available
        RuntimeError: if model does not exist

    Example:
        >>> root = load('5fbbaf38-3.0.0')
        >>> '/'.join(root.split('/')[-2:])
        '5fbbaf38/3.0.0'

    """
    cache_root = audeer.safe_path(cache_root or default_cache_root())
    short_id, version = split_uid(uid)
    return get_archive(short_id, version, cache_root, verbose)


def meta(
        uid: str,
        *,
        cache_root: str = None,
) -> typing.Dict[str, typing.Any]:
    r"""Meta information of model.

    Args:
        uid: unique model ID
        cache_root: cache folder where models and headers are stored.
            If not set :meth:`aumodel.default_cache_root` is used

    Returns:
        dictionary with meta fields

    Raises:
        ConnectionError: if Artifactory is not available
        RuntimeError: if model does not exist

    Example:
        >>> d = meta('5fbbaf38-3.0.0')
        >>> print(yaml.dump(d))
        data:
          emodb:
            version: 1.1.1
            format: wav
            mixdown: true
        melspec64:
          win_dur: 32ms
          hop_dur: 10ms
          num_fft: 512
        cnn10:
          learning-rate: 0.01
          optimizer: adam
        <BLANKLINE>

    """
    return header(uid, cache_root=cache_root)['meta']


def name(
        uid: str,
        *,
        cache_root: str = None,
) -> str:
    r"""Name of model.

    Args:
        uid: unique model ID
        cache_root: cache folder where models and headers are stored.
            If not set :meth:`aumodel.default_cache_root` is used

    Returns:
        model name

    Raises:
        ConnectionError: if Artifactory is not available
        RuntimeError: if model does not exist

    Example:
        >>> name('5fbbaf38-3.0.0')
        'test'

    """
    return header(uid, cache_root=cache_root)['name']


def parameters(
        uid: str,
        *,
        cache_root: str = None,
) -> typing.Dict:
    r"""Parameters of model.

    Args:
        uid: unique model ID
        cache_root: cache folder where models and headers are stored.
            If not set :meth:`aumodel.default_cache_root` is used

    Returns:
        model parameters

    Raises:
        ConnectionError: if Artifactory is not available
        RuntimeError: if model does not exist

    Example:
        >>> parameters('5fbbaf38-3.0.0')
        {'feature': 'melspec64', 'model': 'cnn10', 'sampling_rate': 16000}

    """
    return header(uid, cache_root=cache_root)['parameters']


def publish(
        root: str,
        name: str,
        params: typing.Dict[str, typing.Any],
        version: str,
        *,
        author: str = None,
        date: datetime.date = None,
        meta: typing.Dict[str, typing.Any] = None,
        repository: audbackend.Repository = config.REPOSITORIES[0],
        subgroup: str = None,
) -> str:
    r"""Zip model and publish as a new artifact.

    Before publishing a model,
    pick meaningful model ``params``, ``name``, ``subgroup``
    values.

    For ``name``  we recommend to encode
    the package that was used for training,
    e.g. ``audpann``.

    For model ``params`` we recommend to encode:

    * feature set
    * model type
    * sampling rate

    For ``subgroup`` we recommend to encode:

    * task the model was trained for, e.g. ``gender``
    * maybe also project, e.g. ``projectsmile.client-tone-4``

    All other details that are relevant to the model
    can be stored as ``meta`` information, e.g.

    * class names
    * data the model was trained on
    * frame and hop size used for feature extraction
    * model hyper parameters

    Args:
        root: folder with model files
        name: model name
        params: dictionary with parameters
        version: version string
        author: author name(s), defaults to user name
        date: date, defaults to current timestamp
        meta: dictionary with meta information
        repository: repository where the model will be published
        subgroup: extend group ID to
            ``com.audeering.models.<subgroup>``.
            You can increase the depth
            by using dot-notation,
            e.g. setting
            ``subgroup=foo.bar``
            will result in
            ``com.audeering.models.foo.bar``

    Returns:
        unique model ID

    Raises:
        RuntimeError: if an artifact exists already
        ValueError: if subgroup is set to ``'_uid'``

    """
    root = audeer.safe_path(root)
    subgroup = subgroup or ''

    if subgroup == define.HEADER_FOLDER:
        raise ValueError(
            f"It is not allowed to set subgroup to "
            f"'{define.HEADER_FOLDER}'."
        )

    if not os.path.isdir(root):
        raise FileNotFoundError(
            errno.ENOENT,
            os.strerror(errno.ENOENT),
            root,
        )

    short_id = utils.short_id(name, params, subgroup)
    uid = f'{short_id}-{version}'

    if exists(uid):
        raise RuntimeError(
            f"A model with ID "
            f"'{uid}' "
            "exists already."
        )

    backend = get_backend(repository)
    header = utils.create_header(
        uid,
        author=author,
        date=date,
        meta=meta,
        name=name,
        parameters=params,
        subgroup=subgroup,
        version=version,
    )
    put_header(short_id, version, header, backend)
    put_archive(short_id, version, name, subgroup, root, backend)

    return uid


def subgroup(
        uid: str,
        *,
        cache_root: str = None,
) -> str:
    r"""Subgroup of model.

    Args:
        uid: unique model ID
        cache_root: cache folder where models and headers are stored.
            If not set :meth:`aumodel.default_cache_root` is used

    Returns:
        model subgroup

    Raises:
        ConnectionError: if Artifactory is not available
        RuntimeError: if model does not exist

    Example:
        >>> subgroup('5fbbaf38-3.0.0')
        'audmodel.docstring'

    """
    return header(uid, cache_root=cache_root)['subgroup']


def uid(
        name: str,
        params: typing.Dict[str, typing.Any],
        version: str = None,
        *,
        subgroup: str = None,
) -> str:
    r"""Unique model ID.

    Args:
        name: model name
        params: dictionary with parameters
        version: version string, if not given the short ID is returned
        subgroup: extend group ID to
            ``com.audeering.models.<subgroup>``.
            You can increase the depth
            by using dot-notation,
            e.g. setting
            ``subgroup=foo.bar``
            will result in
            ``com.audeering.models.foo.bar``

    Returns:
        unique or short model ID

    Example:
        >>> uid(
        ...     'test',
        ...     {
        ...         'sampling_rate': 16000,
        ...         'feature': 'melspec64',
        ...         'model': 'cnn10',
        ...     },
        ...     subgroup='audmodel.docstring',
        ... )
        '5fbbaf38'
        >>> uid(
        ...     'test',
        ...     {
        ...         'sampling_rate': 16000,
        ...         'feature': 'melspec64',
        ...         'model': 'cnn10',
        ...     },
        ...     version='3.0.0',
        ...     subgroup='audmodel.docstring',
        ... )
        '5fbbaf38-3.0.0'

    """
    sid = utils.short_id(name, params, subgroup)
    if version is None:
        return sid
    else:
        return f'{sid}-{version}'


def url(
        uid: str,
        *,
        header: bool = False,
        cache_root: str = None,
) -> str:
    r"""URL to model archive or header.

    Args:
        uid: unique model ID
        header: return URL to header instead of archive
        cache_root: cache folder where models and headers are stored.
            If not set :meth:`aumodel.default_cache_root` is used

    Returns:
        URL

    Raises:
        ConnectionError: if Artifactory is not available
        RuntimeError: if model does not exist

    Example:
        >>> path = url('5fbbaf38-3.0.0')
        >>> os.path.basename(path)
        '5fbbaf38-3.0.0.zip'
        >>> path = url('5fbbaf38-3.0.0', header=True)
        >>> os.path.basename(path)
        '5fbbaf38-3.0.0.yaml'

    """
    cache_root = audeer.safe_path(cache_root or default_cache_root())
    short_id, version = split_uid(uid)

    if header:
        backend, path = header_path(short_id, version)
    else:
        backend, path = archive_path(short_id, version, cache_root=cache_root)

    return backend.path(path, version)


def version(
        uid: str
) -> str:
    r"""Version of model.

    Args:
        uid: unique model ID

    Returns:
        model version

    Example:
        >>> version('5fbbaf38-3.0.0')
        '3.0.0'

    """
    return split_uid(uid)[1]


def versions(
        uid: str,
) -> typing.List[str]:
    r"""Available model versions.

    Args:
        uid: unique or short model ID

    Returns:
        list with versions

    Raises:
        ConnectionError: if Artifactory is not available
        RuntimeError: if model does not exist

    Example:
        >>> versions('5fbbaf38')
        ['1.0.0', '2.0.0', '3.0.0']
        >>> versions('5fbbaf38-2.0.0')
        ['1.0.0', '2.0.0', '3.0.0']

    """
    if utils.is_legacy_uid(uid):
        url = legacy.url(uid)
        return legacy.versions(
            legacy.name_from_url(url),
            legacy.parameters(uid),
            subgroup=legacy.subgroup_from_url(url),
            private=legacy.private_from_url(url),
        )
    else:
        short_id, _ = split_uid(uid)
        matches = header_versions(short_id)
        return [match[2] for match in matches]
