Development
===========

Contributions
-------------

The code repository is hosted on `Github`_, testing, bug reports and contributions are highly welcomed and appreciated. Feel free to fork it and submit your PRs against the **develop** branch.

Development setup
-----------------------

The recommended development environment is based on **conda**.

First, clone the repository locally. You can use the following command:

.. code-block:: shell

   git clone --branch develop git@github.com:ecmwf/earthkit-data.git


Next, enter your git repository and run the following commands:

.. code-block:: shell

    make conda-env-update
    conda activate earthkit-data
    make setup
    pip install -e .

This will create a new conda environment called "earthkit-data" with all the dependencies installed into it. This setup enables the `pre-commit`_ hooks, performing a series of quality control checks on every commit. If any of these checks fails the commit will be rejected.

Run unit tests
---------------

To run the test suite, you can use the following command:

.. code-block:: shell

    make unit-tests

Please note this will not run any of the tests based on remote services e.g. :ref:`data-sources-mars`. These are disabled by default because they can take a very long time to complete or just hang. To enable all these tests you need to run:

.. code-block:: shell

    pytest -E long -v

If just want to run e.g. the :ref:`data-sources-cds` tests you can use:

.. code-block:: shell

    pytest -E long -v -k cds


Build documentation
-------------------

To build the documentation locally, please install the Python dependencies first:

.. code-block:: shell

    cd docs
    pip install -r requirements.txt
    make html

To see the generated HTML documentation open the ``docs/_build/html/index.html`` file in your browser.


.. _`Github`: https://github.com/ecmwf/earthkit-data
.. _`pre-commit`: https://pre-commit.com/
