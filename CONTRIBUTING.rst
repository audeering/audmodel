Contributing
============

If you would like to add new functionality fell free to create a `merge
request`_ . If you find errors, omissions, inconsistencies or other things
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
    # Use virtual environment
    pip install -r requirements.txt

.. _Gitlab: https://gitlab.audeering.com/tools/audmodel

This way, your installation always stays up-to-date, even if you pull new
changes from the Gitlab repository.


Coding Convention
-----------------

We follow the PEP8_ convention for Python code
and use ruff_ as a linter and code formatter.
In addition,
we check for common spelling errors with codespell_.
Both tools and possible exceptions
are defined in :file:`pyproject.toml`.

The checks are executed in the CI using `pre-commit`_.
You can enable those checks locally by executing::

    pip install pre-commit  # consider system wide installation
    pre-commit install
    pre-commit run --all-files

Afterwards ruff_ and codespell_ are executed
every time you create a commit.

You can also install ruff_ and codespell_
and call it directly::

    pip install ruff codespell  # consider system wide installation
    ruff check --fix .  # lint all Python files, and fix any fixable errors
    ruff format .  # format code of all Python files
    codespell

It can be restricted to specific folders::

    ruff check audfoo/ tests/
    codespell audfoo/ tests/


.. _codespell: https://github.com/codespell-project/codespell/
.. _PEP8: http://www.python.org/dev/peps/pep-0008/
.. _pre-commit: https://pre-commit.com
.. _ruff: https://beta.ruff.rs


Building the Documentation
--------------------------

If you make changes to the documentation,
you can re-create the HTML pages using Sphinx_.
You can install it and a few other necessary packages with::

    pip install -r docs/requirements.txt

To create the HTML pages, use::

    python -m sphinx docs/ build/sphinx/html -b html

The generated files will be available
in the directory :file:`build/sphinx/html/`.

It is also possible to automatically check if all links are still valid::

    python -m sphinx docs/ build/sphinx/html -b linkcheck

.. _Sphinx: https://www.sphinx-doc.org


Running the Tests
-----------------

You'll need pytest_ for that.
It can be installed with::

    pip install -r tests/requirements.txt

To execute the tests, simply run::

    pytest tests/

To run the tests on the Gitlab CI server,
contributors have to make sure
they have an existing ``artifactory-tokenizer`` repository
as described in the `Artifactory tokenizer documentation`_.

.. _pytest: https://pytest.org/
.. _Artifactory tokenizer documentation: https://gitlab.audeering.com/devops/artifactory/tree/master/token


Creating a New Release
----------------------

New releases are made using the following steps:

#. Update ``CHANGELOG.rst``
#. Commit those changes as "Release X.Y.Z"
#. Create an (annotated) tag with ``git tag -a vX.Y.Z``
#. Make sure you have an `artifactory-tokenizer`_ project
#. Push the commit and the tag to Gitlab

.. _artifactory-tokenizer: https://gitlab.audeering.com/devops/artifactory/tree/master/token
