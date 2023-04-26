# (C) Copyright 2020 ECMWF.
#
# This software is licensed under the terms of the Apache Licence Version 2.0
# which can be obtained at http://www.apache.org/licenses/LICENSE-2.0.
# In applying this licence, ECMWF does not waive the privileges and immunities
# granted to it by virtue of its status as an intergovernmental organisation
# nor does it submit to any jurisdiction.
#

from earthkit.data.core.ipython import ipython_active


def drop_unwanted_series(df, key=None, axis=1):
    if df is None:
        return

    # only show the column for number in the default set of keys if
    # there are any valid values in it
    r = None
    if axis == 1 and key in df.columns:
        r = df[key].unique()
    elif axis == 0 and key in df.index:
        r = df.loc[key].unique()
    if r is not None and len(r) == 1 and r[0] in ["0", None]:
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
    r = [str(t) for t in v]
    return format_list(r, full=full)


def ls(metadata_proc, default_keys, n=None, keys=None, extra_keys=None, **kwargs):
    do_print = kwargs.pop("print", False)

    if kwargs:
        raise ValueError(f"ls: unsupported arguments={kwargs}")

    _keys = {}
    if isinstance(default_keys, (list, tuple)):
        default_keys = {k: k for k in default_keys}

    _keys = dict(default_keys) if keys is None else keys
    if isinstance(_keys, (list, tuple)):
        _keys = {k: k for k in keys}
    elif isinstance(_keys, str):
        _keys = {keys: keys}

    if extra_keys is not None:
        if isinstance(extra_keys, (list, tuple)):
            if len(extra_keys) > 0:
                _keys.update({k: k for k in extra_keys})
        elif isinstance(extra_keys, str):
            _keys.update({extra_keys: extra_keys})
        elif isinstance(extra_keys, dict):
            _keys.update(extra_keys)

    if n == 0:
        raise ValueError("n cannot be 0")

    return format_ls(metadata_proc(_keys, n), do_print)


def format_ls(attributes, do_print):
    import pandas as pd

    df = pd.DataFrame.from_records(attributes)

    # TODO: this is GRIB specific code, should not be here
    drop_unwanted_series(df, key="number", axis=1)

    # test whether we're in the Jupyter environment
    if ipython_active:
        return df
    elif do_print:
        print(df)
    return df


def format_describe(attributes, *args, **kwargs):
    # TODO: this is GRIB specific code, should not be here
    import pandas as pd

    param = args[0] if len(args) == 1 else None
    if param is None:
        param = kwargs.pop("param", None)

    do_print = kwargs.pop("print", True)

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
    elif do_print:
        print(df)
    return df


def format_info(data, selected=None, details=None, **kwargs):
    do_print = kwargs.pop("print", True)
    html = kwargs.pop("html", True)
    raw = kwargs.pop("_as_raw", False)

    rv = {item["title"]: item["data"] for item in data}

    if ipython_active:
        if html:
            from earthkit.data.core.ipython import HTML
            from earthkit.data.utils.html import tab, table_from_dict

            if len(data) == 1:
                return HTML(table_from_dict(data[0]["data"]))
            elif len(data) > 1:
                for item in data:
                    item["text"] = table_from_dict(item["data"])

                return HTML(tab(data, details, selected))
        else:
            return rv

    if do_print:
        print(data if raw else rv)
    else:
        return data if raw else rv
