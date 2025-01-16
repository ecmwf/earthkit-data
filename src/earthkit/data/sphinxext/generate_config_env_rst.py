#!/usr/bin/env python3

# (C) Copyright 2020 ECMWF.
#
# This software is licensed under the terms of the Apache Licence Version 2.0
# which can be obtained at http://www.apache.org/licenses/LICENSE-2.0.
# In applying this licence, ECMWF does not waive the privileges and immunities
# granted to it by virtue of its status as an intergovernmental organisation
# nor does it submit to any jurisdiction.
#

import re

from earthkit.data.core.config import CONFIG_AND_HELP
from earthkit.data.core.config import env_var_name


def execute(*args):
    print()
    print(".. list-table::")
    print("   :header-rows: 1")
    print("   :widths: 40 60")
    print()
    print("   * - Config option name")
    print("     - Environment variable")
    print()
    for k, v in sorted(CONFIG_AND_HELP.items()):
        if len(args) and not any(re.match(arg, k) for arg in args):
            continue

        print("   * -  ", k.replace("-", "\u2011"))  # Non-breaking hyphen
        print("     -  ", f"{env_var_name(k)}")
    print()


if __name__ == "__main__":
    execute()
