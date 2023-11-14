#include <cassert>
#include <array>
#include <bitset>
#include <iostream>
#include <random>

constexpr size_t kW = 32, kN = 624, kM = 397, kBits = kN * kW;

using u32 = uint32_t;
using Bool = std::bitset<kBits + 1>;
using BV32 = std::array<Bool, kW>;

Bool operator&(const Bool &x, bool v) {
    return v ? x : Bool();
}
constexpr u32 MATRIX_A = 0x9908b0df;
constexpr u32 UPPER_MASK = 0x80000000;
constexpr u32 LOWER_MASK = 0x7fffffff;

BV32 operator&(const BV32 &x, u32 v) {
    BV32 r;
    for (size_t i = 0; i < kW; ++i) r[i] = x[i] & ((v >> i) & 1);
    return r;
}
BV32 operator|(const BV32 &x, const BV32 &y) {
    BV32 r;
    for (size_t i = 0; i < kW; ++i) r[i] = x[i] | y[i];
    return r;
}
BV32& operator^=(BV32 &x, const BV32 &y) {
    for (size_t i = 0; i < kW; ++i) x[i] ^= y[i];
    return x;
}
BV32 operator^(const BV32 &x, const BV32 &y) {
    BV32 r = x;
    return r ^= y;
}
BV32 operator>>(const BV32 &x, u32 w) {
    assert(w <= kW);
    BV32 r;
    for (size_t i = w; i < kW; ++i) r[i - w] = x[i];
    return r;
}
BV32 operator<<(const BV32 &x, u32 w) {
    assert(w <= kW);
    BV32 r;
    for (size_t i = w; i < kW; ++i) r[i] = x[i - w];
    return r;
}
BV32 mat_a(const BV32 &x) {
    BV32 r;
    r.fill(x[0]);
    return r & MATRIX_A;
}

struct MT19937 {
    BV32 mt[kN];
    u32 index;
    void update_mt() {
        for (size_t kk = 0; kk < kN; ++kk) {
            auto y = (mt[kk] & UPPER_MASK) | (mt[(kk + 1) % kN] & LOWER_MASK);
            mt[kk] = mt[(kk + kM) % kN] ^ (y >> 1) ^ mat_a(y);
        }
    }
    MT19937() {
        for (size_t i = 0; i < kN; ++i) {
            mt[i] = BV32();
            for (size_t j = 0; j < kW; ++j) {
                mt[i][j].set(i * kW + j);
            }
        }
        index = 226;
    }
    BV32 next() {
        if (index >= kN) update_mt(), index = 0;
        auto y = mt[index++];
        y ^= y >> 11;
        y ^= (y << 7) & 0x9d2c5680;
        y ^= (y << 15) & 0xefc60000;
        y ^= y >> 18;
        return y;
    }
    template<size_t k>
    std::array<Bool, k> getrandbits() {
        static_assert(k > 0);
        std::array<Bool, k> result;
        for (size_t i = 0, j = 0; j < k; ++i) {
            BV32 r = next();
            size_t cw = std::min(kW, k - j);
            std::copy(r.end() - cw, r.end(), result.begin() + j);
            j += cw;
        }
        return result;
    }
};
using Eq = std::bitset<kBits + 1>;
struct Solver {
    std::bitset<kBits + 1> basis[kBits];
    void add_eq(const Bool &lhs, bool rhs) {
        auto tmp = lhs; tmp[kBits] = rhs;
        for (size_t i = 0; i < kBits; ++i) {
            if (!tmp[i]) continue;
            if (basis[i][i]) tmp ^= basis[i];
            else return basis[i] = tmp, void();
        }
        // singular
    }
    template<size_t k>
    void add_eq(const std::array<Bool, k> &lhs, const std::bitset<k> &rhs) {
        for (size_t i = 0; i < k; ++i) add_eq(lhs[i], rhs[i]);
    }
    void add_eq(const BV32 &lhs, u32 rhs) {
        add_eq(lhs, std::bitset<32>(rhs));
    }
} solver;
MT19937 test;
int main() {
    std::mt19937 rng(12345);
    solver.add_eq(test.mt[0], 0x80000000);
    for (size_t i = 0; i < kN; ++i) {
        solver.add_eq(test.next(), (u32)rng());
    }
    Bool init_mt;
    init_mt.set(kBits);
    for (size_t i = kBits; i--;) {
        assert(solver.basis[i][i]);
        init_mt[i] = (init_mt & solver.basis[i]).count() % 2;
    }
    for (int i = 0; i < 1000; ++i) {
        u32 pred = 0, ref = (u32)rng();
        auto tmp = test.next();
        for (size_t i = 0; i < kW; ++i) {
            pred |= (int)(init_mt & tmp[i]).count() % 2 << i;
        }
        assert(pred == ref);
    }
    return 0;
}
