# (C) Copyright 2020 ECMWF.
#
# This software is licensed under the terms of the Apache Licence Version 2.0
# which can be obtained at http://www.apache.org/licenses/LICENSE-2.0.
# In applying this licence, ECMWF does not waive the privileges and immunities
# granted to it by virtue of its status as an intergovernmental organisation
# nor does it submit to any jurisdiction.
#

import itertools
import logging
import os
import re
from functools import cached_property
from pathlib import Path

from .dates import to_datetime
from .dates import to_timedelta

LOG = logging.getLogger(__name__)

RE1 = re.compile(r"{([^}]*)}")
RE2 = re.compile(r"\(([^}]*)\)")


class Any:
    def substitute(self, value, name):
        return value


class Enum:
    def __init__(self, enum=""):
        self.enum = set(enum.split(","))

    def substitute(self, value, name):
        if self.enum and value not in self.enum:
            raise ValueError(
                "Invalid value '{}' for parameter '{}', expected one of {}".format(value, name, self.enum)
            )
        return value


class Int:
    def __init__(self, format="%d"):
        self.format = format

    def substitute(self, value, name):
        if not isinstance(value, int):
            raise ValueError("Invalid value '{}' for parameter '{}', expected an integer".format(value, name))
        return self.format % value


class Float:
    def __init__(self, format="%g"):
        self.format = format

    def substitute(self, value, name):
        if not isinstance(value, (int, float)):
            raise ValueError("Invalid value '{}' for parameter '{}', expected a float".format(value, name))

        return self.format % value


class Datetime:
    def __init__(self, format):
        self.format = format

    def substitute(self, value, name):
        print("Datetime substitute", value, name)
        return to_datetime(value).strftime(self.format)


class DatetimeDelta:
    def __init__(self, params):
        params_list = params.split(";")
        if len(params_list) != 2:
            raise ValueError(
                "Invalid parameters '{}' for class DatetimeDelta, expected (delta;format)".format(params)
            )
        self.delta = params_list[0].strip()
        self.format = params_list[1].strip()

    def substitute(self, value, name):
        sign = -1 if self.delta[0] == "-" else 1
        if re.fullmatch(r"[-\+]?\d+[hms]?", self.delta):
            delta = re.search(r"\d+[hms]?", self.delta).group(0)
        else:
            raise ValueError(
                "Invalid value '{}' for delta, expected time in hour (h), minute (m) or second (s)".format(
                    self.delta
                )
            )

        valid_date = to_datetime(value) + sign * to_timedelta(delta)
        return valid_date.strftime(self.format)


class Str:
    def __init__(self, format="%s"):
        self.format = format

    def substitute(self, value, name):
        if not isinstance(value, str):
            raise ValueError("Invalid value '{}' for parameter '{}', expected a string".format(value, name))
        return self.format % value


TYPES = {
    "": Any,
    "int": Int,
    "float": Float,
    "date": Datetime,
    "strftime": Datetime,
    "strftimedelta": DatetimeDelta,
    "enum": Enum,
}


class Constant:
    name = None

    def __init__(self, value):
        self.value = value

    def substitute(self, params):
        return self.value

    def substitute_all(self, params):
        return self.value

    # def match(self, value):
    #     return self.value == value

    def __repr__(self):
        return f"{self.__class__.__name__}({self.value})"


