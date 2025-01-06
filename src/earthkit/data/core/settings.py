# (C) Copyright 2020 ECMWF.
#
# This software is licensed under the terms of the Apache Licence Version 2.0
# which can be obtained at http://www.apache.org/licenses/LICENSE-2.0.
# In applying this licence, ECMWF does not waive the privileges and immunities
# granted to it by virtue of its status as an intergovernmental organisation
# nor does it submit to any jurisdiction.
#

import functools
import getpass
import logging
import os
import tempfile
import warnings
from abc import ABCMeta
from abc import abstractmethod
from contextlib import contextmanager
from typing import Callable

import yaml

from earthkit.data import __version__ as VERSION
from earthkit.data.utils.html import css
from earthkit.data.utils.humanize import as_bytes
from earthkit.data.utils.humanize import as_percent
from earthkit.data.utils.humanize import as_seconds
from earthkit.data.utils.humanize import interval_to_human
from earthkit.data.utils.humanize import list_to_human
from earthkit.data.utils.interval import Interval

LOG = logging.getLogger(__name__)

DOT_EARTHKIT_DATA = os.path.expanduser("~/.earthkit_data")
EARTHKIT_SETTINGS_DIR = DOT_EARTHKIT_DATA

ENV_PREFIX = "EARTHKIT_DATA_"


class Validator(metaclass=ABCMeta):
    @abstractmethod
    def check(self, value):
        pass

    @abstractmethod
    def explain(self):
        pass

    @staticmethod
    def make(value):
        v = _validators.get(type(value), None)
        if v is not None:
            return v(value)
        else:
            raise TypeError(f"Cannot create Validator for type={type(value)}")


class ValueValidator(Validator):
    def __init__(self, value):
        self.value = value

    def check(self, value):
        return value == self.value

    def explain(self):
        return f"Valid when = {self.value}."


class IntervalValidator(Validator):
    def __init__(self, interval):
        self.interval = interval

    def check(self, value):
        return value in self.interval

    def explain(self):
        return f"Valid when {interval_to_human(self.interval)}."


class ListValidator(Validator):
    def __init__(self, values):
        self.values = values

    def check(self, value):
        return value in self.values

    def explain(self):
        return f"Valid values: {list_to_human(self.values)}."


_validators = {Interval: IntervalValidator, bool: ValueValidator, list: ListValidator}


class Setting:
    def __init__(
        self,
        default,
        description,
        getter=None,
        none_ok=False,
        kind=None,
        docs_default=None,
        validator=None,
    ):
        self.default = default
        self.description = description
        self.getter = getter
        self.none_ok = none_ok
        self.kind = kind if kind is not None else type(default)
        self.docs_default = docs_default if docs_default is not None else self.default
        self.validator = validator

    def kind(self):
        return type(self.default)

    def save(self, name, value, f):
        for n in self.docs_description.split("\n"):
            print(f"# {n.strip()}", file=f)
        print(file=f)
        comment = yaml.dump({name: self.default}, default_flow_style=False)
        for n in comment.split("\n"):
            if n:
                print(f"# {n}", file=f)
        if value != self.default:
            print(file=f)
            yaml.dump({name: value}, f, default_flow_style=False)

    @property
    def docs_description(self):
        d = self.description
        t = ""
        if self.validator:
            t = self.validator.explain()

        return d.replace("{validator}", t)

    def validate(self, name, value):
        if self.validator is not None and not self.validator.check(value):
            raise ValueError(f"Settings {name} cannot be set to {value}. {self.validator.explain()}")


_ = Setting


