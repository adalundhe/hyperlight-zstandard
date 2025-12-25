// Copyright (c) 2020-present, Gregory Szorc
// All rights reserved.
//
// This software may be modified and distributed under the terms
// of the BSD license. See the LICENSE file for details.

//! Rust backend for hyperlight-zstandard with subinterpreter support.
//!
//! This module uses multi-phase initialization (PEP 489) to support
//! Python 3.12+ subinterpreters with per-interpreter GIL.

use pyo3::{prelude::*, types::PySet};
use std::ffi::c_int;
use std::ptr::null_mut;

mod buffers;
mod compression_chunker;
mod compression_dict;
mod compression_parameters;
mod compression_reader;
mod compression_writer;
mod compressionobj;
mod compressor;
mod compressor_iterator;
mod compressor_multi;
mod constants;
mod decompression_reader;
mod decompression_writer;
mod decompressionobj;
mod decompressor;
mod decompressor_iterator;
mod decompressor_multi;
mod exceptions;
mod frame_parameters;
mod stream;
mod zstd_safe;

// Remember to change the string in c-ext/hyperlight-zstandard.h, zstandard/__init__.py,
// and debian/changelog as well.
const VERSION: &str = "0.25.0";

/// Module initialization function called by Python.
/// This sets up the module with all types and constants.
fn init_module(py: Python<'_>, module: &Bound<'_, PyModule>) -> PyResult<()> {
    let features = PySet::new(
        py,
        &[
            "buffer_types",
            "multi_compress_to_buffer",
            "multi_decompress_to_buffer",
        ],
    )?;
    module.add("backend_features", features)?;

    crate::buffers::init_module(module)?;
    crate::compression_dict::init_module(module)?;
    crate::compression_parameters::init_module(module)?;
    crate::compressor::init_module(module)?;
    crate::constants::init_module(py, module)?;
    crate::decompressor::init_module(module)?;
    crate::exceptions::init_module(py, module)?;
    crate::frame_parameters::init_module(module)?;

    Ok(())
}

/// Multi-phase module exec function for subinterpreter support.
/// This is called once per interpreter to initialize the module.
#[allow(non_snake_case)]
unsafe extern "C" fn module_exec(module_ptr: *mut pyo3_ffi::PyObject) -> c_int {
    // Acquire the GIL for PyO3 operations
    Python::with_gil(|py| {
        // Convert raw pointer to PyO3 Bound reference
        let module = match Bound::from_borrowed_ptr_or_opt(py, module_ptr) {
            Some(obj) => obj,
            None => return -1,
        };

        let module = match module.downcast::<PyModule>() {
            Ok(m) => m,
            Err(_) => return -1,
        };

        match init_module(py, &module) {
            Ok(()) => 0,
            Err(e) => {
                e.restore(py);
                -1
            }
        }
    })
}

/// Module definition slots for multi-phase initialization.
/// These configure the module for subinterpreter support.
#[allow(clippy::declare_interior_mutable_const)]
static mut MODULE_SLOTS: [pyo3_ffi::PyModuleDef_Slot; 4] = [
    // Py_mod_exec: Module initialization function
    pyo3_ffi::PyModuleDef_Slot {
        slot: pyo3_ffi::Py_mod_exec,
        value: module_exec as *mut std::ffi::c_void,
    },
    // Py_mod_multiple_interpreters: Enable per-interpreter GIL support (Python 3.12+)
    #[cfg(Py_3_12)]
    pyo3_ffi::PyModuleDef_Slot {
        slot: pyo3_ffi::Py_mod_multiple_interpreters,
        value: pyo3_ffi::Py_MOD_PER_INTERPRETER_GIL_SUPPORTED,
    },
    #[cfg(not(Py_3_12))]
    pyo3_ffi::PyModuleDef_Slot {
        slot: 0,
        value: null_mut(),
    },
    // Py_mod_gil: Declare GIL usage (Python 3.13+)
    #[cfg(Py_3_13)]
    pyo3_ffi::PyModuleDef_Slot {
        slot: pyo3_ffi::Py_mod_gil,
        value: pyo3_ffi::Py_MOD_GIL_NOT_USED,
    },
    #[cfg(not(Py_3_13))]
    pyo3_ffi::PyModuleDef_Slot {
        slot: 0,
        value: null_mut(),
    },
    // Sentinel slot (marks end of slots array)
    pyo3_ffi::PyModuleDef_Slot {
        slot: 0,
        value: null_mut(),
    },
];

/// Module name as a null-terminated byte array.
const MODULE_NAME: &[u8] = b"backend_rust\0";

/// Module docstring as a null-terminated byte array.
const MODULE_DOC: &[u8] = b"Rust backend for zstandard bindings with subinterpreter support\0";

/// Module definition using multi-phase initialization.
#[allow(clippy::declare_interior_mutable_const)]
static mut MODULE_DEF: pyo3_ffi::PyModuleDef = pyo3_ffi::PyModuleDef {
    m_base: pyo3_ffi::PyModuleDef_HEAD_INIT,
    m_name: MODULE_NAME.as_ptr().cast(),
    m_doc: MODULE_DOC.as_ptr().cast(),
    m_size: 0, // No per-module state needed
    m_methods: null_mut(),
    m_slots: unsafe { MODULE_SLOTS.as_mut_ptr() },
    m_traverse: None,
    m_clear: None,
    m_free: None,
};

/// Python module entry point.
/// Uses multi-phase initialization for subinterpreter support.
#[allow(non_snake_case)]
#[no_mangle]
pub unsafe extern "C" fn PyInit_backend_rust() -> *mut pyo3_ffi::PyObject {
    pyo3_ffi::PyModuleDef_Init(std::ptr::addr_of_mut!(MODULE_DEF))
}
