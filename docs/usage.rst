Usage
=====

.. jupyter-execute::
    :stderr:
    :hide-output:
    :hide-code:

    import os
    import glob

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


    def show_model(path):
        path = audeer.safe_path(path)
        for root, dirs, files in os.walk(path):
            level = root.replace(path, "").count(os.sep)
            indent = " " * 4 * (level)
            print("{}{}/".format(indent, os.path.basename(root)))
            subindent = " " * 4 * (level + 1)
            for f in files:
                print("{}{}".format(subindent, f))


    cache_dir = audeer.mkdir("./tmp/cache")
    model_dir = audeer.mkdir("./tmp/models")
    audmodel.config.CACHE_ROOT = cache_dir


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

Let’s assume we have a model folder ``root_v1``,
consisting of the following files:

.. jupyter-execute::
    :hide-code:

    files = [
        "model.yaml",
        "model.onnx",
        "readme.txt",
        "log/eval.yaml",
    ]
    root_v1 = create_model("root_v1", files, model_dir)
    show_model(root_v1)

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

.. jupyter-execute::

    name = "onnx"
    params = {
        "model": "cnn10",
        "data": ["emodb", "msppodcast"],
        "feature": "melspec",
        "sampling_rate": 16000,
    }
    version = "1.0.0"
    author="sphinx"
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

Per default :mod:`audmodel` uses repositories
on Artifactory and S3.
For this example
we create a local temporary repository
in which the model is stored.

.. jupyter-execute::

    import audeer
    import audmodel

    repo = "models"
    host = audeer.path("./tmp/repo")
    audeer.mkdir(audeer.path(host, repo))
    repository = audmodel.Repository(repo, host, "file-system")
    audmodel.config.REPOSITORIES = [repository]



Now we can publish the model with

.. jupyter-execute::

    uid = audmodel.publish(
        root_v1,
        name,
        params,
        version,
        author=author,
        meta=meta,
        subgroup=subgroup,
        repository=repository,
    )
    uid

The publishing process returns a unique model ID,
that can be used to access the model.
The model ID is derived from
``name``, ``params``, ``subgroup``, ``version``.


Load a model
------------

With the model ID we can check if a model exists:

.. jupyter-execute::

    audmodel.exists(uid)

Or get its name,

.. jupyter-execute::

    audmodel.name(uid)

parameters,

.. jupyter-execute::

    audmodel.parameters(uid)

and meta fields.

.. jupyter-execute::

    audmodel.meta(uid)

To actually load the actual model, we do:

.. jupyter-execute::

    model_root = audmodel.load(uid)

Inside the :file:`model_root` folder
we will then have the following structure.

.. jupyter-execute::
    :hide-code:

    show_model(model_root)


Model alias
-----------

In addition to the model ID,
we can create different model aliases
to refer to a model.
An alias can already be selected during publication,
or it can be set afterwards with

.. jupyter-execute::

    audmodel.set_alias("emotion-small", uid)

We can inspect the corresponding model ID with

.. jupyter-execute::

    audmodel.resolve_alias("emotion-small")

and use the alias instead of the model ID
to access the model, e.g.

.. jupyter-execute::

    model_root = audmodel.load("emotion-small")

Note, that resolving a model alias always
requires access to the backend on which the model is stored.

We can add more than one alias for a model

.. jupyter-execute::

    audmodel.set_alias("emotion-production", uid)

and can inspect existing aliases for a model ID with

.. jupyter-execute::

    audmodel.aliases(uid)

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

.. jupyter-execute::

    meta["feature"]["melspec"]["mel_bins"] = 32

Let's again assume we have a model folder,
this time called ``root_v2``:

.. jupyter-execute::
    :hide-code:

    root_v2 = create_model("root_v2", files, model_dir)
    show_model(root_v2)

As this model has the same parameters, name, and subgroup
as our previous model,
we choose a new version number,
and publish it with:

.. jupyter-execute::

    uid_v1 = uid
    uid = audmodel.publish(
        root_v2,
        name,
        params,
        "2.0.0",
        meta=meta,
        subgroup=subgroup,
        repository=repository,
    )
    uid

Now we have published two versions of the model:

.. jupyter-execute::

    audmodel.versions(uid)

To find the latest version we can do:

.. jupyter-execute::

    audmodel.latest_version(uid)

We can update our existing model aliases
to point to the newest version.

.. jupyter-execute::

    audmodel.set_alias("emotion-small", uid)
    audmodel.set_alias("emotion-production", uid)

Now, all model aliases are only pointing to the new version:

.. jupyter-execute::

    audmodel.aliases(uid_v1)

.. jupyter-execute::

    audmodel.aliases(uid)


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

.. jupyter-execute::

    meta = {
        "model": {
            "cnn10": {"layers": 10},
        },
    }
    audmodel.update_meta(uid, meta)
    audmodel.meta(uid)

Alternatively,
we can replace the metadata.

.. jupyter-execute::

    meta = {"new": "meta"}
    audmodel.update_meta(uid, meta, replace=True)
    audmodel.meta(uid)


Cache folder
------------

Models are unpacked to the model cache folder,
which can be checked by:

.. jupyter-execute::

    cache_root = audmodel.default_cache_root()
    cache_root

.. jupyter-execute::

    audeer.list_dir_names(cache_root, basenames=True)

We can change the location of the cache folder
by setting an environment variable:

.. code-block:: bash

    export AUDMODEL_CACHE_ROOT=/path/to/your/cache

Or by changing it inside :class:`audmodel.config`:

.. code-block:: python

    audmodel.config.CACHE_ROOT="/path/to/your/cache"

Or individually,
by calling :func:`audmodel.load`
with a non empty ``cache_root`` argument.

Within the model cache folder
the model is placed in a unique sub-folder, namely
``<uid>/<version>``.


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


.. jupyter-execute::
    :hide-code:

    audeer.rmdir("./tmp")
