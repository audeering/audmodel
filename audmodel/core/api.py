import os
import tempfile
import typing

import oyaml as yaml

import audeer
import audfactory

from audmodel.core.config import config
from audmodel.core.define import defaults
import audmodel.core.legacy as legacy
from audmodel.core.url import (
    name_from_url,
    repository_from_url,
    subgroup_from_url,
    version_from_url,
)
from audmodel.core.utils import upload_folder


def author(uid: str) -> str:
    r"""Author of model.

    The author is defined
    by the Artifactory user name
    of the person that published the model.

    Args:
        uid: unique model ID

    Returns:
        model author

    Example:
        >>> author('98ccb530-b162-11ea-8427-ac1f6bac2502')
        'jwagner'

    """
    model_url = url(uid)
    path = audfactory.path(model_url)
    stats = path.stat()
    return stats.modified_by


def date(uid: str) -> str:
    r"""Publication date of model.

    The publication date is defined
    as the last date the model artifact was modified
    on Artifactory.

    Args:
        uid: unique model ID

    Returns:
        model publication date

    Example:
        >>> date('98ccb530-b162-11ea-8427-ac1f6bac2502')
        '2020/06/18'

    """
    model_url = url(uid)
    path = audfactory.path(model_url)
    stats = path.stat()
    return stats.mtime.strftime('%Y/%m/%d')


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
        verbose: bool = False,
) -> dict:

    model_url = url(uid, version=version)

    with tempfile.TemporaryDirectory() as root:
        path = audfactory.download(
            model_url[:-4] + '.yaml',
            root,
            verbose=verbose,
        )
        with open(path, 'r') as fp:
            return yaml.load(fp, Loader=yaml.Loader)


def latest_version(
        name: str,
        params: typing.Dict[str, typing.Any] = None,
        *,
        subgroup: str = None,
        private: bool = False,
) -> str:
    r"""Latest available version of model.

    The highest version,
    that is available for the combination
    of provided ``name``, ``subgroup``,
    and model ``params``.

    Args:
        name: model name
        params: dictionary with parameters
        subgroup: extend group ID to
            ``com.audeering.models.<subgroup>``.
            You can increase the depth
            by using dot-notation,
            e.g. setting ``subgroup=foo.bar``
            will result in
            ``com.audeering.models.foo.bar``
        private: repository is private

    Returns:
        latest version of model

    Example:
        >>> latest_version('audgender', subgroup='gender')
        '1.0.0'

    """
    vs = versions(
        name,
        params,
        subgroup=subgroup,
        private=private,
    )
    if vs:
        v = vs[-1]
    else:
        v = legacy.latest_version(
            name,
            params,
            subgroup=subgroup,
            private=private,
        )
    return v


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
        uid: unique model identifier
        version: version string,
        root: store model within this folder
        verbose: show verbose output

    Returns:
        path to model folder

    Raises:
        RuntimeError: if model does not exist

    Example:
        >>> model_folder = load('98ccb530-b162-11ea-8427-ac1f6bac2502')
        >>> '/'.join(model_folder.split('/')[-9:])
        'audmodel/models-public-local/com/audeering/models/gender/audgender/98ccb530-b162-11ea-8427-ac1f6bac2502/1.0.0'
        >>> sorted(os.listdir(model_folder))
        ['data-preprocessing',
         'extractor',
         'feature-preprocessing',
         'metrics',
         'post-processing',
         'requirements.txt.lock',
         'trainer']

    """
    model_url = url(uid, version=version)
    repository = repository_from_url(model_url)
    group_id = _group_id(
        name_from_url(model_url),
        subgroup_from_url(model_url),
    )
    if version is None:
        version = version_from_url(model_url)

    root = audeer.safe_path(root or default_cache_root())
    root = os.path.join(
        root or default_cache_root(),
        repository,
        audfactory.group_id_to_path(group_id),
        uid,
        version,
    )
    root = audeer.safe_path(root)

    if not os.path.exists(root):
        tmp_root = audeer.mkdir(root + '~')
        path = audfactory.download(model_url, tmp_root, verbose=verbose)
        audeer.extract_archive(
            path,
            tmp_root,
            keep_archive=False,
            verbose=verbose,
        )
        audeer.mkdir(root)
        os.rename(tmp_root, root)

    return root


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
    model_url = url(uid)
    return name_from_url(model_url)


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
    except RuntimeError:
        return legacy.parameters(uid)


def publish(
        root: str,
        name: str,
        params: typing.Dict[str, typing.Any],
        version: str,
        *,
        subgroup: str = None,
        private: bool = False,
        verbose: bool = False,
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
        subgroup: extend group ID to
            ``com.audeering.models.<subgroup>``.
            You can increase the depth
            by using dot-notation,
            e.g. setting
            ``subgroup=foo.bar``
            will result in
            ``com.audeering.models.foo.bar``
        private: repository is private
        verbose: show verbose output

    Returns:
        unique model ID

    Raises:
        RuntimeError: if an artifact exists already

    """
    group_id = _group_id(name, subgroup)
    repository = _repository(private)
    model_id = uid(name, params, subgroup=subgroup, private=private)

    # publish meta data

    meta = {
        'name': name,
        'subgroup': subgroup,
        'params': params,
        'version': version,
    }
    with tempfile.TemporaryDirectory() as tmp_root:
        meta_path = os.path.join(tmp_root, 'header.yaml')
        with open(meta_path, 'w') as fp:
            yaml.dump(meta, fp)
        url = audfactory.url(
            defaults.ARTIFACTORY_HOST,
            repository=repository,
            group_id=group_id,
            name=model_id,
            version=version,
        )
        meta_url = f'{url}/{model_id}-{version}.yaml'
        audfactory.deploy(meta_path, meta_url, verbose=verbose)

    # upload model

    upload_folder(root, group_id, repository, model_id, version, verbose)

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
    pass


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
    model_url = url(uid)
    return subgroup_from_url(model_url)


