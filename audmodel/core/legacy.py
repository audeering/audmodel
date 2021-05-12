import os
import tempfile
import typing

import oyaml as yaml

import audeer
import audfactory

from audmodel.core.config import config
from audmodel.core.define import defaults
from audmodel.core.url import (
    name_from_url,
    repository_from_url,
    subgroup_from_url,
    version_from_url,
)
from audmodel.core.utils import upload_folder


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
    version = audfactory.Lookup.latest_version(
        defaults.ARTIFACTORY_HOST,
        _repository(private),
        _group_id(name, subgroup),
        params=params,
    )
    return version


def lookup_table(
        name: str,
        version: str = None,
        *,
        subgroup: str = None,
        private: bool = False,
) -> audfactory.Lookup:
    r"""Lookup table of specified models.

    Models are specified by the ``name``, ``subgroup``, ``version``,
    and ``private`` arguments.
    Besides they can vary by having different parameters,
    which are locked inside a lookup table
    and assigned to unique model IDs.
    To get an overview of all different parameters models
    where trained with,
    you can download the lookup table and inspect it.

    Args:
        name: model name
        version: version string
        subgroup: extend group ID to
            ``com.audeering.models.<subgroup>``.
            You can increase the depth
            by using dot-notation,
            e.g. setting ``subgroup=foo.bar``
            will result in
            ``com.audeering.models.foo.bar``
        private: repository is private

    Returns:
        lookup table of models

    Raises:
        RuntimeError: if table does not exist

    Example:
        >>> t = lookup_table('audgender', subgroup='gender', version='1.0.0')
        >>> t.columns
        ['classifier', 'experiment', 'features', 'sampling_rate', 'scaler']
        >>> t.ids
        ['f4e42076-b160-11ea-8427-ac1f6bac2502',
         '98ccb530-b162-11ea-8427-ac1f6bac2502']
        >>> t['98ccb530-b162-11ea-8427-ac1f6bac2502']
        {'classifier': "LinearSVC(C=0.1, class_weight='balanced', random_state=0)",
         'experiment': 'msp.msppodcast-1.0.0',
         'features': 'GeMAPSplus_v01',
         'sampling_rate': 8000,
         'scaler': 'StandardScaler()'}

    """  # noqa: E501
    lookup = audfactory.Lookup(
        defaults.ARTIFACTORY_HOST,
        _repository(private),
        _group_id(name, subgroup),
        version=version,
    )
    return lookup


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
    model_url = url(uid)
    lookup = _lookup_from_url(model_url)
    return lookup[uid]


def remove(uid: str):
    r"""Remove a model.

    The model will be deleted on Artifactory,
    and removed from its corresponding lookup table.

    Args:
        uid: unique model ID

    """
    model_url = url(uid)
    lookup = _lookup_from_url(model_url)
    lookup.remove(lookup[uid])
    audfactory.path(model_url).parent.parent.rmdir()


def uid(
        name: str,
        params: typing.Dict[str, typing.Any],
        version: str = None,
        *,
        subgroup: str = None,
        private: bool = False,
) -> str:
    r"""Unique model ID for given model arguments.

    Look for the unique ID of a published model,
    specified by model ``params``, ``name``, and ``subgroup``.

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

    Raises:
        RuntimeError: if no lookup table for the model exists

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
        ...     version='1.0.0',
        ... )
        '98ccb530-b162-11ea-8427-ac1f6bac2502'

    """  # noqa: E501
    repository = _repository(private)
    group_id = _group_id(name, subgroup)
    if version is None:
        version = audfactory.Lookup.latest_version(
            defaults.ARTIFACTORY_HOST,
            repository,
            group_id,
            params=params,
        )
    lookup = audfactory.Lookup(
        defaults.ARTIFACTORY_HOST,
        repository,
        group_id,
        version=version,
    )
    return lookup.find(params)


def url(uid: str) -> str:
    r"""Search for model of given ID.

    Args:
        uid: unique model ID

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
                    f'The REST API query was not succesful:\n'
                    f'Error code: {r.status_code}\n'
                    f'Error message: {r.text}'
                )
            urls = r.json()['results']
            if len(urls) > 1:  # pragma: no cover
                raise RuntimeError(f'Found more than one model: {urls}')
            elif len(urls) == 1:
                break
        if len(urls) == 0:
            raise RuntimeError(f"A model with ID '{uid}' does not exist")
        url = urls[0]['uri']
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
    versions = audfactory.Lookup.versions(
        defaults.ARTIFACTORY_HOST,
        _repository(private),
        _group_id(name, subgroup),
        name=defaults.LOOKUP_TABLE_NAME,
        params=params,
    )
    return versions


def _group_id(name: str, subgroup: str) -> str:
    if subgroup is None:
        return f'{defaults.GROUP_ID}.{name}'
    else:
        return f'{defaults.GROUP_ID}.{subgroup}.{name}'


def _lookup_from_url(model_url: str) -> audfactory.Lookup:
    group_id = _group_id(
        name_from_url(model_url),
        subgroup_from_url(model_url),
    )
    version = version_from_url(model_url)
    repository = repository_from_url(model_url)
    return audfactory.Lookup(
        defaults.ARTIFACTORY_HOST,
        repository,
        group_id,
        version=version,
    )


def _repository(private: bool) -> str:
    if private:
        return defaults.REPOSITORY_PRIVATE
    else:
        return defaults.REPOSITORY_PUBLIC