SETTINGS_AND_HELP = {
    "user-cache-directory": _(
        os.path.join(tempfile.gettempdir(), "earthkit-data-%s" % (getpass.getuser(),)),
        """Cache directory used when ``cache-policy`` is ``user``.
        See :doc:`/guide/caching` for more information.""",
        docs_default=os.path.join("TMP", "earthkit-data-%s" % (getpass.getuser(),)),
    ),
    "temporary-cache-directory-root": _(
        None,
        """Parent of the cache directory when ``cache-policy`` is ``temporary``.
        See :doc:`/guide/caching` for more information.""",
        getter="_as_str",
        none_ok=True,
    ),
    "temporary-directory-root": _(
        None,
        """Parent of the temporary directory when ``cache-policy`` is ``off``.
        See :doc:`/guide/caching` for more information.""",
        getter="_as_str",
        none_ok=True,
    ),
    "number-of-download-threads": _(
        5,
        """Number of threads used to download data.""",
        getter="_as_int",
    ),
    "cache-policy": _(
        "off",
        """Caching policy. {validator}
        See :doc:`/guide/caching` for more information. """,
        validator=ListValidator(["off", "temporary", "user"]),
    ),
    "use-message-position-index-cache": _(
        False,
        "Stores message offset index for GRIB/BUFR files in the cache.",
    ),
    "maximum-cache-size": _(
        None,
        """Maximum disk space used by the earthkit-data cache (e.g.: 100G or 2T).
        Can be set to None.""",
        getter="_as_bytes",
        none_ok=True,
    ),
    "maximum-cache-disk-usage": _(
        "95%",
        """Disk usage threshold after which earthkit-data expires older cached
        entries (% of the full disk capacity). Can be set to None.
        See :ref:`caching` for more information.""",
        getter="_as_percent",
        none_ok=True,
    ),
    "url-download-timeout": _(
        "30s",
        """Timeout when downloading from an url.""",
        getter="_as_seconds",
    ),
    "check-out-of-date-urls": _(
        True,
        "Perform a HTTP request to check if the remote version of a cache file has changed",
    ),
    "download-out-of-date-urls": _(
        False,
        "Re-download URLs when the remote version of a cached file as been changed",
    ),
    "use-standalone-mars-client-when-available": _(
        True,
        "Use the standalone mars client when available instead of using the web API.",
    ),
    "reader-type-check-bytes": _(
        64,
        """Number of bytes read from the beginning of a source to identify its type.
        {validator}""",
        getter="_as_int",
        validator=IntervalValidator(Interval(8, 4096)),
    ),
    "grib-field-policy": _(
        "persistent",
        """GRIB field management policy for fieldlists with data on disk.  {validator}
        See :doc:`/guide/misc/grib_memory` for more information.""",
        validator=ListValidator(["persistent", "temporary"]),
    ),
    "grib-handle-policy": _(
        "cache",
        """GRIB handle management policy for fieldlists with data on disk.  {validator}
        See :doc:`/guide/misc/grib_memory` for more information.""",
        validator=ListValidator(["cache", "persistent", "temporary"]),
    ),
    "grib-handle-cache-size": _(
        1,
        """Maximum number of GRIB handles cached in memory per fieldlist with data on disk.
        Used when ``grib-handle-policy`` is ``cache``.
        See :doc:`/guide/misc/grib_memory` for more information.""",
        getter="_as_int",
        none_ok=True,
    ),
    "use-grib-metadata-cache": _(
        True,
        """Use in-memory cache kept in each field for GRIB metadata access in
        fieldlists with data on disk.
        See :doc:`/guide/misc/grib_memory` for more information.""",
    ),
}


NONE = object()
DEFAULTS = {}
for k, v in SETTINGS_AND_HELP.items():
    DEFAULTS[k] = v.default


@contextmanager
def new_settings(s):
    """Context manager to create new settings"""
    SETTINGS._stack.append(s)
    SETTINGS._notify()
    try:
        yield None
    finally:
        SETTINGS._stack.pop()
        SETTINGS._notify()


def forward(func):
    @functools.wraps(func)
    def wrapped(self, *args, **kwargs):
        if self._stack:
            return func(self._stack[-1], *args, **kwargs)
        return func(self, *args, **kwargs)

    return wrapped


def save_settings(path, settings):
    LOG.debug("Saving settings")
    from filelock import FileLock

    lock = path + ".lock"
    with FileLock(lock):
        with open(path, "w") as f:
            print("# This file is automatically generated", file=f)
            print(file=f)

            for k, v in sorted(settings.items()):
                h = SETTINGS_AND_HELP.get(k)
                if h:
                    print(file=f)
                    print("#", "-" * 76, file=f)
                    h.save(k, v, f)

            print(file=f)
            print("#", "-" * 76, file=f)
            print("# Version of earthkit-data", file=f)
            print(file=f)
            yaml.dump({"version": VERSION}, f, default_flow_style=False)
            print(file=f)
    try:
        os.unlink(lock)
    except OSError:
        pass


def env_var_name(name):
    return ENV_PREFIX + name.upper().replace("-", "_")


