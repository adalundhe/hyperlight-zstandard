# Type stubs for zstandard module
#
# This file provides type hints for mypy and other static type checkers.
# The actual implementations are in the C or Rust backend modules.

import io
import os
from collections.abc import Buffer
from typing import Any, BinaryIO, Set, Tuple, Union

# Version
__version__: str

# Backend information
backend: str
backend_features: Set[str]

# Constants
BLOCKSIZELOG_MAX: int
BLOCKSIZE_MAX: int
CHAINLOG_MAX: int
CHAINLOG_MIN: int
COMPRESSION_RECOMMENDED_INPUT_SIZE: int
COMPRESSION_RECOMMENDED_OUTPUT_SIZE: int
COMPRESSOBJ_FLUSH_BLOCK: int
COMPRESSOBJ_FLUSH_FINISH: int
CONTENTSIZE_ERROR: int
CONTENTSIZE_UNKNOWN: int
DECOMPRESSION_RECOMMENDED_INPUT_SIZE: int
DECOMPRESSION_RECOMMENDED_OUTPUT_SIZE: int
DICT_TYPE_AUTO: int
DICT_TYPE_FULLDICT: int
DICT_TYPE_RAWCONTENT: int
FLUSH_BLOCK: int
FLUSH_FRAME: int
FORMAT_ZSTD1: int
FORMAT_ZSTD1_MAGICLESS: int
FRAME_HEADER: bytes
HASHLOG_MAX: int
HASHLOG_MIN: int
LDM_BUCKETSIZELOG_MAX: int
LDM_MINMATCH_MAX: int
LDM_MINMATCH_MIN: int
MAGIC_NUMBER: int
MAX_COMPRESSION_LEVEL: int
MINMATCH_MAX: int
MINMATCH_MIN: int
SEARCHLENGTH_MAX: int
SEARCHLENGTH_MIN: int
SEARCHLOG_MAX: int
SEARCHLOG_MIN: int
STRATEGY_BTLAZY2: int
STRATEGY_BTOPT: int
STRATEGY_BTULTRA: int
STRATEGY_BTULTRA2: int
STRATEGY_DFAST: int
STRATEGY_FAST: int
STRATEGY_GREEDY: int
STRATEGY_LAZY: int
STRATEGY_LAZY2: int
TARGETLENGTH_MAX: int
TARGETLENGTH_MIN: int
WINDOWLOG_MAX: int
WINDOWLOG_MIN: int
ZSTD_VERSION: Tuple[int, int, int]


# Exception
class ZstdError(Exception): ...


# Buffer types
class BufferSegment:
    offset: int
    def __len__(self) -> int: ...
    def tobytes(self) -> bytes: ...


class BufferSegments:
    def __len__(self) -> int: ...
    def __getitem__(self, index: int) -> BufferSegment: ...


class BufferWithSegments:
    def __len__(self) -> int: ...
    def __getitem__(self, index: int) -> BufferSegment: ...
    def segments(self) -> BufferSegments: ...
    def tobytes(self) -> bytes: ...


class BufferWithSegmentsCollection:
    def __len__(self) -> int: ...
    def __getitem__(self, index: int) -> BufferWithSegments: ...
    def size(self) -> int: ...


# Frame parameters
class FrameParameters:
    content_size: int
    window_size: int
    dict_id: int
    has_checksum: bool


# Compression parameters
class ZstdCompressionParameters:
    @classmethod
    def from_level(
        cls,
        level: int,
        source_size: int = ...,
        dict_size: int = ...,
        **kwargs: Any,
    ) -> ZstdCompressionParameters: ...
    
    def estimated_compression_context_size(self) -> int: ...
    
    # Parameter properties
    format: int
    compression_level: int
    window_log: int
    hash_log: int
    chain_log: int
    search_log: int
    min_match: int
    target_length: int
    strategy: int
    write_content_size: int
    write_checksum: int
    write_dict_id: int
    job_size: int
    overlap_log: int
    force_max_window: int
    enable_ldm: int
    ldm_hash_log: int
    ldm_min_match: int
    ldm_bucket_size_log: int
    ldm_hash_rate_log: int
    threads: int


# Compression dictionary
class ZstdCompressionDict:
    def __init__(
        self,
        data: bytes,
        dict_type: int = ...,
    ) -> None: ...
    
    def __len__(self) -> int: ...
    def dict_id(self) -> int: ...
    def as_bytes(self) -> bytes: ...
    def precompute_compress(
        self,
        level: int = ...,
        compression_params: ZstdCompressionParameters = ...,
    ) -> None: ...


