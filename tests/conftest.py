import pytest

SKIP = {
    "short": ["download", "ftp", "long_test", "ecfs"],
    "long": ["ftp", "ecfs"],
    "release": [],
    "documentation": None,
}

# Import all fixtures from list of plugins
pytest_plugins = [
    "list_of_dicts.lod_fixtures",
]


def pytest_configure(config):
    pytest.CDS_TIMEOUT = config.getoption("--cds-timeout")


def pytest_addoption(parser):
    help_str = "NAME: short, long, release, documentation. Runs a subset of tests.\n"
    for k, v in SKIP.items():
        if v:
            help_str += f"'{k}': skip tests marked as {','.join(v)}.\n"
        else:
            help_str += f"'{k}': do not skip tests.\n"

    parser.addoption(
        "-E",
        action="store",
        metavar="NAME",
        default="short",
        help=help_str,
    )

    parser.addoption(
        "--cds-timeout",
        action="store",
        metavar="TIMEOUT",
        default=30,
        help="Timeout in seconds for cds tests. 0 means no timeout. Default is 30.",
    )


def pytest_runtest_setup(item):
    # print(f"config {item.config.option}")
    flag = item.config.getoption("-E")
    marks_to_skip = SKIP[flag]

    marks_in_items = list([m.name for m in item.iter_markers()])

    if marks_to_skip is None:
        if flag not in marks_in_items:
            pytest.skip(f"test is skipped because custom pytest option : -E {flag}")
        return

    for m in marks_in_items:
        if m in marks_to_skip:
            pytest.skip(f"test is skipped because custom pytest option: -E {flag}")

    marked_no_cache_init = "no_cache_init" in marks_in_items
    if marked_no_cache_init and not item.config.getoption("--forked"):
        pytest.skip("test is skipped because marked as no_cache_init but --forked is not used")

    need_cache = "cache" in marks_in_items

    # settings
    from earthkit.data import config

    # ensure settings are not saved automatically
    config.autosave = False

    # ensure all the tests use the default settings
    if marked_no_cache_init:
        # do not broadcast setting changes, otherwise
        # the cache would be initialised
        config._notify_enabled = False
        config.reset()
        config._notify_enabled = True
    elif need_cache:
        config.reset()
        config.set("cache-policy", "user")
    else:
        config.reset()
