Authentication
==============

To download or publish a model,
a user has to authenticate.

Credentials for the ``models-local`` repository
on Artifactory
are stored in ``~/.artifactory_python.cfg``:

.. code-block:: cfg

    [artifactory.audeering.com/artifactory]
    username = MY_USERNAME
    password = MY_API_KEY

Alternatively,
they can export them as environment variables:

.. code-block:: bash

    export ARTIFACTORY_USERNAME="MY_USERNAME"
    export ARTIFACTORY_API_KEY="MY_API_KEY"

Credentials for the ``audmodel-internal`` repository
on S3
are stored in ``~/.config/audbackend/minio.cfg``:

.. code-block:: cfg

    [s3.dualstack.eu-north-1.amazonaws.com]
    access_key = MY_ACCESS_KEY
    secret_key = MY_SECRET_KEY

Alternatively,
users can export them as environment variables:

.. code-block:: bash

    export MINIO_ACCESS_KEY="MY_ACCESS_KEY"
    export MINIO_SECRET_KEY="MY_SECRET_KEY"
