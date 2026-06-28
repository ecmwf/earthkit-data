import earthkit.data as ekd

ds_fl = ekd.from_source("sample", "ens_cf_pf.grib")

ds = ds_fl.to_xarray(
    dim_roles={"number": "perturbationNumber"},
)
