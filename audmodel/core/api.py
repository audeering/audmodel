import datetime
import errno
import getpass
import os
import tempfile
import typing

import oyaml as yaml

import audeer

from audmodel.core.backend import (
    get_backend,
    path_version_backend,
)
from audmodel.core.config import config
import audmodel.core.legacy as legacy


def author(
        uid: str,
        version: str = None,
) -> str:
    r"""Author of model.

    Args:
        uid: unique model ID
        version: version string

    Returns:
        model author

    Raises:
        ValueError: if model ID is not valid
        ConnectionError: if Artifactory is not available
        RuntimeError: if Artifactory REST API query fails
        RuntimeError: if model does not exist

    Example:
        >>> author('5a7fd2f6-07da-8b7f-73c5-169fca6aecd2')
        'Calvin and Hobbes'

    """
    try:
        return header(uid, version=version)['author']
    except FileNotFoundError:
        return legacy.author(uid)


def date(
        uid: str,
        version: str = None,
) -> datetime.date:
    r"""Publication date of model.

    Args:
        uid: unique model ID
        version: version string

    Returns:
        model publication date

    Raises:
        ValueError: if model ID is not valid
        ConnectionError: if Artifactory is not available
        RuntimeError: if Artifactory REST API query fails
        RuntimeError: if model does not exist

    Example:
        >>> date('5a7fd2f6-07da-8b7f-73c5-169fca6aecd2')
        datetime.date(1985, 11, 18)

    """
    try:
        return header(uid, version=version)['date']
    except FileNotFoundError:
        return datetime.datetime.strptime(legacy.date(uid), "%Y/%m/%d").date()


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
        version: str = None,
) -> bool:
    r"""Check if a model with this ID exists.

    Args:
        uid: unique model ID
        version: version string

    Returns:
        ``True`` if a model with this ID is found

    Raises:
        ValueError: if model ID is not valid
        ConnectionError: if Artifactory is not available
        RuntimeError: if Artifactory REST API query fails
        RuntimeError: if model does not exist

    Example:
        >>> exists('5a7fd2f6-07da-8b7f-73c5-169fca6aecd2')
        True
        >>> exists('5a7fd2f6-07da-8b7f-73c5-169fca6aecd2', version='1.0.0')
        True
        >>> exists('5a7fd2f6-07da-8b7f-73c5-169fca6aecd2', version='9.9.9')
        False
        >>> exists('00000000-0000-0000-0000-000000000000')
        False
        >>> exists('bad-id')
        False

    """
    try:
        url(uid, version=version)
    except RuntimeError:
        return False
    except ValueError:
        return False

    return True


def header(
        uid: str,
        version: str = None,
) -> dict:
    r"""Load model header.

    Args:
        uid: unique model ID
        version: version string

    Raises:
        ValueError: if model ID is not valid
        ConnectionError: if Artifactory is not available
        RuntimeError: if Artifactory REST API query fails
        RuntimeError: if model does not exist

    Returns:
        dictionary with header fields

    Examples:
        >>> d = header('5a7fd2f6-07da-8b7f-73c5-169fca6aecd2')
        >>> print(yaml.dump(d))
        author: Calvin and Hobbes
        date: 1985-11-18
        meta:
          data:
            emodb:
              version: 1.1.1
              format: wav
              mixdown: true
          spectrogram:
            win_dur: 32ms
            hop_dur: 10ms
            num_fft: 512
            num_bands: 64
          cnn:
            type: pann
            layers: 14
        name: test
        params:
          feature: spectrogram
          model: cnn
          sampling_rate: 16000
        subgroup: audmodel.docstring
        version: 3.0.0
        <BLANKLINE>

    """
    path, version, backend = path_version_backend(uid, version=version)

    with tempfile.TemporaryDirectory() as root:
        src_path = path + '.yaml'
        dst_path = os.path.join(root, 'model.yaml')
        backend.get_file(
            src_path,
            dst_path,
            version,
        )
        with open(dst_path, 'r') as fp:
            return yaml.load(fp, Loader=yaml.Loader)[uid]


def latest_version(uid: str) -> str:
    r"""Latest available version of model.

    Args:
        uid: unique model ID

    Returns:
        latest version of model

    Raises:
        ValueError: if model ID is not valid
        ConnectionError: if Artifactory is not available
        RuntimeError: if Artifactory REST API query fails
        RuntimeError: if model does not exist

    Example:
        >>> latest_version('5a7fd2f6-07da-8b7f-73c5-169fca6aecd2')
        '3.0.0'

    """
    return versions(uid)[-1]


