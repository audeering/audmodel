.. _configuration:

Configuration
=============

:mod:`audmodel` can be configured with a :file:`~/.config/audmodel.yaml` file.
The configuration file is read during import
and will override the default settings.
The default settings are:

.. literalinclude:: ../audmodel/core/etc/audmodel.yaml
    :language: yaml

After loading :mod:`audmodel`
they can be accessed
or changed
using :class:`audmodel.config`.

.. code-block:: pycon

    >>> audmodel.config.CACHE_ROOT
    '~/audmodel'

.. code-block:: pycon

    >>> audmodel.config.REPOSITORIES
    [Repository('audmodel-public', 's3.dualstack.eu-north-1.amazonaws.com', 's3')]

.. code-block:: pycon

    >>> audmodel.config.CACHE_ROOT = "/user/cache"
    >>> audmodel.config.CACHE_ROOT
    '/user/cache'

The cache folder
can also be overridden
with the ``AUDMODEL_CACHE_ROOT`` environment variable.
