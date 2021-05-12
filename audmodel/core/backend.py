import audbackend

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