def load(
        uid: str,
        version: str = None,
        *,
        root: str = None,
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
        version: version string
        root: store model within this folder
        verbose: show debug messages

    Returns:
        path to model folder

    Raises:
        ValueError: if model ID is not valid
        ConnectionError: if Artifactory is not available
        RuntimeError: if Artifactory REST API query fails
        RuntimeError: if model does not exist

    Example:
        >>> root = load(
        ...    '5a7fd2f6-07da-8b7f-73c5-169fca6aecd2',
        ...    version='1.0.0',
        ... )
        >>> '/'.join(root.split('/')[-8:])
        'com/audeering/models/audmodel/docstring/test/5a7fd2f6-07da-8b7f-73c5-169fca6aecd2/1.0.0'

    """
    path, version, backend = path_version_backend(uid, version=version)

    root = audeer.safe_path(root or default_cache_root())
    root = os.path.join(
        root,
        path.replace(backend.sep, os.path.sep),
        version,
    )

    if not os.path.exists(root):
        tmp_root = audeer.mkdir(root + '~')

        # get archive
        src_path = path + '.zip'
        dst_path = os.path.join(tmp_root, 'model.zip')
        backend.get_file(
            src_path,
            dst_path,
            version,
        )

        # extract files
        audeer.extract_archive(
            dst_path,
            tmp_root,
            keep_archive=False,
            verbose=verbose,
        )

        # move folder
        audeer.mkdir(root)
        os.rename(tmp_root, root)

    return root


def meta(
        uid: str,
        version: str = None,
) -> typing.Dict[str, typing.Any]:
    r"""Meta information of model.

    Args:
        uid: unique model ID
        version: version string

    Returns:
        dictionary with meta fields

    Raises:
        ValueError: if model ID is not valid
        ConnectionError: if Artifactory is not available
        RuntimeError: if Artifactory REST API query fails
        RuntimeError: if model does not exist

    Example:
        >>> d = meta('5a7fd2f6-07da-8b7f-73c5-169fca6aecd2')
        >>> print(yaml.dump(d))
        data:
          emodb:
            version: 1.1.1
            format: wav
            mixdown: true
        spectrogram:
          win_dur: 32ms
          hop_dur: 10ms
          num_fft: 512
          num_bands: 64
        cnn:
          type: pann
          layers: 14
        <BLANKLINE>

    """
    try:
        return header(uid, version=version)['meta']
    except FileNotFoundError:
        return {}


def name(uid: str) -> str:
    r"""Name of model.

    Args:
        uid: unique model ID

    Returns:
        model name

    Raises:
        ValueError: if model ID is not valid
        ConnectionError: if Artifactory is not available
        RuntimeError: if Artifactory REST API query fails
        RuntimeError: if model does not exist

    Example:
        >>> name('5a7fd2f6-07da-8b7f-73c5-169fca6aecd2')
        'test'

    """
    path, _, backend = path_version_backend(uid)
    path = backend.split(path)[0]
    return backend.split(path)[1]


def parameters(uid: str) -> typing.Dict:
    r"""Parameters of model.

    Args:
        uid: unique model ID

    Returns:
        model parameters

    Raises:
        ValueError: if model ID is not valid
        ConnectionError: if Artifactory is not available
        RuntimeError: if Artifactory REST API query fails
        RuntimeError: if model does not exist

    Example:
        >>> parameters('5a7fd2f6-07da-8b7f-73c5-169fca6aecd2')
        {'feature': 'spectrogram', 'model': 'cnn', 'sampling_rate': 16000}

    """
    try:
        return header(uid)['params']
    except FileNotFoundError:
        return legacy.parameters(uid)


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
    * maybe also project, e.g. ``projectsmile.client``

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

    """
    date = date or datetime.date.today()
    author = author or getpass.getuser()
    root = audeer.safe_path(root)
    subgroup = subgroup or ''

    if not os.path.isdir(root):
        raise FileNotFoundError(
            errno.ENOENT,
            os.strerror(errno.ENOENT),
            root,
        )

    backend = get_backend(private)
    model_id = uid(name, params, subgroup=subgroup)
    path = backend.join(
        *config.GROUP_ID.split('.'),
        *subgroup.split('.'),
        name,
        model_id,
    )

    for private in [False, True]:
        if get_backend(private).exists(path + '.zip', version):
            raise RuntimeError(
                f"A model with ID "
                f"'{model_id}' "
                f"and version "
                f"'{version}' "
                f"exists already."
            )

    with tempfile.TemporaryDirectory() as tmp_root:

        # header
        src_path = os.path.join(tmp_root, 'model.yaml')
        dst_path = path + '.yaml'

        header = {
            model_id: {
                'author': author,
                'date': date,
                'meta': meta,
                'name': name,
                'params': params,
                'subgroup': subgroup,
                'version': version,
            }
        }
        with open(src_path, 'w') as fp:
            yaml.dump(header, fp)

        backend.put_file(src_path, dst_path, version)

        # archive
        src_path = os.path.join(tmp_root, 'model.zip')
        dst_path = path + '.zip'

        files = scan_files(root)
        audeer.create_archive(root, files, src_path)

        backend.put_file(src_path, dst_path, version)

    return model_id


def scan_files(root: str) -> typing.Sequence[str]:
    r"""Helper function to find all files in directory."""

    def help(root: str, sub_dir: str = ''):
        for entry in os.scandir(root):
            if entry.is_dir(follow_symlinks=False):
                yield from help(entry.path, os.path.join(sub_dir, entry.name))
            else:
                yield sub_dir, entry.name

    return [os.path.join(sub, file) for sub, file in help(root, '')]


def subgroup(uid: str) -> str:
    r"""Subgroup of model.

    Args:
        uid: unique model ID

    Returns:
        model subgroup

    Raises:
        ValueError: if model ID is not valid
        ConnectionError: if Artifactory is not available
        RuntimeError: if Artifactory REST API query fails
        RuntimeError: if model does not exist

    Example:
        >>> subgroup('5a7fd2f6-07da-8b7f-73c5-169fca6aecd2')
        'audmodel.docstring'

    """
    path, _, backend = path_version_backend(uid)
    path = backend.split(path)[0]
    path = path[len(config.GROUP_ID) + 1:]
    path = backend.split(path)[0]
    return path.replace(backend.sep, '.')


def uid(
        name: str,
        params: typing.Dict[str, typing.Any],
        *,
        subgroup: str = None,
) -> str:
    r"""Unique model ID.

    Args:
        name: model name
        params: dictionary with parameters
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

    Example:
        >>> uid(
        ...     'test',
        ...     {
        ...         'sampling_rate': 16000,
        ...         'feature': 'spectrogram',
        ...         'model': 'cnn',
        ...     },
        ...     subgroup='audmodel.docstring',
        ... )
        '5a7fd2f6-07da-8b7f-73c5-169fca6aecd2'
        >>> uid(
        ...     'test',
        ...     {
        ...         'feature': 'spectrogram',
        ...         'model': 'cnn',
        ...         'sampling_rate': 16000,
        ...     },
        ...     subgroup='audmodel.docstring',
        ... )
        '5a7fd2f6-07da-8b7f-73c5-169fca6aecd2'

    """
    group_id = f'{config.GROUP_ID}.{name}' if subgroup is None \
        else f'{config.GROUP_ID}.{subgroup}.{name}'
    params = {key: params[key] for key in sorted(params)}
    unique_string = group_id + str(params)
    return audeer.uid(from_string=unique_string)


def url(
        uid: str,
        version: str = None,
        *,
        header: bool = False,
) -> str:
    r"""Model URL.

    Args:
        uid: unique model ID
        header: return URL of header instead of archive
        version: version string

    Returns:
        URL of model

    Raises:
        ValueError: if model ID is not valid
        ConnectionError: if Artifactory is not available
        RuntimeError: if Artifactory REST API query fails
        RuntimeError: if model does not exist

    Example:
        >>> archive = url('5a7fd2f6-07da-8b7f-73c5-169fca6aecd2')
        >>> archive.split('/')[-1]
        '5a7fd2f6-07da-8b7f-73c5-169fca6aecd2-3.0.0.zip'
        >>> header = url('5a7fd2f6-07da-8b7f-73c5-169fca6aecd2', header=True)
        >>> header.split('/')[-1]
        '5a7fd2f6-07da-8b7f-73c5-169fca6aecd2-3.0.0.yaml'

    """
    path, version, backend = path_version_backend(uid, version=version)
    ext = '.yaml' if header else '.zip'
    return backend.path(path + ext, version)


def versions(uid: str) -> typing.List[str]:
    r"""Available model versions.

    Args:
        uid: unique model ID

    Returns:
        list with versions

    Raises:
        ValueError: if model ID is not valid
        ConnectionError: if Artifactory is not available
        RuntimeError: if Artifactory REST API query fails
        RuntimeError: if model does not exist

    Example:
        >>> versions('5a7fd2f6-07da-8b7f-73c5-169fca6aecd2')
        ['1.0.0', '2.0.0', '3.0.0']

    """
    path, _, backend = path_version_backend(uid)
    return backend.versions(path + '.zip')
