#include <pybind11/pybind11.h>

namespace py = pybind11;
// dataclasses.fields
py::object dataclasses_fields;

// dataclasses.is_dataclass
py::object is_dataclasses;

#ifndef __cplusplus
#error "require at least cpp 17"
#endif

#if __cplusplus < 201703L
#error "require at least cpp 17"
#endif

#include "decode.hpp"
#include "encode.hpp"

PYBIND11_MODULE(__bencode, m, py::mod_gil_not_used()) {
    auto mod = m.import("dataclasses");
    dataclasses_fields = mod.attr("fields");
    dataclasses_fields.inc_ref();
    is_dataclasses = mod.attr("is_dataclass");
    is_dataclasses.inc_ref();

    m.def("bdecode", &bdecode, "");
    m.def("bencode", &bencode, "");
    py::register_exception<DecodeError>(m, "BencodeDecodeError");
    py::register_exception<EncodeError>(m, "BencodeEncodeError");
}
