import typing

import audfactory

from audmodel.core.define import defaults


def name_from_url(url: str) -> str:
    return url.split('/')[-4]


def repository_from_url(url: str) -> str:
    return url.split('/')[4]


def subgroup_from_url(url: str) -> typing.Union[None, str]:
    # Consider length of group ID
    url_start = (
        f'{audfactory.config.ARTIFACTORY_ROOT}/'
        f'repo/'
        f'{audfactory.group_id_to_path(defaults.GROUP_ID)}'
    )
    start_length = len(url_start.split('/'))
    subgroup = '.'.join(url.split('/')[start_length:-4])
    if len(subgroup) == 0:
        return None
    else:
        return subgroup


def version_from_url(url: str) -> str:
    return url.split('/')[-2]
