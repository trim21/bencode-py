#include <pybind11/pybind11.h>

#include "common.h"

namespace py = pybind11;

py::object dataclasses_fields;
py::object is_dataclasses;

extern py::bytes bencode(py::object v);

extern py::object bdecode(py::buffer b);

PYBIND11_MODULE(_bencode, m, py::mod_gil_not_used()) {
    auto mod = m.import("dataclasses");
    mod.inc_ref();
    dataclasses_fields = mod.attr("fields");
    dataclasses_fields.inc_ref();
    is_dataclasses = mod.attr("is_dataclass");
    is_dataclasses.inc_ref();

    m.def("bdecode", &bdecode, "");
    m.def("bencode", &bencode, "");
    py::register_exception<DecodeError>(m, "BencodeDecodeError");
    py::register_exception<EncodeError>(m, "BencodeEncodeError");
}
