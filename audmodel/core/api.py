import datetime
import errno
import getpass
import os
import tempfile
import typing

import audbackend
import oyaml as yaml

import audeer
import audfactory

from audmodel.core.backend import get_backend
from audmodel.core.config import config
import audmodel.core.legacy as legacy


def author(
        uid: str,
        *,
        version: str = None,
) -> str:
    r"""Author of model.

    The author is defined
    by the Artifactory user name
    of the person that published the model.

    Args:
        uid: unique model ID
        version: version string

    Returns:
        model author

    Example:
        >>> author('98ccb530-b162-11ea-8427-ac1f6bac2502')
        'jwagner'

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

    The publication date is defined
    as the last date the model artifact was modified
    on Artifactory.

    Args:
        uid: unique model ID
        *,
        version: str = None,

    Returns:
        model publication date

    Example:
        >>> date('98ccb530-b162-11ea-8427-ac1f6bac2502')
        '2020/06/18'

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

    Example:
        >>> exists('98ccb530-b162-11ea-8427-ac1f6bac2502')
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
    r"""Download model header.

    Args:
        uid: unique model ID
        version: version string

    Returns:
        dictionary with meta information about model

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

    Example:
        >>> latest_version('98ccb530-b162-11ea-8427-ac1f6bac2502')
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
        RuntimeError: if model does not exist

    Example:
        >>> root = load('98ccb530-b162-11ea-8427-ac1f6bac2502')
        >>> '/'.join(root.split('/')[-8:])
        'audmodel/com/audeering/models/gender/audgender/98ccb530-b162-11ea-8427-ac1f6bac2502/1.0.0'
        >>> sorted(os.listdir(root))
        ['data-preprocessing',
         'extractor',
         'feature-preprocessing',
         'metrics',
         'post-processing',
         'requirements.txt.lock',
         'trainer']

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
        dictionary with meta information

    Example:
        >>> meta('98ccb530-b162-11ea-8427-ac1f6bac2502')
        {}

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

    Example:
        >>> name('98ccb530-b162-11ea-8427-ac1f6bac2502')
        'audgender'

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
        RuntimeError: if table does not exist

    Example:
        >>> parameters('98ccb530-b162-11ea-8427-ac1f6bac2502')
        {'classifier': "LinearSVC(C=0.1, class_weight='balanced', random_state=0)",
         'experiment': 'msp.msppodcast-1.0.0',
         'features': 'GeMAPSplus_v01',
         'sampling_rate': 8000,
         'scaler': 'StandardScaler()'}

    """  # noqa: E501
    try:
        return header(uid)['params']
    except FileNotFoundError:
        return legacy.parameters(uid)


def path_version_backend(
        uid: str,
        *,
        version: str = None,
) -> (str, str, audbackend.Backend):
    r"""Get path, version and backend."""

    if not audeer.is_uid(uid):
        raise ValueError(f"'{uid}' is not a valid ID")

    backend = None
    urls = []

    if config.BACKEND_HOST[0] == 'artifactory':
        # use REST API on Artifactory
        try:
            host = config.BACKEND_HOST[1]
            pattern = f'artifact?name={uid}'
            for repository in [
                config.REPOSITORY_PUBLIC,
                config.REPOSITORY_PRIVATE,
            ]:
                search_url = (
                    f'{host}/'
                    f'api/search/{pattern}&repos={repository}'
                )
                r = audfactory.rest_api_get(search_url)
                if r.status_code != 200:  # pragma: no cover
                    raise RuntimeError(
                        f'Error trying to find model.\n'
                        f'The REST API query was not successful:\n'
                        f'Error code: {r.status_code}\n'
                        f'Error message: {r.text}'
                    )
                results = r.json()['results']
                if results:
                    private = repository == config.REPOSITORY_PRIVATE
                    backend = get_backend(private)
                    for result in results:
                        url = result['uri']
                        if url.endswith('.zip'):
                            # Replace beginning of URI
                            # as it includes /api/storage and port
                            url = '/'.join(url.split('/')[6:])
                            url = f'{host}/{url}'
                            v = url.split('/')[-2]
                            # break early if specific version is requested
                            if version is None:
                                urls.append((url, backend))
                            elif v == version:
                                urls.append((url, backend))
                                break
        except ConnectionError:  # pragma: no cover
            raise ConnectionError(
                'Artifactory is offline.\n\n'
                'Please make sure https://artifactory.audeering.com '
                'is reachable.'
            )
    else:
        # use glob otherwise
        pattern = f'**/{uid}/*/*.zip'
        for private in [False, True]:
            backend = get_backend(private)
            for url in backend.glob(pattern):
                v = url.split('/')[-2]
                # break early if specific version is requested
                if version is None:
                    urls.append((url, backend))
                elif v == version:
                    urls.append((url, backend))
                    break

    if not urls:
        if version is None:
            raise RuntimeError(
                f"A model with ID "
                f"'{uid}' "
                f"does not exist."
            )
        else:
            raise RuntimeError(
                f"A model with ID "
                f"'{uid}' "
                f"and version "
                f"'{version}' "
                f"does not exist."
            )

    url, backend = urls[-1]
    version = url.split('/')[-2]
    path = url[len(backend.host) + len(backend.repository) + 2:]
    path = backend.join(*path.split(backend.sep)[:-2])

    return path, version, backend


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

    * data used to train the model
    * sampling rate
    * feature set(s)
    * scaling applied to the features
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


def remove(
        uid: str,
        version: str,
):
    r"""Remove a model.

    The model will be deleted on Artifactory.

    Args:
        uid: unique model ID
        version: version string

    """
    path, version, backend = path_version_backend(uid, version=version)

    if backend.exists(path + '.yaml', version):
        backend.remove_file(path + '.yaml', version)
    backend.remove_file(path + '.zip', version)


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

    Example:
        >>> subgroup('98ccb530-b162-11ea-8427-ac1f6bac2502')
        'gender'

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
        ...     'audgender',
        ...     {
        ...         'classifier': "LinearSVC(C=0.1, class_weight='balanced', random_state=0)",
        ...         'experiment': 'msp.msppodcast-1.0.0',
        ...         'features': 'GeMAPSplus_v01',
        ...         'sampling_rate': 8000,
        ...         'scaler': 'StandardScaler()',
        ...     },
        ...     subgroup='gender',
        ... )
        'b47015a8-6447-5190-ede6-340c4e70b4cb'

    """  # noqa: E501
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
        ValueError: if given unique ID is not valid
        ConnectionError: if Artifactory is not available
        RuntimeError: if Artifactory REST API query failes
        RuntimeError: if more than one model is found
        RuntimeError: if no model is found

    Example:
        >>> model_url = url('98ccb530-b162-11ea-8427-ac1f6bac2502')
        >>> '/'.join(model_url.split('/')[4:10])
        'models-public-local/com/audeering/models/gender/audgender'

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

    Example:
        >>> versions('98ccb530-b162-11ea-8427-ac1f6bac2502')
        ['1.0.0']

    """
    path, _, backend = path_version_backend(uid)
    return backend.versions(path + '.zip')
