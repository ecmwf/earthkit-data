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
sys.path.insert(0, os.path.abspath("../../src"))

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
    "nbsphinx",
    "sphinx.ext.autodoc",
    "sphinx.ext.napoleon",
    "sphinx.ext.intersphinx",
    "sphinx_issues",
    "sphinx_tabs.tabs",
    "sphinx_copybutton",
    "earthkit.data.sphinxext.xref",
    "earthkit.data.sphinxext.module_output",
]

autodoc_inherit_docstrings = True
autodoc_default_options = {
    "members": True,
    "imported-members": False,
    "undoc-members": False,
    "show-inheritance": True,
}
# Modules to hide from autodocs (relative to earthkit.data)
# These modules will not appear in the API documentation sidebar
autodocs_hidden_modules = ["version"]

autosummary_generate = True
autosummary_generate_overwrite = True
autosummary_imported_members = False

# # autodoc configuration
# autodoc_typehints = "none"

# # autoapi configuration
# autoapi_dirs = ["../src/earthkit/data"]
# autoapi_ignore = ["*/_version.py", "sphinxext/*"]
# autoapi_options = [
#     "members",
#     "undoc-members",
#     "show-inheritance",
#     "show-module-summary",
#     "inherited-members",
# ]
# autoapi_root = "_api"
# autoapi_member_order = "alphabetical"
# autoapi_add_toctree_entry = False

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
html_theme = "furo"

# Add any paths that contain custom static files (such as style sheets) here,
# relative to this directory. They are copied after the builtin static files,
# so a file named "default.css" will overwrite the builtin "default.css".
html_static_path = ["_static"]
html_css_files = ["style.css"]

# html_logo = "https://github.com/ecmwf/logos/raw/refs/heads/main/logos/earthkit/earthkit-data-dark.svg"


html_theme_options = {
    "light_css_variables": {
        "color-sidebar-background": "#131320",
        # "color-background-primary": "", # leave as default to avoid overriding the light theme background
        "color-sidebar-link-text": "#ffffff",
        "color-sidebar-brand-text": "#ffffff",
        "color-sidebar-caption-text": "#ffffff",
        "color-brand-primary": "#FCE54B",
        "color-brand-content": "#5f8dd3",
        "color-sidebar-item-background--hover": "#001F3F",
        "color-sidebar-item-expander-background--hover": "#001F3F",
    },
    "dark_css_variables": {
        "color-sidebar-background": "#131320",
        "color-background-primary": "#131320",
        "color-sidebar-link-text": "#ffffff",
        "color-sidebar-brand-text": "#ffffff",
        "color-sidebar-caption-text": "#ffffff",
        "color-brand-primary": "#FCE54B",
        "color-brand-content": "#5f8dd3",
        "color-sidebar-item-background--hover": "#001F3F",
        "color-sidebar-item-expander-background--hover": "#001F3F",
    },
    "light_logo": "earthkit-data-light.svg",
    "dark_logo": "earthkit-data-dark.svg",
    "source_repository": "https://github.com/ecmwf/earthkit-data/",
    # "source_branch": source_branch,
    "source_directory": "docs/source",
    "footer_icons": [
        {
            "name": "GitHub",
            "url": "https://github.com/ecmwf/earthkit-data",
            "html": """
                <svg stroke="currentColor" fill="currentColor" stroke-width="0" viewBox="0 0 16 16">
                    <path fill-rule="evenodd" d="M8 0C3.58 0 0 3.58 0 8c0 3.54 2.29 6.53 5.47 7.59.4.07.55-.17.55-.38 0-.19-.01-.82-.01-1.49-2.01.37-2.53-.49-2.69-.94-.09-.23-.48-.94-.82-1.13-.28-.15-.68-.52-.01-.53.63-.01 1.08.58 1.23.82.72 1.21 1.87.87 2.33.66.07-.52.28-.87.51-1.07-1.78-.2-3.64-.89-3.64-3.95 0-.87.31-1.59.82-2.15-.08-.2-.36-1.02.08-2.12 0 0 .67-.21 2.2.82.64-.18 1.32-.27 2-.27.68 0 1.36.09 2 .27 1.53-1.04 2.2-.82 2.2-.82.44 1.1.16 1.92.08 2.12.51.56.82 1.27.82 2.15 0 3.07-1.87 3.75-3.65 3.95.29.25.54.73.54 1.48 0 1.07-.01 1.93-.01 2.2 0 .21.15.46.55.38A8.013 8.013 0 0 0 16 8c0-4.42-3.58-8-8-8z"></path>
                </svg>
            """,
            "class": "",
        },
    ],
}


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
    "earthkit-utils": (
        "earthkit-utils",
        "https://github.com/ecmwf/earthkit-utils",
    ),
    "eccodes": (
        "ecCodes",
        "https://confluence.ecmwf.int/display/ECC/ecCodes+Home",
    ),
    "eccodes_namespace": (
        "ecCodes namespace",
        "https://confluence.ecmwf.int/display/UDOC/What+are+namespaces+-+ecCodes+GRIB+FAQ",
    ),
    "gribjump": ("GribJump", "https://github.com/ecmwf/gribjump"),
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


# def setup(app):
#     from skip_api_rules import _skip_api_items

#     app.connect("autoapi-skip-member", _skip_api_items)
