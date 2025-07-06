#include <pybind11/pybind11.h>
#include <pybind11/stl.h>

#include "fitparser_wrapper.h"

namespace py = pybind11;

PYBIND11_MODULE(uefitool, m) {
    py::class_<FitParserWrapper>(m, "FitParser")
        .def(py::init<>())
        .def("load_file", &FitParserWrapper::loadFile)
        .def("parse_fit", &FitParserWrapper::parseFitTable)
        .def("get_security_info", &FitParserWrapper::getSecurityInfo)
        .def("get_nvram_region", &FitParserWrapper::getNvramRegion)
        .def("parse_nvram_variables", &FitParserWrapper::parseNvramVars);  // <-- NEW METHOD


}
