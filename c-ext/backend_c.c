/**
 * Copyright (c) 2016-present, Gregory Szorc
 * All rights reserved.
 *
 * This software may be modified and distributed under the terms
 * of the BSD license. See the LICENSE file for details.
 */

/* A Python C extension for Zstandard. */

#if defined(_WIN32)
#define WIN32_LEAN_AND_MEAN
#include <Windows.h>
#elif defined(__APPLE__) || defined(__OpenBSD__) || defined(__FreeBSD__) ||    \
    defined(__NetBSD__) || defined(__DragonFly__)
#include <sys/types.h>

#include <sys/sysctl.h>

#endif

#include "hyperlight-zstandard.h"

#include "bufferutil.c"
#include "compressionchunker.c"
#include "compressiondict.c"
#include "compressionparams.c"
#include "compressionreader.c"
#include "compressionwriter.c"
#include "compressobj.c"
#include "compressor.c"
#include "compressoriterator.c"
#include "constants.c"
#include "decompressionreader.c"
#include "decompressionwriter.c"
#include "decompressobj.c"
#include "decompressor.c"
#include "decompressoriterator.c"
#include "frameparams.c"

ZstdModuleState *zstd_state_from_module(PyObject *m) {
    return (ZstdModuleState *)PyModule_GetState(m);
}

static PyObject *estimate_decompression_context_size(PyObject *self) {
    return PyLong_FromSize_t(ZSTD_estimateDCtxSize());
}

static PyObject *frame_content_size(PyObject *self, PyObject *args,
                                    PyObject *kwargs) {
    ZstdModuleState *st = zstd_state_from_obj(self);
    static char *kwlist[] = {"source", NULL};

    Py_buffer source;
    PyObject *result = NULL;
    unsigned long long size;

    if (!PyArg_ParseTupleAndKeywords(args, kwargs, "y*:frame_content_size",
                                     kwlist, &source)) {
        return NULL;
    }

    size = ZSTD_getFrameContentSize(source.buf, source.len);

    if (size == ZSTD_CONTENTSIZE_ERROR) {
        PyErr_SetString(zstd_error(st), "error when determining content size");
    }
    else if (size == ZSTD_CONTENTSIZE_UNKNOWN) {
        result = PyLong_FromLong(-1);
    }
    else {
        result = PyLong_FromUnsignedLongLong(size);
    }

    PyBuffer_Release(&source);

    return result;
}

static PyObject *frame_header_size(PyObject *self, PyObject *args,
                                   PyObject *kwargs) {
    ZstdModuleState *st = zstd_state_from_obj(self);
    static char *kwlist[] = {"source", NULL};

    Py_buffer source;
    PyObject *result = NULL;
    size_t zresult;

    if (!PyArg_ParseTupleAndKeywords(args, kwargs, "y*:frame_header_size",
                                     kwlist, &source)) {
        return NULL;
    }

    zresult = ZSTD_frameHeaderSize(source.buf, source.len);
    if (ZSTD_isError(zresult)) {
        PyErr_Format(zstd_error(st),
                     "could not determine frame header size: %s",
                     ZSTD_getErrorName(zresult));
    }
    else {
        result = PyLong_FromSize_t(zresult);
    }

    PyBuffer_Release(&source);

    return result;
}

static char zstd_doc[] = "Interface to zstandard";

static PyMethodDef zstd_methods[] = {
    {"estimate_decompression_context_size",
     (PyCFunction)estimate_decompression_context_size, METH_NOARGS, NULL},
    {"frame_content_size", (PyCFunction)frame_content_size,
     METH_VARARGS | METH_KEYWORDS, NULL},
    {"frame_header_size", (PyCFunction)frame_header_size,
     METH_VARARGS | METH_KEYWORDS, NULL},
    {"get_frame_parameters", (PyCFunction)get_frame_parameters,
     METH_VARARGS | METH_KEYWORDS, NULL},
    {"train_dictionary", (PyCFunction)train_dictionary,
     METH_VARARGS | METH_KEYWORDS, NULL},
    {NULL, NULL}};

