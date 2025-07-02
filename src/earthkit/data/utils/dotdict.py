# (C) Copyright 2020 ECMWF.
#
# This software is licensed under the terms of the Apache Licence Version 2.0
# which can be obtained at http://www.apache.org/licenses/LICENSE-2.0.
# In applying this licence, ECMWF does not waive the privileges and immunities
# granted to it by virtue of its status as an intergovernmental organisation
# nor does it submit to any jurisdiction.
#

import json
from typing import Any

import yaml

try:
    import tomllib  # Only available since 3.11
except ImportError:
    import tomli as tomllib


class DotDict(dict):
    """A dictionary that allows access to its keys as attributes.

    >>> d = DotDict({"a": 1, "b": {"c": 2}})
    >>> d.a
    1
    >>> d.b.c
    2
    >>> d.b = 3
    >>> d.b
    3

    The class is recursive, so nested dictionaries are also DotDicts.

    The DotDict class has the same constructor as the dict class.

    >>> d = DotDict(a=1, b=2)
    """

    def __init__(self, *args, **kwargs):
        """Initialize a DotDict instance.

        Parameters
        ----------
        *args : tuple
            Positional arguments for the dict constructor.
        **kwargs : dict
            Keyword arguments for the dict constructor.
        """
        super().__init__(*args, **kwargs)

        for k, v in self.items():
            if isinstance(v, dict):
                self[k] = DotDict(v)

            if isinstance(v, list):
                self[k] = [DotDict(i) if isinstance(i, dict) else i for i in v]

            if isinstance(v, tuple):
                self[k] = [DotDict(i) if isinstance(i, dict) else i for i in v]

    @classmethod
    def from_file(cls, path: str) -> "DotDict":
        """Create a DotDict from a file.

        Parameters
        ----------
        path : str
            The path to the file.

        Returns
        -------
        DotDict
            The created DotDict.
        """
        _, ext = os.path.splitext(path)
        if ext == ".yaml" or ext == ".yml":
            return cls.from_yaml_file(path)
        elif ext == ".json":
            return cls.from_json_file(path)
        elif ext == ".toml":
            return cls.from_toml_file(path)
        else:
            raise ValueError(f"Unknown file extension {ext}")

    @classmethod
    def from_yaml_file(cls, path: str) -> "DotDict":
        """Create a DotDict from a YAML file.

        Parameters
        ----------
        path : str
            The path to the YAML file.

        Returns
        -------
        DotDict
            The created DotDict.
        """
        with open(path, "r") as file:
            data = yaml.safe_load(file)

        return cls(data)

    @classmethod
    def from_json_file(cls, path: str) -> DotDict:
        """Create a DotDict from a JSON file.

        Parameters
        ----------
        path : str
            The path to the JSON file.

        Returns
        -------
        DotDict
            The created DotDict.
        """

        with open(path, "r") as file:
            data = json.load(file)

        return cls(data)

    @classmethod
    def from_toml_file(cls, path: str) -> DotDict:
        """Create a DotDict from a TOML file.

        Parameters
        ----------
        path : str
            The path to the TOML file.

        Returns
        -------
        DotDict
            The created DotDict.
        """
        with open(path, "r") as file:
            data = tomllib.load(file)
        return cls(data)

    def __getattr__(self, attr: str) -> Any:
        """Get an attribute.

        Parameters
        ----------
        attr : str
            The attribute name.

        Returns
        -------
        Any
            The attribute value.
        """
        try:
            return self[attr]
        except KeyError:
            raise AttributeError(attr)

    def __setattr__(self, attr: str, value: Any) -> None:
        """Set an attribute.

        Parameters
        ----------
        attr : str
            The attribute name.
        value : Any
            The attribute value.
        """
        if isinstance(value, dict):
            value = DotDict(value)
        self[attr] = value

    def __repr__(self) -> str:
        """Return a string representation of the DotDict.

        Returns
        -------
        str
            The string representation.
        """
        return f"DotDict({super().__repr__()})"
