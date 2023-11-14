#include "types.h"
#include <cassert>
namespace MT19937 {
    using namespace Types;

    constexpr u32 kM = 397;
    constexpr u32 MATRIX_A = 0x9908b0df;
    constexpr u32 UPPER_MASK = 0x80000000;
    constexpr u32 LOWER_MASK = 0x7fffffff;

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
            constexpr size_t W = BV32().size();
            for (size_t i = 0; i < kN; ++i) {
                mt[i] = BV32();
                for (size_t j = 0; j < W; ++j) {
                    mt[i][j].set(i * W + j);
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
        BV<k> getrandbits() {
            static_assert(k > 0);
            BV<k> result;
            for (size_t i = 0, j = 0; j < k; ++i) {
                BV32 r = next();
                size_t cw = std::min(r.size(), k - j);
                std::copy(r.end() - cw, r.end(), result.begin() + j);
                j += cw;
            }
            return result;
        }
    };
    struct Solver {
        u32 rank;
        Bool basis[kBits];
        Solver(): rank(0), basis {} {};
        void add_eq(const Bool &eq) {
            if (rank == kBits) return; // speedup
            auto tmp = eq;
            for (size_t i = 0; i < kBits; ++i) {
                if (!tmp[i]) continue;
                if (basis[i][i]) tmp ^= basis[i];
                else return ++rank, basis[i] = tmp, void();
            }
            // singular
            // tmp.count() ==> no solution
        }
        template<size_t k>
        void add_eq(const BV<k> &eqs) {
            for (const Bool &eq : eqs) add_eq(eq);
        }
        template<size_t k>
        void add_eq(const BV<k> &lhs, const BV<k> &rhs) {
            add_eq(lhs ^ rhs);
        }
        void add_eq(const BV32 &lhs, u32 rhs) {
            add_eq(lhs, UInt2BV32(rhs));
        }
        Bool get_solution() const {
            assert(rank == kBits);
            Bool sol; sol.set(kBits);
            for (size_t i = kBits; i--;) {
                assert(basis[i][i]);
                sol[i] = (sol & basis[i]).count() & 1;
            }
            return sol;
        }
    };
}