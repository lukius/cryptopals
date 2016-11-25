#include "vector.h"
#include <cassert>


vec_q::vec_q()
{
	this->n = 0;
	this->norm_sq = 0;
}

vec_q::vec_q(size_t n) : v(n)
{
	this->norm_sq = 0;
	this->n = n;
}

vec_q::vec_q(const vec_q& u)
{
	this->v = u.v;
	this->norm_sq = u.norm_sq;
	this->n = u.n;
}

mpq_class vec_q::dot(const vec_q& u) const
{
	if (this == &u)
		return this->norm_sq;

	mpq_class result = 0;
	for(size_t i = 0; i < this->n; ++i)
		result += this->v[i] * u[i];

	return result;
}

vec_q vec_q::scalar_mul(const mpq_class& x) const
{
	vec_q result(this->n);

	for(size_t i = 0; i < this->n; ++i)
		result[i] = x * this->v[i];

	result.norm_sq = this->norm_sq * x * x;

	return result;
}

vec_q vec_q::add(const vec_q& u) const
{
	assert(u.n == this->n);

	vec_q result(this->n);
	mpq_class b = 0, x;

	for(size_t i = 0; i < this->n; ++i)
	{
		x = this->v[i] + u[i];
		result[i] = x;
		b += x*x;
	}
	result.norm_sq = b;

	return result;
}

vec_q vec_q::sub(const vec_q& u) const
{
	assert(u.n == this->n);

	vec_q result(this->n);
	mpq_class b = 0, x;

	for(size_t i = 0; i < this->n; ++i)
	{
		x = this->v[i] - u[i];
		result[i] = x;
		b += x*x;
	}
	result.norm_sq = b;

	return result;
}

vec_q vec_q::sub(const std::vector<mpq_class>& u) const
{
	assert(u.size() == this->n);

	vec_q result(this->n);
	mpq_class b = 0, x;

	for(size_t i = 0; i < this->n; ++i)
	{
		x = this->v[i] - u[i];
		result[i] = x;
		b += x*x;
	}
	result.norm_sq = b;

	return result;
}

mpq_class vec_q::norm_squared() const
{
	return this->norm_sq;
}

size_t vec_q::size() const
{
	return this->n;
}

bool vec_q::is_null() const
{
	for(size_t i = 0; i < this->n; ++i)
		if(this->v[i] != 0)
			return false;
	return true;
}

mpq_class &vec_q::operator[](size_t i)
{
	assert(i >= 0 && i < this->n);
	return this->v[i];
}

const mpq_class &vec_q::operator[](size_t i) const
{
	assert(i >= 0 && i < this->n);
	return this->v[i];
}
