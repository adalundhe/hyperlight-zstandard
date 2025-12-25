"""
Tests for Python 3.13+ subinterpreter compatibility.

This module verifies that zstandard can be imported and used correctly
across multiple Python subinterpreters, which is required for proper
free-threading and concurrent subinterpreter support in Python 3.14+.
"""

import sys
import unittest

# Python 3.13+ is required for the public concurrent.interpreters module
if sys.version_info >= (3, 13):
    from concurrent import interpreters  # type: ignore[attr-defined]


@unittest.skipIf(
    sys.version_info < (3, 13), "Subinterpreters require Python 3.13+"
)
class TestSubinterpreters(unittest.TestCase):
    """Test zstandard in subinterpreter contexts."""

    def test_import_in_subinterpreter(self):
        """Test that zstandard can be imported in a subinterpreter."""
        interp = interpreters.create()
        try:
            interp.exec("import zstandard")
        finally:
            interp.close()

    def test_compress_decompress_in_subinterpreter(self):
        """Test compression and decompression in a subinterpreter."""
        interp = interpreters.create()
        try:
            code = """
import zstandard

# Test basic compression/decompression
data = b"Hello, World! " * 100
cctx = zstandard.ZstdCompressor()
compressed = cctx.compress(data)

dctx = zstandard.ZstdDecompressor()
decompressed = dctx.decompress(compressed)

assert decompressed == data, "Decompressed data does not match original"
"""
            interp.exec(code)
        finally:
            interp.close()

    def test_multiple_subinterpreters_sequential(self):
        """Test zstandard in multiple sequential subinterpreters."""
        for i in range(5):
            interp = interpreters.create()
            try:
                code = f"""
import zstandard

data = b"Test data for interpreter {i} " * 50
cctx = zstandard.ZstdCompressor(level=3)
compressed = cctx.compress(data)

dctx = zstandard.ZstdDecompressor()
decompressed = dctx.decompress(compressed)

assert decompressed == data, f"Mismatch in interpreter {i}"
"""
                interp.exec(code)
            finally:
                interp.close()

    def test_compression_parameters_in_subinterpreter(self):
        """Test ZstdCompressionParameters in a subinterpreter."""
        interp = interpreters.create()
        try:
            code = """
import zstandard

# Test compression parameters
params = zstandard.ZstdCompressionParameters.from_level(5)
cctx = zstandard.ZstdCompressor(compression_params=params)

data = b"Testing compression parameters" * 100
compressed = cctx.compress(data)

dctx = zstandard.ZstdDecompressor()
decompressed = dctx.decompress(compressed)

assert decompressed == data
"""
            interp.exec(code)
        finally:
            interp.close()

    def test_streaming_api_in_subinterpreter(self):
        """Test streaming compression/decompression in a subinterpreter."""
        interp = interpreters.create()
        try:
            code = """
import io
import zstandard

data = b"Streaming test data " * 1000

# Test stream writer (closefd=False to keep buffer open)
buffer = io.BytesIO()
cctx = zstandard.ZstdCompressor()
with cctx.stream_writer(buffer, closefd=False) as compressor:
    compressor.write(data)

# Test stream reader
compressed_data = buffer.getvalue()
read_buffer = io.BytesIO(compressed_data)
dctx = zstandard.ZstdDecompressor()
with dctx.stream_reader(read_buffer) as reader:
    decompressed = reader.read()

assert decompressed == data
"""
            interp.exec(code)
        finally:
            interp.close()

    def test_exception_in_subinterpreter(self):
        """Test that ZstdError is properly raised in a subinterpreter."""
        interp = interpreters.create()
        try:
            code = """
import zstandard

# Try to decompress invalid data - should raise ZstdError
dctx = zstandard.ZstdDecompressor()
try:
    dctx.decompress(b"not valid zstd data")
    raise AssertionError("Expected ZstdError")
except zstandard.ZstdError:
    pass  # Expected
"""
            interp.exec(code)
        finally:
            interp.close()

    def test_concurrent_subinterpreters(self):
        """Test zstandard in concurrent subinterpreters."""
        import threading

        results = []
        errors = []

        def run_in_subinterpreter(interp_id):
            try:
                interp = interpreters.create()
                try:
                    code = f"""
import zstandard

data = b"Concurrent test data for interpreter {interp_id} " * 100
cctx = zstandard.ZstdCompressor(level=1)
compressed = cctx.compress(data)

dctx = zstandard.ZstdDecompressor()
decompressed = dctx.decompress(compressed)

assert decompressed == data
"""
                    interp.exec(code)
                    results.append(interp_id)
                finally:
                    interp.close()
            except Exception as e:
                errors.append((interp_id, str(e)))

        threads = []
        for i in range(10):
            t = threading.Thread(target=run_in_subinterpreter, args=(i,))
            threads.append(t)
            t.start()

        for t in threads:
            t.join()

        self.assertEqual(len(errors), 0, f"Errors occurred: {errors}")
        self.assertEqual(len(results), 10)

    def test_dictionary_in_subinterpreter(self):
        """Test compression dictionaries in a subinterpreter."""
        interp = interpreters.create()
        try:
            code = """
import zstandard

# Create training samples
samples = [b"sample data " * 10 + bytes([i]) for i in range(100)]

# Train a dictionary
dict_data = zstandard.train_dictionary(8192, samples)

# Use dictionary for compression
cctx = zstandard.ZstdCompressor(dict_data=dict_data)
dctx = zstandard.ZstdDecompressor(dict_data=dict_data)

test_data = b"sample data sample data sample data"
compressed = cctx.compress(test_data)
decompressed = dctx.decompress(compressed)

assert decompressed == test_data
"""
            interp.exec(code)
        finally:
            interp.close()


if __name__ == "__main__":
    unittest.main()