class Variable:
    def __init__(self, value):
        bits = value.split(":")
        self.name = bits[0]
        kind = RE2.split(":".join(bits[1:]))
        if len(kind) == 1:
            self.kind = TYPES[kind[0]]()
        else:
            self.kind = TYPES[kind[0]](kind[1])

        self.value = value

    def substitute(self, params):
        """Substitute value for a parameter

        Parameters
        ----------
        params : dict
            The value belonging to ``self.name`` in ``params`` are
            substituted into the Variable. The value to substitute must be a single value.
            If ``self.name`` is not in  ``params``, a ValueError is raised.

        Returns
        -------

            List of substituted values. When ``self.name`` is not
            in ``params``, None is returned.

        Raises
        ------
        ValueError
            If ``self.name`` is not in ``params``.


        Example
        -------
        >>> v = Variable("my_date:date(%Y-%m-%d)")
        >>> v.substitute({"my_date": "2000-01-01"})
        '2000-01-01'

        >>> v = Variable("my_date:date(%Y-%m-%d)")
        >>> v.substitute({"level": "500"})
        ValueError: Missing parameter 'my_date'
        """
        if self.name not in params:
            # return "{" + self.value + "}"
            raise ValueError("Missing parameter '{}'".format(self.name))
        return self.kind.substitute(params[self.name], self.name)

    def substitute_all(self, params):
        """Substitute all values for a parameter

        Parameters
        ----------
        params : dict
            The values belonging to ``self.name`` in ``params`` are
            substituted into the Variable.

        Returns
        -------
        list
            List of substituted values. When ``self.name`` is not
            in ``params``, None is returned.

        Example
        -------
        >>> v = Variable("my_date:date(%Y-%m-%d)")
        >>> v.substitute_all({"my_date": ["2000-01-01", "2000-01-02"]})
        ['2000-01-01', '2000-01-02']

        >>> v = Variable("my_date:date(%Y-%m-%d)")
        >>> v.substitute_all({"my_date": "2000-01-01"})
        ['2000-01-01']

        >>> v = Variable("my_date:date(%Y-%m-%d)")
        >>> v.substitute_all({"level": "500"})
        None
        """
        print(f"substitute_all: {self.name=} {params=}")
        if self.name in params:
            v = params[self.name]
            if not isinstance(v, list):
                v = [v]
            return [self.kind.substitute(x, self.name) for x in v]
        return None

    def __repr__(self):
        return f"Variable({self.name},{self.value},{self.kind})"


FUNCTIONS = dict(lower=lambda s: s.lower())


class Function:
    def __init__(self, value):
        functions = value.split("|")
        self.name = functions[0]
        self.variable = Variable(functions[0])
        self.functions = functions[1:]

    def substitute(self, params):
        value = self.variable.substitute(params)
        for f in self.functions:
            value = FUNCTIONS[f](value)
        return value


class Pattern:
    def __init__(self, pattern, ignore_missing_keys=False):
        self.ignore_missing_keys = ignore_missing_keys

        self.pattern = []
        self.variables = []
        for i, p in enumerate(RE1.split(pattern)):
            if i % 2 == 0:
                if p != "":
                    self.pattern.append(Constant(p))
            else:
                if "|" in p:
                    v = Function(p)
                else:
                    v = Variable(p)
                self.variables.append(v)
                self.pattern.append(v)

    @property
    def names(self):
        return sorted({v.name for v in self.variables})

    def is_constant(self):
        return not self.variables and len(self.pattern) == 1 and isinstance(self.pattern[0], Constant)

    def substitute(self, *args, **kwargs):
        params = {}
        for a in args:
            params.update(a)
        params.update(kwargs)

        for k, v in params.items():
            if isinstance(v, list):
                return self._substitute_many(params)

        return self._substitute_one(params)
        # TODO: discuss if this should be:
        # return [self._substitute_one(params)]

    def _substitute_one(self, params):
        used = set(params.keys())
        result = []
        for p in self.pattern:
            used.discard(p.name)
            result.append(p.substitute(params))
        if used and not self.ignore_missing_keys:
            raise ValueError("Unused parameter(s): {}".format(used))

        return "".join(str(x) for x in result)

    def _substitute_many(self, params):
        for k, v in list(params.items()):
            if not isinstance(v, list):
                params[k] = [v]

        seen = set()
        result = []
        for n in (dict(zip(params.keys(), x)) for x in itertools.product(*params.values())):
            m = self.substitute(n)
            if m not in seen:
                seen.add(m)
                result.append(m)

        return result

    def match(self, value):
        """Match pattern regex against value

        Parameters
        ----------
        value : str
            Value to match

        Returns
        -------
        re.Match
            re.Match object if the value matches the pattern. None otherwise.

        Example
        -------
        >>> p = Pattern("t_{my_date:date(%Y-%m-%d)}.grib")
        >>> p.match("t_2000-01-01.grib")
        <re.Match object; span=(0, 17), match='t_2000-01-01.grib'>

        >>> p = Pattern("t_{my_date:date(%Y-%m-%d)}.grib")
        >>> p.match("2000-01-01.grib")
        None

        >>> p = Pattern("{shortName}_{my_date:date(%Y-%m-%d)}.grib")
        >>> p.match("t_2000-01-01.grib")
        <re.Match object; span=(0, 17), match='t_2000-01-01.grib'>

        >>> p = Pattern("data/t/level")
        >>> p.match("data/t/level")
        <re.Match object; span=(0, 12), match='data/t/level'>
        >>> p.match("data/t/level/500")
        None
        """
        rx = self.regex
        return rx.match(value)

    def __repr__(self):
        t = "pattern:"
        for p in self.pattern:
            t += f"\n {p}"
        return t

    @cached_property
    def regex(self):
        t = ""
        for p in self.pattern:
            if isinstance(p, Constant):
                t += p.value
            else:
                t += f"(?P<{p.name}>\S+)"

        t = rf"^{t}$"
        return re.compile(t)


