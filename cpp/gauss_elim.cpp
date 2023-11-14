#include <cassert>
#include <array>
#include <bitset>
#include <iostream>

constexpr size_t kW = 32, kN = 624, kM = 397, kBits = kN * kW;

using u32 = uint32_t;
using Bool = std::bitset<kBits + 1>;
template<size_t W>
using BV = std::array<Bool, W>;
using BV32 = BV<32>;

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
template<size_t W>
BV<W>& operator^=(BV<W> &x, const BV<W> &y) {
    for (size_t i = 0; i < kW; ++i) x[i] ^= y[i];
    return x;
}
template<size_t W>
BV<W> operator^(const BV<W> &x, const BV<W> &y) {
    auto r = x;
    return r ^= y;
}
template<size_t W>
BV<W> operator>>(const BV<W> &x, u32 w) {
    BV32 r;
    for (size_t i = w; i < kW; ++i) r[i - w] = x[i];
    return r;
}
template<size_t W>
BV<W> operator<<(const BV<W> &x, u32 w) {
    BV<W> r;
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
    void reset() {
        for (size_t i = 0; i < kN; ++i) {
            mt[i] = BV32();
            for (size_t j = 0; j < kW; ++j) {
                mt[i][j].set(i * kW + j);
            }
        }
        index = kN;
    }
    MT19937() { reset(); }
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
    u32 rank;
    std::bitset<kBits + 1> basis[kBits];
    Solver(): rank(0), basis {} {};
    void add_eq(const Bool &lhs, bool rhs) {
        if (rank == kBits) return;
        auto tmp = lhs; tmp[kBits] = rhs;
        for (size_t i = 0; i < kBits; ++i) {
            if (!tmp[i]) continue;
            if (basis[i][i]) tmp ^= basis[i];
            else return ++rank, basis[i] = tmp, void();
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
MT19937 rng;
int main() {
    solver.add_eq(rng.mt[0], 0x80000000);
    for (size_t i = 0; i < kN; ++i) {
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
