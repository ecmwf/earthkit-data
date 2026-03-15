#!/usr/bin/env python3

# (C) Copyright 2020 ECMWF.
#
# This software is licensed under the terms of the Apache Licence Version 2.0
# which can be obtained at http://www.apache.org/licenses/LICENSE-2.0.
# In applying this licence, ECMWF does not waive the privileges and immunities
# granted to it by virtue of its status as an intergovernmental organisation
# nor does it submit to any jurisdiction.
#


# from earthkit.data.specs.time_span import TimeSpan
# from earthkit.data.specs.time_span import TimeSpanMethod


# def test_timespan_1():
#     t = TimeSpan()
#     assert t.value == datetime.timedelta(0)
#     assert t.method == TimeSpanMethod.INSTANT


# def test_timespan_2():
#     t = TimeSpan(3, TimeSpanMethod.AVERAGE)
#     assert t.value == datetime.timedelta(hours=3)
#     assert t.method == TimeSpanMethod.AVERAGE


# def test_timespan_3():
#     with pytest.raises(ValueError):
#         TimeSpan(3)
#     with pytest.raises(ValueError):
#         TimeSpan(3, TimeSpanMethod.INSTANT)


# def test_timespan_method():
#     m = TimeSpanMethod.AVERAGE
#     assert m.value.name == "avg"
#     assert m.name == "AVERAGE"
#     assert str(m) == "TimeSpanMethod.AVERAGE"


# def test_timespan_hash():
#     t1 = TimeSpan()
#     t2 = TimeSpan(3, TimeSpanMethod.AVERAGE)
#     s = set([t1, t2])
#     assert t1 in s
#     assert t2 in s
#     assert len(s) == 2

#     assert TimeSpan() in s
#     assert TimeSpan(3, TimeSpanMethod.AVERAGE) in s
