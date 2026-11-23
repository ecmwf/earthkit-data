# (C) Copyright 2026 ECMWF.
#
# This software is licensed under the terms of the Apache Licence Version 2.0
# which can be obtained at http://www.apache.org/licenses/LICENSE-2.0.
# In applying this licence, ECMWF does not waive the privileges and immunities
# granted to it by virtue of its status as an intergovernmental organisation
# nor does it submit to any jurisdiction.
#


import importlib
import logging
import os
import shutil
import tempfile
import threading
from contextlib import contextmanager

try:
    import copernicusmarine
except ImportError:
    raise ImportError("Copernicus Marine access requires 'copernicusmarine' to be installed")

from earthkit.data.core.ipython import HTML, display, ipython_active
from earthkit.data.utils.request import FileRequestRetriever, RequestBuilder

from .file import FileSource
from .prompt import HTML_MESSAGE, APIKeyPrompt, Markdown, Text

LOG = logging.getLogger(__name__)

USERNAME_ENV = "COPERNICUSMARINE_SERVICE_USERNAME"
PASSWORD_ENV = "COPERNICUSMARINE_SERVICE_PASSWORD"
CREDENTIALS_DIRECTORY_ENV = "COPERNICUSMARINE_CREDENTIALS_DIRECTORY"
DEFAULT_CREDENTIALS_FILENAME = ".copernicusmarine-credentials"

# Credential options are not accepted as arguments or request keys. They must
# come from the environment, the library's credentials file or the prompt.
# Accepting them in a request would persist them in the cache arguments.
CREDENTIAL_KEYS = ("username", "password", "credentials_file")

# Output formats supported by this source (cache file extension).
EXTENSIONS = {"netcdf": ".nc", "csv": ".csv"}
DEFAULT_FILE_FORMAT = "netcdf"

# At least one of these keys must be specified for a request to be a subset.
SELECTION_KEYS = (
    "variables",
    "start_datetime",
    "end_datetime",
    "minimum_longitude",
    "maximum_longitude",
    "minimum_latitude",
    "maximum_latitude",
    "minimum_depth",
    "maximum_depth",
    "minimum_x",
    "maximum_x",
    "minimum_y",
    "maximum_y",
    "platform_ids",
)

# Keys controlled by the source itself. Users are not allowed to set them.
FORBIDDEN_KEYS = (
    "output_directory",
    "output_filename",
    "overwrite",
    "skip_existing",
    "dry_run",
    "disable_progress_bar",
    "request_file",
)


def _default_credentials_file():
    """Path of the library's default credentials file.

    The library honours the ``COPERNICUSMARINE_CREDENTIALS_DIRECTORY``
    environment variable (resolved when it is imported), this function
    resolves it dynamically. The content of the file is never read, only its
    existence is checked.
    """
    directory = os.environ.get(CREDENTIALS_DIRECTORY_ENV) or os.path.join("~", ".copernicusmarine")
    return os.path.join(os.path.expanduser(directory), DEFAULT_CREDENTIALS_FILENAME)


def _missing_credentials_error():
    return FileNotFoundError(
        "Copernicus Marine credentials not found. Set the "
        f"{USERNAME_ENV} and {PASSWORD_ENV} environment variables or store the "
        f"credentials in the file {_default_credentials_file()} (the directory can be "
        "changed with the "
        f"{CREDENTIALS_DIRECTORY_ENV} environment variable). Alternatively, call "
        "from_source() with prompt=True to be guided through the login process, the "
        "credentials will then be stored in that file. Credentials can be created at "
        "https://marine.copernicus.eu/"
    )


# The copernicusmarine library asks for missing credentials interactively
# (click.prompt) in this internal function. The existence pre-check in the
# prompt class cannot validate the content of a credentials file (we never
# read it), so a file with empty fields would still reach the prompt and hang
# a non interactive session. Around every ``copernicusmarine.subset()`` call,
# in the thread performing the download, the library function is replaced by
# one raising an error, making a prompt impossible. The patch is global, so it
# is applied once and reference counted with a lock: it stays active while at
# least one request is in flight (even when another parallel request has
# already failed and the retrieval was abandoned) and the original function is
# restored when the last in-flight ``subset()`` call returns.
PROMPT_MODULE = "copernicusmarine.core_functions.credentials_utils"
PROMPT_FUNCTION = "_retrieve_credential_from_prompt"

