import datetime
import errno
import os
import typing

import oyaml as yaml

import audbackend
import audeer

from audmodel.core.backend import SERIALIZE_ERROR_MESSAGE
from audmodel.core.backend import archive_path
from audmodel.core.backend import get_archive
from audmodel.core.backend import get_header
from audmodel.core.backend import get_meta
from audmodel.core.backend import header_path
from audmodel.core.backend import header_versions
from audmodel.core.backend import meta_path
from audmodel.core.backend import put_archive
from audmodel.core.backend import put_header
from audmodel.core.backend import put_meta
from audmodel.core.backend import raise_model_not_found_error
from audmodel.core.backend import split_uid
from audmodel.core.config import config
import audmodel.core.define as define
from audmodel.core.repository import Repository
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
        audbackend.BackendError: if connection to repository on backend
            cannot be established
        RuntimeError: if model does not exist

    Examples:
        >>> author("d4e9c65b-3.0.0")
        'Calvin and Hobbes'

    """
    return header(uid, cache_root=cache_root)["author"]


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
        audbackend.BackendError: if connection to repository on backend
            cannot be established
        RuntimeError: if model does not exist

    Examples:
        >>> date("d4e9c65b-3.0.0")
        '1985-11-18'

    """
    return str(header(uid, cache_root=cache_root)["date"])


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

    Examples:
        >>> import audeer
        >>> cache_root = default_cache_root()
        >>> audeer.list_dir_names(cache_root, basenames=True)
        ['d4e9c65b']

    """
    return os.environ.get("AUDMODEL_CACHE_ROOT") or config.CACHE_ROOT


def exists(
    uid: str,
) -> bool:
    r"""Check if a model with this ID exists.

    Args:
        uid: unique model ID or short ID for latest version

    Returns:
        ``True`` if a model with this ID is found

    Raises:
        audbackend.BackendError: if connection to repository on backend
            cannot be established

    Examples:
        >>> exists("d4e9c65b-3.0.0")
        True
        >>> exists("d4e9c65b-9.9.9")
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
        audbackend.BackendError: if connection to repository on backend
            cannot be established
        RuntimeError: if model does not exist on backend

    Returns:
        dictionary with header fields

    Examples:
        >>> d = header("d4e9c65b-3.0.0")
        >>> print(yaml.dump(d))
        author: Calvin and Hobbes
        date: 1985-11-18
        name: torch
        parameters:
          model: cnn10
          data: emodb
          feature: melspec
          sampling_rate: 16000
        subgroup: audmodel.dummy.cnn
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
        audbackend.BackendError: if connection to repository on backend
            cannot be established
        RuntimeError: if model does not exist

    Examples:
        >>> latest_version("d4e9c65b")
        '3.0.0'
        >>> latest_version("d4e9c65b-1.0.0")
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

    Examples:
        >>> legacy_uid(
        ...     "test",
        ...     {
        ...         "model": "cnn10",
        ...         "data": "emodb",
        ...         "feature": "melspec",
        ...         "sampling_rate": 16000,
        ...     },
        ...     subgroup="audmodel.dummy.cnn",
        ...     version="1.0.0",
        ... )
        '65206614-dbb7-d61a-b00c-153db7b525c0'

    """
    group_id = (
        f"com.audeering.models.{name}"
        if subgroup is None
        else f"com.audeering.models.{subgroup}.{name}"
    )
    repository = (
        define.LEGACY_REPOSITORY_PRIVATE if private else define.LEGACY_REPOSITORY_PUBLIC
    )
    unique_string = str(params) + group_id + "lookup" + version + repository
    return audeer.uid(from_string=unique_string)


@audeer.deprecated_keyword_argument(
    deprecated_argument="root",
    new_argument="cache_root",
    mapping=lambda value: value,
    removal_version="1.2.0",
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
        audbackend.BackendError: if connection to repository on backend
            cannot be established
        RuntimeError: if model does not exist

    Examples:
        >>> root = load("d4e9c65b-3.0.0")
        >>> "/".join(root.split(os.path.sep)[-2:])
        'd4e9c65b/3.0.0'

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
        audbackend.BackendError: if connection to repository on backend
            cannot be established
        RuntimeError: if model does not exist

    Examples:
        >>> d = meta("d4e9c65b-3.0.0")
        >>> print(yaml.dump(d))
        data:
          emodb:
            version: 1.2.0
        feature:
          melspec:
            win_dur: 32ms
            hop_dur: 10ms
            num_fft: 512
            mel_bins: 64
        model:
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
        audbackend.BackendError: if connection to repository on backend
            cannot be established
        RuntimeError: if model does not exist

    Examples:
        >>> name("d4e9c65b-3.0.0")
        'torch'

    """
    return header(uid, cache_root=cache_root, verbose=verbose)["name"]


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
        audbackend.BackendError: if connection to repository on backend
            cannot be established
        RuntimeError: if model does not exist

    Examples:
        >>> parameters("d4e9c65b-3.0.0")
        {'model': 'cnn10', 'data': 'emodb', 'feature': 'melspec', 'sampling_rate': 16000}

    """  # noqa: E501
    return header(uid, cache_root=cache_root, verbose=verbose)["parameters"]


@audeer.deprecated_keyword_argument(
    deprecated_argument="private",
    removal_version="1.2.0",
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
    repository: Repository = config.REPOSITORIES[0],
    subgroup: str = None,
    verbose: bool = False,
) -> str:
    r"""Zip model and publish as a new artifact.

    Before publishing a model,
    pick meaningful values for
    ``name``,
    ``subgroup``,
    ``params``.
    The following table explains
    what the arguments should encode
    and shows examples.

    +--------------+---------------------+--------------------------------------+
    |              | Encodes             | Examples                             |
    +==============+=====================+=================================++===+
    | ``name``     |  - package          | - onnx                               |
    |              |    used to          | - sklearn                            |
    |              |    train/create     | - torch                              |
    |              |    the model        |                                      |
    +--------------+---------------------+--------------------------------------+
    | ``subgroup`` | - project           | - ser.dimensions.wav2vec2            |
    |              | - task the model    | - projectsmile.sex.cnn               |
    |              |   was trained for   |                                      |
    |              | - model architecture|                                      |
    +--------------+---------------------+--------------------------------------+
    | ``params``   | - model             | - {                                  |
    |              | - data              |   'model': 'facebook/wav2vec2-large',|
    |              | - feature set       |   'data': 'msppodcast',              |
    |              | - sampling rate     |   'sampling_rate': 16000             |
    |              |                     |   }                                  |
    |              |                     | - {                                  |
    |              |                     |   'model': 'cnn10',                  |
    |              |                     |   'data': ['agender', 'emodb'],      |
    |              |                     |   'feature': 'log-melspec',          |
    |              |                     |   'sampling_rate': 8000              |
    |              |                     |   }                                  |
    +--------------+---------------------+--------------------------------------+

    The ``meta`` argument encodes additional information.
    In contrast to ``name``, ``subgroup``, ``params`` it
    can be changed later.
    It should be used to extend information
    of the ``params`` entries
    using the same keys.
    In addition,
    it can store
    example output,
    and benchmark results.
    For example,
    a ``meta`` entry
    corresponding to the first ``params`` example from the table
    might contain:

    .. code-block::

        {
            'model': {'facebook/wav2vec2-large': {'layers': 24}},
            'data': {'msppodcast': {'version': '2.6.0'}},
        }

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
        audbackend.BackendError: if connection to repository on backend
            cannot be established
        RuntimeError: if a model with same UID exists already
        RuntimeError: if an unexpected error occurs during publishing
        RuntimeError: if ``meta`` or ``params``
            cannot be serialized to a YAML file
        ValueError: if subgroup is set to ``'_uid'``
        FileNotFoundError: if ``root`` folder cannot be found

    Examples:
        >>> # Assuming your model files are stored under `model_root`
        >>> # and your repository is given by `repository`
        >>> # (which you usually don't specify, but use its default value)
        >>> import datetime
        >>> name = "torch"
        >>> subgroup = "audmodel.dummy.cnn"
        >>> version = "4.0.0"
        >>> author = "Calvin and Hobbes"
        >>> data = datetime.date(1985, 11, 18)
        >>> params = {
        ...     "model": "cnn10",
        ...     "data": "emodb",
        ...     "feature": "melspec",
        ...     "sampling_rate": 16000,
        ... }
        >>> meta = {
        ...     "model": {
        ...         "cnn10": {
        ...             "learning-rate": 1e-4,
        ...             "optimizer": "sgd",
        ...         },
        ...     },
        ...     "data": {
        ...         "emodb": {
        ...             "version": "1.2.0",
        ...         },
        ...     },
        ...     "feature": {
        ...         "melspec": {
        ...             "win_dur": "32ms",
        ...             "hop_dur": "10ms",
        ...             "num_fft": 512,
        ...             "mel_bins": 64,
        ...         },
        ...     },
        ... }
        >>> publish(
        ...     model_root,
        ...     name,
        ...     params,
        ...     version,
        ...     author=author,
        ...     date=date,
        ...     meta=meta,
        ...     subgroup=subgroup,
        ...     repository=repository,
        ... )
        'd4e9c65b-4.0.0'

    """  # noqa: E501
    root = audeer.safe_path(root)
    subgroup = subgroup or ""

    if subgroup == define.UID_FOLDER:
        raise ValueError(f"It is not allowed to set subgroup to '{define.UID_FOLDER}'.")

    if not os.path.isdir(root):
        raise FileNotFoundError(
            errno.ENOENT,
            os.strerror(errno.ENOENT),
            root,
        )

    short_id = utils.short_id(name, params, subgroup)
    uid = f"{short_id}-{version}"

    if exists(uid):
        raise RuntimeError(f"A model with ID '{uid}' exists already.")

    backend_interface = repository.create_backend_interface()
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
            backend_interface,
            verbose,
        )
        put_meta(
            short_id,
            version,
            meta,
            backend_interface,
            verbose,
        )
        put_archive(
            short_id,
            version,
            name,
            subgroup,
            root,
            backend_interface,
            verbose,
        )
    except Exception as ex:
        # Otherwise remove already published files
        with backend_interface.backend:
            for ext in [define.HEADER_EXT, define.META_EXT]:
                path = backend_interface.join(
                    "/",
                    define.UID_FOLDER,
                    f"{short_id}.{ext}",
                )
                if backend_interface.exists(path, version):
                    backend_interface.remove_file(path, version)

            path = backend_interface.join(
                "/",
                *subgroup.split("."),
                name,
                short_id + ".zip",
            )
            if backend_interface.exists(path, version):  # pragma: no cover
                # we can probably assume that the archive
                # does not exist on the backend
                # if something goes wrong during 'put_archive()'
                # so it's not likely we'll ever end up in this case
                backend_interface.remove_file(path, version)

        # Reraise our custom error if params or meta cannot be serialized
        if isinstance(ex, RuntimeError) and ex.args[0].startswith(
            SERIALIZE_ERROR_MESSAGE
        ):
            raise ex
        else:  # pragma: no cover
            raise RuntimeError("Could not publish model due to an unexpected error.")

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
        audbackend.BackendError: if connection to repository on backend
            cannot be established
        RuntimeError: if model does not exist

    Examples:
        >>> subgroup("d4e9c65b-3.0.0")
        'audmodel.dummy.cnn'

    """
    return header(uid, cache_root=cache_root, verbose=verbose)["subgroup"]


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

    Examples:
        >>> uid(
        ...     "torch",
        ...     {
        ...         "model": "cnn10",
        ...         "data": "emodb",
        ...         "feature": "melspec",
        ...         "sampling_rate": 16000,
        ...     },
        ...     subgroup="audmodel.dummy.cnn",
        ... )
        'd4e9c65b'
        >>> uid(
        ...     "torch",
        ...     {
        ...         "model": "cnn10",
        ...         "data": "emodb",
        ...         "feature": "melspec",
        ...         "sampling_rate": 16000,
        ...     },
        ...     version="3.0.0",
        ...     subgroup="audmodel.dummy.cnn",
        ... )
        'd4e9c65b-3.0.0'

    """
    sid = utils.short_id(name, params, subgroup)
    if version is None:
        return sid
    else:
        return f"{sid}-{version}"


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
        audbackend.BackendError: if connection to repository on backend
            cannot be established
        RuntimeError: if model does not exist
        RuntimeError: if ``meta`` cannot be serialized to a YAML file

    Examples:
        >>> meta = {
        ...     "model": {
        ...         "cnn10": {"layers": 10},
        ...     },
        ... }
        >>> d = update_meta("d4e9c65b-3.0.0", meta)
        >>> print(yaml.dump(d))
        data:
          emodb:
            version: 1.2.0
        feature:
          melspec:
            win_dur: 32ms
            hop_dur: 10ms
            num_fft: 512
            mel_bins: 64
        model:
          cnn10:
            learning-rate: 0.01
            optimizer: adam
            layers: 10
        <BLANKLINE>
        >>> d = update_meta("d4e9c65b-3.0.0", meta, replace=True)
        >>> print(yaml.dump(d))
        model:
          cnn10:
            layers: 10
        <BLANKLINE>

    """
    cache_root = audeer.safe_path(cache_root or default_cache_root())
    short_id, version = split_uid(uid, cache_root)

    # update metadata
    backend_interface, meta_backend = get_meta(
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
        backend_interface,
        verbose,
    )

    # update cache
    local_path = os.path.join(
        cache_root,
        short_id,
        f"{version}.{define.META_EXT}",
    )
    with open(local_path, "w") as fp:
        yaml.dump(header, fp)

    return meta_backend


