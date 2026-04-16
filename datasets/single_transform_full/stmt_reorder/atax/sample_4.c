tmp[i] = SCALAR_VAL(0.0);
for (j = 0; j < _PB_N; j++)
    tmp[i] = tmp[i] + A[i][j] * x[j];
for (j = 0; j < _PB_N; j++)
    y[j] = y[j] + A[i][j] * tmp[i];
