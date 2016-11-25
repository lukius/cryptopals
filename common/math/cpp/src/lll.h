#ifndef _LLL_H_
#define _LLL_H_

#include "interface.h"

#include <boost/python/list.hpp>


basis_q GS_orthogonalize(const basis_q&);
vec_q projection(const vec_q&, const vec_q&);
void LLL_basis_reduction(basis_q&);

mpz_class _round(const mpq_class&);
mpq_class _mu(const vec_q&, const vec_q&);
vec_q _sum_proj(const vec_q&, ssize_t i, const basis_q&);

#endif
