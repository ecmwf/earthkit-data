# (C) Copyright 2020 ECMWF.
#
# This software is licensed under the terms of the Apache Licence Version 2.0
# which can be obtained at http://www.apache.org/licenses/LICENSE-2.0.
# In applying this licence, ECMWF does not waive the privileges and immunities
# granted to it by virtue of its status as an intergovernmental organisation
# nor does it submit to any jurisdiction.
#

import json
import logging
import os
import re
import stat
from getpass import getpass

from earthkit.data.core.ipython import HTML
from earthkit.data.core.ipython import display
from earthkit.data.core.ipython import ipython_active
from earthkit.data.utils.humanize import list_to_human

LOG = logging.getLogger(__name__)


# See https://medium.com/analytics-vidhya/the-ultimate-markdown-guide-for-jupyter-notebook-d5e5abf728fd
HTML_MESSAGE = """
<div style='border: 1px solid orange; color: black;
     background-color: rgb(255, 214, 0);
     margin: 0.5em; padding: 0.5em; font-weight: bold;'>
{message}
</div>
"""

HTML_ASK = """
<div style='border: 1px solid gray; color: black;
     background-color: rgb(230, 230, 230);
     margin: 0.2em; padding: 0.2em; font-weight: bold;'>
{message}
</div>
"""

MESSAGE = """
An API key is needed to access this dataset. Please visit
{register_or_sign_in_url} to register or sign-in
then visit {retrieve_api_key_url} to retrieve you API key.
"""

RC_MESSAGE_BASE = """
You can store the credentials in {rcfile}; if you follow the
instructions below it will be automatically done for you.
"""

RC_MESSAGE_EXT = """
You can store the credentials in {rcfile} or in the file
pointed by the {rcfile_env} environment variable. If you follow
the instructions below {rcfile} will be automatically created
for you.
"""


class RegexValidate:
    def __init__(self, pattern):
        self.pattern = pattern

    def __call__(self, value):
        if not re.fullmatch(self.pattern, value):
            raise ValueError(f"Value={value} does not match pattern={self.pattern}")
        return value


class Prompt:
    def __init__(self, owner):
        self.owner = owner

    def _rc_message(self):
        if self.owner.rcfile:
            if self.owner.rcfile_env:
                return RC_MESSAGE_EXT.format(rcfile=self.owner.rcfile, rcfile_env=self.owner.rcfile_env)
            else:
                if hasattr(self.owner, "rc_message_base"):
                    return self.owner.rc_message_base.format(rcfile=self.owner.rcfile)
                else:
                    return RC_MESSAGE_BASE.format(rcfile=self.owner.rcfile)

        return ""

    def _config_env_message(self):
        ev = self.owner.config_env
        if ev:
            plural = "s" if len(ev) > 1 else ""
            return (
                f" Alternatively, you can use the {list_to_human(ev)}"
                f" environment variable{plural} to specify the credentials."
            )
        return ""

    def ask_user(self):
        self.print_message()

        result = {}

        for p in self.owner.prompts:
            method = getpass if p.get("hidden", False) else input
            value = self.ask(p, method)
            value = value.strip() or p.get("default", "")

            validate = p.get("validate")
            if validate:
                if isinstance(validate, str):
                    validate = RegexValidate(validate)

                value = validate(value)

            result[p["name"]] = value

        return result


class Text(Prompt):
    def print_message(self):
        print(
            MESSAGE.format(
                register_or_sign_in_url=self.owner.register_or_sign_in_url,
                retrieve_api_key_url=self.owner.retrieve_api_key_url,
            )
            + self._rc_message()
            + self._config_env_message()
        )

    def ask(self, p, method):
        message = f"Please enter a value for '{p.get('title')}'"
        if "default" in p:
            message += f" or leave empty for the default value '{p.get('default')}'"
        message += ", then press <ENTER>"
        return method(p.get("title") + ": ").strip()


class Markdown(Prompt):
    def print_message(self):
        import markdown

        message = markdown.markdown(
            MESSAGE.format(
                register_or_sign_in_url=f"<{self.owner.register_or_sign_in_url}>",
                retrieve_api_key_url=f"<{self.owner.retrieve_api_key_url}>",
                rcfile=f"{self.owner.rcfile}",
            )
            + self._rc_message()
            + self._config_env_message()
        )
        # We use Python's markdown instead of IPython's Markdown because
        # jupyter lab/colab/deepnotes all behave differently
        display(HTML(HTML_MESSAGE.format(message=message)))

    def ask(self, p, method):
        import markdown

        message = f"Please enter a value for <span style='color: red;'>{p.get('title')}</span>"
        if "default" in p:
            message += (
                " or leave empty for the default value "
                f"<span style='color: red;'>{p.get('default')}</span>"
            )
        message += ", then press *ENTER*"
        if "example" in p:
            message += f" The value should look like  <span style='color: red;'>{p.get('example')}</span>"
        message = markdown.markdown(message)
        display(HTML(HTML_ASK.format(message=message)))
        return method(p.get("title") + ": ").strip()


class APIKeyPrompt:
    rcfile_env = None
    config_env = []

    def check(self, load=False):
        if not self.has_api_config():
            self.ask_user_and_save()

        if load:
            rcfile = self.existing_rcfile_path()
            if rcfile is not None:
                with open(rcfile) as f:
                    return self.load(f)

    def ask_user(self):
        if ipython_active:
            prompt = Markdown(self)
        else:
            prompt = Text(self)

        return self.validate(prompt.ask_user())

    def ask_user_and_save(self):
        input = self.ask_user()

        rcfile = os.path.expanduser(self.rcfile)
        with open(rcfile, "w") as f:
            self.save(input, f)

        LOG.info("API key saved to '%s'", rcfile)

        try:
            os.chmod(rcfile, stat.S_IREAD | stat.S_IWRITE)
        except OSError:
            LOG.exception("Cannot change access to rcfile")

        return input

    def save(self, input, file):
        json.dump(input, file, indent=4)

    def load(self, file):
        return json.load(file)

    def existing_rcfile_path(self):
        rcfile = os.path.expanduser(self.rcfile)
        if os.path.exists(rcfile):
            return rcfile

        if self.rcfile_env:
            rcfile = os.path.expanduser(os.getenv(self.rcfile_env, ""))
            if os.path.exists(rcfile):
                return rcfile

    def has_config_env(self):
        for ev in self.config_env:
            v = os.getenv(ev, "")
            if v is None or v == "":
                return False
        return True if len(self.config_env) > 0 else False

    def has_api_config(self):
        return self.existing_rcfile_path() is not None or self.has_config_env()

    def validate(self, input):
        return input

    def rcfile_name(self):
        return os.path.basename(os.path.expanduser(self.rcfile))
