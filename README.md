 This repository contains my solutions for the [cryptopals crypto challenges](http://cryptopals.com/).

#### Requirements
 * Some of them use the [PyCrypto](https://www.dlitz.net/software/pycrypto/) library.
 * Challenge 62 (set 8) uses [GMP](https://gmplib.org/) and a [Boost.Python](http://www.boost.org/doc/libs/1_62_0/libs/python/doc/html/index.html) module. Even though it is already compiled here, you may need to install these for compiling it for other platforms (and Python 2.7 headers as well).
   * Copy libraries in `common/math/cpp/bin/` to the system library path before running the challenge.

#### Usage
 * The `run.py` script runs every challenge passed as command-line argument.
 * The `-s` option specifies a comma-separated list of sets to be run.
 * The `-c` option, a comma-separated list of challenges inside the given sets.
 * If any of these options is missing, all sets/challenges will be run.

#### Notes
 * I've also completed [set 8](http://cryptopals.com/sets/8) (including its bonus challenge) but solutions cannot be published yet. Sorry!
