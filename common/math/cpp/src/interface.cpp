#include "interface.h"
#include "lll.h"
#include "vector.h"

#include <string>
#include <gmpxx.h>

#include <boost/python/list.hpp>
#include <boost/python/tuple.hpp>
#include <boost/python/extract.hpp>

using namespace boost::python;


list orthogonalize(const list &l)
{
    basis_q B = _to_cxx(l);
    basis_q Q = GS_orthogonalize(B);
    list result = _to_py(Q);
    return result;
}

list basis_reduction(const list &l)
{
    basis_q B = _to_cxx(l);
    LLL_basis_reduction(B);
    list result = _to_py(B);
    return result;
}

vec_q _list_to_cxx(const list& l)
{
	vec_q v(len(l));
	tuple pair;
	mpz_class num, den;
	std::string num_str, den_str;

	for(ssize_t i = 0; i < len(l); ++i)
	{
		pair = extract<tuple>(l[i]);
		num_str = extract<std::string>(pair[0]);
		den_str = extract<std::string>(pair[1]);
		num = mpz_class(num_str);
		den = mpz_class(den_str);
		mpq_class b(num, den);
		b.canonicalize();
		v[i] = b;
	}

	return v;
}

basis_q _to_cxx(const list& l)
{
	basis_q B;
	vec_q v;
	list l_i;

	for(ssize_t i = 0; i < len(l); ++i)
	{
		l_i = extract<list>(l[i]);
		v = _list_to_cxx(l_i);
		B.push_back(v);
	}

	return B;
}

list _vec_to_py(const vec_q& v)
{
	list l;
	tuple pair;
	mpz_class num, den;
	std::string num_str, den_str;

	for(size_t i = 0; i < v.size(); ++i)
	{
		num = v[i].get_num();
		den = v[i].get_den();
		num_str = num.get_str();
		den_str = den.get_str();
		pair = make_tuple(num_str, den_str);
		l.append(pair);
	}

	return l;
}

list _to_py(const basis_q& B)
{
	list v, result;

	for(size_t i = 0; i < B.size(); ++i)
	{
		v = _vec_to_py(B[i]);
		result.append(v);
	}

	return result;
}
