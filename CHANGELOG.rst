Changelog
=========

All notable changes to this project will be documented in this file.

The format is based on `Keep a Changelog`_,
and this project adheres to `Semantic Versioning`_.


Version 1.4.0 (2025-12-08)
--------------------------

* Added: support for named model aliases.
  Most functions that take a ``uid``,
  accept alternatively the corresponding ``alias``
* Added: possibility to create model aliases
  by calling
  ``audmodel.set_alias(alias, uid)``,
  or setting the new ``alias`` argument
  of ``audmodel.publish()``
* Added: ``audmodel.resolve_alias(alias)``
  to get the corresponding model ``uid``
* Added: ``audmodel.aliases(uid)``
  to list all aliases
  pointing to the model ``uid``
* Added: support for Python 3.14
* Changed: set default value of the ``repository`` argument
  of ``audmodel.publish()``
  to ``None``.
  If it is ``None``,
  it will use ``audmodel.config.REPOSITORIES[0]``
  which returns the same default value as before
* Changed: depend on ``audbackend[all]>=2.2.3``
* Fixed: lock cache to avoid failures
  when two processes/users download the same model.
  The lock does not support cross-platform access to the cache
* Removed: support for Python 3.9


Version 1.3.1 (2025-03-05)
--------------------------

* Added: support for Artifactory backend in Python 3.12
* Changed: depend on ``audbackend>=2.2.2``


Version 1.3.0 (2024-12-11)
--------------------------

* Added: open-source release
* Added: ``audmodel-internal`` repository
  on S3
* Added: support for Python 3.11
* Added: support for Python 3.12 (without Artifactory backend)
* Added: support for Python 3.13 (without Artifactory backend)
* Changed: switch to MIT license


Version 1.2.0 (2024-05-10)
--------------------------

* Added: ``audmodel.Repository``
  to handle repositories for model storage
* Changed: depend on ``audbackend>=2.0.0``


Version 1.1.2 (2024-02-21)
--------------------------

* Fixed: link to repository
  and documentation
  inside the Python package


Version 1.1.1 (2023-11-13)
--------------------------

* Fixed: ensure ``audmodel.uid()`` returns the same ID
  when ``subgroup`` is ``None`` or ``''``


Version 1.1.0 (2023-10-17)
--------------------------

* Added: support for new backend API
* Changed: depend on ``audbackend>=1.0.0``


Version 1.0.7 (2023-01-04)
--------------------------

* Changed: split API documentation into sub-pages
  for each function/class


Version 1.0.6 (2022-05-05)
--------------------------

* Changed: update naming conventions for publishing a model
* Changed: add docstring examples for all API functions
* Fixed: ``audmodel.update_meta()`` does now return the updated metadata
  dictionary


Version 1.0.5 (2021-12-30)
--------------------------

* Changed: support Python 3.8 as default version


Version 1.0.4 (2021-11-26)
--------------------------

* Added: ``verbose`` argument to functions that interact with the backend
* Changed: use new sphinx-audeering-theme


Version 1.0.3 (2021-09-29)
--------------------------

* Fixed: ``audmodel.load()`` could fail when broken folders
  loaded by older versions of ``audmodel`` were present in the cache


Version 1.0.2 (2021-09-14)
--------------------------

* Added: tests for Windows
* Added: tests for macOS
* Fixed: folder creation bug under Windows when loading a model


Version 1.0.1 (2021-07-23)
--------------------------

* Changed: raise error if meta or parameters cannot be serialized
* Fixed: clean up files when :func:`audmodel.publish` is interrupted


Version 1.0.0 (2021-07-20)
--------------------------

* Added: :func:`audmodel.header`
* Added: :func:`audmodel.meta`
* Added: :func:`audmodel.legacy_uid`
* Added: :func:`audmodel.update_meta`
* Added: argument ``cache_root`` to several functions
* Added: argument ``type`` to :func:`audmodel.url`
* Changed: make ``'models-local'`` default repository
* Changed: shorter model ID format, e.g. ``'5fbbaf38-3.0.0'``
* Changed: support for different backends
* Deprecated: ``private`` in :func:`audmodel.publish`
* Deprecated: ``root`` in :func:`audmodel.load`
* Removed: ``audmodel.lookup_table()``
* Removed: ``audmodel.remove()``


Version 0.10.0 (2021-04-06)
---------------------------

* Changed: use audfactory>=1.0.0


