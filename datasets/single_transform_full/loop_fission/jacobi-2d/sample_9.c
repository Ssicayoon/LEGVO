for (i = 1; i < _PB_N/2; i++)
    for (j = 1; j < _PB_N - 1; j++)
        A[i][j] = SCALAR_VAL(0.2) * (B[i][j] + B[i][j-1] + B[i][1+j] + B[1+i][j] + B[i-1][j]);
for (i = _PB_N/2; i < _PB_N - 1; i++)
    for (j = 1; j < _PB_N - 1; j++)
        A[i][j] = SCALAR_VAL(0.2) * (B[i][j] + B[i][j-1] + B[i][1+j] + B[1+i][j] + B[i-1][j]);
