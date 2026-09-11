#include <nanobind/nanobind.h>
namespace nb = nanobind;

#include "common.hpp"

// dataclasses.fields, leaked on purpose: a static destructor would decref
// python objects after the interpreter has been finalized
nb::object *dataclasses_fields = nullptr;

// dataclasses.is_dataclass
nb::object *is_dataclasses = nullptr;

extern nb::bytes bencode(nb::object v);
extern nb::object bdecode(nb::object b);

NB_MODULE(__bencode, m) {
    auto mod = m.import_("dataclasses");
    dataclasses_fields = new nb::object(mod.attr("fields"));
    is_dataclasses = new nb::object(mod.attr("is_dataclass"));

    nb::exception<EncodeError>(m, "BencodeEncodeError", PyExc_ValueError);
    nb::exception<DecodeError>(m, "BencodeDecodeError", PyExc_ValueError);
    m.def("bencode", bencode);
    m.def("bdecode", bdecode);
}
