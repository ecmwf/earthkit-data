# (C) Copyright 2020 ECMWF.
#
# This software is licensed under the terms of the Apache Licence Version 2.0
# which can be obtained at http://www.apache.org/licenses/LICENSE-2.0.
# In applying this licence, ECMWF does not waive the privileges and immunities
# granted to it by virtue of its status as an intergovernmental organisation
# nor does it submit to any jurisdiction.
#

import os
import re


def urlify(text):
    return re.sub(r"(https?://.*\S)", r'<a href="\1" target="_blank">\1</a>', text)


def css(name):
    path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "conf", "css", name)
    with open(path + ".css") as f:
        return """<style type="text/css">%s</style>""" % (f.read(),)


def bold(text):
    return f"<b>{text}</b>"


def td(text):
    return f"<td>{text}</td>"


def tr(key, value):
    return f"<tr>{td(bold(key))}{td(value)}</tr>"


def table(obj):
    style = css("table")

    table = """
<h4>{name}</h4>
<table class="eh">
<tr><td><b>Home page</b></td><td>{home_page}</td></tr>
<tr><td><b>Documentation</b></td><td>{documentation}</td></tr>
<tr><td><b>Citation</b></td><td><pre>{citation}</pre></td></tr>
<tr><td><b>Licence</b></td><td>{licence}</td></tr>
</table>
        """.format(
        name=obj.name,
        home_page=urlify(obj.home_page),
        licence=urlify(obj.licence),
        citation=obj.citation,
        documentation=urlify(obj.documentation),
    )

    return style + table


def table_from_dict(vals, title=None):
    if not isinstance(vals, dict):
        raise TypeError(f"table_from_dict: vals must be a dict not type={type(vals)}")

    t = ""
    if title is not None and title:
        t = f"<h4>{title}</h4>"

    t += """
<table class="eh-table">
{rows}
</table>""".format(
        rows=" ".join([tr(k, v) for k, v in vals.items()])
    )

    style = css("table")
    return style + t


def tab_page(title, tooltip, page_id, text, checked):
    checked = "checked" if checked else ""
    return f"""
<input type="radio" name="eh-tabs" id="{page_id}" {checked} />
<label for="{page_id}" title="{tooltip}">{title}</label>
<div class="tab">
{text}
</div>
    """


def tab(items, details=None, selected=None):
    import uuid

    t = f"""<div class="eh-description">{details}</div>""" if details else ""
    t += """
<div>
<section class="eh-section>
<div class="eh-tabs-container">
<div class="eh-tabs-block">
<div class="eh-tabs">
{pages}
</div>
</div>
</div>
</section>
</div>
        """.format(
        pages=" ".join(
            [
                tab_page(
                    item["title"],
                    item.get("tooltip", ""),
                    str(uuid.uuid4()),
                    item["text"],
                    selected in (None, "") or item["title"] == selected,
                )
                for item in items
            ]
        ),
    )

    style = css("tab")
    return style + t
