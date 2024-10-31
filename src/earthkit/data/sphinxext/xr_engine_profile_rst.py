#!/usr/bin/env python3

# (C) Copyright 2020 ECMWF.
#
# This software is licensed under the terms of the Apache Licence Version 2.0
# which can be obtained at http://www.apache.org/licenses/LICENSE-2.0.
# In applying this licence, ECMWF does not waive the privileges and immunities
# granted to it by virtue of its status as an intergovernmental organisation
# nor does it submit to any jurisdiction.
#

from pprint import pformat

import yaml

from earthkit.data.utils.xarray.profile import Profile


def format_table_cell(v, indent=13):
    def _indent(text, indent_first=False):
        lines = text.split("\n")
        r = ""
        if len(lines) == 1:
            if indent_first:
                r += " " * indent
            return r + lines[0]
        elif len(lines) > 1:
            r = ""
            for line in lines:
                if line:
                    if r or indent_first:
                        r += " " * indent
                    r += "| " + line + "\n"
            if r.endswith("\n"):
                r = r[:-1]
            return r
        return v

    if isinstance(v, list):
        return str(v)
    return _indent(pformat(v, sort_dicts=False, indent=1))


def make_table(d):
    t = """
   .. tab:: Table

      .. list-table::
         :header-rows: 1
         :widths: 20 80

         * - Name
           - Value"""

    for k, v in d.items():
        if k != "coord_attrs":
            t += f"""
         * - {k}
           - {format_table_cell(v, indent=13)}"""

    if "coord_attrs" in d:
        t += """

      Please note that the following options cannot be specified as a kwarg to :func:`to_xarray`.

      .. list-table::
         :header-rows: 1
         :widths: 20 80

         * - Name
           - Value"""

        for k in ["coord_attrs"]:
            t += f"""
         * - {k}
           - {format_table_cell(d[k], indent=13)}"""

    return t


def make_dict(d):
    d = pformat(d, sort_dicts=False, indent=1)
    t = """

   .. tab:: Dictionary

      .. code-block:: python

    """
    for line in d.split("\n"):
        t += f"         {line}\n"

    return t


def make_yaml(d):
    d = yaml.dump(d, default_flow_style=False, sort_keys=False)
    t = """

   .. tab:: YAML

      .. code-block:: yaml

    """
    for line in d.split("\n"):
        t += f"         {line}\n"

    return t


def execute(*args):
    name = args[0]
    if name == "__py_None__":
        name = None
    d = Profile.to_docs(name)

    t = f"""
.. tabs::

{make_table(d)}

{make_dict(d)}

{make_yaml(d)}

"""
    print(t)


if __name__ == "__main__":
    execute()
