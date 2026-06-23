# (C) Copyright 2021 ECMWF.
#
# This software is licensed under the terms of the Apache Licence Version 2.0
# which can be obtained at http://www.apache.org/licenses/LICENSE-2.0.
# In applying this licence, ECMWF does not waive the privileges and immunities
# granted to it by virtue of its status as an intergovernmental organisation
# nor does it submit to any jurisdiction.
#

import json
import os
import urllib.request

import yaml


def _write_earthkit_packages_js(app, ek_branch):
    """Fetch earthkit-packages.yml from remote and write a JS data file into the output _static dir.

    Falls back to the local copy if the remote fetch fails.
    """
    urls = (
        f"https://raw.githubusercontent.com/ecmwf/earthkit/refs/heads/{ek_branch}/docs/earthkit-packages.yml",
        "https://raw.githubusercontent.com/ecmwf/earthkit/refs/heads/main/docs/earthkit-packages.yml",
        "https://raw.githubusercontent.com/ecmwf/earthkit/refs/heads/develop/docs/earthkit-packages.yml",
    )

    for url in urls:
        try:
            with urllib.request.urlopen(url, timeout=10) as response:
                config = yaml.safe_load(response.read())
                break
        except Exception:
            continue
    else:
        raise RuntimeError("Failed to fetch earthkit-packages.yml from remote URLs.")

    packages = config.get("packages", [])
    static_dir = os.path.join(app.outdir, "_static")
    os.makedirs(static_dir, exist_ok=True)
    js_path = os.path.join(static_dir, "earthkit-packages.js")
    with open(js_path, "w", encoding="utf-8") as fh:
        fh.write(f"window.earthkitPackages = {json.dumps(packages)};\n")