void bufferutil_module_init(PyObject *mod);
void compressobj_module_init(PyObject *mod);
void compressor_module_init(PyObject *mod);
void compressionparams_module_init(PyObject *mod);
void constants_module_init(PyObject *mod);
void compressionchunker_module_init(PyObject *mod);
void compressiondict_module_init(PyObject *mod);
void compressionreader_module_init(PyObject *mod);
void compressionwriter_module_init(PyObject *mod);
void compressoriterator_module_init(PyObject *mod);
void decompressor_module_init(PyObject *mod);
void decompressobj_module_init(PyObject *mod);
void decompressionreader_module_init(PyObject *mod);
void decompressionwriter_module_init(PyObject *mod);
void decompressoriterator_module_init(PyObject *mod);
void frameparams_module_init(PyObject *mod);

static int zstd_module_exec(PyObject *m) {
#ifdef Py_GIL_DISABLED
    PyUnstable_Module_SetGIL(m, Py_MOD_GIL_NOT_USED);
#endif

    /*
       hyperlight-zstandard relies on unstable zstd C API features. This means
       that changes in zstd may break expectations in hyperlight-zstandard.

       hyperlight-zstandard is distributed with a copy of the zstd sources.
       hyperlight-zstandard is only guaranteed to work with the bundled version
       of zstd.

       However, downstream redistributors or packagers may unbundle zstd
       from hyperlight-zstandard. This can result in a mismatch between zstd
       versions and API semantics. This essentially "voids the warranty"
       of hyperlight-zstandard and may cause undefined behavior.

       We detect this mismatch here and refuse to load the module if this
       scenario is detected.

       Historically we required exact matches. But over the years the churn
       in libzstd became reasonable and we relaxed this constraint to a minimum
       version check. Our assumption going forward is that we will only rely on
       unstable C API features that are in reality stable for years.
    */
    PyObject *features = NULL;
    PyObject *feature = NULL;
    unsigned zstd_version_no = ZSTD_versionNumber();
    unsigned zstd_version_min = 10506;
    // if either compile-time or runtime version of libzstd is lower than expected, abort initialization
    if (ZSTD_VERSION_NUMBER < zstd_version_min ||
        zstd_version_no < zstd_version_min) {
        PyErr_Format(
            PyExc_ImportError,
            "zstd C API versions mismatch; Python bindings were not "
            "compiled/linked against expected zstd version (%u returned by the "
            "lib, %u hardcoded in zstd headers, %u hardcoded in the cext)",
            zstd_version_no, ZSTD_VERSION_NUMBER, zstd_version_min);
        return -1;
    }

    features = PySet_New(NULL);
    if (NULL == features) {
        PyErr_SetString(PyExc_ImportError, "could not create empty set");
        return -1;
    }

    feature = PyUnicode_FromString("buffer_types");
    if (NULL == feature) {
        PyErr_SetString(PyExc_ImportError, "could not create feature string");
        Py_DECREF(features);
        return -1;
    }

    if (PySet_Add(features, feature) == -1) {
        Py_DECREF(feature);
        Py_DECREF(features);
        return -1;
    }

    Py_DECREF(feature);

#ifdef HAVE_ZSTD_POOL_APIS
    feature = PyUnicode_FromString("multi_compress_to_buffer");
    if (NULL == feature) {
        PyErr_SetString(PyExc_ImportError, "could not create feature string");
        Py_DECREF(features);
        return -1;
    }

    if (PySet_Add(features, feature) == -1) {
        Py_DECREF(feature);
        Py_DECREF(features);
        return -1;
    }

    Py_DECREF(feature);
#endif

#ifdef HAVE_ZSTD_POOL_APIS
    feature = PyUnicode_FromString("multi_decompress_to_buffer");
    if (NULL == feature) {
        PyErr_SetString(PyExc_ImportError, "could not create feature string");
        Py_DECREF(features);
        return -1;
    }

    if (PySet_Add(features, feature) == -1) {
        Py_DECREF(feature);
        Py_DECREF(features);
        return -1;
    }

    Py_DECREF(feature);
#endif

    if (PyObject_SetAttrString(m, "backend_features", features) == -1) {
        Py_DECREF(features);
        return -1;
    }

    Py_DECREF(features);

    bufferutil_module_init(m);
    if (PyErr_Occurred()) {
        return -1;
    }
    compressionparams_module_init(m);
    if (PyErr_Occurred()) {
        return -1;
    }
    compressiondict_module_init(m);
    if (PyErr_Occurred()) {
        return -1;
    }
    compressobj_module_init(m);
    if (PyErr_Occurred()) {
        return -1;
    }
    compressor_module_init(m);
    if (PyErr_Occurred()) {
        return -1;
    }
    compressionchunker_module_init(m);
    if (PyErr_Occurred()) {
        return -1;
    }
    compressionreader_module_init(m);
    if (PyErr_Occurred()) {
        return -1;
    }
    compressionwriter_module_init(m);
    if (PyErr_Occurred()) {
        return -1;
    }
    compressoriterator_module_init(m);
    if (PyErr_Occurred()) {
        return -1;
    }
    constants_module_init(m);
    if (PyErr_Occurred()) {
        return -1;
    }
    decompressor_module_init(m);
    if (PyErr_Occurred()) {
        return -1;
    }
    decompressobj_module_init(m);
    if (PyErr_Occurred()) {
        return -1;
    }
    decompressionreader_module_init(m);
    if (PyErr_Occurred()) {
        return -1;
    }
    decompressionwriter_module_init(m);
    if (PyErr_Occurred()) {
        return -1;
    }
    decompressoriterator_module_init(m);
    if (PyErr_Occurred()) {
        return -1;
    }
    frameparams_module_init(m);
    if (PyErr_Occurred()) {
        return -1;
    }

    return 0;
}

