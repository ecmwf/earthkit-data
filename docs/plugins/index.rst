.. _contributing-overview:

Overview
========

.. toctree::
   :maxdepth: 1

   plugins


The **plugins developer guide** is part of the earthkit-data documentation
and describes how to create plugins to add
data and functionalities to earthkit-data, to make it available to the end-users.

Sharing code using plugins
--------------------------

In order to avoid rewriting the same code over and over, consider
distributing it, the design of earthkit-data allows this through plugins
developed by data providers and data users and other stakeholders.

earthkit-data has several types of plugins.

   - :doc:`Dataset plugin<datasets>`
   - :doc:`Sources plugin<sources>`

Depending on the functionalities provided by your code, it can be integrated
in earthkit-data differently either as a dataset or a source or a reader or a
helper plugin (please refer to the table below.)
If you are distributing or referring to a dataset, the right plugin type
for you is likely to be a :doc:`dataset plugin <datasets>`.

For more details, here is also a general description of the
:ref:`earthkit-data plugin mechanism <plugins-reference>`.


.. _list-plugin-table:

.. list-table::
   :widths: 10 80 10
   :header-rows: 1

   * - Plugin type
     - Use case
     - End-User API
   * - :doc:`Dataset <datasets>`
     - Sharing code to access a curated dataset optionally with additional functionalities.
     - :py:func:`climetlab.load_dataset`
   * - :doc:`Source <sources>`
     - Sharing code to access a new type of location where there are data.
     - :py:func:`climetlab.load_source`


.. How else can I contribute?
.. ------------------------------

.. See the :ref:`todo list <todolist>`.
