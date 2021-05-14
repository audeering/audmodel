import audbackend
import audeer
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


def path_version_backend(
        uid: str,
        *,
        version: str = None,
) -> (str, str, audbackend.Backend):
    r"""Get path, version and backend."""

    if not audeer.is_uid(uid):
        raise ValueError(f"'{uid}' is not a valid ID")

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
