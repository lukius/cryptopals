#ifndef _VECTOR_H_
#define _VECTOR_H_

#include <vector>
#include <gmpxx.h>

typedef std::vector<mpq_class> vector_q;


class vec_q
{
public:
	vec_q();
	vec_q(size_t);
	vec_q(const vec_q&);

	mpq_class dot(const vec_q&) const;
	vec_q scalar_mul(const mpq_class&) const;
	vec_q add(const vec_q&) const;
	vec_q sub(const vec_q&) const;
	vec_q sub(const std::vector<mpq_class>&) const;
	mpq_class norm_squared() const;
	size_t size() const;
	bool is_null() const;

	mpq_class &operator[](size_t);
	const mpq_class &operator[](size_t) const;

private:
	vector_q v;
	mpq_class norm_sq;
	size_t n;
};

#endif
