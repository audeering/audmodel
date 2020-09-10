def name_from_url(url: str) -> str:
    return url.split('/')[-4]


def repository_from_url(url: str) -> str:
    return url.split('/')[4]


def subgroup_from_url(url: str) -> str:
    return '.'.join(url.split('/')[8:-4])


def version_from_url(url: str) -> str:
    return url.split('/')[-2]
