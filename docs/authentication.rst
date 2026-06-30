Authentication
==============

To download or publish a model,
a user has to authenticate.

Credentials for repositories on S3
are stored in ``~/.config/audbackend/minio.cfg``.

E.g. for write access to ``audmodel-public``,
you need to add

.. code-block:: cfg

    [s3.dualstack.eu-north-1.amazonaws.com]
    access_key = MY_ACCESS_KEY
    secret_key = MY_SECRET_KEY

Alternatively,
users can export them as environment variables:

.. code-block:: bash

    export MINIO_ACCESS_KEY="MY_ACCESS_KEY"
    export MINIO_SECRET_KEY="MY_SECRET_KEY"
