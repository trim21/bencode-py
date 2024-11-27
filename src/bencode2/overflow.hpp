#pragma once

#include <stdint.h>

#ifdef _MSC_VER
#define ENABLE_INTSAFE_SIGNED_FUNCTIONS
#include <intsafe.h>
#endif

// some helper to check int operator overflow

static bool inline _i64_add_overflow(int64_t a, int64_t b, int64_t *res) {
#if defined(__GNUC__) or defined(__clang__)
    return __builtin_add_overflow(a, b, res);
#elif defined(_MSC_VER)
    return LongLongAdd(a, b, res);
#else
#error "unknown compiler";
#endif
}

static bool inline _i64_mul_overflow(int64_t a, int64_t b, int64_t *res) {
#if defined(__GNUC__) or defined(__clang__)
    return __builtin_mul_overflow(a, b, res);
#elif defined(_MSC_VER)
    return LongLongMult(a, b, res);
#else
#error "unknown compiler";
#endif
}