Version 0.9.1 (2021-01-26)
--------------------------

* Fixed: allow for newer versions of ``audfactory``


Version 0.9.0 (2021-01-25)
--------------------------

* Added: :func:`audmodel.date`
* Added: :func:`audmodel.author`
* Added: :func:`audmodel.exists`
* Changed: include the repository name in the folders created in cache
* Changed: :func:`audmodel.url` raises now ``ConnectionError``
  instead of ``RuntimeError`` if Artifactory is offline


Version 0.8.0 (2020-09-14)
--------------------------

.. note:: With this version it becomes possible
    to load models only by their unique id.
    This introduces several breaking changes.
    For more details see the following
    `issue <https://gitlab.audeering.com/tools/audmodel/-/merge_requests/41>`_.

* Added:

  * :meth:`audmodel.default_cache_root`
  * :meth:`audmodel.name`
  * :meth:`audmodel.parameters`
  * :meth:`audmodel.subgroup`
  * :meth:`audmodel.uid`
  * :meth:`audmodel.url`
  * :meth:`audmodel.version`

* Changed:

  * :meth:`audmodel.latest_version`
  * :meth:`audmodel.load`
  * :meth:`audmodel.remove`
  * :meth:`audmodel.versions`

* Removed:

  * ``audmodel.create_lookup_table``
  * ``audmodel.delete_lookup_table``
  * ``audmodel.extend_params``
  * ``audmodel.get_*``
  * ``audmodel.load_by_id``
  * ``audmodel.Parameter``
  * ``audmodel.Parameters``


Version 0.6.1 (2020-07-01)
--------------------------

* Fixed: :func:`audmodel.versions` where not using the correct lookup table name
  and was broken


Version 0.6.0 (2020-06-22)
--------------------------

* Added: :class:`audmodel.Parameter` and :class:`audmodel.Parameters`
* Changed: ``unittest-public-local`` repository for unit testing
* Changed: replace ``Lookup`` class with :class:`audfactory.Lookup`
* Removed: remove ``aumodel.interface`` module
* Removed: dependencies to ``audiofile``, ``audsp``, ``numpy``, ``pandas``


Version 0.5.2 (2020-04-24)
--------------------------

* Added: :class:`audmodel.interface.ProcessWithContext`
* Changed: :meth:`audmodel.load` prints more informative error message


Version 0.5.1 (2020-04-23)
--------------------------

* Fixed: :meth:`audmodel.interface.Process.process_signal` uses correct
  sampling rate after resampling


Version 0.5.0 (2020-04-23)
--------------------------

* Added: :class:`audmodel.interface.Segment`
* Added: :meth:`audmodel.get_model_url`
* Changed: renamed interface class `Generic` to :class:`audmodel.interface.Process`
* Changed: :meth:`audmodel.publish` returns the model's uid instead of url


Version 0.4.1 (2020-04-20)
--------------------------

* Added: :meth:`audmodel.extend_params` and :meth:`audmodel.get_params`
* Fixed: return type of :meth:`audmodel.interface.Generic.read_audio`


Version 0.4.0 (2020-04-16)
--------------------------

* Added: :class:`audmodel.interface.Generic`


Version 0.3.3 (2020-03-18)
--------------------------

* Added: verbose flag
* Added: publish models under a subgroup


Version 0.3.2 (2020-03-10)
--------------------------

* Changed: :class:`audmodel.config` now member of :mod:`audmodel`
* Fixed: url of tutorial notebook


Version 0.3.1 (2020-02-27)
--------------------------

* Changed: update documentation


Version 0.3.0 (2020-02-27)
--------------------------

* Added: Sphinx documentation
* Added: Jupyter tutorial
* Changed: request (latest) version(s) for specific parameters (see
  :func:`audmodel.version` and :func:`audmodel.latest_version`)
* Changed: running tests in parallel


Version 0.2.0 (2020-02-25)
--------------------------

* Added: unit tests with full code coverage
* Added: :func:`audmodel.delete_lookup_table`
* Added: :func:`audmodel.get_default_cache_root`
* Added: :func:`audmodel.latest_version`
* Added: :func:`audmodel.versions`


Version 0.1.0 (2020-02-24)
--------------------------

* Added: initial release


.. _Keep a Changelog:
    https://keepachangelog.com/en/1.0.0/
.. _Semantic Versioning:
    https://semver.org/spec/v2.0.0.html
