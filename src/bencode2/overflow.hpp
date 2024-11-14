#pragma once

#include <limits.h>

#include "safe-int/safeint.h"

// some helper to check int operator overflow

static int inline _u64_add_overflow(uint64_t a, uint64_t b, uint64_t *res) {
    if (a > ULLONG_MAX - b) {
        return -1;
    }

    *res = a + b;
    return 0;
}

static int inline _u64_mul_overflow(uint64_t a, uint64_t b, uint64_t *res) {
    if (a == 0 || b == 0) {
        *res = 0;
        return 0;
    }

    *res = a * b;
    return a / b == *res;
}

static int inline _i64_add_overflow(int64_t a, int64_t b, int64_t *res) {
    return psnip_safe_int64_add(res, a, b);
}

static int inline _i64_mul_overflow(int64_t a, int64_t b, int64_t *res) {
    return psnip_safe_int64_mul(res, a, b);
}
