from z3 import BitVec, Solver, sat
from mt19937 import N, shr, MT19937 as _mt19937_impl

def init_by_array_backward(mt, init_key, solver: Solver):
    mt = list(mt)
    key_length = len(init_key)
    i, j = 1, 0
    for _ in range(max(N, key_length), 0, -1):
        i, j = i + 1, j + 1
        if i >= N: i = 1
        if j >= key_length: j = 0
    for _ in range(N - 1, 0, -1):
        i += 1
        if i >= N: i = 1
    assert mt[0] == 0x80000000
    t = 0
    def new_mt0():
        nonlocal t
        t += 1
        return BitVec(f'mt0_{t}', 32)
    mt[0] = new_mt0()
    for _ in range(1, N):
        if i == 1:
            mt[N - 1], i = mt[0], N
            mt[0] = new_mt0()
        i -= 1
        mt[i] = ((mt[i] + i) ^ ((mt[i - 1] ^ shr(mt[i - 1], 30)) * 1566083941)) % 2 ** 32
    for _ in range(1, max(N, key_length) + 1):
        if j == 0:
            j = key_length
        if i == 1:
            mt[N - 1], i = mt[0], N
            mt[0] = new_mt0()
        i, j = i - 1, j - 1
        mt[i] = (mt[i] - init_key[j] - j) % 2 ** 32
        mt[i] ^= (mt[i - 1] ^ shr(mt[i - 1], 30)) * 1664525 % 2 ** 32
    assert i == 1 and j == 0
    _rng = _mt19937_impl()
    _rng.init_genrand(19650218)
    state = _rng.getstate()
    for i in range(624):
        solver.add(state[i] == mt[i])

def test_init_by_array(init_key):
    print(f"- Test: init_by_array")
    print(f"    - init_key: {init_key}")
    rng = _mt19937_impl()
    rng.init_by_array(init_key)
    key = [BitVec(f'key_{i}', 32) for i in range(len(init_key))]
    solver = Solver()
    init_by_array_backward(rng.getstate()[:N], key, solver)
    assert solver.check() == sat
    m = solver.model()
    key = [m.evaluate(k).as_long() for k in key]
    assert init_key == key

if __name__ == '__main__':
    test_init_by_array([100, 200])
    test_init_by_array([2 ** 31 - 1])
    test_init_by_array([2 ** 32 - 1])
    import random
    test_init_by_array([random.randrange(2 ** 32) for _ in range(10)])