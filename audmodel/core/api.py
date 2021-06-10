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
    search_backend,
)
from audmodel.core.config import config
import audmodel.core.legacy as legacy
from audmodel.core.utils import (
    scan_files,
    short_uid,
    split_uid,
)


def author(
        uid: str,
) -> str:
    r"""Author of model.

    Args:
        uid: unique model ID

    Returns:
        model author

    Raises:
        ConnectionError: if Artifactory is not available
        RuntimeError: if Artifactory REST API query fails
        RuntimeError: if model does not exist

    Example:
        >>> author('2f992552-3.0.0')
        'Calvin and Hobbes'

    """
    try:
        return header(uid)['author']
    except FileNotFoundError:
        return legacy.author(uid)


def date(
        uid: str,
) -> str:
    r"""Publication date of model.

    Args:
        uid: unique model ID

    Returns:
        model publication date

    Raises:
        ConnectionError: if Artifactory is not available
        RuntimeError: if Artifactory REST API query fails
        RuntimeError: if model does not exist

    Example:
        >>> date('2f992552-3.0.0')
        '1985-11-18'

    """
    try:
        return str(header(uid)['date'])
    except FileNotFoundError:
        return legacy.date(uid)


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
) -> dict:
    r"""Load model header.

    Args:
        uid: unique model ID

    Raises:
        ConnectionError: if Artifactory is not available
        RuntimeError: if Artifactory REST API query fails
        RuntimeError: if model does not exist

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
    short_id, version = split_uid(uid)
    backend, path = search_backend(short_id, version)

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
        uid: unique or short model ID

    Returns:
        latest version of model

    Raises:
        ConnectionError: if Artifactory is not available
        RuntimeError: if Artifactory REST API query fails
        RuntimeError: if model does not exist

    Example:
        >>> latest_version('2f992552')
        '3.0.0'
        >>> latest_version('2f992552-1.0.0')
        '3.0.0'

    """
    short_id = uid.split('-')[0]
    vs = versions(short_id)
    if not vs:
        raise RuntimeError(
            f"A model with short ID "
            f"'{short_id}' "
            f"does not exist."
        )
    return vs[-1]


def load(
        uid: str,
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
        root: store model within this folder
        verbose: show debug messages

    Returns:
        path to model folder

    Raises:
        ConnectionError: if Artifactory is not available
        RuntimeError: if Artifactory REST API query fails
        RuntimeError: if model does not exist

    Example:
        >>> root = load('2f992552-3.0.0')
        >>> '/'.join(root.split('/')[-8:])
        'com/audeering/models/audmodel/docstring/test/2f992552/3.0.0'

    """
    short_id, version = split_uid(uid)
    backend, path = search_backend(short_id, version)

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
) -> typing.Dict[str, typing.Any]:
    r"""Meta information of model.

    Args:
        uid: unique model ID
        version: version string

    Returns:
        dictionary with meta fields

    Raises:
        ConnectionError: if Artifactory is not available
        RuntimeError: if Artifactory REST API query fails
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
    try:
        return header(uid)['meta']
    except FileNotFoundError:
        return {}


def name(uid: str) -> str:
    r"""Name of model.

    Args:
        uid: unique model ID

    Returns:
        model name

    Raises:
        ConnectionError: if Artifactory is not available
        RuntimeError: if Artifactory REST API query fails
        RuntimeError: if model does not exist

    Example:
        >>> name('2f992552-3.0.0')
        'test'

    """
    short_id, version = split_uid(uid)
    backend, path = search_backend(short_id, version)
    path = backend.split(path)[0]
    return backend.split(path)[1]


def parameters(uid: str) -> typing.Dict:
    r"""Parameters of model.

    Args:
        uid: unique model ID

    Returns:
        model parameters

    Raises:
        ConnectionError: if Artifactory is not available
        RuntimeError: if Artifactory REST API query fails
        RuntimeError: if model does not exist

    Example:
        >>> parameters('2f992552-3.0.0')
        {'feature': 'melspec64', 'model': 'cnn10', 'sampling_rate': 16000}

    """
    try:
        return header(uid)['parameters']
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
    model_id = uid(name, params, version, subgroup=subgroup)
    short_id, _ = split_uid(model_id)
    path = backend.join(
        *config.GROUP_ID.split('.'),
        *subgroup.split('.'),
        name,
        short_id,
    )

    for private in [False, True]:
        if get_backend(private).exists(path + '.zip', version):
            raise RuntimeError(
                f"A model with ID "
                f"'{model_id}' "
                "exists already."
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
        dst_path = path + '.zip'

        files = scan_files(root)
        audeer.create_archive(root, files, src_path)

        backend.put_file(src_path, dst_path, version)

    return model_id


def subgroup(uid: str) -> str:
    r"""Subgroup of model.

    Args:
        uid: unique model ID

    Returns:
        model subgroup

    Raises:
        ConnectionError: if Artifactory is not available
        RuntimeError: if Artifactory REST API query fails
        RuntimeError: if model does not exist

    Example:
        >>> subgroup('2f992552-3.0.0')
        'audmodel.docstring'

    """
    short_id, version = split_uid(uid)
    backend, path = search_backend(short_id, version)
    path = backend.split(path)[0]
    path = path[len(config.GROUP_ID) + 1:]
    path = backend.split(path)[0]
    return path.replace(backend.sep, '.')


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
) -> str:
    r"""Model URL.

    Args:
        uid: unique model ID
        header: return URL of header instead of archive

    Returns:
        URL of model

    Raises:
        ConnectionError: if Artifactory is not available
        RuntimeError: if Artifactory REST API query fails
        RuntimeError: if model does not exist

    Example:
        >>> archive = url('2f992552-3.0.0')
        >>> os.path.basename(archive)
        '2f992552-3.0.0.zip'
        >>> header = url('2f992552-3.0.0', header=True)
        >>> os.path.basename(header)
        '2f992552-3.0.0.yaml'

    """
    short_id, version = split_uid(uid)
    backend, path = search_backend(short_id, version)
    ext = '.yaml' if header else '.zip'
    return backend.path(path + ext, version)


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
        RuntimeError: if Artifactory REST API query fails
        RuntimeError: if model does not exist

    Example:
        >>> versions('2f992552')
        ['1.0.0', '2.0.0', '3.0.0']
        >>> versions('2f992552-1.0.0')
        ['1.0.0', '2.0.0', '3.0.0']

    """
    short_id = uid.split('-')[0]
    matches = search_backend(short_id)
    return [match[2] for match in matches]
