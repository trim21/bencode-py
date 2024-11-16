#pragma once

#include <stdint.h>

#include <safe-math/safe-math.h>

// some helper to check int operator overflow

static int inline _i64_add_overflow(int64_t a, int64_t b, int64_t *res) {
    return psnip_safe_int64_add(res, a, b);
}

static int inline _i64_mul_overflow(int64_t a, int64_t b, int64_t *res) {
    return psnip_safe_int64_mul(res, a, b);
}
