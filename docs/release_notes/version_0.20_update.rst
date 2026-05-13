Version 0.20 Updates
/////////////////////////


Version 0.20.0
===============

Changes
++++++++++++++++++++++++++++++

Previously, when using the :ref:`data-sources-mars` source via the standalone MARS client the ``MARS_AUTO_SPLIT_BY_DATES="1"`` environment variable was set to enable splitting of MARS requests by date when needed. However, this approach has been removed and now users must set this environment variable themselves when needed. This change was made to give users more control over the behavior of MARS requests and to avoid potential issues with unintended splitting of requests. (:pr:`974`)
 