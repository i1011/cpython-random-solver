#pragma GCC target("avx,avx2")
#include "mt19937_solver.h"
#include <cassert>
#include <fstream>
#include <iostream>

using MT19937::kBits;
MT19937::Solver solver;
MT19937::MT19937 rng;

#include <string>
Types::BV<5> var[128];
bool valid[128];
int main() {
    solver.add_eq(rng.mt[0], 0x80000000);

    std::ifstream in("output.txt");
    std::string s;
    in >> s;
    for (int c : s) {
        auto r = rng.getrandbits<5>();
        rng.next();
        if (valid[c]) {
            solver.add_eq(r, var[c]);
        } else {
            valid[c] = true;
            var[c] = r;
        }
    }
    auto init_mt = solver.get_solution();
    char ans[33] = {};
    for (int i = 0; i < 128; ++i) {
        if (!valid[i]) continue;
        uint32_t pred = 0;
        for (size_t j = 0; j < 5; ++j) {
            pred |= (int)(init_mt & var[i][j]).count() % 2 << j;
        }
        ans[pred] = (char)i;
    }
    std::cout << "EPFL{" << ans << "}" << std::endl;
    return 0;
}
