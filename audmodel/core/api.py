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
        *,
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
        >>> author('7d65d639-f8be-b6b3-e789-263cedf559d5')
        'A. Uthor'

    """
    try:
        return header(uid, version=version)['author']
    except FileNotFoundError:
        return legacy.author(uid)


def date(
        uid: str,
        *,
        version: str = None,
) -> str:
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
        >>> date('7d65d639-f8be-b6b3-e789-263cedf559d5')
        '2021-05-15 23:28:32.491352'

    """
    try:
        return header(uid, version=version)['date']
    except FileNotFoundError:
        return legacy.date(uid)


def default_cache_root() -> str:
    r"""Default path under which models are stored.

    It first looks for the environment variable
    ``CACHE_ROOT``,
    which can be set in bash:

    .. code-block:: bash

        export CACHE_ROOT=/path/to/your/cache

    If it the environment variable is not set,
    :attr:`config.CACHE_ROOT`
    is returned.

    Returns:
        path to model cache

    """
    return os.environ.get('CACHE_ROOT') or config.CACHE_ROOT


def exists(uid: str) -> bool:
    r"""Check if a model with this ID exists.

    Args:
        uid: unique model ID

    Returns:
        ``True`` if a model with this ID is found

    Raises:
        ValueError: if model ID is not valid
        ConnectionError: if Artifactory is not available
        RuntimeError: if Artifactory REST API query fails
        RuntimeError: if model does not exist

    Example:
        >>> exists('7d65d639-f8be-b6b3-e789-263cedf559d5')
        True
        >>> exists('00000000-0000-0000-0000-000000000000')
        False
        >>> exists('bad-id')
        False

    """
    try:
        url(uid)
    except RuntimeError:
        return False
    except ValueError:
        return False

    return True


def header(
        uid: str,
        *,
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
        >>> d = header('7d65d639-f8be-b6b3-e789-263cedf559d5')
        >>> print(yaml.dump(d))
        author: A. Uthor
        date: '2021-05-15 23:28:32.491352'
        meta:
          data:
            emodb:
              version: 1.0.0
              format: wav
              mixdown: true
          feature:
            win_dur: 32ms
            hop_dur: 10ms
            num_fft: 512
            num_bands: 64
        name: test
        params:
          sampling_rate: 16000
          feature: spectrogram
        subgroup: audmodel.docstring
        version: 1.0.0
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
        >>> latest_version('7d65d639-f8be-b6b3-e789-263cedf559d5')
        '1.0.0'

    """
    return versions(uid)[-1]


def load(
        uid: str,
        *,
        version: str = None,
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
        ...    '7d65d639-f8be-b6b3-e789-263cedf559d5',
        ...    version='1.0.0',
        ... )
        >>> '/'.join(root.split('/')[-8:])
        'com/audeering/models/audmodel/docstring/test/7d65d639-f8be-b6b3-e789-263cedf559d5/1.0.0'

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
        *,
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
        >>> d = meta('7d65d639-f8be-b6b3-e789-263cedf559d5')
        >>> print(yaml.dump(d))
        data:
          emodb:
            version: 1.0.0
            format: wav
            mixdown: true
        feature:
          win_dur: 32ms
          hop_dur: 10ms
          num_fft: 512
          num_bands: 64
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
        >>> name('7d65d639-f8be-b6b3-e789-263cedf559d5')
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
        >>> parameters('7d65d639-f8be-b6b3-e789-263cedf559d5')
        {'sampling_rate': 16000, 'feature': 'spectrogram'}

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
        author: str = getpass.getuser(),
        date: datetime = datetime.datetime.now(),
        meta: typing.Dict[str, typing.Any] = {},
        subgroup: str = None,
        private: bool = False,
) -> str:
    r"""Zip model and publish as a new artifact.

    Before publishing a model,
    pick meaningful model ``params``, ``name``, ``subgroup``
    values.

    For model ``params`` we recommend to encode:

    * sampling rate
    * feature set
    * classifier

    For ``subgroup`` we recommend to encode:

    * task the model was trained for, e.g. ``gender``
    * maybe also project, e.g. ``projectsmile.agent-tone4``
    * package that was used for training,
      if not encoded in name,
      e.g. ``projectsmile.agent-tone4.autrainer``

    For ``name`` we recommend to encode:

    * package that was used for training, e.g. ``autrainer``
    * or if the package contains different sub-routines,
      encode package in ``subgroup`` and the sub-routine
      in ``name``,
      e.g. ``sklearn``

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
                'date': str(date),
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
        >>> subgroup('7d65d639-f8be-b6b3-e789-263cedf559d5')
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
        ...     },
        ...     subgroup='audmodel.docstring',
        ... )
        '7d65d639-f8be-b6b3-e789-263cedf559d5'

    """
    group_id = f'{config.GROUP_ID}.{name}' if subgroup is None \
        else f'{config.GROUP_ID}.{subgroup}.{name}'
    unique_string = group_id + str(params)
    return audeer.uid(from_string=unique_string)


def url(
        uid: str,
        *,
        header: bool = False,
        version: str = None,
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
        >>> archive = url('7d65d639-f8be-b6b3-e789-263cedf559d5')
        >>> archive.split('/')[-1]
        '7d65d639-f8be-b6b3-e789-263cedf559d5-1.0.0.zip'
        >>> header = url('7d65d639-f8be-b6b3-e789-263cedf559d5', header=True)
        >>> header.split('/')[-1]
        '7d65d639-f8be-b6b3-e789-263cedf559d5-1.0.0.yaml'

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
        >>> versions('7d65d639-f8be-b6b3-e789-263cedf559d5')
        ['1.0.0']

    """
    path, _, backend = path_version_backend(uid)
    return backend.versions(path + '.zip')
