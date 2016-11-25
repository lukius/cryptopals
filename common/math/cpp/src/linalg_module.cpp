#include <boost/python/module.hpp>
#include <boost/python/def.hpp>
#include <string>

#include "interface.h"


BOOST_PYTHON_MODULE(cxx_linalg)
{
    boost::python::def("basis_reduction", basis_reduction);
    boost::python::def("orthogonalize", orthogonalize);
}
