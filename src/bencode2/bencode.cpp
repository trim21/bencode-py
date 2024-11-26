#define FMT_HEADER_ONLY

#include <nanobind/nanobind.h>
namespace nb = nanobind;

// dataclasses.fields
nb::object dataclasses_fields;

// dataclasses.is_dataclass
nb::object is_dataclasses;

#include "decode.hpp"
#include "encode.hpp"

NB_MODULE(__bencode, m) {
    auto mod = m.import_("dataclasses");
    dataclasses_fields = mod.attr("fields");
    dataclasses_fields.inc_ref();
    is_dataclasses = mod.attr("is_dataclass");
    is_dataclasses.inc_ref();

    nb::exception<EncodeError>(m, "BencodeEncodeError", PyExc_ValueError);
    nb::exception<DecodeError>(m, "BencodeDecodeError", PyExc_ValueError);
    m.def("bencode", bencode);
    m.def("bdecode", bdecode);
}
