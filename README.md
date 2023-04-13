# earthkit-data

A format-agnostic interface for geospatial data with a focus on meteorology and
climate science.

**DISCLAIMER**
This project is **BETA** and will be **Experimental** for the foreseeable future.
Interfaces and functionality are likely to change, and the project itself may be scrapped.
**DO NOT** use this software in any project/software that is operational.

**earthkit-data** makes it simple to read, inspect and slice data from a wide range of
geospatial input types (GRIB, netCDF, zarr and more) and transform them into
familiar scientific Python objects (including numpy arrays, pandas dataframes,
xarray datasets).

```
data = earthkit.data.from_source("my-data.nc")
arr = data.to_numpy()
df = data.to_pandas()
dataset = data.to_xarray()
```

**earthkit-data** provides additional convenient methods for quickly inspecting certain
features of your input data, such as data dimensionality, axes, coordinate
reference systems and bounding boxes.

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
```
