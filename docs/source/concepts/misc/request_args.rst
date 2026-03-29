The following logic is applied to build the **requests**:

1. All individual dictionaries found in ``request`` and ``*args`` are used as separate requests.
2. If ``**kwargs`` are provided, they are merged into each request dictionary. If only ``**kwargs`` are provided (no ``request`` or ``*args`` specified), they form a single request.
3. If a request contains the :ref:`split_on <split_on>` key, the request is split into multiple requests based on the specified keys and their values.
