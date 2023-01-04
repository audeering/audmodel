Contributing
============

If you would like to add new functionality fell free to create a `merge
request`_ . If you find errors, omissions, inconsistencies or other thingsh
that need improvement, please create an issue_.
Contributions are always welcome!

.. _issue: https://gitlab.audeering.com/tools/audmodel/issues/new?issue%5BD=
.. _merge request: https://gitlab.audeering.com/tools/audmodel/merge_requests/new


Development Installation
------------------------

Instead of pip-installing the latest release from PyPI, you should get the
newest development version from Gitlab_::

    git clone git@srv-app-01.audeering.local:tools/audmodel.git
    cd audmodel
    # Use virutal environment
    pip install -r requirements.txt

.. _Gitlab: https://gitlab.audeering.com/tools/audmodel

This way, your installation always stays up-to-date, even if you pull new
changes from the Gitlab repository.


Coding Convention
-----------------

We follow the PEP8_ convention for Python code
and check for correct syntax with flake8_.
Exceptions are defined under the ``[flake8]`` section
in :file:`setup.cfg`.

The checks are executed in the CI using `pre-commit`_.
You can enable those checks locally by executing::

    pip install pre-commit  # consider system wide installation
    pre-commit install
    pre-commit run --all-files

Afterwards flake8_ is executed
every time you create a commit.

You can also install flake8_
and call it directly::

    pip install flake8  # consider system wide installation
    flake8

It can be restricted to specific folders::

    flake8 audfoo/ tests/

.. _PEP8: http://www.python.org/dev/peps/pep-0008/
.. _flake8: https://flake8.pycqa.org/en/latest/index.html
.. _pre-commit: https://pre-commit.com


Building the Documentation
--------------------------

If you make changes to the documentation, you can re-create the HTML pages
using Sphinx_.
You can install it and a few other necessary packages with::

    pip install -r requirements.txt
    pip install -r docs/requirements.txt

To create the HTML pages, use::

	python -m sphinx docs/ build/sphinx/html -b html

The generated files will be available in the directory ``build/sphinx/html/``.

It is also possible to automatically check if all links are still valid::

    python -m sphinx docs/ build/sphinx/linkcheck -b linkcheck

.. _Sphinx: http://sphinx-doc.org/


Running the Tests
-----------------

You'll need pytest_ for that.
It can be installed with::

    pip install -r tests/requirements.txt

To execute the tests, simply run::

    python -m pytest

To run the tests on the Gitlab CI server,
contributors have to make sure
they have an existing ``artifactory-tokenizer`` repository
with the content described in the `Artifactory tokenizer documentation`_.

.. _pytest: https://pytest.org/
.. _Artifactory tokenizer documentation: https://gitlab.audeering.com/devops/artifactory/-/tree/master/token


Creating a New Release
----------------------

New releases are made using the following steps:

#. Update ``CHANGELOG.rst``
#. Commit those changes as "Release X.Y.Z"
#. Create an (annotated) tag with ``git tag -a vX.Y.Z``
#. Make sure you have an ``artifactory-tokenizer`` with ``deployers`` group
   permissions
#. Push the commit and the tag to Gitlab

.. _PyPI: https://artifactory.audeering.com/artifactory/api/pypi/pypi-local/simple/
.. _twine: https://twine.readthedocs.io/
