#pragma once

#include <stdint.h>
#if defined(_MSC_VER)
#include <intsafe.h>
#endif

// some helper to check int operator overflow

static int inline _i64_add_overflow(int64_t a, int64_t b, int64_t *res) {
#if defined(__GNUC__) or defined(__clang__)
    return __builtin_add_overflow(a, b, res);
#elif defined(_MSC_VER)
    return IntAdd(a, b, res);
#else
#error "unknown compiler";
#endif
}

static int inline _i64_mul_overflow(int64_t a, int64_t b, int64_t *res) {
#if defined(__GNUC__) or defined(__clang__)
    return __builtin_mul_overflow(a, b, res);
#elif defined(_MSC_VER)
    return IntMult(a, b, res);
#else
#error "unknown compiler";
#endif
}