_prompt_lock = threading.Lock()
_prompt_original = None
_prompt_count = 0


class InteractivePromptError(ValueError):
    """Raised when the copernicusmarine library tries to prompt for credentials.

    earthkit-data sources never wait for interactive input inside a download.
    The library prompts when it cannot find a username or a password, e.g.
    when a credentials file exists but its fields are empty.
    """


class LibraryCompatibilityError(RuntimeError):
    """Raised when the installed copernicusmarine library does not provide the
    internal function needed to block interactive credential prompts. The
    source refuses to download anything rather than risk a hang.
    """


def _prompt_guard_incompatibility_error():
    version = getattr(copernicusmarine, "__version__", "unknown")
    return LibraryCompatibilityError(
        "cannot guard against interactive Copernicus Marine credential prompts: the installed "
        f"copernicusmarine library (version {version}) does not provide "
        f"{PROMPT_MODULE}.{PROMPT_FUNCTION}. Install a copernicusmarine version supported by "
        "earthkit-data (e.g. pip install 'earthkit-data[cmems]') or report this issue "
        "to the earthkit-data project."
    )


def _raise_instead_of_prompt(credential_type=None, *args, **kwargs):
    name = credential_type if credential_type in ("username", "password") else "username or password"
    raise InteractivePromptError(
        f"Copernicus Marine asked for the {name} interactively, which is not supported. Check "
        f"that the credentials are complete: set the {USERNAME_ENV} and {PASSWORD_ENV} "
        f"environment variables or use a credentials file ({_default_credentials_file()}) "
        "containing both a username and a password."
    )


def _install_prompt_guard():
    """Replace the library prompt; return the information needed to undo it.

    Raises ``LibraryCompatibilityError`` when the guard cannot be installed:
    downloading must never proceed unprotected.
    """
    try:
        module = importlib.import_module(PROMPT_MODULE)
    except ImportError:
        raise _prompt_guard_incompatibility_error() from None

    original = getattr(module, PROMPT_FUNCTION, None)
    if original is None:
        raise _prompt_guard_incompatibility_error()

    setattr(module, PROMPT_FUNCTION, _raise_instead_of_prompt)
    return (module, original)


@contextmanager
def _no_interactive_prompt():
    """Make the copernicusmarine library unable to prompt for credentials.

    Safe to enter from several download threads: the patch is applied by the
    first entrant and removed only when the last user leaves the context.
    """
    global _prompt_original, _prompt_count

    with _prompt_lock:
        if _prompt_count == 0:
            # on failure this raises and the state below stays untouched
            _prompt_original = _install_prompt_guard()
        _prompt_count += 1
    try:
        yield
    finally:
        with _prompt_lock:
            _prompt_count -= 1
            if _prompt_count == 0:
                module, original = _prompt_original
                setattr(module, PROMPT_FUNCTION, original)
                _prompt_original = None


class PromptMessage(Text):
    """Text mode prompt with a Copernicus Marine specific introduction."""

    MESSAGE = """
Copernicus Marine credentials are needed to access this dataset. Please visit
{register_or_sign_in_url} to register or sign-in, then find your username and
password in your account (see {retrieve_api_key_url}).
"""

    def print_message(self):
        print(
            self.MESSAGE.format(
                register_or_sign_in_url=self.owner.register_or_sign_in_url,
                retrieve_api_key_url=self.owner.retrieve_api_key_url,
            )
            + self._rc_message()
            + self._config_env_message()
        )


class PromptMarkdownMessage(Markdown):
    """Markdown mode prompt with a Copernicus Marine specific introduction."""

    MESSAGE = PromptMessage.MESSAGE

    def print_message(self):
        import markdown

        message = markdown.markdown(
            self.MESSAGE.format(
                register_or_sign_in_url=f"<{self.owner.register_or_sign_in_url}>",
                retrieve_api_key_url=f"<{self.owner.retrieve_api_key_url}>",
            )
            + self._rc_message()
            + self._config_env_message()
        )
        display(HTML(HTML_MESSAGE.format(message=message)))


