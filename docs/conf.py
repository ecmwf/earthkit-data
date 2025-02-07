# Configuration file for the Sphinx documentation builder.
#
# This file only contains a selection of the most common options. For a full
# list see the documentation:
# https://www.sphinx-doc.org/en/master/usage/configuration.html

# -- Import and path setup ---------------------------------------------------

import datetime
import os
import sys

sys.path.insert(0, os.path.abspath("./"))
sys.path.insert(0, os.path.abspath("../"))

# -- Project information -----------------------------------------------------

project = "earthkit-data"
author = "European Centre for Medium Range Weather Forecasts"

year = datetime.datetime.now().year
years = "2022-%s" % (year,)
copyright = "%s, European Centre for Medium-Range Weather Forecasts (ECMWF)" % (years,)

# version = earthkit.data.__version__
# release = earthkit.data.__version__

# -- General configuration ---------------------------------------------------

# Add any Sphinx extension module names here, as strings. They can be
# extensions coming with Sphinx (named 'sphinx.ext.*') or your custom
# ones.
extensions = [
    "sphinx_rtd_theme",
    "nbsphinx",
    "sphinx.ext.autodoc",
    "sphinx.ext.napoleon",
    "sphinx.ext.intersphinx",
    "autoapi.extension",
    "sphinx_issues",
    "sphinx_tabs.tabs",
    "sphinx_copybutton",
    "earthkit.data.sphinxext.xref",
    "earthkit.data.sphinxext.module_output",
]

# autodoc configuration
autodoc_typehints = "none"

# autoapi configuration
autoapi_dirs = ["../src/earthkit/data"]
autoapi_ignore = ["*/_version.py", "sphinxext/*"]
autoapi_options = [
    "members",
    "undoc-members",
    "show-inheritance",
    "show-module-summary",
    "inherited-members",
]
autoapi_root = "_api"
autoapi_member_order = "alphabetical"
autoapi_add_toctree_entry = False

# napoleon configuration
napoleon_google_docstring = False
napoleon_numpy_docstring = True
napoleon_preprocess_types = True

# Path to GitHub repo {group}/{project}  (note that `group` is the GitHub user or organization)
issues_github_path = "ecmwf/earthkit-data"

# sphinx_tabs configuration
# sphinx_tabs_disable_css_loading = True

# Add any paths that contain templates here, relative to this directory.
templates_path = ["_templates"]

# List of patterns, relative to source directory, that match files and
# directories to ignore when looking for source files.
# This pattern also affects html_static_path and html_extra_path.
exclude_patterns = ["_build", "Thumbs.db", ".DS_Store"]

# The suffix of source filenames.
source_suffix = ".rst"

# -- Options for HTML output -------------------------------------------------

# The theme to use for HTML and HTML Help pages.  See the documentation for
# a list of builtin themes.
#
html_theme = "sphinx_rtd_theme"

# Add any paths that contain custom static files (such as style sheets) here,
# relative to this directory. They are copied after the builtin static files,
# so a file named "default.css" will overwrite the builtin "default.css".
html_static_path = ["_static"]
html_css_files = ["style.css"]

html_logo = "https://github.com/ecmwf/logos/raw/refs/heads/main/logos/earthkit/earthkit-data-dark.svg"

xref_links = {
    "botocore": ("botocore", "https://botocore.amazonaws.com/v1/documentation/api/latest/index.html"),
    "cfgrib": ("cfgirb", "https://github.com/ecmwf/cfgrib"),
    "covjsonkit": ("covjsonkit", "https://github.com/ecmwf/covjsonkit"),
    "earthkit": ("earthkit", "https://earthkit.readthedocs.io/en/latest/"),
    "earthkit-geo": (
        "earthkit-geo",
        "https://earthkit-geo.readthedocs.io/en/latest/",
    ),
    "earthkit-regrid": (
        "earthkit-regrid",
        "https://earthkit-regrid.readthedocs.io/en/latest/",
    ),
    "eccodes": (
        "ecCodes",
        "https://confluence.ecmwf.int/display/ECC/ecCodes+Home",
    ),
    "eccodes_namespace": (
        "ecCodes namespace",
        "https://confluence.ecmwf.int/display/UDOC/What+are+namespaces+-+ecCodes+GRIB+FAQ",
    ),
    "pdbufr": ("pdbufr", "https://github.com/ecmwf/pdbufr"),
    "read_bufr": (
        "pdbufr.read_bufr()",
        "https://pdbufr.readthedocs.io/en/latest/read_bufr.html",
    ),
    "odb": ("ODB", "https://odc.readthedocs.io/en/latest/content/introduction.html"),
    "pyodc": ("pyodc", "https://github.com/ecmwf/pyodc"),
    "s3cmd": ("s3cmd", "https://s3tools.org/s3cmd"),
}


intersphinx_mapping = {
    "pandas": ("https://pandas.pydata.org/docs/", None),
    "xarray": ("https://docs.xarray.dev/en/latest/", None),
}


def setup(app):
    from skip_api_rules import _skip_api_items

    app.connect("autoapi-skip-member", _skip_api_items)
