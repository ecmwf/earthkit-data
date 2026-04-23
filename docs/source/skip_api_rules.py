# (C) Copyright 2020 ECMWF.
#
# This software is licensed under the terms of the Apache Licence Version 2.0
# which can be obtained at http://www.apache.org/licenses/LICENSE-2.0.
# In applying this licence, ECMWF does not waive the privileges and immunities
# granted to it by virtue of its status as an intergovernmental organisation
# nor does it submit to any jurisdiction.
#


def _ends_with_any(name, suffixes):
    for suffix in suffixes:
        if name.endswith(suffix):
            return True
    return False


_SKIP = {
    "function": [
        "sources.from_source",
        "sources.from_source_internal",
        "sources.from_source_lazily",
        "sources.register",
    ],
    "class": [
        "sources.SourceLoader",
        "sources.SourceMaker",
    ],
    "data": [
        "encoders.grib.encoder",
        "sources.get_source",
    ],
    "method": [
        "core.fieldlist.FieldList.to_data_object",
    ],
}


def _skip_api_items(app, what, name, obj, skip, options):
    # if what == "package":
    #     print(f"{name}[{what}]")

    # print(f"{name}[{what}]")
    # if "ArrayLike" in name:
    #     print(f"Skipping {what} {name} {obj}")

    if name.endswith(".LOG"):
        skip = True
    elif what == "data" and ".ArrayLike" in name:
        skip = True
    else:
        s = _SKIP.get(what, [])
        rel_name = name
        if rel_name.startswith("earthkit.data."):
            rel_name = rel_name[len("earthkit.data.") :]

        if rel_name in s:
            skip = True

    # if name.startswith("earthkit.data.sources"):

    #     if what == "class" and _ends_with_any(name, ["SourceLoader", "sources.SourceMaker"]):
    #         skip = True

    #     if what == "function" and _ends_with_any(
    #         name,
    #         [
    #             "sources.from_source",
    #             "sources.from_source_internal",
    #             "sources.from_source_lazily",
    #             "sources.get_source",
    #             "sources.register",
    #         ],
    #     ):
    #         skip = True

    return skip
