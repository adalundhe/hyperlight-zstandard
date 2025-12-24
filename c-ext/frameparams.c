/**
 * Copyright (c) 2017-present, Gregory Szorc
 * All rights reserved.
 *
 * This software may be modified and distributed under the terms
 * of the BSD license. See the LICENSE file for details.
 */

#include "hyperlight-zstandard.h"

FrameParametersObject *get_frame_parameters(PyObject *self, PyObject *args,
                                            PyObject *kwargs) {
    ZstdModuleState *st = zstd_state_from_obj(self);
    static char *kwlist[] = {"data", "format", NULL};

    Py_buffer source;
    ZSTD_frameHeader header;
    ZSTD_format_e format = ZSTD_f_zstd1;
    FrameParametersObject *result = NULL;
    size_t zresult;

    if (!PyArg_ParseTupleAndKeywords(args, kwargs, "y*|I:get_frame_parameters",
                                     kwlist, &source, &format)) {
        return NULL;
    }

    zresult = ZSTD_getFrameHeader_advanced(&header, source.buf, source.len, format);

    if (ZSTD_isError(zresult)) {
        PyErr_Format(zstd_error(st), "cannot get frame parameters: %s",
                     ZSTD_getErrorName(zresult));
        goto finally;
    }

    if (zresult) {
        PyErr_Format(zstd_error(st),
                     "not enough data for frame parameters; need %zu bytes",
                     zresult);
        goto finally;
    }

    result = PyObject_New(FrameParametersObject, st->FrameParametersTypeObj);
    if (!result) {
        goto finally;
    }

    result->frameContentSize = header.frameContentSize;
    result->windowSize = header.windowSize;
    result->dictID = header.dictID;
    result->checksumFlag = header.checksumFlag ? 1 : 0;

finally:
    PyBuffer_Release(&source);
    return result;
}

static void FrameParameters_dealloc(PyObject *self) {
    PyObject_Del(self);
}

static PyMemberDef FrameParameters_members[] = {
    {"content_size", T_ULONGLONG,
     offsetof(FrameParametersObject, frameContentSize), READONLY,
     "frame content size"},
    {"window_size", T_ULONGLONG, offsetof(FrameParametersObject, windowSize),
     READONLY, "window size"},
    {"dict_id", T_UINT, offsetof(FrameParametersObject, dictID), READONLY,
     "dictionary ID"},
    {"has_checksum", T_BOOL, offsetof(FrameParametersObject, checksumFlag),
     READONLY, "checksum flag"},
    {NULL}};

PyType_Slot FrameParametersSlots[] = {
    {Py_tp_dealloc, FrameParameters_dealloc},
    {Py_tp_members, FrameParameters_members},
    {0, NULL},
};

PyType_Spec FrameParametersSpec = {
    "zstandard.backend_c.FrameParameters",
    sizeof(FrameParametersObject),
    0,
    Py_TPFLAGS_DEFAULT,
    FrameParametersSlots,
};

void frameparams_module_init(PyObject *mod) {
    ZstdModuleState *st = zstd_state_from_module(mod);

    st->FrameParametersTypeObj =
        (PyTypeObject *)PyType_FromModuleAndSpec(
            mod, &FrameParametersSpec, NULL);
    if (!st->FrameParametersTypeObj) {
        return;
    }

    if (PyType_Ready(st->FrameParametersTypeObj) < 0) {
        return;
    }

    PyModule_AddObjectRef(mod, "FrameParameters",
                          (PyObject *)st->FrameParametersTypeObj);
}
