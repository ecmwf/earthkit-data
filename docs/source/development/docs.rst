.. _dev_docs:


Documentation
-------------------

Building the documentation locally
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

To build the documentation locally, please install the Python dependencies first:

.. code-block:: shell

    pip install ".[docs]"
    cd docs

Then the documentation can be built by running the following command from the ``docs`` folder:

.. code-block:: shell

    make html

To see the generated HTML documentation open the ``docs/_build/html/index.html`` file in your browser.

Notebook examples
~~~~~~~~~~~~~~~~~~~~~~

The notebook examples are located in the ``docs/source/tutorials`` folder and are listed in the ``index.rst`` files in the subfolders. The notebooks are also part of the test suite and are run automatically. However, some notebooks are skipped mainly because they use remote data sources. This is controlled via the ``SKIP`` list in ``tests/documentation/test_notebooks.py``. You can modify this list to add or remove notebooks to be skipped.


If you add a new notebook example please:

- also add it to the relevant ``index.rst`` so that it appears in the documentation.
- ensure the title and the subchapter headings have the correct sizes: Titles use ``#``, subchapters use ``##``.
