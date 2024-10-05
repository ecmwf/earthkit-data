# (C) Copyright 2020 ECMWF.
#
# This software is licensed under the terms of the Apache Licence Version 2.0
# which can be obtained at http://www.apache.org/licenses/LICENSE-2.0.
# In applying this licence, ECMWF does not waive the privileges and immunities
# granted to it by virtue of its status as an intergovernmental organisation
# nor does it submit to any jurisdiction.
#


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
    # do_print = kwargs.pop("print", False)

    if kwargs:
        raise TypeError(f"ls: unsupported arguments={kwargs}")

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

    return format_ls(metadata_proc(_keys, n))


def format_ls(attributes):
    import pandas as pd

    df = pd.DataFrame.from_records(attributes)
    return df


def format_describe(attributes, *args, **kwargs):
    # TODO: this is GRIB specific code, should not be here
    import pandas as pd

    param = args[0] if len(args) == 1 else None
    if param is None:
        param = kwargs.pop("param", None)

    # do_print = kwargs.pop("print", True)

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

    return df


class NamespaceDump(dict):
    def __init__(self, data, **kwargs):
        d = {item["title"]: item["data"] for item in data}
        super().__init__(d)
        self.data = data
        self._kwargs = kwargs

    def _repr_html_(self):
        from earthkit.data.core.ipython import ipython_active

        if ipython_active:
            from earthkit.data.utils.html import tab
            from earthkit.data.utils.html import table_from_dict

            if len(self.data) == 1:
                return table_from_dict(self.data[0]["data"])
            elif len(self.data) > 1:
                for item in self.data:
                    item["text"] = table_from_dict(item["data"])

                return tab(self.data, **self._kwargs)
        else:
            return str(self)


def format_namespace_dump(data, selected=None, details=None, **kwargs):
    raw = kwargs.pop("_as_raw", False)

    if not raw:
        return NamespaceDump(data, selected=selected, details=details)
    else:
        return data


class BUFRTree:
    """Restructures the result of the bufr_dump ecCodes command."""

    def __init__(self, data, subset, compressed, uncompressed):
        self.data = data
        self.subset = subset
        self.compressed = compressed
        self.uncompressed = uncompressed

    def make_tree(self):
        """Restructures the the result of json bufr_dump into a format better
        suited for generating a tree view out of it.

        Returns
        -------
        dict
        """
        return self._load_dump()

    def _load_dump(self):
        r = {"header": [], "data": []}

        # data = data["messages"][0]

        for i, v in enumerate(self.data):
            # print(v)
            k = v["key"]
            val = v["value"]
            if isinstance(val, list):
                val = "array"

            r["header"].append({"key": k, "value": val})

            # start data section
            if k == "unexpandedDescriptors":
                # for uncompressed data tries to shown only the branch
                # with given subset
                if self.subset is not None and self.subset > 0 and self.uncompressed:
                    try:
                        subset_index = self.subset - 1
                        d = self.data[i + 1][subset_index][0]
                        if d["key"] == "subsetNumber" and d["value"] == self.subset:
                            self._parse_dump(self.data[i + 1][subset_index], r["data"])
                            break
                    except Exception:
                        pass
                self._parse_dump(self.data[i + 1], r["data"])
                break
        return r

    def _parse_dump(self, data, parent):
        arrayCnt = 0
        keyCnt = 0
        for v in data:
            if isinstance(v, list):
                arrayCnt += 1
            else:
                keyCnt += 1

        for v in data:
            if not isinstance(v, list):
                vals = v["value"]
                if isinstance(vals, list):
                    vals = self._format_list(vals)
                parent.append(
                    {
                        "key": v["key"],
                        "value": vals,
                        "units": v.get("units", None),
                    }
                )
            else:
                if arrayCnt > 1:
                    item = []
                    parent.append(item)
                    self._parse_dump(v, item)
                else:
                    self._parse_dump(v, parent)

    def _format_list(self, vals):
        if len(vals) > 0:
            if self.subset is not None and self.subset > 0:
                index = self.subset - 1
                if index < len(vals):
                    return f"{vals[index]} ({len(vals)} items)"
                else:
                    return f"[{vals[0]}, ...] ({len(vals)-1} items)"
            else:
                return f"[{vals[0]}, ...] ({len(vals)} items)"
        else:
            return "[]"


class BUFRHtmlTree:
    def make_html(self, data):
        """Generates a html/css tree view from the input representing the
        result of bufr_dump.

        Parameters
        ----------
        data: dict

        Returns
        -------
        str
        """
        return self._build(data)

    def _build(self, data):
        td1 = self._node(data["header"], [])
        td2 = self._node(data["data"], [])

        td = self._top_node("header", td1) + self._top_node("data", td2)
        t = f"""
        <ul class="tree">
        <li>
            {td}
        </li>
        </ul>
        """
        return t

    def _leaf(self, k, v, units):
        if units is not None:
            return f"""<li>{k}: {v} [{units}]</li>"""
        else:
            return f"""<li>{k}: {v}</li>"""

    def _top_node(self, name, v):
        return f"""
        <li>
        <details>
            <summary>{name}</summary>
            <ul>
            {v}
            </ul>
            </details>
        </li>
        """

    def _start_node(self, k, v):
        return f"""
        <li>
        <details>
            <summary>{k}: {v}</summary>
            <ul>
        """

    def _end_node(self):
        return """</ul>
            </details>
        </li>
        """

    def _node(self, data, parent):
        td = ""
        if isinstance(data, list):
            if parent:
                td += self._start_node(data[0]["key"], data[0]["value"])
            for v in data:
                td += self._node(v, data)
            if parent:
                td += self._end_node()
        else:
            td += self._leaf(data["key"], data["value"], data.get("units", None))

        return td


def make_bufr_html_tree(data, title, subset, compressed, uncompressed):
    from earthkit.data.core.ipython import ipython_active

    tree = BUFRTree(data, subset, compressed, uncompressed).make_tree()
    if ipython_active:
        from IPython.display import HTML

        from earthkit.data.utils.html import css

        t = ""
        if title is not None and title:
            t = f"""<div class="eh-description">{title}</div>"""

        t += BUFRHtmlTree().make_html(tree)
        style = css("tree")
        return HTML(style + t)

    return tree


def ncdump(path):
    import subprocess

    result = subprocess.run(["ncdump", "-h", path], stdout=subprocess.PIPE)
    t = result.stdout.decode("utf-8").split("\n")
    for line in t:
        print(line)