def uid(
        name: str,
        params: typing.Dict[str, typing.Any] = None,
        *,
        subgroup: str = None,
        private: bool = False,
) -> str:
    r"""Unique model ID for given model arguments.

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
        private: repository is private

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
        '944dcc3e-04f3-5837-f3aa-8d19714b4735'

    """  # noqa: E501
    group_id = _group_id(name, subgroup)
    repository = _repository(private)
    unique_string = (
        '' if params is None else str(params)
        + group_id
        + repository
    )
    return audeer.uid(from_string=unique_string)


def url(
        uid: str,
        *,
        version: str = None,
) -> str:
    r"""Search for model of given ID.

    Args:
        uid: unique model ID
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
    if not audeer.is_uid(uid):
        raise ValueError(f"'{uid}' is not a valid ID")
    try:
        pattern = f'artifact?name={uid}'
        for repository in [
                defaults.REPOSITORY_PUBLIC,
                defaults.REPOSITORY_PRIVATE,
        ]:
            search_url = (
                f'{defaults.ARTIFACTORY_HOST}/'
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
            urls = r.json()['results']
            if len(urls) > 0:
                break
        if len(urls) == 0:
            raise RuntimeError(f"A model with ID '{uid}' does not exist.")

        if version is None:
            url = urls[-1]['uri']
        else:
            url = None
            for u in urls:
                if u['uri'].endswith(f'{version}.zip'):
                    url = u['uri']
                    break
            if url is None:
                raise RuntimeError(f"A model with ID '{uid}' "
                                   f"and version '{version}' "
                                   f"does not exist.")

    except ConnectionError:  # pragma: no cover
        raise ConnectionError(
            'Artifactory is offline.\n\n'
            'Please make sure https://artifactory.audeering.com '
            'is reachable.'
        )
    # Replace beginning of URL as it includes /api/storage and port
    relative_repo_url = '/'.join(url.split('/')[6:])
    url = f'{defaults.ARTIFACTORY_HOST}/{relative_repo_url}'
    return url


def version(uid: str) -> str:
    r"""Version of model.

    Args:
        uid: unique model ID

    Returns:
        model version

    Example:
        >>> version('98ccb530-b162-11ea-8427-ac1f6bac2502')
        '1.0.0'

    """
    model_url = url(uid)
    return version_from_url(model_url)


def versions(
        name: str,
        params: typing.Dict[str, typing.Any] = None,
        *,
        subgroup: str = None,
        private: bool = False,
) -> typing.List[str]:
    r"""Available model versions.

    All versions,
    that are available for the combination
    of provided ``name``, ``subgroup``,
    and model ``params``.

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
        private: repository is private

    Returns:
        available model versions

    Example:
        >>> versions('voxcnn', subgroup='speakerid')
        ['0.1.0', '0.2.0', '0.3.0', '0.3.1', '0.3.2']

    """
    model_id = uid(
        name,
        params,
        subgroup=subgroup,
        private=private,
    )
    vs = audfactory.versions(
        defaults.ARTIFACTORY_HOST,
        repository=_repository(private),
        group_id=_group_id(name, subgroup),
        name=model_id,
    )
    if not vs:
        vs = legacy.versions(
            name,
            params,
            subgroup=subgroup,
            private=private,
        )
    return vs


def _group_id(name: str, subgroup: str) -> str:
    if subgroup is None:
        return f'{defaults.GROUP_ID}.{name}'
    else:
        return f'{defaults.GROUP_ID}.{subgroup}.{name}'


def _repository(private: bool) -> str:
    if private:
        return defaults.REPOSITORY_PRIVATE
    else:
        return defaults.REPOSITORY_PUBLIC
