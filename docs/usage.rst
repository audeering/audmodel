Usage
=====

.. Preload some data to avoid stderr print outs from tqdm,
.. but still avoid using the verbose=False flag later on

.. jupyter-execute::
    :stderr:
    :hide-output:
    :hide-code:

    import os
    import shutil
    import glob
    import audeer
    import audfactory
    import audmodel


    audmodel.core.define.defaults.REPOSITORY_PUBLIC = 'unittests-public-local'
    # Create a unique group iD
    # to not interrupt if another process is running in parallel
    audmodel.core.define.defaults.GROUP_ID += '.audmodel.' + audeer.uid()

    def create_model(name, files):
        root = os.path.join(os.getcwd(), 'models', name)
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


Introduction
------------

* We want to **publish** models on Artifactory_
* We want to **load** models from Artifactory_
* We want to tag models with **parameters**
  (e.g. the sampling rate it was trained on)

We assume that a model consists of one or more files
that are stored in a folder on your local disk,
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
        'task': 'anger,
        'rate': 8000,
    }

If we now publish the model (e.g. as version ``1.0.0``),
the following will happen:

1. A unique ``<id>`` is created
2. The model folder is zipped and published as artifact ``<id>-<version>.zip``
3. A row is added to a lookup table with ``<id>`` as index
   and ``params`` as values

And if we later download the model:

1. The requested ``<id>`` is resolved by Artifactory_
2. The artifact ``<id>-<version>.zip`` is downloaded
3. The archive is unpacked to the local model cache folder


Publish a model
---------------

Let’s assume we have a model folder ``root_mlp``,
consisting of the following files:

.. jupyter-execute::
    :hide-code:

    files = ['meta.yaml', 'network.txt', 'bin/mlp-weights.pkl']
    root_mlp = create_model('mymodel-mlp', files)
    show_model(root_mlp)

Before we can publish a model,
we have to define four different arguments:

* ``params``, parameters of the model
* ``name``, name of the model, e.g ``voxcnn``
* ``subgroup``, subgroup of the model, e.g. ``anger.autrainer``
* ``version``, version of the model, e.g. ``1.0.0``

For a discussion on how to select those arguments,
have a look at the discussion in the API documentation of
:func:`audmodel.publish`.

Let's define the four arguments for our example model:

.. jupyter-execute::

    params_mlp = {
        'data': 'emodb',
        'sampling_rate': 16000,
        'network': 'mlp',
    }
    name = 'voxcnn'
    subgroup = 'anger.autrainer'
    version = '1.0.0'

Now we can publish the model with

.. jupyter-execute::

    uid = audmodel.publish(
        root=root_mlp,
        name=name,
        subgroup=subgroup,
        params=params_mlp,
        version=version,
    )
    uid

The publishing process returns a unique model ID,
that can be used to access the model.
The model ID is derived from
``name``, ``version``, ``subgroup``, ``params``
and can always be used to safely identify a model.


Load a model
------------

With the model ID we can find its actual URL
on Artifactory:

.. jupyter-execute::

    audmodel.url(uid)

Or get information, about its name or its parameters:

.. jupyter-execute::

    audmodel.name(uid)

.. jupyter-execute::

    audmodel.parameters(uid)

To load a model from Artifactory_ to a model folder
is that simple as well:

.. jupyter-execute::

    model_folder = audmodel.load(uid)
    os.listdir(model_folder)


Publish another model
---------------------

Let's assume our published model wasn't very successful.
Hence, we decide to train another model using LSTMs.
To differentiate it from the first model,
we just need to update the parameters accordingly.

Let's again assume we have a model folder,
this time called ``root_lstm``:

.. jupyter-execute::
    :hide-code:

    files = ['meta.yaml', 'network.txt', 'bin/lstm-weights.pkl']
    root_lstm = create_model('mymodel-lstm', files)
    show_model(root_lstm)

We can then publish it with

.. jupyter-execute::

    params_lstm = {
        'data': 'emodb',
        'sampling_rate': 16000,
        'network': 'lstm',
    }
    uid = audmodel.publish(
        root=root_lstm,
        name=name,
        subgroup=subgroup,
        params=params_lstm,
        version=version,
    )
    uid

Now we published two different models with the same name,
subgroup, and version.

For a given name, subgroup, and version,
you can check which model IDs and parameters were used
by requesting the model lookup table.

.. jupyter-execute::

    audmodel.lookup_table(
        name=name,
        subgroup=subgroup,
        version=version,
    )


Different model parameters
--------------------------

After some analysis,
you find out the model will improve
if you normalize the audio data during training.
You therefore introduce a new parameter ``normalize``,
which is either ``True`` or ``False``.

.. jupyter-execute::

    params_lstm = {
        'data': 'emodb',
        'sampling_rate': 16000,
        'network': 'lstm',
        'normalize': True,
    }
    audmodel.publish(
        root=root_lstm,
        name=name,
        subgroup=subgroup,
        params=params_lstm,
        version=version,
    )
    audmodel.lookup_table(
        name=name,
        subgroup=subgroup,
        version=version,
    )

The new parameter is added to the lookup table,
and set to ``None`` for already submitted models.

If you submit another model,
but this time omitting one of the parameters inside the lookup table,
the parameter is set to ``None`` as well:

.. jupyter-execute::

    params_lstm = {
        'data': 'emodb',
        'sampling_rate': 8000,
        'network': 'lstm',
    }
    audmodel.publish(
        root=root_lstm,
        name=name,
        subgroup=subgroup,
        params=params_lstm,
        version=version,
    )
    audmodel.lookup_table(
        name=name,
        subgroup=subgroup,
        version=version,
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

    audmodel.config.AUDMODEL_CACHE_ROOT='/path/to/your/cache'

Or individually,
by calling :func:`audmodel.load`
with a non empty ``root`` argument.

Within the model cache folder
the model is placed in a unique sub-folder, namely
``<subgroup>/<name>/<version>/<uid>``.


.. jupyter-execute::
    :hide-code:

    def cleanup():
        root = os.path.join(os.getcwd(), 'models')
        if os.path.exists(root):
            shutil.rmtree(root)
        path = audfactory.artifactory_path(
            audfactory.server_url(audmodel.core.define.defaults.GROUP_ID,
                                  name='mymodel',
                                  repository='models-public-local')).parent
        if path.exists():
            path.rmdir()

    cleanup()


.. _Artifactory:
    https://artifactory.audeering.com/
