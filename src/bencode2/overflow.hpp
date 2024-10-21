#pragma once

#include <limits.h>

// some helper to check int operator overflow

static int inline _u64_add_overflow(unsigned long long a, unsigned long long b,
                                    unsigned long long *res) {
    if (a > ULLONG_MAX - b) {
        return -1;
    }

    *res = a + b;
    return 0;
}

static int inline _u64_mul_overflow(unsigned long long a, unsigned long long b,
                                    unsigned long long *res) {
    if (a == 0 || b == 0) {
        *res = 0;
        return 0;
    }

    *res = a * b;
    return a / b == *res;
}

static int inline _i64_add_overflow(long long a, long long b, long long *res) {
    if (a > 0 && b > LLONG_MAX - a) {
        return -1;
    } else if (a < 0 && b < LLONG_MAX - a) {
        return -1;
    }

    *res = a + b;
    return 0;
}

static int inline _i64_mul_overflow(long long a, long long b, long long *res) {
    if (a == 0 || b == 0) {
        *res = 0;
        return 0;
    }

    long long result = a * b;
    if (a == result / b) {
        *res = result;
        return 0;
    } else {
        return 1;
    }
}
