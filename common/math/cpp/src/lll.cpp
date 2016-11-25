#include "lll.h"
#include <gmpxx.h>
#include <algorithm>
#include <iostream>

#define LLL_DELTA 0.9999


basis_q GS_orthogonalize(const basis_q& B)
{
	basis_q Q;
	size_t n = B[0].size();
	vec_q w(n);

	for(size_t i = 0; i < B.size(); ++i)
	{
		vec_q u(n);
		for(size_t j = 0; j < i; ++j)
			u = u.add(projection(Q[j], B[i]));
		w = B[i].sub(u);
		Q.push_back(w);
	}

	return Q;
}

vec_q projection(const vec_q &u, const vec_q &v)
{
    if(u.is_null())
        return u;
    mpq_class x(v.dot(u) / u.norm_squared());
    x.canonicalize();
    return u.scalar_mul(x);
}

mpq_class _mu(const vec_q &u, const vec_q &v)
{
	mpq_class m(v.dot(u) / v.norm_squared());
	return m;
}

mpz_class _round(const mpq_class &x)
{
	mpz_class rounded = abs(x.get_num() / x.get_den());

	if(abs(x)-abs(rounded) >= 0.5)
		rounded++;
	return rounded * sgn(x);
}

vec_q _sum_proj(const vec_q &v, ssize_t i, const basis_q &Q)
{
	vec_q p;
	std::vector<mpq_class> w(v.size());

	for(size_t j = 0; j < i; ++j)
	{
		p = projection(Q[j], v);
		for(size_t k = 0; k < v.size(); ++k)
			w[k] += p[k];
	}

	return v.sub(w);
}

void LLL_basis_reduction(basis_q &B)
{
	basis_q Q = GS_orthogonalize(B);
	ssize_t k = 1;
	mpq_class mu, a, b;
	vec_q temp;

	while(k < B.size())
	{
		for(ssize_t j = k-1; j >= 0; j--)
		{
			mu = _mu(B[k], Q[j]);
			if(abs(mu) > 0.5)
			{
				B[k] = B[k].sub(B[j].scalar_mul(_round(mu)));
				for(ssize_t i = k; i < Q.size(); ++i)
					Q[i] = _sum_proj(B[i], i, Q);
			}
		}

		a = Q[k].norm_squared();
		mu = _mu(B[k], Q[k-1]);
		b = (LLL_DELTA - mu*mu) * Q[k-1].norm_squared();
		if(a >= b)
			k++;
		else
		{
			temp = B[k];
			B[k] = B[k-1];
			B[k-1] = temp;

			for(ssize_t i = k-1; i < Q.size(); ++i)
				Q[i] = _sum_proj(B[i], i, Q);

			k = std::max(k-1, (ssize_t)1);
		}
	}
}
