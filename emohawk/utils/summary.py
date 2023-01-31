# (C) Copyright 2020 ECMWF.
#
# This software is licensed under the terms of the Apache Licence Version 2.0
# which can be obtained at http://www.apache.org/licenses/LICENSE-2.0.
# In applying this licence, ECMWF does not waive the privileges and immunities
# granted to it by virtue of its status as an intergovernmental organisation
# nor does it submit to any jurisdiction.
#

from emohawk.core.ipython import ipython_active

GRIB_LS_KEYS = [
    "centre",
    "shortName",
    "typeOfLevel",
    "level",
    "dataDate",
    "dataTime",
    "stepRange",
    "dataType",
    "number",
    "gridType",
]

GRIB_DESCRIBE_KEYS = [
    "shortName",
    "typeOfLevel",
    "level",
    "date",
    "time",
    "step",
    "number",
    "paramId",
    "marsClass",
    "marsStream",
    "marsType",
    "experimentVersionNumber",
]


def drop_unwanted_series(df, key=None, axis=1):
    # only show the column for number in the default set of keys if
    # there are any valid values in it
    r = None
    if axis == 1 and key in df.columns:
        r = df[key].unique()
    elif axis == 0 and key in df.index:
        r = df.loc[key].unique()
    if len(r) == 1 and r[0] in ["0", None]:
        df.drop(key, axis=axis, inplace=True)


def format_list(v, full=False):
    if isinstance(v, list):
        if full is True:
            return ",".join([str(x) for x in v])
        else:
            if len(v) == 1:
                return v[0]
            if len(v) > 2:
                return ",".join([str(x) for x in [v[0], v[1], "..."]])
            else:
                return ",".join([str(x) for x in v])
    else:
        return v


def make_unique(x, full=False):
    v = set(x)
    r = []
    for t in v:
        r.append(str(t))
    return format_list(r, full=full)


def format_ls(attributes, **kwargs):
    import pandas as pd

    no_print = kwargs.pop("no_print", False)

    df = pd.DataFrame.from_records(attributes)

    if df is None or df.empty:
        return None

    drop_unwanted_series(df, key="number", axis=1)

    # test whether we're in the Jupyter environment
    if ipython_active:
        return df
    elif not no_print:
        print(df)
    return df


def format_describe(attributes, *args, **kwargs):
    import pandas as pd

    param = args[0] if len(args) == 1 else None
    if param is None:
        param = kwargs.pop("param", None)
    no_print = kwargs.pop("no_print", False)

    df = pd.DataFrame.from_records(attributes, **kwargs)

    if df is None or df.empty:
        return None

    # these keys are changed in the output
    labels = {"marsClass": "class", "marsStream": "stream", "marsType": "type"}

    no_header = False
    main_axis = 1
    if param is None:
        df = df.groupby(["shortName", "typeOfLevel"]).agg(make_unique)
        df.rename(labels, axis=1, inplace=True)
    else:
        param_names = {int: "paramId", str: "shortName"}
        param_name = param_names.get(type(param), None)
        if param_name is not None:
            df = pd.DataFrame(df[df[param_name] == param].agg(make_unique, full=True).T)
            df.rename(labels, axis=0, inplace=True)
            no_header = True
            main_axis = 0
        else:
            return pd.DataFrame()

    drop_unwanted_series(df, key="number", axis=main_axis)

    df = df.style.set_properties(**{"text-align": "left"})
    df.set_table_styles([dict(selector="th", props=[("text-align", "left")])])
    if no_header:
        df.hide(axis="columns")

    if ipython_active:
        return df
    elif not no_print:
        print(df)
    return df
