#pragma once

#include "ffi.hpp"

#include <cassert>
#include <iomanip>
#include <iostream>
#include <sstream>
#include <string>

template <int W>
std::string encodeToHexString(const std::string& in)
{
    std::ostringstream out;
    out << std::setfill('0');
    for (unsigned char const& c : in) {
        out << std::hex << std::setw(W) << static_cast<unsigned int>(c);
    }
    return out.str();
}

// conversion byte[N] <-> libsnark bigint.
template <mp_size_t N>
libff::bigint<N> libsnarkBigintFromBytes(const uint8_t* _x)
{
    libff::bigint<N> x;
    for (unsigned i = 0; i < N; i++) {
        for (unsigned j = 0; j < 8; j++) {
            x.data[N - 1 - i] |= uint64_t(_x[i * 8 + j]) << (8 * (7 - j));
        }
    }
    return x;
}

template <mp_size_t N>
std::string hexStringFromLibsnarkBigint(libff::bigint<N> _x)
{
    uint8_t x[N * sizeof(mp_limb_t)];
    for (unsigned i = 0; i < N; i++) {
        for (unsigned j = 0; j < 8; j++) {
            x[i * 8 + j] = uint8_t(uint64_t(_x.data[N - 1 - i]) >> (8 * (7 - j)));
        }
    }
    std::string tmp((char*)x, N * sizeof(mp_limb_t));
    return encodeToHexString<2>(tmp);
}

template <mp_size_t Q>
std::string outputInputAsHex(libff::bigint<Q> _x)
{
    return "\"0x" + hexStringFromLibsnarkBigint<Q>(_x) + "\"";
}

template <mp_size_t Q, typename G1>
std::string outputPointG1AffineAsHexJson(G1 _p)
{
    G1 aff = _p;
    aff.to_affine_coordinates();
    return "[\"0x" + hexStringFromLibsnarkBigint<Q>(aff.X.as_bigint()) + "\",\"0x" + hexStringFromLibsnarkBigint<Q>(aff.Y.as_bigint()) + "\"]";
}

template <mp_size_t Q, typename G2>
std::string outputPointG2AffineAsHexJson(G2 _p)
{
    G2 aff = _p;
    aff.to_affine_coordinates();
    return "[[\"0x" + hexStringFromLibsnarkBigint<Q>(aff.X.c1.as_bigint()) + "\",\"0x" + hexStringFromLibsnarkBigint<Q>(aff.X.c0.as_bigint()) + "\"], [\"0x" + hexStringFromLibsnarkBigint<Q>(aff.Y.c1.as_bigint()) + "\", \"0x" + hexStringFromLibsnarkBigint<Q>(aff.Y.c0.as_bigint()) + "\"]]";
}


template <typename T>
inline void fromBuffer(buffer_t* buffer, T& t)
{
    std::string tmp((char*)buffer->data, buffer->length);
    std::stringstream ss(tmp);
    ss >> t;
}

template <typename T>
inline std::string serialize(const T& t)
{
    std::stringstream ss;
    ss << t;
    return ss.str();
}

template <typename T>
inline buffer_t createBuffer(T& t)
{
    std::string tmp = serialize(t);
    size_t length = tmp.length();

    buffer_t buffer;
    buffer.data = (uint8_t*)malloc(length);
    buffer.length = length;

    tmp.copy(reinterpret_cast<char*>(buffer.data), buffer.length);
    return buffer;
}