Usage
=====

.. Preload some data to avoid stderr print outs from tqdm,
.. but still avoid using the verbose=False flag later on

.. jupyter-execute::
    :stderr:
    :hide-output:
    :hide-code:

    import os
    import glob


    def create_model(name, files):
        root = os.path.join(ROOT, 'models', name)
        audeer.mkdir(root)
        for file in files:
            path = os.path.join(root, file)
            audeer.mkdir(os.path.dirname(path))
            with open(path, 'w'):
                pass
        return root

    def show_model(path):
        path = audeer.safe_path(path)
        for root, dirs, files in os.walk(path):
            level = root.replace(path, '').count(os.sep)
            indent = ' ' * 4 * (level)
            print('{}{}/'.format(indent, os.path.basename(root)))
            subindent = ' ' * 4 * (level + 1)
            for f in files:
                print('{}{}'.format(subindent, f))


To avoid publishing the
following examples on Artifactory,
we replace the default backend
with a folder on the local file system.

.. jupyter-execute::

    import audeer
    import audmodel


    ROOT = audeer.mkdir('./docs/tmp')
    audmodel.config.BACKEND_HOST = (
        'file-system',
        ROOT,
    )
    audmodel.config.CACHE_ROOT = os.path.join(
        ROOT,
        'cache',
    )


Introduction
------------

:mod:`audmodel` is a versatile tool
that

* **publishes** models on Artifactory_
* **loads** models from Artifactory_
* tags models with **parameters**
  (e.g. the sampling rate it was trained on)

:mod:`audmodel` assumes
a model consists of file(s)
stored in a local folder,
e.g:

.. code-block::

    <root>/
        file.yaml
        file.txt
        bin/
            another-file.pkl

In addition,
a dictionary holding the parameters
needs to be passed, e.g.:

.. code-block:: python

    params = {
        'feature': 'melspec64',
        'model': 'cnn10',
        'sampling_rate': 16000,
    }

When publishing the model,
:mod:`audmodel`

1. creates a unique ``<id>``
2. publishes model header as artifact ``<id>-<version>.yaml``
3. zips the model folder and publishes it as artifact ``<id>-<version>.zip``

When downloading the model,
:mod:`audmodel`

1. requests the ``<id>`` on Artifactory_
2. downloads the artifact ``<id>-<version>.zip``
3. unpacks the archive to the local model cache folder


Publish a model
---------------

Let’s assume we have a model folder ``root_v1``,
consisting of the following files:

.. jupyter-execute::
    :hide-code:

    files = ['meta.yaml', 'network.txt', 'bin/weights_v1.pkl']
    root_v1 = create_model('cnn-v1', files)
    show_model(root_v1)

Before we can publish a model,
we have to define several arguments:

* ``author``, name of the author
* ``name``, name of the model, e.g ``cnn``
* ``meta``, dictionary with meta information
* ``params``, parameters of the model
* ``subgroup``, subgroup of the model, e.g. ``emotion.onnx``
* ``version``, version of the model, e.g. ``1.0.0``

For a discussion on how to select those arguments,
have a look at the discussion in the API documentation of
:func:`audmodel.publish`.

Let's define the four arguments for our example model:

.. jupyter-execute::

    author='sphinx'
    name = 'cnn'
    meta_v1 = {
        'data': {
            'emodb': {
                'version': '1.1.1',
                'format': 'wav',
                'mixdown': True,
            }
        },
        'melspec64': {
            'win_dur': '32ms',
            'hop_dur': '10ms',
            'num_fft': 512,
        },
        'cnn10': {
            'learning-rate': 1e-2,
            'optimizer': 'adam',
        }
    }
    params = {
        'feature': 'melspec64',
        'model': 'cnn10',
        'sampling_rate': 16000,
    }
    subgroup = 'emotion.onnx'
    version = '1.0.0'

Now we can publish the model with

.. jupyter-execute::

    uid = audmodel.publish(
        author=author,
        name=name,
        meta=meta_v1,
        params=params,
        subgroup=subgroup,
        root=root_v1,
        version=version,
    )
    uid

The publishing process returns a unique model ID,
that can be used to access the model.
The model ID is derived from
``name``, ``params``, ``subgroup``
and can always be used to safely identify a model.


Load a model
------------

With the model ID we can check if a model exists:

.. jupyter-execute::

    audmodel.exists(uid)

Or get information, about its name, parameters or meta fields:

.. jupyter-execute::

    audmodel.name(uid)

.. jupyter-execute::

    audmodel.parameters(uid)

.. jupyter-execute::

    audmodel.meta(uid)

To actually load the actual model, we do

.. jupyter-execute::

    model_root = audmodel.load(uid)
    show_model(model_root)


Publish another model
---------------------

Let's assume our published model wasn't very successful.
Hence, we decide to train the model on more data.

Let's again assume we have a model folder,
this time called ``root_v2``:

.. jupyter-execute::
    :hide-code:

    files = ['meta.yaml', 'network.txt', 'bin/weights_v2.pkl']
    root_v2 = create_model('cnn-v2', files)
    show_model(root_v2)

We include information about the new data
in the meta dictionary:

.. jupyter-execute::

    meta_v2 = meta_v1.copy()
    meta_v2['data']['msppodcast'] = {
        'version': '2.3.1',
        'format': 'wav',
        'mixdown': True,
    }

And publish it with

.. jupyter-execute::

    uid = audmodel.publish(
        name=name,
        meta=meta_v2,
        params=params,
        root=root_v2,
        subgroup=subgroup,
        version='2.0.0',
    )
    uid

Now we have published two versions of the model:

.. jupyter-execute::

    audmodel.versions(
        name=name,
        params=params,
        subgroup=subgroup,
    )

To get only the the latest version of a model we can do:

.. jupyter-execute::

    audmodel.latest_version(
        name=name,
        params=params,
        subgroup=subgroup,
    )


Cache folder
------------

Models are unpacked to the model cache folder,
which can be checked by...

.. jupyter-execute::

    audmodel.default_cache_root()

You can change the location of the cache folder
by setting an environment variable:

.. code-block:: bash

    export AUDMODEL_CACHE_ROOT=/path/to/your/cache

Or by changing it inside :class:`audmodel.config`:

.. code-block:: python

    audmodel.config.CACHE_ROOT='/path/to/your/cache'

Or individually,
by calling :func:`audmodel.load`
with a non empty ``root`` argument.

Within the model cache folder
the model is placed in a unique sub-folder, namely
``com/audeering/models/<subgroup>/<name>/<uid>/<version>``.


.. jupyter-execute::
    :hide-code:

    import shutil


    shutil.rmtree(ROOT)


.. _Artifactory:
    https://artifactory.audeering.com/
