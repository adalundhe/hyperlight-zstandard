.. _installing:

==========
Installing
==========

This package is uploaded to PyPI at https://pypi.python.org/pypi/zstandard.
So, to install this package::

   $ pip install zstandard

Binary wheels are made available for some platforms. If you need to
install from a source distribution, all you should need is a working C
compiler and the Python development headers/libraries. On many Linux
distributions, you can install a ``python-dev`` or ``python-devel``
package to provide these dependencies.

Packages are also uploaded to Anaconda Cloud at
https://anaconda.org/indygreg/zstandard. See that URL for how to install
this package with ``conda``.

Requirements
============

This package is designed to run with Python 3.12, 3.13, and 3.14
on common platforms (Linux, Windows, and macOS). x86_64 and arm64
are well-tested on all platforms.

Backends
========

This package provides two backends:

**C Backend (Primary)**
   The default backend, implemented as a C extension using the Python C API.
   This backend supports Python subinterpreters (Python 3.12+) and free-threaded
   Python (Python 3.13+).

**Rust Backend (Fallback)**
   An alternative backend implemented in Rust using PyO3. The Rust backend
   is automatically used as a fallback when the C backend is unavailable
   (e.g., when building from source on a system without a C compiler but
   with Rust tooling). The Rust backend also supports subinterpreters
   via multi-phase initialization (PEP 489).

   To build the Rust backend from source, you need Rust and Cargo installed.

Legacy Format Support
=====================

To enable legacy zstd format support which is needed to handle files compressed
with zstd < 1.0 you need to provide an installation option::

   $ pip install zstandard --config-settings='--global-option=--legacy'

All Install Arguments
=====================

``setup.py`` accepts the following arguments for influencing behavior:

``--legacy``
   Enable legacy zstd format support in order to read files produced with
   zstd < 1.0.

``--system-zstd``
   Attempt to link against the zstd library present on the system instead
   of the version distributed with the extension.

``--warning-as-errors``
   Treat all compiler warnings as errors.

``--no-c-backend``
   Do not compile the C-based backend.

``--rust-backend``
   Compile the Rust backend. The Rust backend supports subinterpreters
   via multi-phase initialization (PEP 489).

Packaging tools newer than ~2023 likely require using a PEP 517
build backend instead of invoking ``setup.py`` directly. In order to send
custom arguments to our ``setup.py``, you need to use ``--config-settings``.
e.g. ``python3 -m pip install zstandard --config-settings='--global-option=--rust-backend'``.

In addition, the following environment variables are recognized:

``ZSTD_EXTRA_COMPILER_ARGS``
   Extra compiler arguments to compile the C backend with.

``ZSTD_WARNINGS_AS_ERRORS``
   Equivalent to ``setup.py --warnings-as-errors``.

Building Against External libzstd
=================================

By default, this package builds and links against a single file ``libzstd``
bundled as part of the package distribution. This copy of ``libzstd`` is
statically linked into the extension.

It is possible to point ``setup.py`` at an external (typically system provided)
``libzstd``. To do this, simply pass ``--system-zstd`` to ``setup.py``. e.g.

``python3.14 setup.py --system-zstd`` or ``python3.14 -m pip install zstandard
--install-option="--system-zstd"``.

When building against a system libzstd, you may need to specify extra compiler
arguments to help Python's build system find the external library. These can
be specified via the ``ZSTD_EXTRA_COMPILER_ARGS`` environment variable. e.g.
``ZSTD_EXTRA_COMPILER_ARGS="-I/usr/local/include" python3 setup.py
--system-zstd``.

``hyperlight-zstandard`` can be sensitive about what version of ``libzstd`` it links
against. For best results, point this package at the exact same version of
``libzstd`` that it bundles. See the bundled ``zstd/zstd.h`` or
``zstd/zstd.c`` for which version that is.

A build or run-time error can occur if the version of ``libzstd`` being built
against does not exactly match our bundled version. Historically, we required
an exact version match. But in September 2025 we relaxed this constraint to
only require a minimum version match.

When linking against an external ``libzstd``, not all package features may be
available. Notably, the ``multi_compress_to_buffer()`` and
``multi_decompress_to_buffer()`` APIs are not available, as these rely on private
symbols in the ``libzstd`` C source code, which require building against private
header files to use.
