Changelog
=========

All notable changes to this project will be documented in this file.

The format is based on `Keep a Changelog`_,
and this project adheres to `Semantic Versioning`_.


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
* Fixed: return tpye of :meth:`audmodel.interface.Generic.read_audio`


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
