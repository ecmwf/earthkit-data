#!/usr/bin/env python3

# (C) Copyright 2022- ECMWF.
#
# This software is licensed under the terms of the Apache Licence Version 2.0
# which can be obtained at http://www.apache.org/licenses/LICENSE-2.0.
# In applying this licence, ECMWF does not waive the privileges and immunities
# granted to it by virtue of its status as an intergovernmental organisation
# nor does it submit to any jurisdiction.


from emohawk import load_from
from emohawk.testing import emohawk_examples_file


def test_describe():

    f = load_from("file", emohawk_examples_file("tuv_pl.grib"))

    # full contents
    df = f.describe(no_print=True)
    df = df.data

    ref = {
        "level": {
            ("t", "isobaricInhPa"): "1000,300,...",
            ("u", "isobaricInhPa"): "1000,300,...",
            ("v", "isobaricInhPa"): "1000,300,...",
        },
        "date": {
            ("t", "isobaricInhPa"): "20180801",
            ("u", "isobaricInhPa"): "20180801",
            ("v", "isobaricInhPa"): "20180801",
        },
        "time": {
            ("t", "isobaricInhPa"): "1200",
            ("u", "isobaricInhPa"): "1200",
            ("v", "isobaricInhPa"): "1200",
        },
        "step": {
            ("t", "isobaricInhPa"): "0",
            ("u", "isobaricInhPa"): "0",
            ("v", "isobaricInhPa"): "0",
        },
        "paramId": {
            ("t", "isobaricInhPa"): "130",
            ("u", "isobaricInhPa"): "131",
            ("v", "isobaricInhPa"): "132",
        },
        "class": {
            ("t", "isobaricInhPa"): "od",
            ("u", "isobaricInhPa"): "od",
            ("v", "isobaricInhPa"): "od",
        },
        "stream": {
            ("t", "isobaricInhPa"): "oper",
            ("u", "isobaricInhPa"): "oper",
            ("v", "isobaricInhPa"): "oper",
        },
        "type": {
            ("t", "isobaricInhPa"): "an",
            ("u", "isobaricInhPa"): "an",
            ("v", "isobaricInhPa"): "an",
        },
        "experimentVersionNumber": {
            ("t", "isobaricInhPa"): "0001",
            ("u", "isobaricInhPa"): "0001",
            ("v", "isobaricInhPa"): "0001",
        },
    }

    assert ref == df.to_dict()

    # repeated use
    df = f.describe()
    df = df.data
    assert ref == df.to_dict()

    # single param by shortName
    df = f.describe("t", no_print=True)
    df = df.data

    ref = {
        0: {
            "shortName": "t",
            "typeOfLevel": "isobaricInhPa",
            "level": "1000,300,400,850,500,700",
            "date": "20180801",
            "time": "1200",
            "step": "0",
            "paramId": "130",
            "class": "od",
            "stream": "oper",
            "type": "an",
            "experimentVersionNumber": "0001",
        }
    }

    assert ref[0] == df[0].to_dict()

    # repeated use
    df = f.describe(param="t", no_print=True)
    df = df.data
    assert ref[0] == df[0].to_dict()

    df = f.describe("t")
    df = df.data
    assert ref[0] == df[0].to_dict()

    df = f.describe(param="t")
    df = df.data
    assert ref[0] == df[0].to_dict()

    # single param by paramId
    df = f.describe(130, no_print=True)
    df = df.data

    ref = {
        0: {
            "shortName": "t",
            "typeOfLevel": "isobaricInhPa",
            "level": "1000,300,400,850,500,700",
            "date": "20180801",
            "time": "1200",
            "step": "0",
            "paramId": "130",
            "class": "od",
            "stream": "oper",
            "type": "an",
            "experimentVersionNumber": "0001",
        }
    }

    assert ref[0] == df[0].to_dict()

    df = f.describe(param=130, no_print=True)
    df = df.data
    assert ref[0] == df[0].to_dict()

    df = f.describe(130)
    df = df.data
    assert ref[0] == df[0].to_dict()

    df = f.describe(param=130)
    df = df.data
    assert ref[0] == df[0].to_dict()


def test_ls():
    f = load_from("file", emohawk_examples_file("tuv_pl.grib"))

    # default keys
    f1 = f.sel(count=[1, 2, 3, 4])
    df = f1.ls(no_print=True)

    ref = {
        "centre": {0: "ecmf", 1: "ecmf", 2: "ecmf", 3: "ecmf"},
        "shortName": {0: "t", 1: "u", 2: "v", 3: "t"},
        "typeOfLevel": {
            0: "isobaricInhPa",
            1: "isobaricInhPa",
            2: "isobaricInhPa",
            3: "isobaricInhPa",
        },
        "level": {0: 1000, 1: 1000, 2: 1000, 3: 850},
        "dataDate": {0: 20180801, 1: 20180801, 2: 20180801, 3: 20180801},
        "dataTime": {0: 1200, 1: 1200, 2: 1200, 3: 1200},
        "stepRange": {0: "0", 1: "0", 2: "0", 3: "0"},
        "dataType": {0: "an", 1: "an", 2: "an", 3: "an"},
        "number": {0: 0, 1: 0, 2: 0, 3: 0},
        "gridType": {
            0: "regular_ll",
            1: "regular_ll",
            2: "regular_ll",
            3: "regular_ll",
        },
    }

    assert ref == df.to_dict()

    # extra keys
    f1 = f.sel(count=[1, 2])
    df = f1.ls(extra_keys=["paramId"], no_print=True)

    ref = {
        "centre": {0: "ecmf", 1: "ecmf"},
        "shortName": {0: "t", 1: "u"},
        "typeOfLevel": {0: "isobaricInhPa", 1: "isobaricInhPa"},
        "level": {0: 1000, 1: 1000},
        "dataDate": {0: 20180801, 1: 20180801},
        "dataTime": {0: 1200, 1: 1200},
        "stepRange": {0: "0", 1: "0"},
        "dataType": {0: "an", 1: "an"},
        "number": {0: 0, 1: 0},
        "gridType": {0: "regular_ll", 1: "regular_ll"},
        "paramId": {0: 130, 1: 131},
    }

    assert ref == df.to_dict()
