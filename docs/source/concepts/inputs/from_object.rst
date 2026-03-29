.. _from_object:

from_object
===============

.. warning::
   This guide is currently under construction and may be incomplete or inaccurate.


Getting data from a source
----------------------------

We can get data from a given source by using :func:`from_source`:

.. py:function:: from_object(name, *args, **kwargs)

  Return a :ref:`data object <data-object>` from the source specified by ``name`` .

  :param str name: the source (see below)
  :param tuple *args: specifies the data location and additional parameters to access the data
  :param dict **kwargs: provides **additional functionalities** including caching, filtering, sorting and indexing
