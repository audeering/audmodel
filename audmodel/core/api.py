import datetime
import errno
import getpass
import os
import tempfile
import typing

import oyaml as yaml

import audeer

from audmodel.core.backend import (
    archive_path,
    get_backend,
    header_path,
    header_versions,
    load_archive,
    load_header,
)
from audmodel.core.config import config
import audmodel.core.define as define
import audmodel.core.legacy as legacy
from audmodel.core.utils import (
    is_legacy_uid,
    scan_files,
    short_uid,
    split_uid,
)


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
        >>> author('2f992552-3.0.0')
        'Calvin and Hobbes'

    """
    cache_root = audeer.safe_path(cache_root or default_cache_root())
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
        >>> date('2f992552-3.0.0')
        '1985-11-18'

    """
    cache_root = audeer.safe_path(cache_root or default_cache_root())
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
    return os.environ.get('CACHE_ROOT') or config.CACHE_ROOT


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
        >>> exists('2f992552-3.0.0')
        True
        >>> exists('2f992552-9.9.9')
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
        >>> d = header('2f992552-3.0.0')
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
    if is_legacy_uid(uid):
        return {
            'author': legacy.author(uid),
            'date': legacy.date(uid),
            'name': legacy.name(uid),
            'meta': {},
            'parameters': legacy.parameters(uid),
            'subgroup': legacy.subgroup(uid),
            'version': legacy.version(uid),
        }

    cache_root = audeer.safe_path(cache_root or default_cache_root())
    return load_header(uid, cache_root)[1]


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
        >>> latest_version('2f992552')
        '3.0.0'
        >>> latest_version('2f992552-1.0.0')
        '3.0.0'

    """
    if is_legacy_uid(uid):
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
    group_id = f'{config.GROUP_ID}.{name}' if subgroup is None \
        else f'{config.GROUP_ID}.{subgroup}.{name}'
    repository = config.REPOSITORY_PRIVATE if private \
        else config.REPOSITORY_PUBLIC
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
        >>> root = load('2f992552-3.0.0')
        >>> '/'.join(root.split('/')[-2:])
        '2f992552/3.0.0'

    """
    cache_root = audeer.safe_path(cache_root or default_cache_root())

    if is_legacy_uid(uid):
        return legacy.load(uid, cache_root, verbose=verbose)

    return load_archive(uid, cache_root, verbose)[1]


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
        >>> d = meta('2f992552-3.0.0')
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
    cache_root = audeer.safe_path(cache_root or default_cache_root())
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
        >>> name('2f992552-3.0.0')
        'test'

    """
    cache_root = audeer.safe_path(cache_root or default_cache_root())
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
        >>> parameters('2f992552-3.0.0')
        {'feature': 'melspec64', 'model': 'cnn10', 'sampling_rate': 16000}

    """
    cache_root = audeer.safe_path(cache_root or default_cache_root())
    return header(uid, cache_root=cache_root)['parameters']


def publish(
        root: str,
        name: str,
        params: typing.Dict[str, typing.Any],
        version: str,
        *,
        author: str = None,
        date: datetime.date = None,
        meta: typing.Dict[str, typing.Any] = {},
        subgroup: str = None,
        private: bool = False,
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

    Raises:
        RuntimeError: if an artifact exists already
        ValueError: if subgroup is set to ``'_uid'``

    """
    date = date or datetime.date.today()
    author = author or getpass.getuser()
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

    backend = get_backend(private)
    model_id = uid(name, params, version, subgroup=subgroup)
    short_id, _ = split_uid(model_id)

    archive_path = backend.join(
        *config.GROUP_ID.split('.'),
        *subgroup.split('.'),
        name,
        short_id + '.zip',
    )
    header_path = backend.join(
        *config.GROUP_ID.split('.'),
        define.HEADER_FOLDER,
        short_id + '.yaml',
    )

    for private in [False, True]:
        if get_backend(private).exists(archive_path, version):
            raise RuntimeError(
                f"A model with ID "
                f"'{model_id}' "
                "exists already."
            )

    with tempfile.TemporaryDirectory() as tmp_root:

        # header
        src_path = os.path.join(tmp_root, 'model.yaml')
        dst_path = header_path

        header = {
            model_id: {
                'author': author,
                'date': date,
                'meta': meta,
                'name': name,
                'parameters': params,
                'subgroup': subgroup,
                'version': version,
            }
        }
        with open(src_path, 'w') as fp:
            yaml.dump(header, fp)

        backend.put_file(src_path, dst_path, version)

        # archive
        src_path = os.path.join(tmp_root, 'model.zip')
        dst_path = archive_path

        files = scan_files(root)
        audeer.create_archive(root, files, src_path)

        backend.put_file(src_path, dst_path, version)

    return model_id


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
        >>> subgroup('2f992552-3.0.0')
        'audmodel.docstring'

    """
    cache_root = audeer.safe_path(cache_root or default_cache_root())
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
        '2f992552'
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
        '2f992552-3.0.0'

    """
    sid = short_uid(name, params, subgroup)
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
        >>> path = url('2f992552-3.0.0')
        >>> os.path.basename(path)
        '2f992552-3.0.0.zip'
        >>> path = url('2f992552-3.0.0', header=True)
        >>> os.path.basename(path)
        '2f992552-3.0.0.yaml'

    """
    cache_root = audeer.safe_path(cache_root or default_cache_root())

    if header:
        if is_legacy_uid(uid):
            raise NotImplementedError()
        backend, path, version = header_path(uid)
    else:
        if is_legacy_uid(uid):
            return legacy.url(uid)
        backend, path, version = archive_path(uid, cache_root=cache_root)

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
        >>> version('2f992552-3.0.0')
        '3.0.0'

    """
    if is_legacy_uid(uid):
        return legacy.version(uid)
    else:
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
        >>> versions('2f992552')
        ['1.0.0', '2.0.0', '3.0.0']
        >>> versions('2f992552-2.0.0')
        ['1.0.0', '2.0.0', '3.0.0']

    """
    if is_legacy_uid(uid):
        url = legacy.url(uid)
        return legacy.versions(
            legacy.name_from_url(url),
            legacy.parameters(uid),
            subgroup=legacy.subgroup_from_url(url),
            private=legacy.private_from_url(url),
        )
    else:
        short_id = uid.split('-')[0]
        matches = header_versions(short_id)
        return [match[2] for match in matches]