#if defined(__GNUC__) && (__GNUC__ >= 4)
#define PYTHON_ZSTD_VISIBILITY __attribute__((visibility("default")))
#else
#define PYTHON_ZSTD_VISIBILITY
#endif

static int zstd_traverse(PyObject *m, visitproc visit, void *arg) {
    ZstdModuleState *st = zstd_state_from_module(m);
    if (!st) {
        return 0;
    }

    Py_VISIT(st->ZstdErrorType);

    Py_VISIT((PyObject *)st->ZstdCompressionParametersTypeObj);
    Py_VISIT((PyObject *)st->FrameParametersTypeObj);
    Py_VISIT((PyObject *)st->ZstdCompressionDictTypeObj);
    Py_VISIT((PyObject *)st->ZstdCompressorTypeObj);
    Py_VISIT((PyObject *)st->ZstdCompressionObjTypeObj);
    Py_VISIT((PyObject *)st->ZstdCompressionWriterTypeObj);
    Py_VISIT((PyObject *)st->ZstdCompressorIteratorTypeObj);
    Py_VISIT((PyObject *)st->ZstdCompressionReaderTypeObj);
    Py_VISIT((PyObject *)st->ZstdCompressionChunkerTypeObj);
    Py_VISIT((PyObject *)st->ZstdCompressionChunkerIteratorTypeObj);
    Py_VISIT((PyObject *)st->ZstdDecompressorTypeObj);
    Py_VISIT((PyObject *)st->ZstdDecompressionObjTypeObj);
    Py_VISIT((PyObject *)st->ZstdDecompressionReaderTypeObj);
    Py_VISIT((PyObject *)st->ZstdDecompressionWriterTypeObj);
    Py_VISIT((PyObject *)st->ZstdDecompressorIteratorTypeObj);
    Py_VISIT((PyObject *)st->ZstdBufferSegmentsTypeObj);
    Py_VISIT((PyObject *)st->ZstdBufferSegmentTypeObj);
    Py_VISIT((PyObject *)st->ZstdBufferWithSegmentsTypeObj);
    Py_VISIT((PyObject *)st->ZstdBufferWithSegmentsCollectionTypeObj);

    return 0;
}

static int zstd_clear(PyObject *m) {
    ZstdModuleState *st = zstd_state_from_module(m);
    if (!st) {
        return 0;
    }

    Py_CLEAR(st->ZstdErrorType);

    Py_CLEAR(st->ZstdCompressionParametersTypeObj);
    Py_CLEAR(st->FrameParametersTypeObj);
    Py_CLEAR(st->ZstdCompressionDictTypeObj);
    Py_CLEAR(st->ZstdCompressorTypeObj);
    Py_CLEAR(st->ZstdCompressionObjTypeObj);
    Py_CLEAR(st->ZstdCompressionWriterTypeObj);
    Py_CLEAR(st->ZstdCompressorIteratorTypeObj);
    Py_CLEAR(st->ZstdCompressionReaderTypeObj);
    Py_CLEAR(st->ZstdCompressionChunkerTypeObj);
    Py_CLEAR(st->ZstdCompressionChunkerIteratorTypeObj);
    Py_CLEAR(st->ZstdDecompressorTypeObj);
    Py_CLEAR(st->ZstdDecompressionObjTypeObj);
    Py_CLEAR(st->ZstdDecompressionReaderTypeObj);
    Py_CLEAR(st->ZstdDecompressionWriterTypeObj);
    Py_CLEAR(st->ZstdDecompressorIteratorTypeObj);
    Py_CLEAR(st->ZstdBufferSegmentsTypeObj);
    Py_CLEAR(st->ZstdBufferSegmentTypeObj);
    Py_CLEAR(st->ZstdBufferWithSegmentsTypeObj);
    Py_CLEAR(st->ZstdBufferWithSegmentsCollectionTypeObj);

    return 0;
}

