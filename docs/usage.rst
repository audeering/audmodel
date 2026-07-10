Usage
=====

.. invisible-code-block: python

    import os

    import audeer
    import audmodel


    def create_model(name, files, root):
        root = os.path.join(root, name)
        audeer.mkdir(root)
        for file in files:
            path = os.path.join(root, file)
            audeer.mkdir(os.path.dirname(path))
            with open(path, "w"):
                pass
        return root


    cache_dir = audeer.mkdir("./tmp/cache")
    model_dir = audeer.mkdir("./tmp/models")
    audmodel.config.CACHE_ROOT = cache_dir

    files = [
        "model.yaml",
        "model.onnx",
        "readme.txt",
        "log/eval.yaml",
    ]
    root_v1 = create_model("root_v1", files, model_dir)


Introduction
------------

:mod:`audmodel` is a versatile tool
to **publish**,
**load**,
and tag
machine learning models
with **parameters**,
(e.g. data and sampling rate),
and **metadata**
(e.g. hyperparameter).


Publish a model
---------------

Let's assume we have a model folder ``root_v1``,
consisting of the following files:

.. code-block:: text

    root_v1/
        model.onnx
        model.yaml
        readme.txt
        log/
            eval.yaml

Before we can publish a model,
we have to define several arguments:

* ``name``, name of the model, e.g ``onnx``
* ``params``, parameters of the model
* ``version``, version of the model, e.g. ``1.0.0``
* ``author``, name of the author
* ``meta``, dictionary with meta information
* ``subgroup``, subgroup of the model, e.g. ``emotion.cnn``

For a discussion on how to select those arguments,
have a look at the discussion in the API documentation of
:func:`audmodel.publish`.

Let's define the arguments for our example model:

.. code-block:: python

    name = "onnx"
    params = {
        "model": "cnn10",
        "data": ["emodb", "msppodcast"],
        "feature": "melspec",
        "sampling_rate": 16000,
    }
    version = "1.0.0"
    author = "sphinx"
    meta = {
        "model": {
            "cnn10": {
                "learning-rate": 1e-2,
                "optimizer": "adam",
            },
        },
        "data": {
            "emodb": {"version": "1.1.1"},
            "msppodcast": {"version": "2.6.0"},
        },
        "feature": {
            "melspec": {
                "win_dur": "32ms",
                "hop_dur": "10ms",
                "mel_bins": 64,
            },
        },
    }
    subgroup = "emotion.cnn"

By default :mod:`audmodel` uses repositories on S3.
For this example
we create a local temporary repository
in which the model is stored.

.. code-block:: python

    import audeer
    import audmodel

    repo = "models"
    host = audeer.path("./tmp/repo")
    audeer.mkdir(audeer.path(host, repo))
    repository = audmodel.Repository(repo, host, "file-system")
    audmodel.config.REPOSITORIES = [repository]

Now we can publish the model with

.. code-block:: pycon

    >>> uid = audmodel.publish(
    ...     root_v1,
    ...     name,
    ...     params,
    ...     version,
    ...     author=author,
    ...     meta=meta,
    ...     subgroup=subgroup,
    ...     repository=repository,
    ... )
    >>> uid
    '3e120e8d-1.0.0'

The publishing process returns a unique model ID,
that can be used to access the model.
The model ID is derived from
``name``, ``params``, ``subgroup``, ``version``.


Load a model
------------

With the model ID we can check if a model exists:

.. code-block:: pycon

    >>> audmodel.exists(uid)
    True

Or get its name,

.. code-block:: pycon

    >>> audmodel.name(uid)
    'onnx'

parameters,

.. code-block:: pycon

    >>> audmodel.parameters(uid)
    {'model': 'cnn10', 'data': ['emodb', 'msppodcast'], 'feature': 'melspec', 'sampling_rate': 16000}

and meta fields.

.. code-block:: pycon

    >>> audmodel.meta(uid)
    {'model': {'cnn10': {'learning-rate': 0.01, 'optimizer': 'adam'}},
     'data': {'emodb': {'version': '1.1.1'}, 'msppodcast': {'version': '2.6.0'}},
     'feature': {'melspec': {'win_dur': '32ms', 'hop_dur': '10ms', 'mel_bins': 64}}}

To actually load the actual model, we do:

.. code-block:: python

    model_root = audmodel.load(uid)

Inside the :file:`model_root` folder
we will then have the following structure.

.. code-block:: text

    1.0.0/
        model.onnx
        model.yaml
        readme.txt
        log/
            eval.yaml


Model alias
-----------

In addition to the model ID,
we can create different model aliases
to refer to a model.
An alias can already be selected during publication,
or it can be set afterwards with

.. code-block:: python

    audmodel.set_alias("emotion-small", uid)

