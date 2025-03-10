# earthkit-data

<img src="https://github.com/ecmwf/logos/raw/refs/heads/main/logos/earthkit/earthkit-data-light.svg" width="160">

<p align="center">
  <a href="https://github.com/ecmwf/codex/raw/refs/heads/main/ESEE">
    <img src="https://github.com/ecmwf/codex/raw/refs/heads/main/ESEE/foundation_badge.svg" alt="Static Badge">
  </a>
  <a href="https://github.com/ecmwf/codex/raw/refs/heads/main/Project%20Maturity">
    <img src="https://github.com/ecmwf/codex/raw/refs/heads/main/Project%20Maturity/incubating_badge.svg" alt="Static Badge">
  </a>

<a href="https://opensource.org/licenses/apache-2-0">
    <img src="https://img.shields.io/badge/License-Apache%202.0-blue.svg" alt="License: Apache 2.0">
  </a>

<a href="https://github.com/ecmwf/earthkit-data/releases">
    <img src="https://img.shields.io/github/v/release/ecmwf/earthkit-data?color=blue&label=Release&style=flat-square" alt="Latest Release">
  </a>
  <a href="https://earthkit-data.readthedocs.io/en/latest/?badge=latest">
    <img src="https://readthedocs.org/projects/earthkit-data/badge/?version=latest" alt="Documentation Status">
  </a>
</p>

<p align="center">
  <a href="#quick-start">Quick Start</a> *
  <a href="#installation">Installation</a> *
  <a href="https://earthkit-data.readthedocs.io/en/latest/">Documentation</a>
</p>

> \[!IMPORTANT\]
> This software is **Incubating** and subject to ECMWF's guidelines on [Software Maturity](https://github.com/ecmwf/codex/raw/refs/heads/main/Project%20Maturity).

A format-agnostic interface for geospatial data with a focus on meteorology and
climate science.

## Quick Start

```python
import earthkit.data as ekd

data = ekd.from_source("sample", "test.grib")
arr = data.to_numpy()
df = data.to_pandas()
dataset = data.to_xarray()
```

## Installation

Install from PyPI:

```
python -m pip install earthkit-data
```

More details, such as optional dependencies can be found at https://earthkit-data.readthedocs.io/en/latest/install.html.

Alternatively, install via `conda` with:

```
$ conda install earthkit-data -c conda-forge
```

## License

```
Copyright 2022, European Centre for Medium Range Weather Forecasts.

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

    http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.

In applying this licence, ECMWF does not waive the privileges and immunities
granted to it by virtue of its status as an intergovernmental organisation
nor does it submit to any jurisdiction.
```