static PyModuleDef_Slot zstd_module_slots[] = {
    {Py_mod_exec, zstd_module_exec},
#ifdef Py_mod_multiple_interpreters
    /* Support for per-interpreter GIL (free-threading) and isolated subinterpreters */
    {Py_mod_multiple_interpreters, Py_MOD_PER_INTERPRETER_GIL_SUPPORTED},
#endif
#ifdef Py_mod_gil
    {Py_mod_gil, Py_MOD_GIL_NOT_USED},
#endif
    {0, NULL},
};

static struct PyModuleDef zstd_module = {
    PyModuleDef_HEAD_INIT,
    "backend_c",
    zstd_doc,
    sizeof(ZstdModuleState),
    zstd_methods,
    zstd_module_slots,
    zstd_traverse,
    zstd_clear,
    NULL,
};

PYTHON_ZSTD_VISIBILITY PyMODINIT_FUNC PyInit_backend_c(void) {
    return PyModuleDef_Init(&zstd_module);
}

/* Attempt to resolve the number of CPUs in the system. */
int cpu_count() {
    int count = 0;

#if defined(_WIN32)
    SYSTEM_INFO si;
    si.dwNumberOfProcessors = 0;
    GetSystemInfo(&si);
    count = si.dwNumberOfProcessors;
#elif defined(__APPLE__)
    int num;
    size_t size = sizeof(int);

    if (0 == sysctlbyname("hw.logicalcpu", &num, &size, NULL, 0)) {
        count = num;
    }
#elif defined(__linux__)
    count = sysconf(_SC_NPROCESSORS_ONLN);
#elif defined(__OpenBSD__) || defined(__FreeBSD__) || defined(__NetBSD__) ||   \
    defined(__DragonFly__)
    int mib[2];
    size_t len = sizeof(count);
    mib[0] = CTL_HW;
    mib[1] = HW_NCPU;
    if (0 != sysctl(mib, 2, &count, &len, NULL, 0)) {
        count = 0;
    }
#elif defined(__hpux)
    count = mpctl(MPC_GETNUMSPUS, NULL, NULL);
#endif

    return count;
}

size_t roundpow2(size_t i) {
    i--;
    i |= i >> 1;
    i |= i >> 2;
    i |= i >> 4;
    i |= i >> 8;
    i |= i >> 16;
    i++;

    return i;
}

/* Safer version of _PyBytes_Resize().
 *
 * _PyBytes_Resize() only works if the refcount is 1. In some scenarios,
 * we can get an object with a refcount > 1, even if it was just created
 * with PyBytes_FromStringAndSize()! That's because (at least) CPython
 * pre-allocates PyBytes instances of size 1 for every possible byte value.
 *
 * If non-0 is returned, obj may or may not be NULL.
 */
int safe_pybytes_resize(PyObject **obj, Py_ssize_t size) {
    PyObject *tmp;

    if (PyUnstable_Object_IsUniquelyReferenced(*obj)) {
        return _PyBytes_Resize(obj, size);
    }

    tmp = PyBytes_FromStringAndSize(NULL, size);
    if (!tmp) {
        return -1;
    }

    memcpy(PyBytes_AS_STRING(tmp), PyBytes_AS_STRING(*obj),
           PyBytes_GET_SIZE(*obj));

    Py_DECREF(*obj);
    *obj = tmp;

    return 0;
}

// Set/raise an `io.UnsupportedOperation` exception.
void set_io_unsupported_operation(void) {
    PyObject *iomod;
    PyObject *exc;

    iomod = PyImport_ImportModule("io");
    if (NULL == iomod) {
        return;
    }

    exc = PyObject_GetAttrString(iomod, "UnsupportedOperation");
    if (NULL == exc) {
        Py_DECREF(iomod);
        return;
    }

    PyErr_SetNone(exc);
    Py_DECREF(exc);
    Py_DECREF(iomod);
}
