#include "mt19937_solver.h"
#include <cassert>
#include <iostream>

using MT19937::u32;
using MT19937::Bool;
using MT19937::kBits;
using MT19937::kW;

MT19937::Solver solver;
MT19937::MT19937 rng;
int main() {
    solver.add_eq(rng.mt[0], 0x80000000);
    for (size_t i = 0; i < MT19937::kN; ++i) {
        u32 ref;
        std::cin >> ref;
        solver.add_eq(rng.next(), ref);
    }
    Bool init_mt;
    init_mt.set(kBits);
    for (size_t i = kBits; i--;) {
        assert(solver.basis[i][i]);
        init_mt[i] = (init_mt & solver.basis[i]).count() % 2;
    }
    int c = 0;
    std::cin.seekg(0, std::ios::beg);
    rng.reset();
    for (u32 ref; std::cin >> ref; ++c) {
        u32 pred = 0;
        auto tmp = rng.next();
        for (size_t i = 0; i < kW; ++i) {
            pred |= (int)(init_mt & tmp[i]).count() % 2 << i;
        }
        if (pred != ref) std::cout << "!" << c << std::endl;
    }
    std::cout << "OK " << c << " items" << std::endl;
    return 0;
}
