import typing

import audbackend
import audfactory

from audmodel.core.config import config


def get_backend(private: bool) -> audbackend.Backend:
    r"""Get backend.

    Args:
        private: private repository

    Returns:
        backend object

    """
    if private:  # pragma: no cover
        repository = config.REPOSITORY_PRIVATE
    else:
        repository = config.REPOSITORY_PUBLIC
    return audbackend.create(
        name=config.BACKEND_HOST[0],
        host=config.BACKEND_HOST[1],
        repository=repository,
    )


def search_backend(
        short_uid: str,
        version: str = None,
) -> typing.Union[
    typing.Tuple[audbackend.Backend, str],
    typing.Sequence[typing.Tuple[audbackend.Backend, str, str]]
]:
    r"""Find all or specific version of a model.

    If no match is found:
    -> raise error if specific version is requested
    -> return empty list otherwise

    """
    urls = []

    if config.BACKEND_HOST[0] == 'artifactory':
        # use REST API on Artifactory
        try:
            host = config.BACKEND_HOST[1]
            pattern = f'artifact?name={short_uid}'
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
        if version is None:
            pattern = f'**/{short_uid}/*/*.zip'
        else:
            pattern = f'**/{short_uid}/{version}/{short_uid}-{version}.zip'
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

    if not urls and version is not None:
        uid = short_uid if len(short_uid) != 8 else f'{short_uid}-{version}'
        raise RuntimeError(
            f"A model with ID "
            f"'{uid}' "
            f"does not exist."
        )

    if version is not None:
        url, backend = urls[-1]
        path = url_to_path(backend, url)
        return backend, path

    matches = []
    for url, backend in urls:
        path = url_to_path(backend, url)
        v = url.split('/')[-2]
        matches.append((backend, path, v))
    return matches


def url_to_path(
        backend: audbackend.Backend,
        url: str,
) -> str:
    path = url[len(backend.host) + len(backend.repository) + 2:]
    path = backend.join(*path.split(backend.sep)[:-2])
    return path
