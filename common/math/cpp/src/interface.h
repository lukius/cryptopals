#ifndef _INTERFACE_H_
#define _INTERFACE_H_

#include <boost/python/list.hpp>

#include "vector.h"

#include <gmpxx.h>

typedef std::vector<vec_q> basis_q;
typedef boost::python::list list;


list basis_reduction(const list&);
list orthogonalize(const list&);

vec_q _list_to_cxx(const list&);
list _vec_to_py(const vec_q&);

basis_q _to_cxx(const list&);
list _to_py(const basis_q&);


#endif
