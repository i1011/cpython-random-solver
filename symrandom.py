from mt19937 import MT19937 as _mt19937_impl
from z3 import (
    BitVec, BitVecRef, Concat, Extract,
    Solver, sat, simplify,
    IntVal, Int2BV
)

class SymRandom():

    def __init__(self, *, seed=None, solver: (Solver|None) = None):
        self.solver = solver if solver else Solver()
        self.seed(seed)

    def seed(self, a=None):
        if a is None:
            self.init_key = None
        elif isinstance(a, BitVecRef) and a.size() == 32:
            self.init_key = [a]
        elif isinstance(a, list) and all(isinstance(x, BitVecRef) and x.size() == 32 for x in a):
            if len(a) == 0:
                raise ValueError('seed is an empty list')
            self.init_key = a[:]
        else:
            raise TypeError('The only supported seed types are: z3.BitVec(32), List[z3.BitVec(32)] and None.')

        self._rng = _mt19937_impl()
        self.solver.reset()
        self.ts = 0
        self.init_mt = [Int2BV(IntVal(0x80000000), 32)] + [BitVec(f"init_mt_{i}", 32) for i in range(1, 624)]
        self._rng.setstate(self.init_mt + [624])

    def seed_recovery_slow(self, mt):
        self._rng.init_by_array(self.init_key)
        state = self._rng.getstate()
        for i in range(624):
            self.solver.add(state[i] == mt[i])
    
    def seed_recovery_fast(self, mt):
        from mt19937_backward import init_by_array_backward
        init_by_array_backward(mt, self.init_key, self.solver)

    def solve(self, fast_seed_recovery=True):
        status = self.solver.check()
        if status != sat:
            return (status, None, None)
        m = self.solver.model()
        mt = [m.evaluate(s).as_long() for s in self.init_mt]
        if self.init_key is None:
            return (sat, mt, None)

        self.solver.reset()
        if fast_seed_recovery: self.seed_recovery_fast(mt)
        else: self.seed_recovery_slow(mt)
        status = self.solver.check()
        if status != sat:
            return (status, mt, None)
        m = self.solver.model()
        seed = [m.evaluate(s).as_long() for s in self.init_key]
        return (status, mt, seed)

    def add_dummy_vars(self):
        self.ts += 1
        state = self._rng.getstate()
        dummy = [BitVec(f"dummy{self.ts}_{i}", 32) for i in range(624)]
        for i in range(624):
            self.solver.add(state[i] == dummy[i])
        self._rng.setstate(dummy + [state[-1]])

    def next(self):
        r = self._rng.genrand_uint32()
        if self._rng.sig_mtupdate:
            self._rng.sig_mtupdate = False
            self.add_dummy_vars()
        return simplify(r)

    def random(self):
        """Get the next random number in the range 0.0 <= X < 1.0."""
        a = Extract(31, 5, self.next()) # a: BitVec(27)
        b = Extract(31, 6, self.next()) # b: BitVec(26)
        return simplify(Concat(a, b)) # (a << 27 | b): BitVec(53)

    def getrandbits(self, k: int):
        """getrandbits(k) -> x.  Generates an int with k random bits."""
        if k < 0:
            raise ValueError('number of bits must be non-negative')
        if k == 0:
            return 0
        words = (k - 1) // 32 + 1
        result = None
        for _ in range(words):
            r = self.next()
            assert isinstance(r, BitVecRef)
            if k < 32:
                r = Extract(31, 32 - k, r)
            result = r if result is None else Concat(r, result)
            k -= 32
        return simplify(result)

from z3 import sat
import random

def test_getrandbits(n: int, w: int):
    seed = random.getrandbits(32)
    print(f"- Test: getrandbits({w})")
    print(f"    - {n} elements")
    print(f"    - seed: {seed}")
    random.seed(seed)
    init_state = list(random.getstate()[1][:624])
    refs = [random.getrandbits(w) for _ in range(n)]
    sol = Solver()
    rng = SymRandom(solver=sol)
    for ref in refs:
        sol.add(rng.getrandbits(w) == ref)
    from z3 import simplify
    result, state, _ = rng.solve()
    assert result == sat
    random.setstate((3, tuple(state + [624]), None))
    for ref in refs:
        assert(random.getrandbits(w) == ref)
    assert(state == init_state)

def test_random(n: int):
    seed = random.getrandbits(32)
    print(f"- Test: random")
    print(f"    - {n} elements")
    print(f"    - seed: {seed}")
    random.seed(seed)
    init_state = list(random.getstate()[1][:624])
    refs = [random.random() for _ in range(n)]
    sol = Solver()
    rng = SymRandom(solver=sol)
    for ref in refs:
        sol.add(rng.random() == int(ref * 2 ** 53))
    result, state, _ = rng.solve()
    assert result == sat
    random.setstate((3, tuple(state + [624]), None))
    for ref in refs:
        assert(random.random() == ref)
    assert(state == init_state)

def test_seed(n: int, w: int, seed: int, fast_seed_recovery: bool):
    print(f"- Test: seed recovery")
    print(f"    - {n} elements, {w}-bit")
    print(f"    - seed: {seed}")
    print(f"    - fast_seed_recovery: {fast_seed_recovery}")
    random.seed(seed)
    init_state = list(random.getstate()[1][:624])
    refs = [random.getrandbits(w) for _ in range(n)]
    sol = Solver()
    rng = SymRandom(solver=sol)
    rng.seed([BitVec(f'seed', 32)])
    for ref in refs:
        sol.add(rng.getrandbits(w) == ref)
    result, state, s = rng.solve(fast_seed_recovery)
    assert result == sat
    assert state == init_state
    assert s[0] == abs(seed)

if __name__ == '__main__':
    test_getrandbits(624, 32)
    test_getrandbits(700, 32)
    test_getrandbits(500, 100)
    test_random(1248)
    test_seed(1248, 21, -1, True)
    test_seed(624, 32, 0, True)
    test_seed(624, 32, 0, False)
