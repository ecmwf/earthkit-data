# (C) Copyright 2020 ECMWF.
#
# This software is licensed under the terms of the Apache Licence Version 2.0
# which can be obtained at http://www.apache.org/licenses/LICENSE-2.0.
# In applying this licence, ECMWF does not waive the privileges and immunities
# granted to it by virtue of its status as an intergovernmental organisation
# nor does it submit to any jurisdiction.
#

from earthkit.data.core.ipython import ipython_active


class BUFRTree:
    """Restructure the result of the bufr_dump ecCodes command."""

    def make_tree(self, data):
        """Restructure the the result of json bufr_dump into a format better
        suited for generating a tree view out of it.

        Parameters
        ----------
        data: dict
            The result of the json bufr_dump loaded into a dict.

        Returns
        -------
        dict
        """
        return self._load_dump(data)

    def _load_dump(self, data):
        r = {"header": [], "data": []}

        # data = data["messages"][0]

        for i, v in enumerate(data):
            # print(v)
            k = v["key"]
            val = v["value"]
            if isinstance(val, list):
                val = "array"

            r["header"].append({"key": k, "value": val})

            if k == "unexpandedDescriptors":
                self._parse_dump(data[i + 1], r["data"])
                break
        return r

    def _parse_dump(self, data, parent):
        arrayCnt = 0
        keyCnt = 0
        for v in data:
            if isinstance(v, list):
                arrayCnt += 1
            else:
                # print(v)
                keyCnt += 1
        # if arrayCnt > 1:
        #     for i, v in enumerate(data):
        #         print(i, v)
        #     return

        for i, v in enumerate(data):
            if not isinstance(v, list):
                # print(i, v["key"], arrayCnt)
                parent.append(
                    {
                        "key": v["key"],
                        "value": v["value"],
                        "units": v.get("units", None),
                    }
                )
            else:
                # print("    arrayCnt=", arrayCnt)
                if arrayCnt > 1:
                    # print("->", v[0])
                    # print("  ", v[1])
                    item = []
                    parent.append(item)
                    self._parse_dump(v, item)
                    # print(f"item={item}")
                    # break
                else:
                    self._parse_dump(v, parent)


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
        return f"""<li>{k}: {v} [{units}]</li>"""

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


def make_bufr_html_tree(data, **kwargs):
    tree = BUFRTree().make_tree(data)
    if ipython_active:
        from IPython.display import HTML

        from earthkit.data.utils.html import css

        t = BUFRHtmlTree().make_html(tree)
        style = css("tree")
        return HTML(style + t)

    return tree
