# (C) Copyright 2020 ECMWF.
#
# This software is licensed under the terms of the Apache Licence Version 2.0
# which can be obtained at http://www.apache.org/licenses/LICENSE-2.0.
# In applying this licence, ECMWF does not waive the privileges and immunities
# granted to it by virtue of its status as an intergovernmental organisation
# nor does it submit to any jurisdiction.
#


def download_example_file(file_names, remote_dir="examples", force=False):
    import os
    import urllib.request

    from earthkit.data.testing import earthkit_remote_test_data_file

    if isinstance(file_names, str):
        file_names = [file_names]

    for f_name in file_names:
        if force or not os.path.exists(f_name):
            urllib.request.urlretrieve(
                earthkit_remote_test_data_file(os.path.join(remote_dir, f_name)), f_name
            )


def remote_example_file(file_name, remote_dir="examples"):
    import os

    from earthkit.data.testing import earthkit_remote_test_data_file

    return earthkit_remote_test_data_file(os.path.join(remote_dir, file_name))
