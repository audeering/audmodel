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
    uv sync

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

    uvx pre-commit install
    uvx pre-commit run --all-files

Afterwards ruff_ and codespell_ are executed
every time you create a commit.

You can also install ruff_ and codespell_
and call it directly::

    uvx ruff check --fix .  # lint all Python files, and fix any fixable errors
    uvx ruff format .  # format code of all Python files
    uvx codespell

It can be restricted to specific folders::

    uvx ruff check audmodel/ tests/
    uvx codespell audmodel/ tests/


.. _codespell: https://github.com/codespell-project/codespell/
.. _PEP8: http://www.python.org/dev/peps/pep-0008/
.. _pre-commit: https://pre-commit.com
.. _ruff: https://beta.ruff.rs


Building the Documentation
--------------------------

If you make changes to the documentation,
you can re-create the HTML pages using Sphinx_::

    uv run python -m sphinx docs/ build/html -b html

The generated files will be available
in the directory :file:`build/html/`.

It is also possible to automatically check if all links are still valid::

    uv run python -m sphinx docs/ build/html -b linkcheck

.. _Sphinx: https://www.sphinx-doc.org


Running the Tests
-----------------

You can run tests with pytest_::

    uv run pytest

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
