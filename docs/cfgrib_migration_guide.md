# Migration Guide: cfgrib to earthkit-data 1.0

This guide maps every cfgrib feature to its earthkit-data 1.0 / xr_engine equivalent.
All examples are self-contained and testable.

______________________________________________________________________

## Quick Start

```python
# cfgrib (before)
import xarray as xr
ds = xr.open_dataset("era5.grib", engine="cfgrib")

# earthkit-data 1.0 (after) — option A: via xarray
ds = xr.open_dataset("era5.grib", engine="earthkit", profile="earthkit")

# earthkit-data 1.0 (after) — option B: via earthkit API (recommended)
import earthkit.data as ekd
fl = ekd.from_source("file", "era5.grib").to_fieldlist()
ds = fl.to_xarray(profile="earthkit")
```

______________________________________________________________________

## Table of Contents

1. [Opening Files](#1-opening-files)
1. [filter_by_keys → .sel()](#2-filter_by_keys--sel)
1. [read_keys → extra_dims / attrs](#3-read_keys--extra_dims--attrs)
1. [encode_cf → profile + decode options](#4-encode_cf--profile--decode-options)
1. [squeeze](#5-squeeze)
1. [time_dims](#6-time_dims)
1. [errors / allow_holes](#7-errors--allow_holes)
1. [indexpath (.idx files)](#8-indexpath-idx-files)
1. [open_datasets → split_dims](#9-open_datasets--split_dims)
1. [Level / Vertical Handling](#10-level--vertical-handling)
1. [Coordinate Encoding](#11-coordinate-encoding)
1. [CF Attributes](#12-cf-attributes)
1. [cf2cdm → profiles + rename_dims](#13-cf2cdm--profiles--rename_dims)
1. [extra_coords → aux_coords](#14-extra_coords--aux_coords)
1. [coords_as_attributes → dims_as_attrs](#15-coords_as_attributes--dims_as_attrs)
1. [Lazy Loading / Dask](#16-lazy-loading--dask)
1. [values_dtype → dtype](#17-values_dtype--dtype)
1. [Ensemble Members](#18-ensemble-members)
1. [Remapping (new)](#19-remapping-new-in-earthkit-data)
1. [CLI Tools](#20-cli-tools)
1. [Write Support](#21-write-support)
1. [Low-level API](#22-low-level-api)

______________________________________________________________________

## 1. Opening Files

### cfgrib

```python
import xarray as xr
import cfgrib

# Via xarray engine
ds = xr.open_dataset("era5.grib", engine="cfgrib")

# Via cfgrib helper
ds = cfgrib.open_dataset("era5.grib")

# Multiple datasets from heterogeneous file
datasets = cfgrib.open_datasets("era5.grib")

# Low-level Dataset object
ds = cfgrib.open_file("era5.grib")
```

### earthkit-data 1.0

```python
import xarray as xr
import earthkit.data as ekd

# Via xarray engine
ds = xr.open_dataset("era5.grib", engine="earthkit", profile="earthkit")

# Via earthkit API (recommended — more control)
fl = ekd.from_source("file", "era5.grib").to_fieldlist()
ds = fl.to_xarray(profile="earthkit")

# Multiple datasets (see §9 for full split_dims usage)
ds_list, splits = fl.to_xarray(split_dims=["vertical.level_type"])

# Pass a FieldList directly to xarray
ds = xr.open_dataset(fl, engine="earthkit", profile="earthkit")
```

### Testable example

```python
from earthkit.data import from_source

# Synthetic data — no file needed
proto = {
    "geography": {"latitudes": [10.0, 0.0, -10.0], "longitudes": [20.0, 40.0]},
    "values": [1, 2, 3, 4, 5, 6],
}
d = [
    {"parameter": {"variable": "t"}, "vertical": {"level": 500},
     "time": {"base_datetime": "2024-06-03T00:00:00", "step": 0}, **proto},
    {"parameter": {"variable": "t"}, "vertical": {"level": 500},
     "time": {"base_datetime": "2024-06-03T00:00:00", "step": 6}, **proto},
    {"parameter": {"variable": "u"}, "vertical": {"level": 500},
     "time": {"base_datetime": "2024-06-03T00:00:00", "step": 0}, **proto},
    {"parameter": {"variable": "u"}, "vertical": {"level": 500},
     "time": {"base_datetime": "2024-06-03T00:00:00", "step": 6}, **proto},
]
fl = from_source("list-of-dicts", d).to_fieldlist()
ds = fl.to_xarray(profile="earthkit")

assert set(ds.data_vars) == {"t", "u"}
assert "step" in ds.sizes
```

______________________________________________________________________

## 2. filter_by_keys → .sel()

### cfgrib

```python
ds = xr.open_dataset("era5.grib", engine="cfgrib",
    backend_kwargs={"filter_by_keys": {"typeOfLevel": "isobaricInhPa", "level": 500}})

ds = xr.open_dataset("era5.grib", engine="cfgrib",
    backend_kwargs={"filter_by_keys": {"shortName": ["t", "u"]}})
```

### earthkit-data 1.0

```python
fl = ekd.from_source("file", "era5.grib").to_fieldlist()

# Filter BEFORE conversion — faster, less memory
fl_filtered = fl.sel(**{"vertical.level": 500})
ds = fl_filtered.to_xarray(profile="earthkit")

# Filter by multiple keys
fl_filtered = fl.sel(**{"parameter.variable": ["t", "u"], "vertical.level": 500})
ds = fl_filtered.to_xarray(profile="earthkit")
```

### Testable example

```python
from earthkit.data import from_source
from earthkit.data.utils.testing import earthkit_test_data_file

# t_pl.grib has temperature on 6 pressure levels (300-1000 hPa)
fl = from_source("file", earthkit_test_data_file("t_pl.grib")).to_fieldlist()
assert len(fl) == 6

# Filter to 500 hPa only
fl_500 = fl.sel(**{"vertical.level": 500})
assert len(fl_500) == 1

ds = fl_500.to_xarray(profile="earthkit")
assert "level" not in ds.sizes  # squeezed (single value)
```

______________________________________________________________________

## 3. read_keys → extra_dims / attrs

### cfgrib

```python
# Promote GRIB key to variable attribute
ds = xr.open_dataset("era5.grib", engine="cfgrib",
    backend_kwargs={"read_keys": ["experimentVersionNumber"]})
print(ds.t.attrs["GRIB_experimentVersionNumber"])  # '0001'
```

### earthkit-data 1.0

```python
fl = ekd.from_source("file", "era5.grib").to_fieldlist()

# Option A: Promote to a DIMENSION (more powerful than cfgrib)
ds = fl.to_xarray(
    profile="earthkit",
    extra_dims=[{"experiment": "metadata.expver"}],
    squeeze=False,
)
# "experiment" is now a dimension coordinate

# Option B: Promote to an ATTRIBUTE (like cfgrib read_keys)
ds = fl.to_xarray(
    profile="earthkit",
    variable_attrs=["metadata.expver"],
    add_earthkit_attrs=False,
)
# ds["t"].attrs["expver"] == "0001"

# Option C: Use mars profile (includes many metadata attrs by default)
ds = fl.to_xarray(profile="mars")
# ds.attrs includes class, stream, expver, levtype, type, etc.
```

### Testable example

```python
from earthkit.data import from_source
from earthkit.data.utils.testing import earthkit_test_data_file

fl = from_source("file", earthkit_test_data_file("t_pl.grib")).to_fieldlist()

# Promote expver to dimension
ds = fl.to_xarray(
    profile="earthkit",
    extra_dims=[{"experiment": "metadata.expver"}],
    squeeze=False,
)
assert "experiment" in ds.sizes

# Or keep as attribute via mars profile
ds = fl.to_xarray(profile="mars")
assert "expver" in ds.attrs
```

______________________________________________________________________

## 4. encode_cf → profile + decode options

### cfgrib

```python
# Control which aspects get CF-encoded
ds = xr.open_dataset("era5.grib", engine="cfgrib",
    backend_kwargs={"encode_cf": ("parameter", "time", "geography", "vertical")})

# Disable all CF encoding
ds = xr.open_dataset("era5.grib", engine="cfgrib",
    backend_kwargs={"encode_cf": ()})
```

### earthkit-data 1.0

| cfgrib `encode_cf` | earthkit-data equivalent |
|---------------------|--------------------------|
| `"parameter"` | `variable_attrs=["parameter.standard_name", "parameter.long_name", "parameter.units"]` |
| `"time"` | `decode_times=True`, `decode_timedelta=True` |
| `"geography"` | `add_geo_coords=True` (default) |
| `"vertical"` | `level_dim_mode="level_per_type"` |
| Disable all | `profile="grib"`, `decode_times=False`, `decode_timedelta=False`, `add_geo_coords=False` |

### Testable example

```python
from earthkit.data import from_source
from earthkit.data.utils.testing import earthkit_test_data_file

fl = from_source("file", earthkit_test_data_file("t_pl.grib")).to_fieldlist()

# Full CF encoding (default with earthkit profile)
ds = fl.to_xarray(
    profile="earthkit",
    variable_attrs=["parameter.standard_name", "parameter.long_name", "parameter.units"],
    add_earthkit_attrs=False,
)
assert ds["t"].attrs["standard_name"] == "air_temperature"
assert ds["t"].attrs["units"] == "kelvin"

# Minimal encoding (raw GRIB-like)
ds = fl.to_xarray(profile="grib")
assert "level" in ds.sizes
```

______________________________________________________________________

## 5. squeeze

### cfgrib

```python
ds = xr.open_dataset("era5.grib", engine="cfgrib",
    backend_kwargs={"squeeze": True})   # default: remove size-1 dims

ds = xr.open_dataset("era5.grib", engine="cfgrib",
    backend_kwargs={"squeeze": False})  # keep all dims
```

### earthkit-data 1.0

```python
# Same behavior
ds = fl.to_xarray(profile="earthkit", squeeze=True)   # default
ds = fl.to_xarray(profile="earthkit", squeeze=False)  # keep all

# NEW: selective — keep specific size-1 dims
ds = fl.to_xarray(profile="earthkit", squeeze=True, ensure_dims=["level_type"])

# NEW: convert size-1 dim to attribute instead of dropping
ds = fl.to_xarray(profile="earthkit", dims_as_attrs=["level_type"])
```

### Testable example

```python
from earthkit.data import from_source
from earthkit.data.utils.testing import earthkit_test_data_file

fl = from_source("file", earthkit_test_data_file("t_pl.grib")).to_fieldlist()

# Default: squeeze=True removes level_type (size 1)
ds = fl.to_xarray(profile="earthkit", squeeze=True)
assert "level_type" not in ds.sizes

# squeeze=False keeps all
ds = fl.to_xarray(profile="earthkit", squeeze=False)
assert "level_type" in ds.sizes
assert ds.sizes["level_type"] == 1

# dims_as_attrs: demote to variable attribute
ds = fl.to_xarray(profile="earthkit", dims_as_attrs=["level_type"])
assert "level_type" not in ds.sizes
assert "level_type" in ds["t"].attrs
```

______________________________________________________________________

## 6. time_dims

### cfgrib

```python
# Default: ("time", "step")
ds = xr.open_dataset("era5.grib", engine="cfgrib",
    backend_kwargs={"time_dims": ("time", "step")})

# Use valid_time
ds = xr.open_dataset("era5.grib", engine="cfgrib",
    backend_kwargs={"time_dims": ("time", "valid_time")})
```

### earthkit-data 1.0

```python
# Default: forecast_reference_time + step
ds = fl.to_xarray(profile="earthkit", time_dims=["forecast_reference_time", "step"])

# Single valid_time dimension
ds = fl.to_xarray(profile="earthkit", time_dims=["valid_time"])

# Three raw dimensions: date, time-of-day, step
ds = fl.to_xarray(profile="earthkit", time_dims=["date", "time", "step"])
```

### Testable example

```python
import numpy as np
from earthkit.data import from_source

proto = {
    "geography": {"latitudes": [10.0, 0.0], "longitudes": [20.0, 40.0]},
    "values": [1, 2, 3, 4],
}
d = [
    {"parameter": {"variable": "t"}, "vertical": {"level": 500},
     "time": {"base_datetime": "2024-06-03T00:00:00", "step": 0}, **proto},
    {"parameter": {"variable": "t"}, "vertical": {"level": 500},
     "time": {"base_datetime": "2024-06-03T00:00:00", "step": 6}, **proto},
    {"parameter": {"variable": "t"}, "vertical": {"level": 500},
     "time": {"base_datetime": "2024-06-04T00:00:00", "step": 0}, **proto},
    {"parameter": {"variable": "t"}, "vertical": {"level": 500},
     "time": {"base_datetime": "2024-06-04T00:00:00", "step": 6}, **proto},
]
fl = from_source("list-of-dicts", d).to_fieldlist()

# forecast_reference_time + step (cfgrib default equivalent)
ds = fl.to_xarray(profile="earthkit", time_dims=["forecast_reference_time", "step"])
assert "forecast_reference_time" in ds.sizes
assert "step" in ds.sizes
assert ds.sizes["forecast_reference_time"] == 2
assert ds.sizes["step"] == 2
assert ds.coords["forecast_reference_time"].dtype == np.dtype("datetime64[ns]")
assert ds.coords["step"].dtype == np.dtype("timedelta64[ns]")

# valid_time (combined)
ds = fl.to_xarray(profile="earthkit", time_dims=["valid_time"])
assert "valid_time" in ds.sizes
assert ds.sizes["valid_time"] == 4
assert "forecast_reference_time" not in ds.sizes
assert "step" not in ds.sizes
```

______________________________________________________________________

## 7. errors / allow_holes

### cfgrib

```python
# Default: warns on inconsistencies
ds = xr.open_dataset("era5.grib", engine="cfgrib",
    backend_kwargs={"errors": "warn"})    # default

ds = xr.open_dataset("era5.grib", engine="cfgrib",
    backend_kwargs={"errors": "raise"})   # strict

ds = xr.open_dataset("era5.grib", engine="cfgrib",
    backend_kwargs={"errors": "ignore"})  # silent
```

### earthkit-data 1.0

```python
# Default is STRICTER than cfgrib (raises on inconsistency)
ds = fl.to_xarray(profile="earthkit", errors="raise")      # default

# cfgrib-like lenient behavior
ds = fl.to_xarray(profile="earthkit", errors="warn", allow_holes=True)

# allow_holes fills missing data with NaN
ds = fl.to_xarray(profile="earthkit", allow_holes=True)
```

### Testable example

```python
import numpy as np
from earthkit.data import from_source

# Create data with a "hole" (missing combination)
proto = {
    "geography": {"latitudes": [10.0, 0.0], "longitudes": [20.0, 40.0]},
    "values": [1, 2, 3, 4],
}
d = [
    {"parameter": {"variable": "t"}, "vertical": {"level": 500},
     "time": {"base_datetime": "2024-06-03T00:00:00", "step": 0}, **proto},
    {"parameter": {"variable": "t"}, "vertical": {"level": 500},
     "time": {"base_datetime": "2024-06-03T00:00:00", "step": 6}, **proto},
    {"parameter": {"variable": "t"}, "vertical": {"level": 850},
     "time": {"base_datetime": "2024-06-03T00:00:00", "step": 0}, **proto},
    # MISSING: t, 850 hPa, step=6
]
fl = from_source("list-of-dicts", d).to_fieldlist()

# allow_holes=True fills gap with NaN
ds = fl.to_xarray(profile="earthkit", allow_holes=True)
assert ds.sizes["step"] == 2
assert ds.sizes["level"] == 2
assert np.isnan(ds["t"].values).any()  # The hole is filled with NaN
```

______________________________________________________________________

## 8. indexpath (.idx files)

### cfgrib

```python
# Default: writes .idx sidecar file for faster re-opening
ds = xr.open_dataset("era5.grib", engine="cfgrib",
    backend_kwargs={"indexpath": "{path}.{short_hash}.idx"})

# Disable index file creation
ds = xr.open_dataset("era5.grib", engine="cfgrib",
    backend_kwargs={"indexpath": ""})
```

### earthkit-data 1.0

**No equivalent.** earthkit-data does not create `.idx` sidecar files. Indexing is handled in-memory. No configuration needed.

______________________________________________________________________

## 9. open_datasets → split_dims

### cfgrib

```python
import cfgrib

# Automatically splits heterogeneous GRIB into valid hypercubes
datasets = cfgrib.open_datasets("heterogeneous.grib")
# Returns a list of xarray.Dataset — one per compatible group
```

### earthkit-data 1.0

```python
fl = ekd.from_source("file", "heterogeneous.grib").to_fieldlist()

# Explicitly split by level type (most common need)
ds_list, splits = fl.to_xarray(
    profile="earthkit",
    split_dims=["vertical.level_type"],
)

# Split by multiple keys (stream, dataType, grid size...)
ds_list, splits = fl.to_xarray(
    profile="earthkit",
    split_dims=["metadata.stream", "metadata.dataType"],
)
```

**Key difference:** cfgrib auto-detects what to split on (opaque recursive algorithm). earthkit-data requires you to explicitly name split keys (predictable, transparent).

### Testable example

```python
from earthkit.data import from_source
from earthkit.data.utils.testing import earthkit_test_data_file

fl = from_source("file", earthkit_test_data_file("t_pl.grib")).to_fieldlist()

# Split by level value — creates one dataset per level
ds_list, splits = fl.to_xarray(
    profile="earthkit",
    split_dims=["vertical.level"],
)
assert len(ds_list) == 6  # 6 pressure levels → 6 datasets
assert all("vertical.level" in s for s in splits)
```

______________________________________________________________________

## 10. Level / Vertical Handling

### cfgrib

```python
# cfgrib names level dimension by typeOfLevel (e.g., "isobaricInhPa")
ds = xr.open_dataset("era5.grib", engine="cfgrib")
# ds.dims includes "isobaricInhPa" (for pressure levels)
# ds.coords["isobaricInhPa"] = [1000, 850, 500, ...]
```

### earthkit-data 1.0

```python
# Default: generic "level" dimension name
ds = fl.to_xarray(profile="earthkit", level_dim_mode="level")
# ds.dims: {"level": 6, ...}

# Name dimension by level type (closest to cfgrib behavior)
ds = fl.to_xarray(profile="earthkit", level_dim_mode="level_per_type")
# ds.dims: {"pressure": 6, ...} for pressure levels

# Combined level + type label
ds = fl.to_xarray(profile="earthkit", level_dim_mode="level_and_type")
# ds.dims: {"level_and_type": 6, ...}
# coordinates are strings like "500pl", "850pl"
```

### Testable example

```python
from earthkit.data import from_source
from earthkit.data.utils.testing import earthkit_test_data_file

fl = from_source("file", earthkit_test_data_file("t_pl.grib")).to_fieldlist()

# Default: "level" dimension
ds = fl.to_xarray(profile="earthkit", level_dim_mode="level")
assert "level" in ds.sizes
assert ds.sizes["level"] == 6

# Keep level_type as a dimension (not squeezed)
ds = fl.to_xarray(profile="earthkit", level_dim_mode="level", squeeze=False)
assert "level_type" in ds.sizes
```

______________________________________________________________________

## 11. Coordinate Encoding

### cfgrib

```python
# time → datetime64[ns], step → timedelta64[ns], valid_time → computed
# level → float (named by typeOfLevel)
# latitude/longitude → float with CF attributes
```

### earthkit-data 1.0

Same encoding with `decode_times=True` (default):

```python
# Datetime coordinates
ds = fl.to_xarray(profile="earthkit", time_dims=["forecast_reference_time", "step"])
# forecast_reference_time: datetime64[ns]
# step: timedelta64[ns]

# Raw integer coordinates (disable decoding)
ds = fl.to_xarray(
    profile="earthkit",
    time_dims=["date", "time", "step"],
    decode_times=False,
    decode_timedelta=False,
)
# date: int (20240603), time: int (0, 1200), step: int (hours)
```

### Testable example

```python
import numpy as np
from earthkit.data import from_source

proto = {
    "geography": {"latitudes": [10.0, 0.0], "longitudes": [20.0, 40.0]},
    "values": [1, 2, 3, 4],
}
d = [
    {"parameter": {"variable": "t"}, "vertical": {"level": 500},
     "time": {"base_datetime": "2024-06-03T00:00:00", "step": 0}, **proto},
    {"parameter": {"variable": "t"}, "vertical": {"level": 500},
     "time": {"base_datetime": "2024-06-03T00:00:00", "step": 6}, **proto},
    {"parameter": {"variable": "t"}, "vertical": {"level": 500},
     "time": {"base_datetime": "2024-06-04T00:00:00", "step": 0}, **proto},
    {"parameter": {"variable": "t"}, "vertical": {"level": 500},
     "time": {"base_datetime": "2024-06-04T00:00:00", "step": 6}, **proto},
]
fl = from_source("list-of-dicts", d).to_fieldlist()

# Decoded (default)
ds = fl.to_xarray(profile="earthkit", time_dims=["forecast_reference_time", "step"])
assert ds.coords["forecast_reference_time"].dtype == np.dtype("datetime64[ns]")
assert ds.coords["step"].dtype == np.dtype("timedelta64[ns]")

# Geographic coordinates have CF attributes
assert ds.coords["latitude"].attrs["units"] == "degrees_north"
assert ds.coords["longitude"].attrs["units"] == "degrees_east"
```

______________________________________________________________________

## 12. CF Attributes

### cfgrib

```python
# Attributes prefixed with GRIB_: GRIB_paramId, GRIB_shortName, GRIB_units, ...
# CF attrs: standard_name, long_name, units
# Global attrs: GRIB_edition, GRIB_centre, Conventions: CF-1.7, institution
ds = xr.open_dataset("era5.grib", engine="cfgrib")
print(ds.t.attrs["GRIB_shortName"])  # "t"
print(ds.attrs["Conventions"])       # "CF-1.7"
```

### earthkit-data 1.0

```python
# earthkit profile: clean CF attributes
ds = fl.to_xarray(
    profile="earthkit",
    variable_attrs=["parameter.standard_name", "parameter.long_name", "parameter.units"],
    add_earthkit_attrs=False,
)
# ds["t"].attrs: {"standard_name": "air_temperature", "long_name": "Temperature", "units": "kelvin"}
# ds.attrs: {"Conventions": "CF-1.8", "institution": "ECMWF"}

# mars profile: comprehensive GRIB metadata (like cfgrib's GRIB_ attrs)
ds = fl.to_xarray(profile="mars")
# ds.attrs includes: class, stream, expver, levtype, type, ...
```

### Testable example

```python
from earthkit.data import from_source
from earthkit.data.utils.testing import earthkit_test_data_file

fl = from_source("file", earthkit_test_data_file("t_pl.grib")).to_fieldlist()

# CF variable attributes
ds = fl.to_xarray(
    profile="earthkit",
    variable_attrs=["parameter.standard_name", "parameter.long_name", "parameter.units"],
    add_earthkit_attrs=False,
)
assert ds["t"].attrs["standard_name"] == "air_temperature"
assert ds["t"].attrs["long_name"] == "Temperature"
assert ds["t"].attrs["units"] == "kelvin"
assert ds.attrs["Conventions"] == "CF-1.8"

# mars profile for GRIB-level metadata
ds = fl.to_xarray(profile="mars")
assert "expver" in ds.attrs
assert "class" in ds.attrs
```

______________________________________________________________________

## 13. cf2cdm → profiles + rename_dims

### cfgrib

```python
import cf2cdm

ds = xr.open_dataset("era5.grib", engine="cfgrib")

# Translate to ECMWF naming (isobaricInhPa → level)
ds_ecmwf = cf2cdm.translate_coords(ds, cf2cdm.ECMWF)

# Translate to CDS naming (time → forecast_reference_time, lat/lon, plev)
ds_cds = cf2cdm.translate_coords(ds, cf2cdm.CDS)
```

### earthkit-data 1.0

**No separate translation step needed** — use profiles or `rename_dims`:

```python
fl = ekd.from_source("file", "era5.grib").to_fieldlist()

# ECMWF-like: generic "level" name (already the default!)
ds = fl.to_xarray(profile="earthkit", level_dim_mode="level")
# Dimension is already called "level"

# CDS-like naming
ds = fl.to_xarray(
    profile="earthkit",
    time_dims=["forecast_reference_time", "step"],
    rename_dims={
        "forecast_reference_time": "forecast_reference_time",
        "level": "plev",
        "latitude": "lat",
        "longitude": "lon",
    },
)
```

### Testable example

```python
from earthkit.data import from_source
from earthkit.data.utils.testing import earthkit_test_data_file

fl = from_source("file", earthkit_test_data_file("t_pl.grib")).to_fieldlist()

# Rename dimensions (replaces cf2cdm.translate_coords)
ds = fl.to_xarray(
    profile="earthkit",
    rename_dims={"level": "pressure_level"},
)
assert "pressure_level" in ds.sizes
assert "level" not in ds.sizes
```

______________________________________________________________________

## 14. extra_coords → aux_coords

### cfgrib

```python
# extra_coords creates a non-dimension coordinate indexed by an existing dimension.
# E.g., add "valid_time" as a coordinate indexed along the "step" dimension:
ds = xr.open_dataset("era5.grib", engine="cfgrib",
    backend_kwargs={"extra_coords": {"valid_time": "step"}})
# ds.coords["valid_time"] exists with dims=("step",) — NOT a new dimension
```

### earthkit-data 1.0

```python
# aux_coords is the direct equivalent: creates a non-dimension coordinate
# indexed by one or more existing dimensions.
# Syntax: {"coord_name": ("metadata_key", ["dim1", "dim2", ...])}
ds = fl.to_xarray(
    profile="earthkit",
    time_dims=["forecast_reference_time", "step"],
    aux_coords={"valid_time": ("time.valid_datetime", ["forecast_reference_time", "step"])},
)
# ds.coords["valid_time"] exists with dims=("forecast_reference_time", "step")

# Single-dimension example (like cfgrib's {"valid_time": "step"}):
ds = fl.to_xarray(
    profile="earthkit",
    time_dims=["step"],
    aux_coords={"valid_time": ("time.valid_datetime", ["step"])},
)
# ds.coords["valid_time"] has dims=("step",)
```

> **Note:** Don't confuse `aux_coords` with `extra_dims`. `extra_dims` promotes a metadata key
> to a *new dimension* of the dataset (like cfgrib's `read_keys` but stronger).
> `aux_coords` adds a *non-dimension coordinate* indexed along existing dimensions
> (the direct equivalent of cfgrib's `extra_coords`).

### Testable example

```python
import numpy as np
from earthkit.data import from_source

proto = {
    "geography": {"latitudes": [10.0, 0.0], "longitudes": [20.0, 40.0]},
    "values": [1, 2, 3, 4],
}
d = [
    {"parameter": {"variable": "t"}, "vertical": {"level": 500},
     "time": {"base_datetime": "2024-06-03T00:00:00", "step": 0}, **proto},
    {"parameter": {"variable": "t"}, "vertical": {"level": 500},
     "time": {"base_datetime": "2024-06-03T00:00:00", "step": 6}, **proto},
    {"parameter": {"variable": "t"}, "vertical": {"level": 500},
     "time": {"base_datetime": "2024-06-04T00:00:00", "step": 0}, **proto},
    {"parameter": {"variable": "t"}, "vertical": {"level": 500},
     "time": {"base_datetime": "2024-06-04T00:00:00", "step": 6}, **proto},
]
fl = from_source("list-of-dicts", d).to_fieldlist()

# aux_coords: valid_time as non-dimension coordinate indexed by (forecast_reference_time, step)
ds = fl.to_xarray(
    profile="earthkit",
    time_dims=["forecast_reference_time", "step"],
    aux_coords={"valid_time": ("time.valid_datetime", ["forecast_reference_time", "step"])},
)
assert "valid_time" in ds.coords
assert "valid_time" not in ds.sizes  # NOT a dimension — just a coordinate
assert ds.coords["valid_time"].dims == ("forecast_reference_time", "step")
assert ds.coords["valid_time"].dtype == np.dtype("datetime64[ns]")
```

______________________________________________________________________

## 15. coords_as_attributes → dims_as_attrs

### cfgrib

```python
# Force single-valued coords to be attributes instead of scalar coords
ds = xr.open_dataset("era5.grib", engine="cfgrib",
    backend_kwargs={"coords_as_attributes": {"step": "step"}})
```

### earthkit-data 1.0

```python
# Convert single-valued dimension to variable attribute
ds = fl.to_xarray(profile="earthkit", dims_as_attrs=["level_type"])
# level_type appears in ds["t"].attrs, not as a dimension
```

### Testable example

```python
from earthkit.data import from_source
from earthkit.data.utils.testing import earthkit_test_data_file

fl = from_source("file", earthkit_test_data_file("t_pl.grib")).to_fieldlist()

# level_type (always "pressure" for this file) → attribute
ds = fl.to_xarray(profile="earthkit", dims_as_attrs=["level_type"])
assert "level_type" not in ds.sizes
assert ds["t"].attrs["level_type"] == "pressure"
```

______________________________________________________________________

## 16. Lazy Loading / Dask

### cfgrib

```python
# cfgrib always uses lazy loading via OnDiskArray
ds = xr.open_dataset("era5.grib", engine="cfgrib")
# Data loaded on access via LazilyIndexedArray
```

### earthkit-data 1.0

```python
# Lazy loading (default) — similar to cfgrib
ds = fl.to_xarray(profile="earthkit", lazy_load=True)

# Eager loading (all in memory) — cfgrib has no equivalent
ds = fl.to_xarray(profile="earthkit", lazy_load=False)

# Eager + release source memory (low peak memory)
ds = fl.to_xarray(profile="earthkit", lazy_load=False, release_source=True)
```

### Testable example

```python
import numpy as np
from earthkit.data import from_source

proto = {
    "geography": {"latitudes": [10.0, 0.0], "longitudes": [20.0, 40.0]},
    "values": [1, 2, 3, 4],
}
d = [
    {"parameter": {"variable": "t"}, "vertical": {"level": 500},
     "time": {"base_datetime": "2024-06-03T00:00:00", "step": 0}, **proto},
]
fl = from_source("list-of-dicts", d).to_fieldlist()

# Eager: data in memory as numpy
ds = fl.to_xarray(profile="earthkit", lazy_load=False)
assert isinstance(ds["t"].values, np.ndarray)
```

______________________________________________________________________

## 17. values_dtype → dtype

### cfgrib

```python
import numpy as np

# Default: float32
ds = xr.open_dataset("era5.grib", engine="cfgrib",
    backend_kwargs={"values_dtype": np.float64})
```

### earthkit-data 1.0

```python
# Default: float64 (higher precision than cfgrib!)
ds = fl.to_xarray(profile="earthkit", dtype="float64")

# Match cfgrib default precision
ds = fl.to_xarray(profile="earthkit", dtype="float32")
```

### Testable example

```python
import numpy as np
from earthkit.data import from_source
from earthkit.data.utils.testing import earthkit_test_data_file

fl = from_source("file", earthkit_test_data_file("t_pl.grib")).to_fieldlist()

# float32 (cfgrib default)
ds = fl.to_xarray(profile="earthkit", dtype="float32", lazy_load=False)
assert ds["t"].dtype == np.float32

# float64 (earthkit-data default)
ds = fl.to_xarray(profile="earthkit", dtype="float64", lazy_load=False)
assert ds["t"].dtype == np.float64
```

______________________________________________________________________

## 18. Ensemble Members

### cfgrib

```python
# cfgrib uses "number" dimension for ensemble members
ds = xr.open_dataset("era5-levels-members.grib", engine="cfgrib")
# ds.dims: {"number": 10, "time": 4, "isobaricInhPa": 2, ...}
```

### earthkit-data 1.0

```python
# earthkit-data uses "member" dimension
ds = fl.to_xarray(profile="earthkit")
# ds.dims: {"member": 10, ...}

# Use raw GRIB key for dimension name
ds = fl.to_xarray(
    profile="earthkit",
    dim_roles={"member": "metadata.perturbationNumber"},
    dim_name_from_role_name=False,
)
# ds.dims: {"perturbationNumber": 10, ...}
```

### Testable example

```python
from earthkit.data import from_source
from earthkit.data.utils.testing import earthkit_test_data_file

# ens_50.grib has 51 ensemble members (0=control + 50 perturbed)
fl = from_source("file", earthkit_test_data_file("ens_50.grib")).to_fieldlist()

ds = fl.to_xarray(profile="earthkit")
assert "member" in ds.sizes
assert ds.sizes["member"] == 51
```

______________________________________________________________________

## 19. Remapping (new in earthkit-data)

**No cfgrib equivalent.** Remapping creates synthetic metadata keys from field metadata.

```python
fl = ekd.from_source("file", "era5.grib").to_fieldlist()

# Create composite variable names: "t_500", "u_850", etc.
ds = fl.to_xarray(
    profile="earthkit",
    remapping={"param_level": "{parameter.variable}_{vertical.level}"},
    variable_key="param_level",
)
# ds.data_vars: ["t_500", "t_850", "u_500", "u_850", ...]
```

### Testable example

```python
from earthkit.data import from_source
from earthkit.data.utils.testing import earthkit_test_data_file

fl = from_source("file", earthkit_test_data_file("t_pl.grib")).to_fieldlist()

# Remap: create variable names as "t_<level>"
ds = fl.to_xarray(
    profile="earthkit",
    remapping={"param_level": "{parameter.variable}_{vertical.level}"},
    variable_key="param_level",
)
assert "t_500" in ds.data_vars
assert "t_850" in ds.data_vars
assert "t_300" in ds.data_vars
```

______________________________________________________________________

## 20. CLI Tools

### cfgrib

```bash
python -m cfgrib selfcheck
python -m cfgrib to_netcdf era5.grib -o era5.nc
python -m cfgrib dump era5.grib
```

### earthkit-data 1.0

**No built-in CLI equivalent.** Use Python directly:

```python
import earthkit.data as ekd

fl = ekd.from_source("file", "era5.grib").to_fieldlist()
ds = fl.to_xarray(profile="earthkit")
ds.to_netcdf("era5.nc")
```

______________________________________________________________________

## 21. Write Support

### cfgrib

```python
from cfgrib.xarray_to_grib import to_grib
to_grib(ds, "output.grib", grib_keys={"edition": 2})  # Alpha quality
```

### earthkit-data 1.0

**Not part of xr_engine.** GRIB writing is handled separately via the FieldList API:

```python
# Convert xarray back to FieldList, then save
fl = ds.earthkit.to_fieldlist()
fl.save("output.grib")
```

______________________________________________________________________

## 22. Low-level API

### cfgrib

```python
import cfgrib
from cfgrib.messages import FileStream, Message

# Read individual GRIB messages
stream = FileStream("era5.grib")
for msg in stream:
    print(msg["shortName"], msg["level"])

# Build custom index
ds = cfgrib.open_file("era5.grib")
print(ds.dimensions)
print(ds.variables.keys())
```

### earthkit-data 1.0

```python
import earthkit.data as ekd

fl = ekd.from_source("file", "era5.grib").to_fieldlist()

# Iterate fields
for field in fl:
    print(field.get("parameter.variable"), field.get("vertical.level"))

# Query unique values
print(fl.unique("parameter.variable"))
print(fl.unique("vertical.level"))

# Group by parameter
for group in fl.group_by("parameter.variable"):
    print(f"Parameter: {group[0].get('parameter.variable')}, fields: {len(group)}")

# Order
fl_sorted = fl.order_by(["vertical.level"])
```

### Testable example

```python
from earthkit.data import from_source
from earthkit.data.utils.testing import earthkit_test_data_file

fl = from_source("file", earthkit_test_data_file("t_pl.grib")).to_fieldlist()

# Iterate and inspect
levels = [f.get("vertical.level") for f in fl]
assert sorted(levels) == [300, 400, 500, 700, 850, 1000]

# Unique values
unique = fl.unique("vertical.level")
assert unique == {"vertical.level": (1000, 850, 700, 500, 400, 300)}

# Selection
fl_500 = fl.sel(**{"vertical.level": 500})
assert len(fl_500) == 1
```

______________________________________________________________________

## Summary: Default Differences

| Aspect | cfgrib default | earthkit-data default |
|--------|---------------|----------------------|
| dtype | `float32` | `float64` |
| errors | `"warn"` | `"raise"` |
| squeeze | `True` | `True` |
| time_dims | `("time", "step")` | `["forecast_reference_time", "step"]` |
| Level dim name | `typeOfLevel` value (e.g., "isobaricInhPa") | `"level"` |
| CF version | CF-1.7 | CF-1.8 |
| Index files | Writes `.idx` files | No sidecar files |
| Attribute prefix | `GRIB_*` | Clean names via profiles |
| Lazy loading | Always (OnDiskArray) | `lazy_load=True` (configurable) |

______________________________________________________________________

## Migration Checklist

- \[ \] Replace `engine="cfgrib"` with `engine="earthkit"` (add `profile="earthkit"`)
- \[ \] Move `filter_by_keys` to `.sel()` before `.to_xarray()`
- \[ \] Replace `read_keys` with `extra_dims` or `variable_attrs`
- \[ \] Replace `errors="warn"` with `errors="warn", allow_holes=True`
- \[ \] Add `dtype="float32"` if you need cfgrib-level precision
- \[ \] Replace `cfgrib.open_datasets()` with `split_dims=["vertical.level_type"]`
- \[ \] Replace `cf2cdm.translate_coords()` with `rename_dims={...}` or profiles
- \[ \] Replace `coords_as_attributes` with `dims_as_attrs`
- \[ \] Remove `indexpath` config (not needed)
- \[ \] Remove `encode_cf` and use profiles + `decode_times`/`decode_timedelta` instead
