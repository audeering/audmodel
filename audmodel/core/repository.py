import audbackend

import audmodel.core.define as define


class Repository:
    r"""Repository object.

    It stores all information
    needed to address a repository:
    the repository name,
    host,
    and the backend name.

    Args:
        name: repository name
        host: repository host
        backend: repository backend

    Examples:
        >>> Repository("data-local", "/data", "file-system")
        Repository('data-local', '/data', 'file-system')

    """

    _backends = {
        "file-system": audbackend.backend.FileSystem,
    }

    if hasattr(audbackend.backend, "Artifactory"):
        _backends["artifactory"] = audbackend.backend.Artifactory  # pragma: no cover

    backend_registry = _backends
    r"""Backend registry.

    Holds mapping between registered backend names,
    and their corresponding backend classes.

    """

    def __init__(
        self,
        name: str,
        host: str,
        backend: str,
    ):
        self.name = name
        r"""Repository name."""
        self.host = host
        r"""Repository host."""
        self.backend = backend
        r"""Repository backend."""

    def __eq__(self, other) -> bool:
        """Compare two repository instances.

        Args:
            other: repository instance

        Returns:
            ``True`` if the string representation of the repositories matches

        """
        return str(self) == str(other)

    def __repr__(self):  # noqa: D105
        return (
            f"Repository("
            f"'{self.name}', "
            f"'{self.host}', "
            f"'{self.backend}'"
            f")"
        )

    def create_backend_interface(self) -> audbackend.interface.Maven:
        r"""Return interface to access repository.

        When :attr:`Repository.backend` equals ``artifactory``,
        it creates an instance of :class:`audbackend.backend.Artifactory`.
        When :attr:`Repository.backend` equals ``file-system``,
        it creates an instance of :class:`audbackend.backend.FileSystem`.

        A :class:`audbackend.interface.Maven` interface
        is then wrapped around the backend.

        Returns:
            interface to repository

        """
        backend_class = self.backend_registry[self.backend]
        backend = backend_class(self.host, self.name)
        interface = audbackend.interface.Maven(
            backend,
            extensions=[
                define.HEADER_EXT,
                define.META_EXT,
            ],
        )
        return interface

    @classmethod
    def register(
        cls,
        backend_name: str,
        backend_class: type[audbackend.backend.Base],
    ):
        r"""Register backend class.

        Adds an entry to the dictionary
        stored in the class variable :data:`Repository.backend_registry`,
        mapping a backend name
        to an actual backend class.

        Args:
            backend_name: name of the backend,
                e.g. ``"file-system"``
            backend_class: class of the backend,
                that should be associated with ``backend_name``,
                e.g. ``"audbackend.backend.Filesystem"``

        Examples:
            >>> import audbackend
            >>> Repository.register("file-system", audbackend.backend.FileSystem)

        """
        cls.backend_registry[backend_name] = backend_class
