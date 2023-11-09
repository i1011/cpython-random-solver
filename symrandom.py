from mt19937 import MT19937 as _mt19937_impl
from z3 import BitVec, BitVecRef, Concat, Extract

class SymRandom():

    def __init__(self, solver=None):
        self.mt = [BitVec(0x80000000 - 1, 32) + 1] + [BitVec(f"init_mt_{i}", 32) for i in range(1, 624)]
        self._rng = _mt19937_impl()
        self._rng.setstate(self.mt + [624])

    def random(self):
        """Get the next random number in the range 0.0 <= X < 1.0."""
        a = Extract(31, 5, self._rng.genrand_uint32())
        b = Extract(31, 6, self._rng.genrand_uint32())
        return Concat(a, b)

    def getrandbits(self, k: int):
        """getrandbits(k) -> x.  Generates an int with k random bits."""
        if k < 0:
            raise ValueError('number of bits must be non-negative')
        if k == 0:
            return 0
        words = (k - 1) // 32 + 1
        result = None
        for _ in range(words):
            r = self._rng.genrand_uint32()
            assert isinstance(r, BitVecRef)
            if k < 32:
                r = Extract(31, 32 - k, r)
            result = r if result is None else Concat(r, result)
            k -= 32
        return result
    '''

    def seed(self, a):
        if a == None:
            return
        if isinstance(a, int):
            self.init_key = []
            while a != 0:
                self.init_key.append(a % 2 ** 32)
                a //= 2 ** 32
        elif isinstance(a, list) and all(isinstance(x, BitVecRef) and x.size() == 32 for x in a):
            self.init_key = a
        else:
            raise TypeError('The only supported seed types are: int, List[z3.BitVec(32)] and None.')
        
        if len(self.init_key) == 0:
            self.init_key = [0]
        self._rng.init_by_array(self.init_key)
        return
    '''

from z3 import Solver, sat
import random

def test_getrandbits(n: int, w: int):
    seed = random.getrandbits(32)
    print(f"- Test: getrandbits({w})")
    print(f"    - {n} elements")
    print(f"    - seed: {seed}")
    random.seed(seed)
    refs = [random.getrandbits(w) for _ in range(n)]
    sol = Solver()
    rng = SymRandom()
    for ref in refs:
        sol.add(rng.getrandbits(w) == ref)
    assert sol.check() == sat
    m = sol.model()
    state = [m.evaluate(s).as_long() for s in rng.mt]
    random.setstate((3, tuple(state + [624]), None))
    for ref in refs:
        assert(random.getrandbits(w) == ref)

def test_random(n: int):
    seed = random.getrandbits(32)
    print(f"- Test: random")
    print(f"    - {n} elements")
    print(f"    - seed: {seed}")
    random.seed(seed)
    refs = [random.random() for _ in range(n)]
    sol = Solver()
    rng = SymRandom()
    for ref in refs:
        sol.add(rng.random() == int(ref * 2 ** 53))
    assert sol.check() == sat
    m = sol.model()
    state = [m.evaluate(s).as_long() for s in rng.mt]
    random.setstate((3, tuple(state + [624]), None))
    for ref in refs:
        assert(random.random() == ref)

if __name__ == '__main__':
    test_random(200)
    test_getrandbits(625, 32)
    test_getrandbits(180, 100)
    # test_getrandbits(624 * 8, 4)
