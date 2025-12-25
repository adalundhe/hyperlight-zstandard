# Copyright (c) 2017-present, Gregory Szorc
# All rights reserved.
#
# This software may be modified and distributed under the terms
# of the BSD license. See the LICENSE file for details.

# ruff: noqa: F403, F405

"""Python interface to the Zstandard (zstd) compression library."""

from __future__ import absolute_import, unicode_literals

# This module exports the C backend through a central module and implements
# additional functionality built on top of it.
import builtins
import io
import os
import sys

if sys.version_info >= (3, 12):
    from collections.abc import Buffer
else:
    from typing import ByteString as Buffer

# Import the C backend. The behavior can be overridden via environment variable
# for special cases (e.g., testing the Rust backend).
_module_policy = os.environ.get(
    "HYPERLIGHT_ZSTANDARD_IMPORT_POLICY",
    os.environ.get("PYTHON_ZSTANDARD_IMPORT_POLICY", "default"),
).strip()

if _module_policy in ("default", "cext"):
    from .backend_c import *  # type: ignore

    backend = "cext"
elif _module_policy == "rust":
    from .backend_rust import *  # type: ignore

    backend = "rust"
else:
    raise ImportError(
        "unknown module import policy: %s; use default, cext, or rust"
        % _module_policy
    )

# Keep this in sync with hyperlight-zstandard.h, rust-ext/src/lib.rs, and debian/changelog.
__version__ = "0.25.0"

_MODE_CLOSED = 0
_MODE_READ = 1
_MODE_WRITE = 2


def open(
    filename,
    mode="rb",
    cctx=None,
    dctx=None,
    encoding=None,
    errors=None,
    newline=None,
    closefd=None,
):
    """Create a file object with zstd (de)compression.

    The object returned from this function will be a
    :py:class:`ZstdDecompressionReader` if opened for reading in binary mode,
    a :py:class:`ZstdCompressionWriter` if opened for writing in binary mode,
    or an ``io.TextIOWrapper`` if opened for reading or writing in text mode.

    :param filename:
       ``bytes``, ``str``, or ``os.PathLike`` defining a file to open or a
       file object (with a ``read()`` or ``write()`` method).
    :param mode:
       ``str`` File open mode. Accepts any of the open modes recognized by
       ``open()``.
    :param cctx:
       ``ZstdCompressor`` to use for compression. If not specified and file
       is opened for writing, the default ``ZstdCompressor`` will be used.
    :param dctx:
       ``ZstdDecompressor`` to use for decompression. If not specified and file
       is opened for reading, the default ``ZstdDecompressor`` will be used.
    :param encoding:
        ``str`` that defines text encoding to use when file is opened in text
        mode.
    :param errors:
       ``str`` defining text encoding error handling mode.
    :param newline:
       ``str`` defining newline to use in text mode.
    :param closefd:
       ``bool`` whether to close the file when the returned object is closed.
        Only used if a file object is passed. If a filename is specified, the
        opened file is always closed when the returned object is closed.
    """
    normalized_mode = mode.replace("t", "")

    if normalized_mode in ("r", "rb"):
        dctx = dctx or ZstdDecompressor()
        open_mode = "r"
        raw_open_mode = "rb"
    elif normalized_mode in ("w", "wb", "a", "ab", "x", "xb"):
        cctx = cctx or ZstdCompressor()
        open_mode = "w"
        raw_open_mode = normalized_mode
        if not raw_open_mode.endswith("b"):
            raw_open_mode = raw_open_mode + "b"
    else:
        raise ValueError("Invalid mode: {!r}".format(mode))

    if hasattr(os, "PathLike"):
        types = (str, bytes, os.PathLike)
    else:
        types = (str, bytes)

    if isinstance(filename, types):  # type: ignore
        inner_fh = builtins.open(filename, raw_open_mode)
        closefd = True
    elif hasattr(filename, "read") or hasattr(filename, "write"):
        inner_fh = filename
        closefd = bool(closefd)
    else:
        raise TypeError(
            "filename must be a str, bytes, file or PathLike object"
        )

    if open_mode == "r":
        fh = dctx.stream_reader(inner_fh, closefd=closefd)
    elif open_mode == "w":
        fh = cctx.stream_writer(inner_fh, closefd=closefd)
    else:
        raise RuntimeError("logic error in zstandard.open() handling open mode")

    if "b" not in normalized_mode:
        return io.TextIOWrapper(
            fh, encoding=encoding, errors=errors, newline=newline
        )
    else:
        return fh


def compress(data: Buffer, level: int = 3) -> bytes:
    """Compress source data using the zstd compression format.

    This performs one-shot compression using basic/default compression
    settings.

    This method is provided for convenience and is equivalent to calling
    ``ZstdCompressor(level=level).compress(data)``.

    If you find yourself calling this function in a tight loop,
    performance will be greater if you construct a single ``ZstdCompressor``
    and repeatedly call ``compress()`` on it.
    """
    cctx = ZstdCompressor(level=level)

    return cctx.compress(data)


def decompress(data: Buffer, max_output_size: int = 0) -> bytes:
    """Decompress a zstd frame into its original data.

    This performs one-shot decompression using basic/default compression
    settings.

    This method is provided for convenience and is equivalent to calling
    ``ZstdDecompressor().decompress(data, max_output_size=max_output_size)``.

    If you find yourself calling this function in a tight loop, performance
    will be greater if you construct a single ``ZstdDecompressor`` and
    repeatedly call ``decompress()`` on it.
    """
    dctx = ZstdDecompressor()

    return dctx.decompress(data, max_output_size=max_output_size)