class CMEMSAPIKeyPrompt(APIKeyPrompt):
    """Ask for the Copernicus Marine username and password.

    The credentials are not written by this class: they are stored with
    ``copernicusmarine.login()`` so that the library writes its own
    credentials file format. The file is never read, only its existence is
    checked.
    """

    register_or_sign_in_url = "https://marine.copernicus.eu/"
    retrieve_api_key_url = (
        "https://help.marine.copernicus.eu/en/articles/4444552-i-forgot-my-username-or-my-password-what-should-i-do"
    )

    prompts = [
        dict(name="username", title="Username", validate=r"\S.*"),
        dict(name="password", title="Password", hidden=True, validate=r".+"),
    ]

    config_env = (USERNAME_ENV, PASSWORD_ENV)

    @property
    def rcfile(self):
        """Path of the library's default credentials file (display only)."""
        return _default_credentials_file()

    def existing_rcfile_path(self):
        path = _default_credentials_file()
        if os.path.isfile(path):
            return path
        return None

    def ask_user(self):
        if ipython_active:
            prompt = PromptMarkdownMessage(self)
        else:
            prompt = PromptMessage(self)

        return self.validate(prompt.ask_user())

    def ask_user_and_save(self):
        answers = self.ask_user()

        # Let the library write its own credentials file. login() honours the
        # COPERNICUSMARINE_CREDENTIALS_DIRECTORY environment variable (it is
        # resolved when the library is imported) and never prompts because
        # both the username and the password are given. The password is never
        # logged.
        stored = copernicusmarine.login(
            username=answers["username"],
            password=answers["password"],
            force_overwrite=True,
            check_credentials_valid=False,
        )
        if not stored:
            raise RuntimeError(
                "Copernicus Marine login failed: the credentials were not stored in "
                f"{_default_credentials_file()}. Check your username and password."
            )

        LOG.info("Copernicus Marine credentials stored in '%s'", _default_credentials_file())

        return answers


def _collect_requests(request):
    """Return the request dictionaries found in ``request``.

    The returned dictionaries are copies, so they can be modified without
    affecting the caller's objects.
    """
    items = request if isinstance(request, (list, tuple)) else [request]

    requests = []
    for item in items:
        if not isinstance(item, dict):
            raise TypeError(f"cmems: requests must be dictionaries! type={type(item)}")
        requests.append(dict(item))

    return requests


def _validate_request(request):
    for key in CREDENTIAL_KEYS:
        if request.get(key) is not None:
            raise ValueError(
                f"cmems: the {key!r} parameter is not supported. Credentials "
                f"are taken from the {USERNAME_ENV} and {PASSWORD_ENV} environment "
                "variables, the default credentials file or the interactive prompt "
                "(prompt=True)"
            )

    file_format = request.get("file_format", DEFAULT_FILE_FORMAT)
    if file_format not in EXTENSIONS:
        raise ValueError(
            f"cmems: unsupported file format: {file_format!r}. Supported formats are {sorted(EXTENSIONS)}."
        )

    for key in FORBIDDEN_KEYS:
        if request.get(key) is not None:
            raise ValueError(
                f"cmems: the {key!r} parameter is controlled by the source and cannot be set in the request"
            )

    if not any(request.get(key) is not None for key in SELECTION_KEYS):
        raise ValueError(
            "cmems: missing subset selection. At least one of 'variables', "
            "'start_datetime'/'end_datetime', the longitude/latitude or depth ranges or "
            "'minimum_x'/'maximum_x'/'minimum_y'/'maximum_y' must be specified"
        )


