# (C) Copyright 2020 ECMWF.
#
# This software is licensed under the terms of the Apache Licence Version 2.0
# which can be obtained at http://www.apache.org/licenses/LICENSE-2.0.
# In applying this licence, ECMWF does not waive the privileges and immunities
# granted to it by virtue of its status as an intergovernmental organisation
# nor does it submit to any jurisdiction.
#

import operator


class Interval:
    def __init__(self, left, right, closed="both"):
        if left is not None and right is not None and left >= right:
            raise ValueError(f"Invalid bounds, left={left} >= right={right}")
        if closed not in ("both", "left", "right", "none"):
            raise ValueError(f"Invalid closed={closed}")

        self._left = left
        self._right = right
        self._closed = closed
        self._left_oper = operator.lt if closed in ["both", "left"] else operator.le
        self._right_oper = operator.gt if closed in ["both", "right"] else operator.ge

    def __contains__(self, value):
        if self.bounded:
            if self._left is not None and self._left_oper(value, self._left):
                return False
            elif self._right is not None and self._right_oper(value, self._right):
                return False
        return True

    def __repr__(self):
        return f"{self.__class__.__name__}(left={self.left}, right={self.right}, closed={self.closed})"

    @property
    def left(self):
        return self._left

    @property
    def right(self):
        return self._right

    @property
    def closed(self):
        return self._closed

    @property
    def closed_left(self):
        return self._closed in ["both", "left"]

    @property
    def closed_right(self):
        return self._closed in ["both", "right"]

    @property
    def open_left(self):
        return not self.closed_left

    @property
    def open_right(self):
        return not self.closed_right

    @property
    def bounded_left(self):
        return self.left is not None

    @property
    def bounded_right(self):
        return self.right is not None

    @property
    def bounded(self):
        return self.bounded_left or self.bounded_right