# Compression reader
class ZstdCompressionReader(io.RawIOBase):
    def __enter__(self) -> ZstdCompressionReader: ...
    def __exit__(self, *args: Any) -> None: ...
    def readable(self) -> bool: ...
    def writable(self) -> bool: ...
    def seekable(self) -> bool: ...
    def readline(self, size: int | None = ...) -> bytes: ...  # type: ignore[override]
    def readlines(self, hint: int = ...) -> list[bytes]: ...
    def read(self, size: int = ...) -> bytes: ...
    def readinto(self, b: Buffer) -> int: ...  # type: ignore[override]
    def read1(self, size: int = ...) -> bytes: ...
    def readinto1(self, b: Buffer) -> int: ...
    def close(self) -> None: ...
    @property
    def closed(self) -> bool: ...
    def flush(self) -> None: ...
    def tell(self) -> int: ...


# Compression writer
class ZstdCompressionWriter(io.RawIOBase):
    def __enter__(self) -> ZstdCompressionWriter: ...
    def __exit__(self, *args: Any) -> None: ...
    def readable(self) -> bool: ...
    def writable(self) -> bool: ...
    def seekable(self) -> bool: ...
    def write(self, data: Buffer) -> int: ...  # type: ignore[override]
    def flush(self, flush_mode: int = ...) -> int: ...  # type: ignore[override]
    def close(self) -> None: ...
    @property
    def closed(self) -> bool: ...
    def fileno(self) -> int: ...
    def tell(self) -> int: ...


# Compressor
class ZstdCompressor:
    def __init__(
        self,
        level: int = ...,
        dict_data: ZstdCompressionDict = ...,
        compression_params: ZstdCompressionParameters = ...,
        write_checksum: bool = ...,
        write_content_size: bool = ...,
        write_dict_id: bool = ...,
        threads: int = ...,
    ) -> None: ...
    
    def compress(self, data: bytes) -> bytes: ...
    def compressobj(self, size: int = ...) -> ZstdCompressionObj: ...
    def chunker(
        self,
        size: int = ...,
        chunk_size: int = ...,
    ) -> ZstdCompressionChunker: ...
    def copy_stream(
        self,
        ifh: BinaryIO,
        ofh: BinaryIO,
        size: int = ...,
        read_size: int = ...,
        write_size: int = ...,
    ) -> Tuple[int, int]: ...
    def stream_reader(
        self,
        source: Union[BinaryIO, bytes],
        size: int = ...,
        read_size: int = ...,
        closefd: bool = ...,
    ) -> ZstdCompressionReader: ...
    def stream_writer(
        self,
        writer: BinaryIO,
        size: int = ...,
        write_size: int = ...,
        write_return_read: bool = ...,
        closefd: bool = ...,
    ) -> ZstdCompressionWriter: ...
    def read_to_iter(
        self,
        reader: BinaryIO,
        size: int = ...,
        read_size: int = ...,
        write_size: int = ...,
    ) -> ZstdCompressorIterator: ...
    def frame_progression(self) -> Tuple[int, int, int]: ...
    def memory_size(self) -> int: ...
    def multi_compress_to_buffer(
        self,
        data: Any,
        threads: int = ...,
    ) -> BufferWithSegmentsCollection: ...


# Compression object (for compressobj interface)
class ZstdCompressionObj:
    def compress(self, data: bytes) -> bytes: ...
    def flush(self, flush_mode: int = ...) -> bytes: ...


# Compression chunker
class ZstdCompressionChunker:
    def compress(self, data: bytes) -> Any: ...
    def flush(self) -> Any: ...
    def finish(self) -> Any: ...


# Compressor iterator
class ZstdCompressorIterator:
    def __iter__(self) -> ZstdCompressorIterator: ...
    def __next__(self) -> bytes: ...


