#!/usr/bin/env python
# Copyright (c) 2016-present, Gregory Szorc
# All rights reserved.
#
# This software may be modified and distributed under the terms
# of the BSD license. See the LICENSE file for details.

from __future__ import print_function

import os
import sys

from setuptools import setup

if sys.version_info[0:2] < (3, 12):
    print("Python 3.12+ is required", file=sys.stderr)
    sys.exit(1)

ext_suffix = os.environ.get("SETUPTOOLS_EXT_SUFFIX")
if ext_suffix:
    import sysconfig

    # setuptools._distutils.command.build_ext doesn't use
    # SETUPTOOLS_EXT_SUFFIX like setuptools.command.build_ext does.
    # Work around the issue so that cross-compilation can work
    # properly.
    sysconfig.get_config_vars()["EXT_SUFFIX"] = ext_suffix
    try:
        # Older versions of python didn't have EXT_SUFFIX, and setuptools
        # sets its own value, but since we've already set one, we don't
        # want setuptools to overwrite it.
        import setuptools._distutils.compat.py39 as py39compat
    except ImportError:
        try:
            import setuptools._distutils.py39compat as py39compat
        except ImportError:
            py39compat = None
    if py39compat:
        py39compat.add_ext_suffix = lambda vars: None

sys.path.insert(0, ".")

import setup_zstd  # noqa: E402

SUPPORT_LEGACY = False
SYSTEM_ZSTD = False
WARNINGS_AS_ERRORS = False
C_BACKEND = True
RUST_BACKEND = False

if os.environ.get("ZSTD_WARNINGS_AS_ERRORS", ""):
    WARNINGS_AS_ERRORS = True

if "--legacy" in sys.argv:
    SUPPORT_LEGACY = True
    sys.argv.remove("--legacy")

if "--system-zstd" in sys.argv:
    SYSTEM_ZSTD = True
    sys.argv.remove("--system-zstd")

if "--warnings-as-errors" in sys.argv:
    WARNINGS_AS_ERRORS = True
    sys.argv.remove("--warning-as-errors")

if "--no-c-backend" in sys.argv:
    C_BACKEND = False
    sys.argv.remove("--no-c-backend")

if "--rust-backend" in sys.argv:
    RUST_BACKEND = True
    sys.argv.remove("--rust-backend")

# Code for obtaining the Extension instance is in its own module to
# facilitate reuse in other projects.
extensions = []

if C_BACKEND:
    extensions.append(
        setup_zstd.get_c_extension(
            support_legacy=SUPPORT_LEGACY,
            system_zstd=SYSTEM_ZSTD,
            warnings_as_errors=WARNINGS_AS_ERRORS,
        )
    )

if RUST_BACKEND:
    extensions.append(setup_zstd.get_rust_extension())

version = None

with open("c-ext/hyperlight-zstandard.h", "r") as fh:
    for line in fh:
        if not line.startswith("#define HYPERLIGHT_ZSTANDARD_VERSION"):
            continue

        version = line.split()[2][1:-1]
        break

if not version:
    raise Exception(
        "could not resolve package version; this should never happen"
    )

setup(
    name="zstandard",
    version=version,
    packages=["zstandard"],
    package_data={"zstandard": ["__init__.pyi", "py.typed"]},
    ext_modules=extensions,
    cmdclass={"build_ext": setup_zstd.RustBuildExt},
    test_suite="tests",
    tests_require=["hypothesis"],
)