def url(
    uid: str,
    *,
    type: str = "model",
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
        audbackend.BackendError: if connection to repository on backend
            cannot be established
        RuntimeError: if URL does not exist
        ValueError: if wrong ``type`` is given

    Examples:
        >>> path = url("d4e9c65b-3.0.0")
        >>> os.path.basename(path)
        'd4e9c65b-3.0.0.zip'
        >>> path = url("d4e9c65b-3.0.0", type="header")
        >>> os.path.basename(path)
        'd4e9c65b-3.0.0.header.yaml'
        >>> path = url("d4e9c65b-3.0.0", type="meta")
        >>> os.path.basename(path)
        'd4e9c65b-3.0.0.meta.yaml'

    """
    cache_root = audeer.safe_path(cache_root or default_cache_root())
    short_id, version = split_uid(uid, cache_root)

    if type == "model":
        backend_interface, path = archive_path(
            short_id,
            version,
            cache_root,
            verbose,
        )
    elif type == "header":
        backend_interface, path = header_path(short_id, version)
    elif type == "meta":
        backend_interface, path = meta_path(
            short_id,
            version,
            cache_root,
            verbose,
        )
    else:
        raise ValueError(
            "'type' has to be one of "
            "'model', "
            "'header', "
            "'meta', "
            f"not '{type}'"
        )
    path = backend_interface._path_with_version(path, version)
    # Check for underlying backend of backend interface
    if isinstance(backend_interface.backend, audbackend.backend.FileSystem):
        path = backend_interface.sep.join([backend_interface.backend._root, path])
    elif isinstance(
        backend_interface.backend, audbackend.backend.Artifactory
    ):  # pragma: nocover
        # The tests should work locally,
        # so we don't test using a repository on Artifactory.
        # I tested the following line,
        # by manually calling
        # audmodel.url("90398682-2.0.0")
        path = str(backend_interface.backend.path(path))
    return path


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
        audbackend.BackendError: if connection to repository on backend
            cannot be established
        RuntimeError: if model does not exist

    Examples:
        >>> version("d4e9c65b-3.0.0")
        '3.0.0'

    """
    return header(uid, cache_root=cache_root, verbose=verbose)["version"]


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
        audbackend.BackendError: if connection to repository on backend
            cannot be established
        RuntimeError: if model does not exist

    Examples:
        >>> versions("d4e9c65b")
        ['1.0.0', '2.0.0', '3.0.0', '4.0.0']
        >>> versions("d4e9c65b-2.0.0")
        ['1.0.0', '2.0.0', '3.0.0', '4.0.0']

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
        short_id = uid.split("-")[0]
        matches = header_versions(short_id)
        return [match[2] for match in matches]