class HivePattern:
    def __init__(self, pattern, values):
        self.pattern = pattern

        path = Path(pattern)

        # analyze path structure
        self.root = ""
        self.rest = ""
        path_parts = path.parts
        LOG.debug(f"{pattern=} {path_parts=}")
        self.parts = [Pattern(x) for x in path_parts]
        for i, part in enumerate(self.parts):
            if part.is_constant():
                self.root = os.path.join(self.root, part.pattern[0].value)
            else:
                self.rest = os.path.join(*path_parts[i:])
                self.parts = self.parts[i:]
                break

        self.keys = []
        self.fixed_keys = {}
        for p in self.parts:
            for v in p.variables:
                if v.name is not self.keys:
                    s = v.substitute_all(values)
                    if s is not None:
                        self.fixed_keys[v.name] = s
                    self.keys.append(v.name)

        # for k in list(params.keys()):
        #     if k in self.fixed_keys:
        #         del params[k]

        assert len(self.fixed_keys) == len(values)
        # self.fixed_keys = params

        LOG.debug(f"root={self.root}")
        LOG.debug(f"rest={self.rest}")
        LOG.debug(f"keys={self.keys}")
        LOG.debug(f"fixed_keys={self.fixed_keys}")
        for p in self.parts:
            LOG.debug(f" {p=}")
            LOG.debug(f"   re={p.regex}")

        LOG.debug()

    def scan(self, *args, **kwargs):
        params = {}
        for a in args:
            params.update(a)
        params.update(kwargs)

        # for i in range(len(self.parts)):
        #     self.parts[i] = self.parts[i].substitute_for_scan(params)

        # for p in self.parts:
        #     print(" p=", p)

        # print("params=", params)

        rest = Path(self.rest).parts
        LOG.debug(f"{rest=}")

        res = []

        keys = dict(**self.fixed_keys)
        for k, v in params.items():
            if not isinstance(v, list):
                v = [v]
            if k in self.keys:
                if k in self.fixed_keys:
                    if not all(x in self.fixed_keys[k] for x in v):
                        raise ValueError(
                            f"Invalid value '{v}' for parameter '{k}', expected one of {self.fixed_keys[k]}"
                        )

                keys[k] = v

        for k in keys:
            keys[k] = set([str(x) for x in keys[k]])

        LOG.debug(f"{keys=}")

        root_num = len(Path(self.root).parts)

        last = len(self.parts) - 1
        for root, dirs, files in os.walk(self.root):
            LOG.debug(f"walk: {root=}")
            index = len(Path(root).parts) - root_num
            LOG.debug(f"{index=} {last=}")
            # index = _get_index(root)
            part = self.parts[index]

            # intermediate level
            if index != last:
                exclude = []
                for d in dirs:
                    g = self.collect(d, part, keys)
                    if g is None:
                        exclude.append(d)
                LOG.debug(f"   {exclude=}")
                if exclude:
                    dirs[:] = [d for d in dirs if d not in exclude]
                    continue

            # last level (collection)
            else:
                for file in files:
                    print("  ", file)
                    d = self.collect(file, part, keys)
                    if d:
                        res.append(os.path.join(root, file))
                        LOG.debug("MATCH")
                    else:
                        LOG.debug("NO MATCH")

        return res

    def collect(self, file, part, keys):
        m = part.regex.match(file)
        print(m)
        if m:
            group = m.groupdict()
            if len(group) == len(part.variables):
                for k, v in group.items():
                    if k in keys:
                        LOG.debug(f"  {k=} {v=} {keys[k]=}")
                        if v not in keys[k]:
                            return None
            return group
