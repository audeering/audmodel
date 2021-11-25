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
    get_meta,
    header_path,
    header_versions,
    meta_path,
    put_archive,
    put_header,
    put_meta,
    raise_model_not_found_error,
    SERIALIZE_ERROR_MESSAGE,
    split_uid,
)
from audmodel.core.config import config
import audmodel.core.define as define
import audmodel.core.utils as utils


def author(
        uid: str,
        *,
        cache_root: str = None,
) -> str:
    r"""Author of model.

    Args:
        uid: unique model ID or short ID for latest version
        cache_root: cache folder where models and headers are stored.
            If not set :meth:`audmodel.default_cache_root` is used

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
        uid: unique model ID or short ID for latest version
        cache_root: cache folder where models and headers are stored.
            If not set :meth:`audmodel.default_cache_root` is used

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
        uid: unique model ID or short ID for latest version

    Returns:
        ``True`` if a model with this ID is found

    Raises:
        ConnectionError: if Artifactory is not available

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
        verbose: bool = False,
) -> typing.Dict[str, typing.Any]:
    r"""Load model header.

    Args:
        uid: unique model ID or short ID for latest version
        cache_root: cache folder where models and headers are stored.
            If not set :meth:`audmodel.default_cache_root` is used
        verbose: show debug messages

    Raises:
        ConnectionError: if Artifactory is not available
        RuntimeError: if model does not exist on backend

    Returns:
        dictionary with header fields

    Examples:
        >>> d = header('5fbbaf38-3.0.0')
        >>> print(yaml.dump(d))
        author: Calvin and Hobbes
        date: 1985-11-18
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
    short_id, version = split_uid(uid, cache_root)
    return get_header(short_id, version, cache_root, verbose)[1]


def latest_version(
        uid: str,
) -> str:
    r"""Latest available version of model.

    Args:
        uid: unique model ID or short ID

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
    vs = versions(uid)
    if not vs:
        raise_model_not_found_error(uid, None)
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

    Example:

        >>> legacy_uid(
        ...     'test',
        ...     {
        ...         'sampling_rate': 16000,
        ...         'feature': 'melspec64',
        ...         'model': 'cnn10',
        ...     },
        ...     subgroup='audmodel.docstring',
        ...     version='1.0.0',
        ... )
        '3a117099-8039-ab5e-b834-ae16dafdaf42'

    """
    group_id = f'com.audeering.models.{name}' if subgroup is None \
        else f'com.audeering.models.{subgroup}.{name}'
    repository = define.LEGACY_REPOSITORY_PRIVATE if private \
        else define.LEGACY_REPOSITORY_PUBLIC
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
    removal_version='1.2.0',
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
        uid: unique model ID or short ID for latest version
        cache_root: cache folder where models and headers are stored.
            If not set :meth:`audmodel.default_cache_root` is used
        verbose: show debug messages

    Returns:
        path to model folder

    Raises:
        ConnectionError: if Artifactory is not available
        RuntimeError: if model does not exist

    Example:
        >>> root = load('5fbbaf38-3.0.0')
        >>> '/'.join(root.split(os.path.sep)[-2:])
        '5fbbaf38/3.0.0'

    """
    cache_root = audeer.safe_path(cache_root or default_cache_root())
    short_id, version = split_uid(uid, cache_root)
    return get_archive(short_id, version, cache_root, verbose)


def meta(
        uid: str,
        *,
        cache_root: str = None,
        verbose: bool = False,
) -> typing.Dict[str, typing.Any]:
    r"""Meta information of model.

    Args:
        uid: unique model ID or short ID for latest version
        cache_root: cache folder where models and headers are stored.
            If not set :meth:`audmodel.default_cache_root` is used
        verbose: show debug messages

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
    cache_root = audeer.safe_path(cache_root or default_cache_root())
    short_id, version = split_uid(uid, cache_root)
    return get_meta(short_id, version, cache_root, verbose)[1]


def name(
        uid: str,
        *,
        cache_root: str = None,
        verbose: bool = False,
) -> str:
    r"""Name of model.

    Args:
        uid: unique model ID or short ID for latest version
        cache_root: cache folder where models and headers are stored.
            If not set :meth:`audmodel.default_cache_root` is used
        verbose: show debug messages

    Returns:
        model name

    Raises:
        ConnectionError: if Artifactory is not available
        RuntimeError: if model does not exist

    Example:
        >>> name('5fbbaf38-3.0.0')
        'test'

    """
    return header(uid, cache_root=cache_root, verbose=verbose)['name']