We can inspect the corresponding model ID with

.. code-block:: pycon

    >>> audmodel.resolve_alias("emotion-small")
    '3e120e8d-1.0.0'

and use the alias instead of the model ID
to access the model, e.g.

.. code-block:: python

    model_root = audmodel.load("emotion-small")

Note, that resolving a model alias always
requires access to the backend on which the model is stored.

We can add more than one alias for a model

.. code-block:: python

    audmodel.set_alias("emotion-production", uid)

and can inspect existing aliases for a model ID with

.. code-block:: pycon

    >>> audmodel.aliases(uid)
    ['emotion-production', 'emotion-small']

We can update to which model ID an alias is pointing
by running :func:`audmodel.set_alias` again,
see next sub-section.


Publish a new version
---------------------

When making only minor changes to the model
that does not affect any of its parameters,
we can publish a new version of the model
and update only the ``meta`` entry.
As an example,
let's assume we switch to less Mel frequency bins
in the feature extractor.

.. code-block:: python

    meta["feature"]["melspec"]["mel_bins"] = 32

.. invisible-code-block: python

    root_v2 = create_model("root_v2", files, model_dir)

Let's again assume we have a model folder,
this time called ``root_v2``:

.. code-block:: text

    root_v2/
        model.onnx
        model.yaml
        readme.txt
        log/
            eval.yaml

As this model has the same parameters, name, and subgroup
as our previous model,
we choose a new version number,
and publish it with:

.. code-block:: pycon

    >>> uid_v1 = uid
    >>> uid = audmodel.publish(
    ...     root_v2,
    ...     name,
    ...     params,
    ...     "2.0.0",
    ...     meta=meta,
    ...     subgroup=subgroup,
    ...     repository=repository,
    ... )
    >>> uid
    '3e120e8d-2.0.0'

Now we have published two versions of the model:

.. code-block:: pycon

    >>> audmodel.versions(uid)
    ['1.0.0', '2.0.0']

To find the latest version we can do:

.. code-block:: pycon

    >>> audmodel.latest_version(uid)
    '2.0.0'

We can update our existing model aliases
to point to the newest version.

.. code-block:: python

    audmodel.set_alias("emotion-small", uid)
    audmodel.set_alias("emotion-production", uid)

Now, all model aliases are only pointing to the new version:

.. code-block:: pycon

    >>> audmodel.aliases(uid_v1)
    []

.. code-block:: pycon

    >>> audmodel.aliases(uid)
    ['emotion-production', 'emotion-small']


Update metadata
---------------

While the parameters of a model cannot be changed,
it is possible to update its metadata.

For instance,
we can update or add fields
by passing a dictionary
that holds new / altered information.
As the following example shows
this even works with nested fields.

.. code-block:: pycon

    >>> meta = {
    ...     "model": {
    ...         "cnn10": {"layers": 10},
    ...     },
    ... }
    >>> audmodel.update_meta(uid, meta)
    {'model': {'cnn10': {'learning-rate': 0.01, 'optimizer': 'adam', 'layers': 10}},
     'data': {'emodb': {'version': '1.1.1'}, 'msppodcast': {'version': '2.6.0'}},
     'feature': {'melspec': {'win_dur': '32ms', 'hop_dur': '10ms', 'mel_bins': 32}}}

Alternatively,
we can replace the metadata.

.. code-block:: pycon

    >>> meta = {"new": "meta"}
    >>> audmodel.update_meta(uid, meta, replace=True)
    {'new': 'meta'}


Cache folder
------------

Models are unpacked to the model cache folder,
which can be checked by:

.. code-block:: python

    cache_root = audmodel.default_cache_root()

We can change the location of the cache folder
by setting an environment variable:

.. code-block:: bash

    export AUDMODEL_CACHE_ROOT=/path/to/your/cache

Or by changing it inside :class:`audmodel.config`:

.. skip: next

.. code-block:: python

    audmodel.config.CACHE_ROOT = "/path/to/your/cache"

Or individually,
by calling :func:`audmodel.load`
with a non empty ``cache_root`` argument.

Within the model cache folder
the model is placed in a unique sub-folder, namely
``<uid>/<version>``.

.. code-block:: pycon

    >>> audeer.list_dir_names(cache_root, basenames=True)
    ['3e120e8d']


Shared cache folder
-------------------

You can use a shared cache folder.
Ensure to set the correct access rights,
compare the
`shared cache section <https://audeering.github.io/audb/caching.html#shared-cache>`_
in ``audb``'s documentation.
``audmodel`` uses lock files to avoid race conditions
when trying to access the same file.
You can only use a shared cache on the same platform
as the file lock mechanism is not cross-platform compatible.
