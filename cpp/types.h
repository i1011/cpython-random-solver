#include <array>
#include <bitset>
#include <ranges>

namespace Types {
    constexpr size_t kW = 32, kN = 624, kBits = kN * kW;
    using u32 = uint32_t;
    using Bool = std::bitset<kBits + 1>;
    template<size_t W>
    using BV = std::array<Bool, W>;
    using BV32 = BV<32>;

    Bool operator&(const Bool &x, bool v) {
        return v ? x : Bool();
    }

    const auto BV32_index_view = std::ranges::iota_view((size_t)0, BV32().size());

    BV32 operator&(const BV32 &x, u32 v) {
        BV32 r;
        for (size_t i : BV32_index_view) r[i] = x[i] & (v & 1), v >>= 1;
        return r;
    }
    BV32 operator|(const BV32 &x, const BV32 &y) {
        BV32 r;
        for (size_t i : BV32_index_view) r[i] = x[i] | y[i];
        return r;
    }
    BV32 UInt2BV32(u32 x) {
        BV32 r;
        for (auto &ri : r) ri[kBits] = x & 1, x >>= 1;
        return r;
    }
    template<size_t W>
    BV<W>& operator^=(BV<W> &x, const BV<W> &y) {
        for (size_t i = 0; i < W; ++i) x[i] ^= y[i];
        return x;
    }
    template<size_t W>
    BV<W> operator^(const BV<W> &x, const BV<W> &y) {
        auto r = x;
        return r ^= y;
    }
    template<size_t W>
    BV<W> operator>>(const BV<W> &x, u32 shift) {
        BV32 r;
        for (size_t i = shift; i < W; ++i) r[i - shift] = x[i];
        return r;
    }
    template<size_t W>
    BV<W> operator<<(const BV<W> &x, u32 shift) {
        BV<W> r;
        for (size_t i = shift; i < W; ++i) r[i] = x[i - shift];
        return r;
    }
}