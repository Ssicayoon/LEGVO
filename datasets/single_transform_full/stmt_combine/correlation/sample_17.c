stddev[j] = SQRT_FUN(stddev[j]);
stddev[j] = stddev[j] <= eps ? SCALAR_VAL(1.0) : stddev[j];
