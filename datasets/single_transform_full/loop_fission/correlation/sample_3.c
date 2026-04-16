for (j = 0; j < _PB_M; j++)
{
    data[i][j] -= mean[j];
    data[i][j] /= SQRT_FUN(float_n) * stddev[j];
}
