Version 0.14 Updates
/////////////////////////


Version 0.14.0
===============

CDS/ADS retrievals
+++++++++++++++++++++

- The date request parameter(s) in the :ref:`data-sources-cds` and :ref:`data-sources-ads` sources are now passed without any normalization to the underlying API. Previously, date parameters were normalised using the same set of rules as for :ref:`data-sources-mars` requests leading to inconsistencies. This is a breaking change enforcing the use of the CDS date syntax in :ref:`data-sources-cds` and :ref:`data-sources-ads` retrievals (:pr:`605`)