class Settings:
    _auto_save_settings = True
    _notify_enabled = True

    def __init__(self, settings_yaml: str, defaults: dict, callbacks=[]):
        self._defaults = defaults
        self._settings = dict(**defaults)
        self._callbacks = [c for c in callbacks]
        self._settings_yaml = settings_yaml
        self._pytest = None
        self._stack = []

    @forward
    def get(self, name: str, default=NONE):
        """[summary]

        Parameters
        ----------
            name: str
                [description]
            default: [type]
                [description]. Defaults to NONE.

        Returns
        -------
            [type]: [description]
        """
        if name not in SETTINGS_AND_HELP:
            raise KeyError("No setting name '%s'" % (name,))

        settings_item = SETTINGS_AND_HELP[name]

        getter, none_ok = (
            settings_item.getter,
            settings_item.none_ok,
        )
        if getter is None:
            getter = lambda name, value, none_ok: value  # noqa: E731
        else:
            getter = getattr(self, getter)

        st, value, _ = self._env(name)
        if not st:
            if default is NONE:
                value = self._settings[name]
            else:
                value = self._settings.get(name, default)

        return getter(name, value, none_ok)

    @forward
    def set(self, *args, **kwargs):
        """[summary]

        Parameters
        ----------
            name: str
                [description]
            value: [type]
                [description]
        """
        if len(args) == 0:
            assert len(kwargs) > 0
            for k, v in kwargs.items():
                self._set(k.replace("_", "-"), v)
            self._changed()
        else:
            if len(args) == 1 and isinstance(args[0], dict):
                for k, v in args[0].items():
                    self._set(k, v)
            else:
                self._set(*args, **kwargs)
        self._changed()

    def _set(self, name: str, *args, **kwargs):
        """[summary]

        Parameters
        ----------
            name: str
                [description]
            value: [type]
                [description]
        """
        if name not in SETTINGS_AND_HELP:
            raise KeyError("No setting name '%s'" % (name,))

        if self._has_env(name):
            msg = (
                f"Setting '{name}' is also set by environment variable '{env_var_name(name)}'."
                "The environment variable takes precedence and its value is returned when calling get()."
            )
            if self._auto_save_settings:
                msg += " Still, the value set here will be saved to the settings file."
            warnings.warn(msg)

        settings_item = SETTINGS_AND_HELP[name]

        klass = settings_item.kind

        if klass in (bool, int, float, str):
            # TODO: Proper exceptions
            assert len(args) == 1
            assert len(kwargs) == 0
            value = args[0]
            value = klass(value)

        if klass is list:
            assert len(args) > 0
            assert len(kwargs) == 0
            value = list(args)
            if len(args) == 1 and isinstance(args[0], list):
                value = args[0]

        if klass is dict:
            assert len(args) <= 1
            if len(args) == 0:
                assert len(kwargs) > 0
                value = kwargs

            if len(args) == 1:
                assert len(kwargs) == 0
                value = args[0]

        getter, none_ok = (
            settings_item.getter,
            settings_item.none_ok,
        )
        if getter is not None:
            assert len(args) == 1
            assert len(kwargs) == 0
            value = args[0]
            # Check if value is properly formatted for getter
            getattr(self, getter)(name, value, none_ok)
        else:
            if not isinstance(value, klass):
                raise TypeError("Setting '%s' must be of type '%s'" % (name, klass))

        settings_item.validate(name, value)
        self._settings[name] = value

        LOG.debug(f"_set {name}={value} stack_size={len(self._stack)}")

    @forward
    def reset(self, name: str = None):
        """Reset setting(s) to default values.

        Parameters
        ----------
            name: str, optional
                The name of the setting to reset to default. If the setting
                does not have a default, it is removed. If `None` is passed, all settings are
                reset to their default values. Defaults to None.
        """
        if name is None:
            self._settings = dict(**DEFAULTS)
        else:
            if name not in DEFAULTS:
                raise KeyError("No setting name '%s'" % (name,))

            self._settings.pop(name, None)
            if name in DEFAULTS:
                if self._has_env(name):
                    msg = (
                        f"Setting '{name}' is also set by environment variable '{env_var_name(name)}'."
                        "The environment variable takes precedence and its value is returned when calling get()."
                    )
                    if self._auto_save_settings:
                        msg += " Still, the value reset here will be saved to the settings file."
                    warnings.warn(msg)
                self._settings[name] = DEFAULTS[name]
        self._changed()

    @forward
    def __repr__(self):
        r = []
        env = self.env()
        for k, v in sorted(self._settings.items()):
            setting = SETTINGS_AND_HELP.get(k, None)
            default = setting.default if setting else ""
            if k in env:
                r.append(f"{k}: ({env[k][0]}={env[k][1]}, {v}, {default})")
            else:
                r.append(f"{k}: ({v}, {default})")
        return "\n".join(r)

    @forward
    def _repr_html_(self):
        html = [css("table")]
        html.append("<table class='ek'>")

        env = self.env()
        columns = ["Name", "Value", "Default"]
        html.append("<tr><th>%s</th></tr>" % ("</th><th>".join(columns)))

        for k, v in sorted(self._settings.items()):
            setting = SETTINGS_AND_HELP.get(k, None)
            default = setting.default if setting else ""
            if k in env:
                html.append(
                    "<tr><td>%s</td><td>%s=%r<br>(%r)</td><td>%r</td></tr>"
                    % (k, env[k][0], env[k][1], v, default)
                )
            else:
                html.append("<tr><td>%s</td><td>%r</td><td>%r</td></tr>" % (k, v, default))

        html.append("</table>")
        return "".join(html)

    @forward
    def dump(self):
        for k, v in sorted(self._settings.items()):
            yield ((k, v, SETTINGS_AND_HELP.get(k)))

    def _changed(self):
        if self._auto_save_settings:
            self._save()
        self._notify()

    def _notify(self):
        if self._notify_enabled:
            for cb in self._callbacks:
                cb()

    def on_change(self, callback: Callable[[], None]):
        self._callbacks.append(callback)

    def _save(self):
        if self._settings_yaml is None:
            return

        try:
            save_settings(self._settings_yaml, self._settings)
        except Exception:
            LOG.error(
                "Cannot save earthkit-data settings (%s)",
                self._settings_yaml,
                exc_info=True,
            )

    def save_as(self, path):
        try:
            save_settings(path, self._settings)
        except Exception:
            LOG.error(
                f"Cannot save earthkit-data settings ({path})",
                exc_info=True,
            )

    def _as_bytes(self, name, value, none_ok):
        return as_bytes(value, name=name, none_ok=none_ok)

    def _as_percent(self, name, value, none_ok):
        return as_percent(value, name=name, none_ok=none_ok)

    def _as_seconds(self, name, value, none_ok):
        return as_seconds(value, name=name, none_ok=none_ok)

    def _as_str(self, name, value, none_ok):
        if value is None and none_ok:
            return None
        return str(value)

    def _as_int(self, name, value, none_ok):
        if value is None and none_ok:
            return None
        if isinstance(value, str):
            value = value.replace('"', "").replace("'", "").strip()
        return int(value)

    @forward
    def temporary(self, *args, **kwargs):
        tmp = Settings(None, self._settings)
        # until the tmp object is at the top of the stack we do not want
        # notify the observers
        if len(args) > 0 or len(kwargs) > 0:
            # tmp does not have any callbacks so it will not broadcast the changes
            tmp.set(*args, **kwargs)
        tmp._callbacks = self._callbacks
        return new_settings(tmp)

    @property
    def auto_save_settings(self):
        return Settings._auto_save_settings

    @auto_save_settings.setter
    def auto_save_settings(self, v):
        Settings._auto_save_settings = v

    def env(self):
        r = {}
        for k in sorted(self._settings.keys()):
            st, value, name = self._env(k)
            if st:
                r[k] = (name, value)
        return r

    @staticmethod
    def _has_env(name):
        return env_var_name(name) in os.environ

    @staticmethod
    def _env(name):
        name = env_var_name(name)
        if name in os.environ:
            return (True, os.environ.get(name), name)
        return (False, None, None)


save = False
settings_yaml = os.path.expanduser(os.path.join(DOT_EARTHKIT_DATA, "settings.yaml"))

try:
    if not os.path.exists(DOT_EARTHKIT_DATA):
        os.mkdir(DOT_EARTHKIT_DATA, 0o700)
    if not os.path.exists(settings_yaml):
        save_settings(settings_yaml, DEFAULTS)
except Exception:
    LOG.error(
        "Cannot create earthkit-data settings directory, using defaults (%s)",
        settings_yaml,
        exc_info=True,
    )

settings = dict(**DEFAULTS)
try:
    with open(settings_yaml) as f:
        s = yaml.load(f, Loader=yaml.SafeLoader)
        if not isinstance(s, dict):
            s = {}

        settings.update(s)

    # if s != settings:
    #     save = True

    if settings.get("version") < VERSION:
        save = True

except Exception:
    LOG.error(
        "Cannot load earthkit-data settings (%s), reverting to defaults",
        settings_yaml,
        exc_info=True,
    )

SETTINGS = Settings(settings_yaml, settings)
if save:
    SETTINGS._save()
