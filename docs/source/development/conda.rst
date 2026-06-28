.. _conda_setup:

Development setup with Conda
------------------------------

You can set up a development environment using Conda. Below are the instructions to do so.

First, clone the repository locally. You can use the following command:

.. code-block:: shell

   git clone --branch develop git@github.com:ecmwf/earthkit-data.git

Then, create a new environment and activate it:

.. code-block:: shell

    conda create -n earthkit-data python=3.12
    conda activate earthkit-data

Lastly, enter your git repository and run the following commands:

.. code-block:: shell

    pip install -e .[dev]
    pre-commit install

This setup enables the `pre-commit`_ hooks, performing a series of quality control checks on every commit. If any of these checks fails the commit will be rejected.
