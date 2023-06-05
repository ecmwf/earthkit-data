# (C) Copyright 2020 ECMWF.
#
# This software is licensed under the terms of the Apache Licence Version 2.0
# which can be obtained at http://www.apache.org/licenses/LICENSE-2.0.
# In applying this licence, ECMWF does not waive the privileges and immunities
# granted to it by virtue of its status as an intergovernmental organisation
# nor does it submit to any jurisdiction.
#


def check_or_download_data_file(filename):
    import os
    import urllib.request

    from earthkit.data.testing import earthkit_remote_test_data_file

    if not os.path.exists(filename):
        urllib.request.urlretrieve(
            earthkit_remote_test_data_file(os.path.join("examples", filename)), filename
        )
