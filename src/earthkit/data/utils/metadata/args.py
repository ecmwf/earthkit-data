# (C) Copyright 2020 ECMWF.
#
# This software is licensed under the terms of the Apache Licence Version 2.0
# which can be obtained at http://www.apache.org/licenses/LICENSE-2.0.
# In applying this licence, ECMWF does not waive the privileges and immunities
# granted to it by virtue of its status as an intergovernmental organisation
# nor does it submit to any jurisdiction.
#


def metadata_argument(*args, namespace=None, astype=None):
    """Helps parsing the input arguments for the metadata methods"""
    key = []
    key_arg_type = None
    if len(args) == 1 and isinstance(args[0], str):
        key_arg_type = str
    elif len(args) >= 1:
        key_arg_type = tuple
        for k in args:
            if isinstance(k, list):
                key_arg_type = list

    for k in args:
        if isinstance(k, str):
            key.append(k)
        elif isinstance(k, (list, tuple)):
            key.extend(k)
        else:
            raise ValueError(f"metadata: invalid key argument={k}")

    if key:
        if namespace is not None:
            if not isinstance(namespace, str):
                raise ValueError(f"metadata: namespace={namespace} must be a str when key specified")

        if isinstance(astype, (list, tuple)):
            if len(astype) != len(key):
                if len(astype) == 1:
                    astype = [astype[0]] * len(key)
                else:
                    raise ValueError("metadata: astype must have the same number of items as key")
        else:
            astype = [astype] * len(key)

    if namespace is None:
        namespace = []
    elif isinstance(namespace, str) and namespace == "":
        namespace = []
    elif isinstance(namespace, str) or namespace == all:
        namespace = [namespace]
    elif namespace == [""]:
        namespace = []

    return (key, namespace, astype, key_arg_type)
