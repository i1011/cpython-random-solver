# Translated from https://github.com/python/cpython/blob/main/Modules/_randommodule.c
'''
/* ------------------------------------------------------------------
   The code in this module was based on a download from:
      http://www.math.sci.hiroshima-u.ac.jp/~m-mat/MT/MT2002/emt19937ar.html

   It was modified in 2002 by Raymond Hettinger as follows:

    * the principal computational lines untouched.

    * renamed genrand_res53() to random_random() and wrapped
      in python calling/return code.

    * genrand_uint32() and the helper functions, init_genrand()
      and init_by_array(), were declared static, wrapped in
      Python calling/return code.  also, their global data
      references were replaced with structure references.

    * unused functions from the original were deleted.
      new, original C python code was added to implement the
      Random() interface.

   The following are the verbatim comments from the original code:

   A C-program for MT19937, with initialization improved 2002/1/26.
   Coded by Takuji Nishimura and Makoto Matsumoto.

   Before using, initialize the state by using init_genrand(seed)
   or init_by_array(init_key, key_length).

   Copyright (C) 1997 - 2002, Makoto Matsumoto and Takuji Nishimura,
   All rights reserved.

   Redistribution and use in source and binary forms, with or without
   modification, are permitted provided that the following conditions
   are met:

     1. Redistributions of source code must retain the above copyright
    notice, this list of conditions and the following disclaimer.

     2. Redistributions in binary form must reproduce the above copyright
    notice, this list of conditions and the following disclaimer in the
    documentation and/or other materials provided with the distribution.

     3. The names of its contributors may not be used to endorse or promote
    products derived from this software without specific prior written
    permission.

   THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS
   "AS IS" AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT
   LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR
   A PARTICULAR PURPOSE ARE DISCLAIMED.  IN NO EVENT SHALL THE COPYRIGHT OWNER OR
   CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL,
   EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO,
   PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR
   PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF
   LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING
   NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS
   SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.


   Any feedback is very welcome.
   http://www.math.sci.hiroshima-u.ac.jp/~m-mat/MT/emt.html
   email: m-mat @ math.sci.hiroshima-u.ac.jp (remove space)
*/
'''
#


from z3 import LShR, BitVecRef
def shr(x: (int | BitVecRef), shift: int):
    if isinstance(x, BitVecRef):
        return LShR(x, shift)
    return x >> shift

N, M = 624, 397
MATRIX_A = 0x9908b0df # constant vector a
UPPER_MASK = 0x80000000 # most significant w-r bits
LOWER_MASK = 0x7fffffff # least significant r bits

class MT19937():

    def __init__(self):
        self.index = 0
        self.state = [0] * N
    
    def _update_mt(self):
        mt = self.state
        for kk in range(N):
            y = (mt[kk] & UPPER_MASK) | (mt[(kk + 1) % N] & LOWER_MASK)
            mt[kk] = mt[(kk + M) % N] ^ shr(y, 1) ^ (y % 2)* MATRIX_A

    def genrand_uint32(self):
        if self.index >= N:
            self._update_mt()
            self.index = 0
        y = self.state[self.index]
        self.index += 1
        y ^= shr(y, 11)
        y ^= (y << 7) & 0x9d2c5680
        y ^= (y << 15) & 0xefc60000
        y ^= shr(y, 18)
        return y
    
    def init_genrand(self, s: int):
        """initializes mt[N] with a seed"""
        assert isinstance(s, int)
        mt = self.state
        mt[0] = s
        for mti in range(1, N):
            mt[mti] = (1812433253 * (mt[mti - 1] ^ shr(mt[mti - 1], 30)) + mti) % 2 ** 32
        self.index = N

    def init_by_array(self, init_key):
        """initialize by an array with array-length"""
        key_length = len(init_key)
        mt = self.state
        self.init_genrand(19650218)
        i, j = 1, 0
        for _ in range(max(N, key_length), 0, -1):
            mt[i] = ((mt[i] ^ ((mt[i - 1] ^ shr(mt[i - 1], 30)) * 1664525)) + init_key[j] + j) % 2 ** 32
            i, j = i + 1, j + 1
            if i >= N:
                mt[0], i = mt[N - 1], 1
            if j >= key_length:
                j = 0
        for _ in range(N - 1, 0, -1):
            mt[i] = ((mt[i] ^ ((mt[i - 1] ^ shr(mt[i - 1], 30)) * 1566083941)) - i) % 2 ** 32
            i += 1
            if i >= N:
                mt[0], i = mt[N - 1], 1
        mt[0] = 0x80000000

import random
from typing import List
def test_state(n: int):
    print("- Test: internal state")
    print(f"    - {n} elements")
    rng = MT19937()
    state = list(random.getstate()[1])
    rng.state, rng.index = state[:624], state[-1]
    for x in range(n):
        assert rng.genrand_uint32() == random.getrandbits(32)
        assert rng.state + [rng.index] == list(random.getstate()[1])

def test_seed(n: int, seeds: List[int]):
    print("- Test: init by seed")
    print(f"    - {n} elements")
    for seed in seeds:
        print(f"    - seed: {hex(seed)}")
        random.seed(seed)
        key = []
        seed = abs(seed)
        while seed:
            key.append(seed % 2 ** 32)
            seed >>= 32
        if len(key) == 0:
            key = [0]
        rng = MT19937()
        rng.init_by_array(key)
        for x in range(n):
            assert rng.genrand_uint32() == random.getrandbits(32)
            assert rng.state + [rng.index] == list(random.getstate()[1])

if __name__ == '__main__':
    test_state(1000)
    seeds = [0, 2 ** 32 - 1] + [random.randrange(2 ** random.randrange(100)) for _ in range(5)]
    test_seed(1000, seeds)
    seeds = [-1, -2 ** 100]
    test_seed(1000, seeds)