def parameters(
        uid: str,
        *,
        cache_root: str = None,
        verbose: bool = False,
) -> typing.Dict:
    r"""Parameters of model.

    Args:
        uid: unique model ID or short ID for latest version
        cache_root: cache folder where models and headers are stored.
            If not set :meth:`audmodel.default_cache_root` is used
        verbose: show debug messages

    Returns:
        model parameters

    Raises:
        ConnectionError: if Artifactory is not available
        RuntimeError: if model does not exist

    Example:
        >>> parameters('5fbbaf38-3.0.0')
        {'feature': 'melspec64', 'model': 'cnn10', 'sampling_rate': 16000}

    """
    return header(uid, cache_root=cache_root, verbose=verbose)['parameters']


@audeer.deprecated_keyword_argument(
    deprecated_argument='private',
    removal_version='1.2.0',
)
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
        verbose: bool = False,
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
        verbose: show debug messages

    Returns:
        unique model ID

    Raises:
        RuntimeError: if a model with same UID exists already
        RuntimeError: if an unexpected error occurs during publishing
        RuntimeError: if ``meta`` or ``params``
            cannot be serialized to a YAML file
        ValueError: if subgroup is set to ``'_uid'``
        FileNotFoundError: if ``root`` folder cannot be found

    """
    root = audeer.safe_path(root)
    subgroup = subgroup or ''

    if subgroup == define.UID_FOLDER:
        raise ValueError(
            f"It is not allowed to set subgroup to "
            f"'{define.UID_FOLDER}'."
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
        name=name,
        parameters=params,
        subgroup=subgroup,
        version=version,
    )

    try:
        put_header(
            short_id,
            version,
            header,
            backend,
            verbose,
        )
        put_meta(
            short_id,
            version,
            meta,
            backend,
            verbose,
        )
        put_archive(
            short_id,
            version,
            name,
            subgroup,
            root,
            backend,
            verbose,
        )
    except Exception as ex:
        # if something goes wrong
        # remove files that were already published
        for ext in [define.HEADER_EXT, define.META_EXT]:
            path = backend.join(
                define.UID_FOLDER,
                f'{short_id}.{ext}',
            )
            if backend.exists(path, version, ext=ext):
                backend.remove_file(path, version, ext=ext)

        path = backend.join(
            *subgroup.split('.'),
            name,
            short_id + '.zip',
        )
        if backend.exists(path, version):  # pragma: no cover
            # we can probably assume that the archive
            # does not exist on the backend
            # if something goes wrong during 'put_archive()'
            # so it's not likely we'll ever end up in this case
            backend.remove_file(path, version)

        # Reraise our custom error if params or meta cannot be serialized
        if (
                type(ex) == RuntimeError
                and ex.args[0].startswith(SERIALIZE_ERROR_MESSAGE)
        ):
            raise ex
        else:  # pragma: no cover
            raise RuntimeError(
                f'Could not publish model due to an unexpected error.'
            )

    return uid


def subgroup(
        uid: str,
        *,
        cache_root: str = None,
        verbose: bool = False,
) -> str:
    r"""Subgroup of model.

    Args:
        uid: unique model ID or short ID for latest version
        cache_root: cache folder where models and headers are stored.
            If not set :meth:`audmodel.default_cache_root` is used
        verbose: show debug messages

    Returns:
        model subgroup

    Raises:
        ConnectionError: if Artifactory is not available
        RuntimeError: if model does not exist

    Example:
        >>> subgroup('5fbbaf38-3.0.0')
        'audmodel.docstring'

    """
    return header(uid, cache_root=cache_root, verbose=verbose)['subgroup']


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


def update_meta(
        uid: str,
        meta: typing.Dict[str, typing.Any],
        *,
        replace: bool = False,
        cache_root: str = None,
        verbose: bool = False,
) -> typing.Dict[str, typing.Any]:
    r"""Update metadata of model on backend and in cache.

    Unless ``replace`` is set to ``True``
    iterates through current meta dictionary and
    updates fields where they match or
    adds missing fields,
    but keeps all existing fields.

    For instance, updating:

    .. code-block::

        {
            'data': {
                'emodb': {
                    'version': '1.0.0',
                    'format': 'wav',
                },
            },
        }

    with:

    .. code-block::

        {
            'data': {
                'emodb': {
                    'version': '2.0.0',
                },
                'myai': {
                    'version': '1.0.0',
                    'format': 'wav',
                }
            },
            'loss': 'ccc',
        }

    results in:

    .. code-block::

        {
            'data': {
                'emodb': {
                    'version': '2.0.0',
                    'format': 'wav',
                },
                'myai': {
                    'version': '1.0.0',
                    'format': 'wav',
                }
            },
            'loss': 'ccc',
        }

    Args:
        uid: unique model ID or short ID for latest version
        meta: dictionary with meta information
        replace: replace existing dictionary
        cache_root: cache folder where models and headers are stored.
            If not set :meth:`audmodel.default_cache_root` is used
        verbose: show debug messages

    Returns:
        new meta dictionary

    Raises:
        ConnectionError: if Artifactory is not available
        RuntimeError: if model does not exist
        RuntimeError: if ``meta`` cannot be serialized to a YAML file

    """
    cache_root = audeer.safe_path(cache_root or default_cache_root())
    short_id, version = split_uid(uid, cache_root)

    # update metadata
    backend, meta_backend = get_meta(
        short_id,
        version,
        cache_root,
        verbose,
    )
    if replace:
        meta_backend = meta
    else:
        utils.update_dict(meta_backend, meta)

    # upload metadata
    put_meta(
        short_id,
        version,
        meta_backend,
        backend,
        verbose,
    )

    # update cache
    local_path = os.path.join(
        cache_root,
        short_id,
        f'{version}.{define.META_EXT}',
    )
    with open(local_path, 'w') as fp:
        yaml.dump(header, fp)

    return meta


def url(
        uid: str,
        *,
        type: str = 'model',
        cache_root: str = None,
        verbose: bool = False,
) -> str:
    r"""URL to model archive or header.

    Args:
        uid: unique model ID or short ID for latest version
        type: return URL to specified type.
            ``'model'`` corresponds to the archive file
            storing the model,
            ``'header'`` to the model header,
            and ``'meta'`` to the model metadata
        cache_root: cache folder where models and headers are stored.
            If not set :meth:`audmodel.default_cache_root` is used
        verbose: show debug messages

    Returns:
        URL

    Raises:
        ConnectionError: if Artifactory is not available
        RuntimeError: if URL does not exist
        ValueError: if wrong ``type`` is given

    Example:
        >>> path = url('5fbbaf38-3.0.0')
        >>> os.path.basename(path)
        '5fbbaf38-3.0.0.zip'
        >>> path = url('5fbbaf38-3.0.0', type='header')
        >>> os.path.basename(path)
        '5fbbaf38-3.0.0.header.yaml'
        >>> path = url('5fbbaf38-3.0.0', type='meta')
        >>> os.path.basename(path)
        '5fbbaf38-3.0.0.meta.yaml'

    """
    cache_root = audeer.safe_path(cache_root or default_cache_root())
    short_id, version = split_uid(uid, cache_root)

    if type == 'model':
        backend, path = archive_path(
            short_id,
            version,
            cache_root,
            verbose,
        )
        return backend.path(path, version)
    elif type == 'header':
        backend, path = header_path(short_id, version)
        return backend.path(path, version, ext=define.HEADER_EXT)
    elif type == 'meta':
        backend, path = meta_path(
            short_id,
            version,
            cache_root,
            verbose,
        )
        return backend.path(path, version, ext=define.META_EXT)
    else:
        raise ValueError(
            "'type' has to be one of "
            "'model', "
            "'header', "
            "'meta', "
            f"not '{type}'"
        )


def version(
        uid: str,
        *,
        cache_root: str = None,
        verbose: bool = False,
) -> str:
    r"""Version of model.

    Args:
        uid: unique model ID or short ID for latest version
        cache_root: cache folder where models and headers are stored.
            If not set :meth:`audmodel.default_cache_root` is used
        verbose: show debug messages

    Returns:
        model version

    Raises:
        ConnectionError: if Artifactory is not available
        RuntimeError: if model does not exist

    Example:
        >>> version('5fbbaf38-3.0.0')
        '3.0.0'

    """
    return header(uid, cache_root=cache_root, verbose=verbose)['version']


def versions(
        uid: str,
        *,
        cache_root: str = None,
) -> typing.List[str]:
    r"""Available model versions.

    Args:
        uid: unique model ID or short ID
        cache_root: cache folder where models and headers are stored.
            If not set :meth:`audmodel.default_cache_root` is used

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
    cache_root = audeer.safe_path(cache_root or default_cache_root())
    if utils.is_legacy_uid(uid):
        try:
            # legacy IDs can only have one version
            _, version = split_uid(uid, cache_root)
            return [version]
        except RuntimeError:
            return []
    else:
        short_id = uid.split('-')[0]
        matches = header_versions(short_id)
        return [match[2] for match in matches]