# Decompression reader
class ZstdDecompressionReader(io.RawIOBase):
    def __enter__(self) -> ZstdDecompressionReader: ...
    def __exit__(self, *args: Any) -> None: ...
    def readable(self) -> bool: ...
    def writable(self) -> bool: ...
    def seekable(self) -> bool: ...
    def readline(self, size: int | None = ...) -> bytes: ...  # type: ignore[override]
    def readlines(self, hint: int = ...) -> list[bytes]: ...
    def read(self, size: int = ...) -> bytes: ...
    def readinto(self, b: Buffer) -> int: ...  # type: ignore[override]
    def read1(self, size: int = ...) -> bytes: ...
    def readinto1(self, b: Buffer) -> int: ...
    def close(self) -> None: ...
    @property
    def closed(self) -> bool: ...
    def flush(self) -> None: ...
    def tell(self) -> int: ...
    def seek(self, offset: int, whence: int = ...) -> int: ...


# Decompression writer
class ZstdDecompressionWriter(io.RawIOBase):
    def __enter__(self) -> ZstdDecompressionWriter: ...
    def __exit__(self, *args: Any) -> None: ...
    def readable(self) -> bool: ...
    def writable(self) -> bool: ...
    def seekable(self) -> bool: ...
    def write(self, data: Buffer) -> int: ...  # type: ignore[override]
    def flush(self) -> None: ...
    def close(self) -> None: ...
    @property
    def closed(self) -> bool: ...
    def fileno(self) -> int: ...
    def tell(self) -> int: ...


# Decompressor
class ZstdDecompressor:
    def __init__(
        self,
        dict_data: ZstdCompressionDict = ...,
        max_window_size: int = ...,
        format: int = ...,
    ) -> None: ...
    
    def decompress(
        self,
        data: bytes,
        max_output_size: int = ...,
        read_across_frames: bool = ...,
        allow_extra_data: bool = ...,
    ) -> bytes: ...
    def decompressobj(self, write_size: int = ...) -> ZstdDecompressionObj: ...
    def copy_stream(
        self,
        ifh: BinaryIO,
        ofh: BinaryIO,
        read_size: int = ...,
        write_size: int = ...,
    ) -> Tuple[int, int]: ...
    def stream_reader(
        self,
        source: Union[BinaryIO, bytes],
        read_size: int = ...,
        read_across_frames: bool = ...,
        closefd: bool = ...,
    ) -> ZstdDecompressionReader: ...
    def stream_writer(
        self,
        writer: BinaryIO,
        write_size: int = ...,
        write_return_read: bool = ...,
        closefd: bool = ...,
    ) -> ZstdDecompressionWriter: ...
    def read_to_iter(
        self,
        reader: BinaryIO,
        read_size: int = ...,
        write_size: int = ...,
        skip_bytes: int = ...,
    ) -> ZstdDecompressorIterator: ...
    def memory_size(self) -> int: ...
    def multi_decompress_to_buffer(
        self,
        frames: Any,
        decompressed_sizes: Any = ...,
        threads: int = ...,
    ) -> BufferWithSegmentsCollection: ...


# Decompression object (for decompressobj interface)
class ZstdDecompressionObj:
    def decompress(self, data: bytes) -> bytes: ...
    def flush(self, length: int = ...) -> bytes: ...
    @property
    def unused_data(self) -> bytes: ...
    @property
    def unconsumed_tail(self) -> bytes: ...
    @property
    def eof(self) -> bool: ...


# Decompressor iterator
class ZstdDecompressorIterator:
    def __iter__(self) -> ZstdDecompressorIterator: ...
    def __next__(self) -> bytes: ...


# Module-level functions
def compress(data: bytes, level: int = ...) -> bytes: ...
def decompress(data: bytes, max_output_size: int = ...) -> bytes: ...
def train_dictionary(
    dict_size: int,
    samples: list[bytes],
    k: int = ...,
    d: int = ...,
    f: int = ...,
    split_point: float = ...,
    accel: int = ...,
    notifications: int = ...,
    dict_id: int = ...,
    level: int = ...,
    steps: int = ...,
    threads: int = ...,
) -> ZstdCompressionDict: ...
def frame_header_size(data: bytes) -> int: ...
def frame_content_size(data: bytes) -> int: ...
def get_frame_parameters(data: bytes) -> FrameParameters: ...
def estimate_decompression_context_size() -> int: ...
def open(
    filename: Union[str, bytes, os.PathLike[Any], BinaryIO],
    mode: str = ...,
    cctx: ZstdCompressor = ...,
    dctx: ZstdDecompressor = ...,
    encoding: str = ...,
    errors: str = ...,
    newline: str = ...,
    closefd: bool = ...,
) -> Union[ZstdCompressionReader, ZstdDecompressionReader, ZstdCompressionWriter, io.TextIOWrapper]: ...