class CMEMSRetriever(FileSource):
    """Retrieve a subset of a Copernicus Marine dataset.

    Signature::

        CMEMSRetriever(dataset, *, request, prompt=True)

    Parameters
    ----------
    dataset : str
        The Copernicus Marine dataset id.
    request : dict or list/tuple of dict
        A single request dictionary or a list/tuple of request dictionaries.
        Required, keyword-only. It contains the options passed to
        ``copernicusmarine.subset()``, the ``file_format`` key ("netcdf" or
        "csv", by default "netcdf") and may contain the ``split_on`` key and a
        ``dataset`` or ``dataset_id`` key equal to the positional argument.
    prompt : bool
        When True (default) and no credentials are found (the
        ``COPERNICUSMARINE_SERVICE_USERNAME`` and
        ``COPERNICUSMARINE_SERVICE_PASSWORD`` environment variables or the
        library's default credentials file), the user is asked for a username
        and a password and they are stored in the credentials file. When
        False no question is asked and an error is raised when no credentials
        can be found.
    """

    sphinxdoc = """
    CMEMSRetriever

    Signature::

        from_source("cmems", dataset, *, request, prompt=True)
    """

    def __init__(self, dataset, *, request, prompt=True):
        super().__init__()

        if not isinstance(dataset, str):
            raise TypeError(f"cmems: dataset must be a string! type={type(dataset)}")

        self.prompt = prompt

        requests = _collect_requests(request)
        for r in requests:
            for key in ("dataset", "dataset_id"):
                if r.get(key) is not None and r[key] != dataset:
                    raise ValueError(f"cmems: conflicting values for {key!r}: {dataset!r} and {r[key]!r}")
            # ``dataset_id`` is the name of the library option: it is always
            # added by the request builder below, so the user-facing key is
            # removed and ``subset()`` only receives ``dataset_id``.
            r.pop("dataset", None)

        request_builder = RequestBuilder(
            self, *requests, request=None, normaliser=self._normalise_request, dataset_id=dataset
        )
        self.request = request_builder.requests

        for r in self.request:
            _validate_request(r)

        # Credentials are only needed when a file has to be downloaded: a
        # cache hit must work without them. The lock and the flag make sure
        # the user is asked at most once, even when several requests are
        # downloaded in parallel.
        self._credentials_lock = threading.Lock()
        self._credentials_checked = False

        # Download each request in parallel when the config allows it
        retriever = FileRequestRetriever(self, retriever=self._retrieve_one)
        self.path = retriever.retrieve(self.request)

    def _ensure_credentials(self):
        """Check that credentials are available, prompting the user once.

        Called from the download threads, only for requests which are not
        cached. When ``self.prompt`` is False no question is asked and a
        ``FileNotFoundError`` is raised if no credentials can be found. The
        password is never logged.
        """
        with self._credentials_lock:
            if self._credentials_checked:
                return

            prompt = CMEMSAPIKeyPrompt()
            if not prompt.has_api_config():
                if not self.prompt:
                    raise _missing_credentials_error()
                # asks for the username (visible) and the password (hidden)
                # and stores them with copernicusmarine.login()
                prompt.ask_user_and_save()

            self._credentials_checked = True

    def _retrieve_one(self, request):
        extension = EXTENSIONS[request.get("file_format", DEFAULT_FILE_FORMAT)]

        def retrieve(target, args):
            # Only checked when the file has to be downloaded: a cache hit
            # must work without credentials.
            self._ensure_credentials()

            # ``subset()`` appends the format extension to a filename which
            # does not already end with it, so we download into a temporary
            # directory with a matching file name and move the result onto
            # the cache target (which typically ends with ".tmp").
            output_directory = tempfile.mkdtemp(prefix="cmems-")
            try:
                # the guard is applied per request, in the download thread,
                # and reference counted: it cannot be removed while another
                # request is still inside subset(), even when this retrieval
                # has already been abandoned because of a failure elsewhere
                with _no_interactive_prompt():
                    response = copernicusmarine.subset(
                        **args,
                        output_directory=output_directory,
                        output_filename=f"cmems-subset{extension}",
                        overwrite=True,
                        disable_progress_bar=True,
                    )

                file_path = os.fspath(response.file_path)
                if not os.path.isabs(file_path):
                    outdir = getattr(response, "output_directory", None) or output_directory
                    file_path = os.path.join(os.fspath(outdir), file_path)

                shutil.move(file_path, target)
            finally:
                shutil.rmtree(output_directory, ignore_errors=True)

        return self._cache_file(retrieve, request, extension=extension)

    @staticmethod
    def _normalise_request(**kwargs):
        # Normalise dates to strings so the cache key is stable
        for key in ("start_datetime", "end_datetime"):
            value = kwargs.get(key)
            if value is not None and not isinstance(value, str):
                kwargs[key] = value.isoformat() if hasattr(value, "isoformat") else str(value)

        # Make the file format explicit so the cache extension and the format
        # used by ``subset()`` can never diverge
        file_format = kwargs.pop("file_format", None)
        if file_format is None:
            file_format = DEFAULT_FILE_FORMAT
        if isinstance(file_format, str):
            file_format = file_format.lower()
        kwargs["file_format"] = file_format

        return kwargs

    # TODO: review if we need this property
    @property
    def requests(self):
        return self.request
